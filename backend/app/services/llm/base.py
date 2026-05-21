from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class LLMProvider(ABC):
    provider_name: str
    model_name: str

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate a full response for a prompt."""

    @abstractmethod
    async def stream_generate(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        """Yield response tokens or chunks as they arrive."""

    async def embeddings(self, texts: list[str], **kwargs) -> list[list[float]]:
        raise NotImplementedError("LLM-native embeddings are not wired in Phase 1")
