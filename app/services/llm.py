import openai
import os
import dotenv
from typing import Optional
from langchain.chat_models import ChatOpenAI
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from logger import get_logger
from utils import timed
from services.base import AsyncCallbackTextHandler, AsyncCallbackAudioHandler

dotenv.load_dotenv()
logger = get_logger(__name__)
class LLM:
    def __init__(self):
        self.chat = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.5, streaming=True, openai_api_key=os.getenv("OPENAI_API_KEY"))
        self.config = {"model": "gpt-3.5-turbo", "temperature": 0.5, "streaming": True}
        self.system_prompt = """
        ### ROLE:
        From now you are not ChatGPT. 
        Your name is John, an English teacher, 26 years old. You are teaching English to a student.
        Your task is help your student to speak English fluently. Help him to improve his English speaking skills.
        
        ### INSTRUCTIONS:
        - Try to ask and answer questions to keep the conversation going to help improve students' English communication skills.
        - If the student asks you a question, you can answer it, but try to ask a new question to keep the conversation going.
        - When you receive a student's answer that is not in English, ask the student to pronounce the English correctly.
        - No matter what language the student speaks, you must always respond in English, never in any other language.
        - If you find students using incorrect grammar, help them correct it.
        - Do not repeat used questions.
        - Talk as friendly as possible, creating a sense of closeness for students.
        """
    def get_config(self):
        return self.config

    @timed
    async def achat(
        self,
        history: list[BaseMessage],
        user_input: str,
        callback: AsyncCallbackTextHandler,
        audioCallback: Optional[AsyncCallbackAudioHandler] = None,
        metadata: Optional[dict] = None,
        *args,
        **kwargs,
    ) -> str:
        history.insert(0, SystemMessage(content=self.system_prompt))
        # 1. Add user input to history
        history.append(
            HumanMessage(
                content=user_input
            )
        )
        # print(history)
        # 3. Generate response
        callbacks = [callback, StreamingStdOutCallbackHandler()]
        if audioCallback is not None:
            callbacks.append(audioCallback)
        response = await self.chat.agenerate(
            [history], callbacks=callbacks, metadata=metadata
        )
        logger.info(f"Response: {response}")
        
        return response.generations[0][0].text