from collections.abc import AsyncIterator
from typing import Any

from app.core.config import get_settings
from app.services.llm.base import LLMHealth, LLMProvider


class AnthropicProvider(LLMProvider):
    provider_name = "anthropic"

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.ANTHROPIC_API_KEY
        self.model_name = settings.ANTHROPIC_MODEL

    async def generate(self, prompt: str, *, model: str | None = None, **kwargs: Any) -> str:
        raise NotImplementedError("Anthropic provider scaffold is configured but not enabled for generation yet")

    async def stream_generate(self, prompt: str, *, model: str | None = None, **kwargs: Any) -> AsyncIterator[str]:
        raise NotImplementedError("Anthropic streaming scaffold is configured but not enabled yet")
        yield ""

    async def health_check(self, *, model: str | None = None) -> LLMHealth:
        return LLMHealth(
            ok=bool(self.api_key),
            provider=self.provider_name,
            model=model or self.model_name,
            error=None if self.api_key else "ANTHROPIC_API_KEY is not configured",
        )
