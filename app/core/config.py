"""Application configuration and environment settings."""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Project Information
    PROJECT_NAME: str = "Multi-Agent Banking Assistant"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True
    APP_ENV: str = "development"

    # OpenAI Settings
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Database Settings (defaults to SQLite if not provided)
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'banking.db'}"

    # Secret Key
    SECRET_KEY: str = "banking-assistant-secret-key-development"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
