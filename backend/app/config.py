"""Application configuration using pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="allow")

    # App
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "postgresql://eventhint:eventhint_password@localhost:5432/eventhint"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/google/callback"

    # OCR
    GOOGLE_CLOUD_VISION_API_KEY: str = ""
    TESSERACT_PATH: str = "/usr/bin/tesseract"
    OCR_CONFIDENCE_THRESHOLD: float = 0.75

    # LLM
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_MAX_TOKENS: int = 2000

    # Calendar
    GOOGLE_CALENDAR_WEBHOOK_URL: str = ""

    # URLs
    FRONTEND_URL: str = "http://localhost:5173"
    BACKEND_URL: str = "http://localhost:8000"
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # File Upload
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    UPLOAD_DIR: str = "/tmp/eventhint_uploads"

    # Feature Flags
    ENABLE_AUTO_APPROVE: bool = False
    ENABLE_LLM_FALLBACK: bool = True
    ENABLE_GOOGLE_VISION: bool = False


settings = Settings()

