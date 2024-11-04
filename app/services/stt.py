import io
import os
import subprocess
import types
# from openai import OpenAI
import speech_recognition as sr
from faster_whisper import WhisperModel
from pydub import AudioSegment
from logger import get_logger
from utils import Singleton, timed
import dotenv
from transformers import pipeline
dotenv.load_dotenv()

logger = get_logger(__name__)
WHISPER_LANGUAGE_CODE_MAPPING = {
    "en-US": "en",
    "es-ES": "es",
    "fr-FR": "fr",
    "de-DE": "de",
    "it-IT": "it",
    "pt-PT": "pt",
    "hi-IN": "hi",
    "pl-PL": "pl",
    "zh-CN": "zh",
    "ja-JP": "jp",
    "ko-KR": "ko",
}
config = types.SimpleNamespace(
    **{
        "model": os.getenv("LOCAL_WHISPER_MODEL", "base"),
        "language": "en",
        "api_key": os.getenv("OPENAI_API_KEY"),
    }
)
class Whisper(Singleton):
    def __init__(self, use="local"):
        super().__init__()
        # if use == "local":
        try:
            subprocess.check_output(["nvidia-smi"])
            device = "cuda"
        except Exception:
            device = "cpu"
        # logger.info(f"Loading [Local Whisper] model: [{config.model}]({device}) ...")
        # self.model = WhisperModel(
        #     model_size_or_path=config.model,
        #     device="auto",
        #     download_root=None,
        # )
        print("Loading model...")
        self.model = pipeline(task="automatic-speech-recognition", model="datdo2717/whisper-small-ori-vi2")
        self.recognizer = sr.Recognizer()
        self.use = use

    @timed
    def transcribe(self, audio_bytes, platform, prompt="", language="en-US", suppress_tokens=[-1]):
        logger.info("Transcribing audio...")
        platform = "local"
        if platform == "web":
            audio = self._convert_webm_to_wav(audio_bytes, self.use == "local")
        elif platform == "twilio":
            audio = self._ulaw_to_wav(audio_bytes, self.use == "local")
        else:
            audio = self._convert_bytes_to_wav(audio_bytes, self.use == "local")
        # if self.use == "local":
        return self._transcribe(audio_bytes)
        # elif self.use == "api":
        #     return self._transcribe_api(audio, prompt)

    def _transcribe(self, audio):
        # language = WHISPER_LANGUAGE_CODE_MAPPING.get(language, config.language)
        # segs, _ = self.model.transcribe(
        #     audio,
        #     language=language,
        #     vad_filter=True,
        #     initial_prompt=prompt,
        #     suppress_tokens=suppress_tokens,
        # )
        # text = " ".join([seg.text for seg in segs])
        result = self.model(audio)
        transcription = result["text"].strip()
        return transcription

    def _transcribe_api(self, audio_bytes, prompt="", language="en"):
        """
        Sử dụng OpenAI Whisper API để chuyển đổi giọng nói thành văn bản từ byte dữ liệu âm thanh
        :param audio_bytes: Dữ liệu âm thanh dưới dạng byte
        :param prompt: Gợi ý văn bản để hỗ trợ quá trình chuyển đổi (tùy chọn)
        :param language: Ngôn ngữ của âm thanh (ví dụ: "en" cho tiếng Anh, "vi" cho tiếng Việt)
        :return: Văn bản được chuyển đổi từ âm thanh
        """
        # Save audio_bytes to a file
        with open("audio.mp3", "wb") as f:
            f.write(audio_bytes)
        audio_file = open("audio.mp3", "rb")
        # client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        import openai
        # Truyền trực tiếp audio_bytes vào yêu cầu API
        response = openai.Audio.translate(
            model="whisper-1",
            file=audio_file,  # Truyền dữ liệu byte trực tiếp dưới dạng BytesIO
            prompt="Always transcribe in English",
            api_key=os.getenv("OPENAI_API_KEY"),  # Sử dụng API key từ môi trường
            response_format="text"  # Kết quả trả về là văn bản
    )

        # Trả về văn bản đã được chuyển đổi từ âm thanh
        return response

    def _convert_webm_to_wav(self, webm_data, local=True):
        webm_audio = AudioSegment.from_file(io.BytesIO(webm_data))
        wav_data = io.BytesIO()
        webm_audio.export(wav_data, format="wav")
        # if local:
        #     return wav_data
        # with sr.AudioFile(wav_data) as source:
        #     audio = self.recognizer.record(source)
        # return audio
        return webm_data
    def _convert_bytes_to_wav(self, audio_bytes, local=True):
        if local:
            audio = io.BytesIO(sr.AudioData(audio_bytes, 44100, 2).get_wav_data())
            return audio
        return sr.AudioData(audio_bytes, 44100, 2)

    def _ulaw_to_wav(self, audio_bytes, local=True):
        sound = AudioSegment(data=audio_bytes, sample_width=1, frame_rate=8000, channels=1)

        audio = io.BytesIO()
        sound.export(audio, format="wav")
        if local:
            return audio

        return sr.AudioData(audio_bytes, 8000, 1)