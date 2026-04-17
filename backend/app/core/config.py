# path: backend/app/core/config.py
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GROK_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""

    DATABASE_URL: str = "sqlite:///./dev.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    JWT_SECRET: str = "changeme"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

    CHROMA_PERSIST_DIR: str = "./chroma_db"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"

    ENVIRONMENT: str = "development"
    RATE_LIMIT_PER_MINUTE: int = 60

    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "https://your-app.vercel.app",
    ]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()