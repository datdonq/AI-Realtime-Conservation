from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
from services.llm import LLM
from fastapi import APIRouter, Depends, HTTPException, Path, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
# from app.database.connection import get_db
from services import get_speech_to_text, get_text_to_speech
from services.base import AsyncCallbackTextHandler, TextToSpeech, SpeechToText, AsyncCallbackAudioHandler
from logger import get_logger
from utils import *
import uuid
timer = get_timer()
logger = get_logger(__name__)
router = APIRouter()
manager = ConnectionManager()

# Logger và các thành phần quản lý
router = APIRouter()
manager = ConnectionManager.get_instance()
@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, 
                            speech_to_text=Depends(get_speech_to_text),
                            default_text_to_speech=Depends(get_text_to_speech),
                             ):
    await manager.connect(websocket)
    try:
        main_task = asyncio.create_task(
            handle_receive(
                websocket=websocket,
                llm=LLM(),
                speech_to_text=speech_to_text,
                default_text_to_speech=default_text_to_speech,
                language="English",
            )
        )
        await asyncio.gather(main_task)

    except WebSocketDisconnect:
        await manager.disconnect(websocket)


async def handle_receive(
    websocket: WebSocket,
    llm: LLM,
    speech_to_text: SpeechToText,
    default_text_to_speech: TextToSpeech,
    language: str
):
    try:
        conversation_history = ConversationHistory()
        data = await websocket.receive()

        text_to_speech = default_text_to_speech

        tts_event = asyncio.Event()
        tts_task = None
        previous_transcript = None
        token_buffer = []

        # Chào User
        greeting_text = "Hi, my friend, what brings you here today?"
        await manager.send_message(message= "[start]" + greeting_text, websocket=websocket)
        conversation_history.system_prompt = greeting_text
        tts_task = asyncio.create_task(
            text_to_speech.stream(
                text=greeting_text,
                websocket=websocket,
                tts_event=tts_event,
                voice_id="en-US-ChristopherNeural",
                first_sentence=True,
                language=language,
                priority=0,
            )
        )
        tts_task.add_done_callback(task_done_callback)
        # Send end of the greeting so the client knows when to start listening
        await manager.send_message(message="[end start]\n", websocket=websocket)

        async def on_new_token(token):
            return await manager.send_message(message=token, websocket=websocket)

        async def stop_audio():
            if tts_task and not tts_task.done():
                tts_event.set()
                tts_task.cancel()
                if previous_transcript:
                    conversation_history.user.append(previous_transcript)
                    conversation_history.ai.append(" ".join(token_buffer))
                    token_buffer.clear()
                try:
                    await tts_task
                except asyncio.CancelledError:
                    pass
                tts_event.clear()

        speech_recognition_interim = False
        current_speech = ""
        speaker_audio_samples = {}

        while True:
            data = await websocket.receive()
            if data["type"] != "websocket.receive":
                raise WebSocketDisconnect(reason="disconnected")

            # show latency info
            timer.report()

            # handle text message
            if "text" in data:
                timer.start("LLM First Token")
                msg_data = data["text"]
                if msg_data != "ping":
                    # Handle client side commands
                    if msg_data.startswith("[!"):
                        command_end = msg_data.find("]")
                        command = msg_data[2:command_end]
                        command_content = msg_data[command_end + 1 :]
                        if command == "JOURNAL_MODE":
                            journal_mode = command_content == "true"
                        elif command == "ADD_SPEAKER":
                            speaker_audio_samples[command_content] = None
                        elif command == "DELETE_SPEAKER":
                            if command_content in speaker_audio_samples:
                                del speaker_audio_samples[command_content]
                                logger.info(f"Deleted speaker: {command_content}")
                        continue

                    # 1. Whether client will send speech interim audio clip in the next message.
                    if msg_data.startswith("[&Speech]"):
                        speech_recognition_interim = True
                        # stop the previous audio stream, if new transcript is received
                        await stop_audio()
                        continue

                    # 2. If client finished speech, use the sentence as input.
                    if msg_data.startswith("[SpeechFinished]"):
                        msg_data = current_speech
                        logger.info(f"Full transcript: {current_speech}")
                        # Stop recognizing next audio as interim.
                        speech_recognition_interim = False
                        # Filter noises
                        if not current_speech:
                            continue

                        await manager.send_message(
                            message=f"[+]You said: {current_speech}", websocket=websocket
                        )
                        current_speech = ""

                    # 3. Send message to LLM
                    message_id = str(uuid.uuid4().hex)[:16]

                    async def text_mode_tts_task_done_call_back(response):
                        # Update conversation history
                        # Send response to client, indicates the response is done
                        conversation_history.user.append(msg_data)
                        conversation_history.ai.append(response)
                        token_buffer.clear()
                        await manager.send_message(message=f"[end={response}]\n", websocket=websocket)
              

                    tts_task = asyncio.create_task(
                        llm.achat(
                            history=build_history(conversation_history),
                            user_input=msg_data,
                            callback=AsyncCallbackTextHandler(
                                on_new_token, token_buffer, text_mode_tts_task_done_call_back
                            ),
                            audioCallback=AsyncCallbackAudioHandler(
                                text_to_speech, websocket, tts_event, "en-US-ChristopherNeural", language
                            ),
                            metadata={"message_id": message_id},
                        )
                    )
                    tts_task.add_done_callback(task_done_callback)

                    # 5. Persist interaction in the database

            # handle binary message(audio)
            elif "bytes" in data:
                binary_data = data["bytes"]

                # 0. Handle interim speech.
                if speech_recognition_interim:
                    interim_transcript: str = (
                        await asyncio.to_thread(
                            speech_to_text.transcribe,
                            binary_data,
                            platform="web",
                            prompt=current_speech,
                            language=language,
                            # suppress_tokens=[0, 11, 13, 30],
                        )
                    ).strip()
                    speech_recognition_interim = False
                    # Filter noises.
                    if not interim_transcript:
                        continue
                    await manager.send_message(
                        message=f"[+&]{interim_transcript}", websocket=websocket
                    )
                    logger.info(f"Speech interim: {interim_transcript}")
                    current_speech = current_speech + " " + interim_transcript
                    continue

                # 1. Transcribe audio
                transcript: str = (
                    await asyncio.to_thread(
                        speech_to_text.transcribe,
                        binary_data,
                        platform="web",
                        prompt="",
                        language=language,
                    )
                ).strip()

                # ignore audio that picks up background noise
                if not transcript or len(transcript) < 2:
                    continue

                # start counting time for LLM to generate the first token
                timer.start("LLM First Token")

                # 2. Send transcript to client
                await manager.send_message(
                    message=f"[+]You said: {transcript}", websocket=websocket
                )

                # 3. stop the previous audio stream, if new transcript is received
                await stop_audio()

                previous_transcript = transcript

                message_id = str(uuid.uuid4().hex)[:16]

                async def audio_mode_tts_task_done_call_back(response):
                    # Send response to client, [=] indicates the response is done
                    await manager.send_message(message=f"[end={response}]\n", websocket=websocket)
                    # Update conversation history
                    conversation_history.user.append(transcript)
                    conversation_history.ai.append(response)
                    token_buffer.clear()

                # 5. Send message to LLM
                tts_task = asyncio.create_task(
                    llm.achat(
                        history=build_history(conversation_history),
                        user_input=transcript,
                        callback=AsyncCallbackTextHandler(
                            on_new_token, token_buffer, audio_mode_tts_task_done_call_back
                        ),
                        audioCallback=AsyncCallbackAudioHandler(
                            text_to_speech, websocket, tts_event, "en-US-ChristopherNeural", language
                        ),
                        metadata={"message_id": message_id},
                    )
                )
                tts_task.add_done_callback(task_done_callback)

    except WebSocketDisconnect:
        logger.info(f"User closed the connection")
        timer.reset()
        await manager.disconnect(websocket)
        return
