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

    Phase 2.5: in-memory dict with TTL.
    Phase 3.5: optional Redis if REDIS_URL is set.
    """

    def __init__(self) -> None:
        self._mem: Dict[str, _Entry] = {}
        self._redis = None
        self._redis_enabled = False

        if settings.REDIS_URL:
            try:
                import redis  # type: ignore

                self._redis = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
                # simple connectivity check
                self._redis.ping()
                self._redis_enabled = True
            except Exception:
                # If Redis is misconfigured, fail open to in-memory cache.
                self._redis = None
                self._redis_enabled = False

    def make_key(self, image_bytes: bytes, *, mode: str, include_laws: bool) -> str:
        h = hashlib.sha256(image_bytes).hexdigest()
        return f"analyze:{mode}:{int(include_laws)}:{h}"

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        if self._redis_enabled and self._redis is not None:
            raw = self._redis.get(key)
            return json.loads(raw) if raw else None

        ent = self._mem.get(key)
        if not ent:
            return None
        if ent.expires_at < time.time():
            self._mem.pop(key, None)
            return None
        return ent.payload

    def set(self, key: str, payload: Dict[str, Any], ttl_seconds: Optional[int] = None) -> None:
        ttl = settings.CACHE_TTL_SECONDS if ttl_seconds is None else ttl_seconds
        if ttl <= 0:
            return

        if self._redis_enabled and self._redis is not None:
            self._redis.setex(key, ttl, json.dumps(payload, ensure_ascii=False))
            return

        self._mem[key] = _Entry(payload=payload, expires_at=time.time() + ttl)


cache_store = CacheStore()
