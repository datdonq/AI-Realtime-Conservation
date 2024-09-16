import asyncio
import websockets

async def test_websocket():
    uri = "ws://localhost:8592/ws/22"  # Thay thế URI và session_id nếu cần

    async with websockets.connect(uri) as websocket:
        try:
            print("Connected to WebSocket server")

            # Hàm để gửi tin nhắn và chờ phản hồi [end=message_id]
            async def send_message_and_wait_for_end(message):
                await websocket.send(message)
                print(f"Message sent: {message}")
                
                while True:
                    response = await websocket.recv()
                    if response.startswith("[end"):
                        print(f"Response received: {response}")
                        break

            # Gửi tin nhắn đầu tiên
            await send_message_and_wait_for_end("Hello, chatbot!")
            
            # Gửi thêm tin nhắn và chờ phản hồi [end=message_id] sau mỗi tin nhắn
            messages = ["How are you today", "What is the weather like?", "Tell me a joke", "How's your day?", "What can you do?"]

            for message in messages:
                await send_message_and_wait_for_end(message)

        except Exception as e:
            print(f"An error occurred: {e}")

# Chạy script
if __name__ == "__main__":
    asyncio.run(test_websocket())
