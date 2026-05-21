from app.services.llm.base import LLMProvider
from app.services.llm.registry import provider_registry


def get_llm_provider(provider_name: str | None = None) -> LLMProvider:
    return provider_registry.get(provider_name)
