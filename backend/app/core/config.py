import os
import secrets
from typing import List, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings. Prefer environment variables / .env over defaults."""

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )

    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 8)))

    PROJECT_NAME: str = "糖尿病智能健康助理"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Default to local SQLite for zero-friction demo / tests.
    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./diabetes_assistant.db",
    )
    SQLALCHEMY_DATABASE_URI_FALLBACK: str = "sqlite:///./diabetes_assistant.db"
    AUTO_CREATE_TABLES: bool = os.getenv("AUTO_CREATE_TABLES", "true").lower() == "true"

    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    CORS_ALLOW_CREDENTIALS: bool = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str):
            if v.strip() == "*":
                raise ValueError("CORS_ORIGINS must list explicit origins")
            return [i.strip() for i in v.split(",") if i.strip()]
        if "*" in v:
            raise ValueError("CORS_ORIGINS must list explicit origins")
        return v

    VECTOR_STORE_DIR: str = os.getenv(
        "VECTOR_STORE_DIR",
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "vector_db"),
    )

    # LLM / Agent (OpenAI-compatible proxy supplied by the local environment).
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai_compatible")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "http://localhost:18318/v1")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini/gemini-3.6-flash")
    LLM_TIMEOUT_SECONDS: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
    LLM_MAX_TOOL_ROUNDS: int = int(os.getenv("LLM_MAX_TOOL_ROUNDS", "4"))
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    AGENT_ENABLED: bool = os.getenv("AGENT_ENABLED", "true").lower() == "true"
    AGENT_REQUIRE_CONFIRM_WRITE: bool = os.getenv("AGENT_REQUIRE_CONFIRM_WRITE", "true").lower() == "true"
    SCHEDULER_ENABLED: bool = os.getenv("SCHEDULER_ENABLED", "false").lower() == "true"

    # Legacy fields kept for older modules
    MODEL_PROVIDER: str = os.getenv("MODEL_PROVIDER", "disabled")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gemini/gemini-3.6-flash")
    MODEL_DEVICE: str = os.getenv("MODEL_DEVICE", "cpu")
    MODEL_PATH: str = os.getenv("MODEL_PATH", "./models")
    MODEL_QUANTIZATION: str = os.getenv("MODEL_QUANTIZATION", "int4")
    MODEL_PRELOAD: bool = False

settings = Settings()
