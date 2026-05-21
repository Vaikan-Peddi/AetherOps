from app.core.config import get_settings
from app.services.llm.anthropic_provider import AnthropicProvider
from app.services.llm.base import LLMProvider
from app.services.llm.ollama_provider import OllamaProvider
from app.services.llm.openai_provider import OpenAIProvider


class LLMProviderRegistry:
    def __init__(self) -> None:
        self._provider_factories = {
            "ollama": OllamaProvider,
            "openai": OpenAIProvider,
            "anthropic": AnthropicProvider,
        }

    def get(self, provider_name: str | None = None) -> LLMProvider:
        settings = get_settings()
        selected = (provider_name or settings.DEFAULT_LLM_PROVIDER).lower()
        provider_cls = self._provider_factories.get(selected)
        if provider_cls is None:
            raise ValueError(f"Unsupported LLM provider: {selected}")
        return provider_cls()

    def enabled_provider_names(self) -> list[str]:
        settings = get_settings()
        names = [name.strip().lower() for name in settings.ENABLED_LLM_PROVIDERS.split(",") if name.strip()]
        return [name for name in names if name in self._provider_factories]

    def all_provider_names(self) -> list[str]:
        return sorted(self._provider_factories.keys())


provider_registry = LLMProviderRegistry()
