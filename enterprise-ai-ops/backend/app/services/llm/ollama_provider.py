import json
from collections.abc import AsyncIterator

import httpx

from app.core.config import get_settings
from app.services.llm.base import LLMProvider


class OllamaProvider(LLMProvider):
    provider_name = "ollama"

    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model_name = settings.OLLAMA_MODEL
        self.timeout = settings.LLM_REQUEST_TIMEOUT_SECONDS

    async def generate(self, prompt: str, **kwargs) -> str:
        payload = {
            "model": kwargs.get("model", self.model_name),
            "prompt": prompt,
            "stream": False,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")

    async def stream_generate(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        payload = {
            "model": kwargs.get("model", self.model_name),
            "prompt": prompt,
            "stream": True,
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

    async def embeddings(self, texts: list[str], **kwargs) -> list[list[float]]:
        vectors: list[list[float]] = []
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for text in texts:
                response = await client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": kwargs.get("model", self.model_name), "prompt": text},
                )
                response.raise_for_status()
                vectors.append(response.json().get("embedding", []))
        return vectors
