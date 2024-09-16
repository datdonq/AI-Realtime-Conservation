import asyncio
from langchain.schema import HumanMessage
from services.base import AsyncCallbackTextHandler  # Điều chỉnh đường dẫn nếu cần
from services.llm import LLM  # Điều chỉnh đường dẫn đến file chứa lớp LLM

async def test_achat():
    llm = LLM()

    # Khởi tạo các callback giả lập
    async def on_new_token(token: str):
        print(f"New token: {token}")

    async def on_llm_end(text: str):
        print(f"LLM End: {text}")

    # Tạo đối tượng callback
    callback = AsyncCallbackTextHandler(on_new_token=on_new_token, token_buffer=[], on_llm_end=on_llm_end)
    
    # Tạo history và user_input
    history = [HumanMessage(content="Hello")]
    user_input = "How are you?"

    # Gọi phương thức achat và lấy phản hồi
    response = await llm.achat(
        history=history,
        user_input=user_input,
        callback=callback,
    )

    print(f"Final response: {response}")

# Chạy script
if __name__ == "__main__":
    asyncio.run(test_achat())
