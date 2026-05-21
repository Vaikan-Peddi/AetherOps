from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LLMHealth:
    ok: bool
    provider: str
    model: str
    latency_ms: int | None = None
    error: str | None = None


class LLMProvider(ABC):
    provider_name: str
    model_name: str

    @abstractmethod
    async def generate(self, prompt: str, *, model: str | None = None, **kwargs: Any) -> str:
        """Generate a full response for a prompt."""

    @abstractmethod
    async def stream_generate(self, prompt: str, *, model: str | None = None, **kwargs: Any) -> AsyncIterator[str]:
        """Yield response tokens or chunks as they arrive."""

    async def embeddings(self, texts: list[str], *, model: str | None = None, **kwargs: Any) -> list[list[float]]:
        raise NotImplementedError("LLM-native embeddings are not wired in Phase 2")

    @abstractmethod
    async def health_check(self, *, model: str | None = None) -> LLMHealth:
        """Return provider/model health without raising to callers."""
