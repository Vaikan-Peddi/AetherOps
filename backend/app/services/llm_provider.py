from app.core.config import get_settings
from app.services.llm.anthropic_provider import AnthropicProvider
from app.services.llm.base import LLMProvider
from app.services.llm.ollama_provider import OllamaProvider
from app.services.llm.openai_provider import OpenAIProvider


def get_llm_provider(provider_name: str | None = None) -> LLMProvider:
    settings = get_settings()
    selected = (provider_name or settings.DEFAULT_LLM_PROVIDER).lower()
    if selected == "ollama":
        return OllamaProvider()
    if selected == "openai":
        return OpenAIProvider()
    if selected == "anthropic":
        return AnthropicProvider()
    raise ValueError(f"Unsupported LLM provider: {selected}")
