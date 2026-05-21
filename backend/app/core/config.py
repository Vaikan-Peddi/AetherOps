from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "AetherOps"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@postgres:5432/aetherops"
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8
    ALGORITHM: str = "HS256"

    BACKEND_CORS_ORIGINS: List[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    QDRANT_URL: str = "http://qdrant:6333"
    QDRANT_COLLECTION: str = "aetherops_document_chunks"
    STORAGE_DIR: str = "storage"
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    DOCUMENT_CHUNK_SIZE: int = 900
    DOCUMENT_CHUNK_OVERLAP: int = 150
    RAG_DEFAULT_TOP_K: int = 6
    RAG_RERANK_TOP_K: int = 5

    DEFAULT_LLM_PROVIDER: str = "ollama"
    ENABLED_LLM_PROVIDERS: str = "ollama"
    OLLAMA_BASE_URL: str = "http://host.docker.internal:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"
    OLLAMA_CHAT_MODEL: str = "llama3.1:8b"
    OLLAMA_RAG_MODEL: str = "llama3.1:8b"
    OLLAMA_CODING_MODEL: str = "qwen2.5-coder:7b"
    OLLAMA_REASONING_MODEL: str = "deepseek-r1:8b"
    OLLAMA_SUMMARIZATION_MODEL: str = "llama3.1:8b"
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    ANTHROPIC_API_KEY: str | None = None
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-latest"
    AI_GATEWAY_FALLBACK_PROVIDER: str = "ollama"
    LLM_REQUEST_TIMEOUT_SECONDS: float = 90.0
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 120

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, value: str | List[str]) -> List[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
