from pydantic_settings import BaseSettings
from typing import Optional
import secrets


class Settings(BaseSettings):
    # App
    APP_ENV: str = "development"
    SECRET_KEY: str = secrets.token_hex(32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    FRONTEND_URL: str = "http://localhost:3000"

    # MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "qoneqt_creator"

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_LLM_MODEL: str = "gpt-4o"
    OPENAI_IMAGE_MODEL: str = "dall-e-3"
    OPENAI_TTS_VOICE: str = "alloy"
    OPENAI_TTS_MODEL: str = "tts-1"

    # Stability AI
    STABILITY_API_KEY: Optional[str] = None

    # ElevenLabs
    ELEVENLABS_API_KEY: Optional[str] = None

    # Storage
    STORAGE_BACKEND: str = "local"
    LOCAL_STORAGE_PATH: str = "./storage"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_S3_BUCKET: str = "qoneqt-creator"
    AWS_S3_REGION: str = "us-east-1"
    AWS_S3_ENDPOINT_URL: Optional[str] = None

    # FFmpeg
    FFMPEG_PATH: str = "ffmpeg"

    # Qoneqt
    QONEQT_APP_URL: str = "https://qoneqt.com"
    QONEQT_API_URL: Optional[str] = None
    QONEQT_API_KEY: Optional[str] = None

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    AUTH_RATE_LIMIT_PER_MINUTE: int = 10

    @property
    def demo_mode(self) -> bool:
        """Returns True if no real AI provider keys are configured."""
        return not self.OPENAI_API_KEY

    @property
    def has_llm(self) -> bool:
        return bool(self.OPENAI_API_KEY)

    @property
    def has_image_gen(self) -> bool:
        return bool(self.OPENAI_API_KEY or self.STABILITY_API_KEY)

    @property
    def has_tts(self) -> bool:
        return bool(self.OPENAI_API_KEY or self.ELEVENLABS_API_KEY)

    @property
    def has_qoneqt_api(self) -> bool:
        return bool(self.QONEQT_API_URL and self.QONEQT_API_KEY)

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
