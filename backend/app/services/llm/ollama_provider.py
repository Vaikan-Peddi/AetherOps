import json
import time
from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.core.config import get_settings
from app.services.llm.base import LLMHealth, LLMProvider


class OllamaProvider(LLMProvider):
    provider_name = "ollama"

    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model_name = settings.OLLAMA_MODEL
        self.timeout = settings.LLM_REQUEST_TIMEOUT_SECONDS

    async def generate(self, prompt: str, *, model: str | None = None, **kwargs: Any) -> str:
        payload = {
            "model": model or kwargs.get("model") or self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": kwargs.get("options", {}),
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")

    async def stream_generate(self, prompt: str, *, model: str | None = None, **kwargs: Any) -> AsyncIterator[str]:
        payload = {
            "model": model or kwargs.get("model") or self.model_name,
            "prompt": prompt,
            "stream": True,
            "options": kwargs.get("options", {}),
        }
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", f"{self.base_url}/api/generate", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    if data.get("done"):
                        break
                    yield data.get("response", "")

    async def embeddings(self, texts: list[str], *, model: str | None = None, **kwargs: Any) -> list[list[float]]:
        vectors: list[list[float]] = []
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for text in texts:
                response = await client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": model or kwargs.get("model") or self.model_name, "prompt": text},
                )
                response.raise_for_status()
                vectors.append(response.json().get("embedding", []))
        return vectors

    async def health_check(self, *, model: str | None = None) -> LLMHealth:
        started = time.perf_counter()
        selected_model = model or self.model_name
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                models = response.json().get("models", [])
                known_models = {item.get("name") for item in models}
                ok = not known_models or selected_model in known_models
                return LLMHealth(
                    ok=ok,
                    provider=self.provider_name,
                    model=selected_model,
                    latency_ms=int((time.perf_counter() - started) * 1000),
                    error=None if ok else f"Model {selected_model} not found in Ollama tags",
                )
        except Exception as exc:
            return LLMHealth(
                ok=False,
                provider=self.provider_name,
                model=selected_model,
                latency_ms=int((time.perf_counter() - started) * 1000),
                error=str(exc),
            )
