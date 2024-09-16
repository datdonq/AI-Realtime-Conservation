import openai
import os
import dotenv
from typing import Optional
from langchain.chat_models import ChatOpenAI
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.schema import BaseMessage, HumanMessage
from logger import get_logger
from utils import timed
from services.base import AsyncCallbackTextHandler, AsyncCallbackAudioHandler

dotenv.load_dotenv()
logger = get_logger(__name__)
class LLM:
    def __init__(self):
        self.chat = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.5, streaming=True, openai_api_key=os.getenv("OPENAI_API_KEY"))
        self.config = {"model": "gpt-3.5-turbo", "temperature": 0.5, "streaming": True}
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

        # 1. Add user input to history
        history.append(
            HumanMessage(
                content=user_input
            )
        )

        # 3. Generate response
        callbacks = [callback, StreamingStdOutCallbackHandler()]
        if audioCallback is not None:
            callbacks.append(audioCallback)
        response = await self.chat.agenerate(
            [history], callbacks=callbacks, metadata=metadata
        )
        logger.info(f"Response: {response}")
        
        return response.generations[0][0].text