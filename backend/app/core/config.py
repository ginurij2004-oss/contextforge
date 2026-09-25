from pathlib import Path

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


BACKEND_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_ROOT / ".env"


class Settings(BaseSettings):

    DATABASE_URL: str = (
        "postgresql+psycopg://"
        "contextforge:contextforge"
        "@localhost:5432/contextforge"
    )

    OPENAI_API_KEY: str
    OPENAI_CHAT_MODEL: str
    OPENAI_EMBEDDING_MODEL: str = (
        "text-embedding-3-small"
    )
    OPENAI_TRANSCRIPTION_MODEL: str = (
        "gpt-4o-mini-transcribe"
    )

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = (
        "contextforge_documents"
    )

    UPLOAD_DIR: str = "uploads"
    MAX_PDF_SIZE_MB: int = 10

    RAG_SCORE_THRESHOLD: float = 0.45
    RAG_TOP_K: int = 5
    RAG_CHUNK_SIZE: int = 2500
    RAG_CHUNK_OVERLAP: int = 300

    LLM_PRIMARY_PROVIDER: str = "openai"
    LLM_FALLBACK_PROVIDER: str | None = "gemini"
    GEMINI_API_KEY: str | None = None
    GEMINI_CHAT_MODEL: str = "gemini-3.7-flash"

    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM_EMAIL: str | None = None
    SMTP_FROM_NAME: str = "ContextForge"
    SMTP_USE_TLS: bool = True
    SMTP_USE_SSL: bool = False
    SMTP_TIMEOUT_SECONDS: int = 20

    # Production frontend origins. Comma-separated when multiple
    # origins are required. Local development still falls back to
    # localhost / 127.0.0.1 when this is empty.
    CONTEXTFORGE_ALLOWED_ORIGINS: str | None = None

    # n8n automation execution
    N8N_ACTION_WEBHOOK_URL: str | None = None
    N8N_WEBHOOK_SECRET: str | None = None
    N8N_TIMEOUT_SECONDS: int = 30

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
