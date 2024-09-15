import os
from typing import Optional
from services.base import SpeechToText, TextToSpeech
from services.stt import Whisper
from services.tts import EdgeTTS

def get_speech_to_text() -> SpeechToText:
    Whisper.initialize(use="api")
    return Whisper.get_instance()

def get_text_to_speech() -> TextToSpeech:

    from services.tts import EdgeTTS

    EdgeTTS.initialize()
    return EdgeTTS.get_instance()
