from dotenv import load_dotenv

load_dotenv()
import os


class Settings:
    def __init__(self) -> None:
        self.host = os.getenv("VOICE_SERVER_HOST", "0.0.0.0")
        self.port = int(os.getenv("VOICE_SERVER_PORT", "8080"))
        self.deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")
        self.deepgram_model = os.getenv("DEEPGRAM_MODEL", "nova-2-general")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self.murf_api_key = os.getenv("MURF_API_KEY")
        self.murf_voice_id = os.getenv("MURF_VOICE_ID", "en-US-natalie")
        self.murf_base_url = os.getenv("MURF_BASE_URL", "https://global.api.murf.ai")
        self.default_language = os.getenv("DEFAULT_LANGUAGE", "en-US")
        self.tts_sample_rate = int(os.getenv("TTS_SAMPLE_RATE", "24000"))
        self.max_history_turns = int(os.getenv("MAX_HISTORY_TURNS", "10"))
        self.request_timeout = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "20"))


settings = Settings()
