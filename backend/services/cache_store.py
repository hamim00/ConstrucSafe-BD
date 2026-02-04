from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

from backend.config import settings


@dataclass
class _Entry:
    payload: Dict[str, Any]
    expires_at: float


class CacheStore:
    """Small cache abstraction.

    - Always works with an in-memory dict + TTL
    - Optionally uses Redis if REDIS_URL is set and reachable

    NOTE: redis-py type stubs sometimes declare `.get()` as returning very broad types
    (e.g., ResponseSet). We normalize the value before json.loads to satisfy Pylance
    and to be runtime-safe.
    """

    def __init__(self) -> None:
        self._mem: Dict[str, _Entry] = {}
        self._redis: Any = None
        self._redis_enabled = False

        if getattr(settings, "REDIS_URL", None):
            try:
                import redis  # type: ignore

                # decode_responses=False => bytes are returned, which json.loads can accept
                self._redis = redis.Redis.from_url(settings.REDIS_URL, decode_responses=False)
                self._redis.ping()
                self._redis_enabled = True
            except Exception:
                # Fail open to in-memory cache if Redis misconfigured/unavailable
                self._redis = None
                self._redis_enabled = False

    def make_key(self, image_bytes: bytes, *, mode: str, include_laws: bool) -> str:
        h = hashlib.sha256(image_bytes).hexdigest()
        return f"analyze:{mode}:{int(include_laws)}:{h}"

    @staticmethod
    def _safe_json_loads(raw: Any) -> Optional[Dict[str, Any]]:
        if raw is None:
            return None

        # Most common: bytes (decode_responses=False) or str (decode_responses=True)
        if isinstance(raw, (bytes, bytearray, str)):
            try:
                obj = json.loads(raw)  # type: ignore[arg-type]
            except Exception:
                return None
            return obj if isinstance(obj, dict) else None

        # Unexpected types (e.g., sets) => treat as cache miss
        return None

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        if self._redis_enabled and self._redis is not None:
            raw = self._redis.get(key)
            return self._safe_json_loads(raw)

        ent = self._mem.get(key)
        if not ent:
            return None
        if ent.expires_at < time.time():
            self._mem.pop(key, None)
            return None
        return ent.payload

    def set(self, key: str, payload: Dict[str, Any], ttl_seconds: Optional[int] = None) -> None:
        ttl = getattr(settings, "CACHE_TTL_SECONDS", 300) if ttl_seconds is None else ttl_seconds
        if ttl <= 0:
            return

        if self._redis_enabled and self._redis is not None:
            # store JSON as utf-8 bytes
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self._redis.setex(key, ttl, data)
            return

        self._mem[key] = _Entry(payload=payload, expires_at=time.time() + ttl)


cache_store = CacheStore()
