from collections.abc import AsyncIterator

from app.services.llm.base import LLMProvider


class AnthropicProvider(LLMProvider):
    provider_name = "anthropic"
    model_name = "not-configured"

    async def generate(self, prompt: str, **kwargs) -> str:
        raise NotImplementedError("Anthropic provider will be implemented in a later phase")

    async def stream_generate(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        raise NotImplementedError("Anthropic provider will be implemented in a later phase")
        yield ""
