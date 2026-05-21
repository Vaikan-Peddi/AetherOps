from collections.abc import AsyncIterator

from app.services.llm.base import LLMProvider


class OpenAIProvider(LLMProvider):
    provider_name = "openai"
    model_name = "not-configured"

    async def generate(self, prompt: str, **kwargs) -> str:
        raise NotImplementedError("OpenAI provider will be implemented in a later phase")

    async def stream_generate(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        raise NotImplementedError("OpenAI provider will be implemented in a later phase")
        yield ""
