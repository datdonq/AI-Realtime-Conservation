import io

# Import các lớp và phương thức cần thiết từ các file của bạn
from services.stt import Whisper  # Điều chỉnh đường dẫn đến file chứa lớp Whisper

async def test_whisper():
    # Khởi tạo đối tượng Whisper
    whisper = Whisper(use="api")  # Hoặc "remote" nếu bạn sử dụng dịch vụ từ xa
    
    # Tạo dữ liệu âm thanh giả lập (thay thế với dữ liệu âm thanh thực tế nếu có)
    with open("app/output_audio.wav", "rb") as f:
        audio_bytes = io.BytesIO(f.read())
    # TODO: Thêm dữ liệu âm thanh vào audio_bytes
    
    # Gọi phương thức transcribe
    platform = "web"  # Hoặc "twilio" hoặc bất kỳ nền tảng nào bạn đang sử dụng
    result = whisper.transcribe(
        audio_bytes=audio_bytes,
        platform=platform,
        prompt="",
        language="en-US"
    )
    
    # In kết quả
    print("Transcription result:", result)

# Chạy script
if __name__ == "__main__":
    import asyncio
    asyncio.run(test_whisper())
