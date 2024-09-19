import asyncio
import websockets

async def test_websocket():
    uri = "ws://localhost:8592/ws/22"  # Thay thế URI và session_id nếu cần

    async with websockets.connect(uri, ping_timeout=60000) as websocket:  # Tăng thời gian timeout lên 60 giây
        try:
            print("Connected to WebSocket server")

            # Hàm để gửi tin nhắn và chờ phản hồi [end=message_id]
            async def send_message_and_wait_for_end(message):
                await websocket.send(message)
                print(f"Message sent: {message}")
                
                while True:
                    response = await websocket.recv()
                    
                    if response.startswith("[end="):
                        print(f"Response received: {response}")
                        break
            
            # Hàm để gửi tin nhắn và chờ phản hồi [end=message_id]
            async def send_first_message_and_wait_for_end(message):
                await websocket.send(message)
                print(f"Message sent: {message}")
                text = []
                while True:
                    response = await websocket.recv()
                    
                    if response.startswith("[end]"):
                        text = " ".join(text)
                        print(f"Response received: {text}")
                        text = []
                        break
                    text.append(response)
                messages = ["How are you today", "What is the weather like?", "Tell me a joke", "How's your day?", "What can you do?"]
                for message in messages:
                    await websocket.send(message)
                    print(f"Message sent: {message}")
                    text = []
                    while True:
                        response = await websocket.recv()
                        if type(response) == str:
                            if response.startswith("[end="):
                                text = "".join(text)
                                print(f"Response received: {text}")
                                break
                            text.append(response)
                        # if type(response) == bytes:
                        #     with open("response_audio.mp3", "wb") as audio_file:
                        #         audio_file.write(response)
                        #     break
            async def send_first_message_bytes_and_wait_for_end(message):
                await websocket.send(message)
                print(f"Message sent: {message}")             
                while True:
                    response = await websocket.recv()
                    if type(response) == str:
                        print(f"Response received: {response}")
                    if type(response) == bytes:
                        break
                with open("response_audio.mp3", "rb") as audio_file:
                    audio_bytes = audio_file.read()
                
                await websocket.send(audio_bytes)
                while True:
                    response = await websocket.recv()
                    if type(response) == str:
                        print(f"Response received: {response}")
                    if type(response) == bytes:
                        with open("response_audio.mp3", "wb") as audio_file:
                            audio_file.write(response)
                        break
            # Gửi tin nhắn đầu tiên
            await send_first_message_and_wait_for_end("Hello, chatbot!")
            
            # # Gửi thêm tin nhắn và chờ phản hồi [end=message_id] sau mỗi tin nhắn
            # messages = ["How are you today", "What is the weather like?", "Tell me a joke", "How's your day?", "What can you do?"]

            # for message in messages:
            #     await send_message_and_wait_for_end(message)

        except Exception as e:
            print(f"An error occurred: {e}")

# Chạy script
if __name__ == "__main__":
    asyncio.run(test_websocket())
