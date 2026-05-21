import hashlib
import json
from typing import Any

import redis

from app.core.config import get_settings


class RedisCache:
    def __init__(self) -> None:
        settings = get_settings()
        self.client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

    def key(self, namespace: str, payload: Any) -> str:
        serialized = json.dumps(payload, sort_keys=True, default=str)
        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        return f"aetherops:{namespace}:{digest}"

    def get_json(self, key: str) -> Any | None:
        try:
            value = self.client.get(key)
            return json.loads(value) if value else None
        except Exception:
            return None

    def set_json(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        try:
            self.client.setex(key, ttl_seconds, json.dumps(value, default=str))
        except Exception:
            return


cache = RedisCache()
