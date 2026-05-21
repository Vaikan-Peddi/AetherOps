import enum
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass

from app.core.config import get_settings
from app.services.llm.base import LLMProvider
from app.services.llm.registry import provider_registry


class AITaskType(str, enum.Enum):
    CHAT = "CHAT"
    RAG = "RAG"
    CODING = "CODING"
    REASONING = "REASONING"
    SUMMARIZATION = "SUMMARIZATION"


@dataclass(frozen=True)
class ModelRoute:
    provider: str
    model: str
    task_type: AITaskType


class AIGateway:
    def route(self, task_type: AITaskType, provider_name: str | None = None, model: str | None = None) -> ModelRoute:
        settings = get_settings()
        provider = provider_name or settings.DEFAULT_LLM_PROVIDER
        if model:
            return ModelRoute(provider=provider, model=model, task_type=task_type)

        if provider == "ollama":
            model_by_task = {
                AITaskType.CHAT: settings.OLLAMA_CHAT_MODEL,
                AITaskType.RAG: settings.OLLAMA_RAG_MODEL,
                AITaskType.CODING: settings.OLLAMA_CODING_MODEL,
                AITaskType.REASONING: settings.OLLAMA_REASONING_MODEL,
                AITaskType.SUMMARIZATION: settings.OLLAMA_SUMMARIZATION_MODEL,
            }
            return ModelRoute(provider=provider, model=model_by_task[task_type], task_type=task_type)

        selected_provider = provider_registry.get(provider)
        return ModelRoute(provider=provider, model=selected_provider.model_name, task_type=task_type)

    def provider(self, route: ModelRoute) -> LLMProvider:
        return provider_registry.get(route.provider)

    async def generate(
        self,
        prompt: str,
        *,
        task_type: AITaskType,
        provider_name: str | None = None,
        model: str | None = None,
    ) -> tuple[str, ModelRoute, int]:
        route = self.route(task_type, provider_name=provider_name, model=model)
        provider = self.provider(route)
        started = time.perf_counter()
        try:
            response = await provider.generate(prompt, model=route.model)
            return response, route, int((time.perf_counter() - started) * 1000)
        except Exception:
            settings = get_settings()
            fallback_route = self.route(task_type, provider_name=settings.AI_GATEWAY_FALLBACK_PROVIDER)
            fallback_provider = self.provider(fallback_route)
            response = await fallback_provider.generate(prompt, model=fallback_route.model)
            return response, fallback_route, int((time.perf_counter() - started) * 1000)

    async def stream(
        self,
        prompt: str,
        *,
        task_type: AITaskType,
        provider_name: str | None = None,
        model: str | None = None,
    ) -> tuple[ModelRoute, AsyncIterator[str]]:
        route = self.route(task_type, provider_name=provider_name, model=model)
        provider = self.provider(route)
        return route, provider.stream_generate(prompt, model=route.model)


ai_gateway = AIGateway()
