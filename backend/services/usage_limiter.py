from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from datetime import date
from typing import Dict, Tuple

from fastapi import HTTPException, Request

from backend.config import settings


@dataclass
class _IpState:
    # minute-bucket counters
    minute_start: float
    minute_count: int
    # daily counters
    day: date
    day_count: int


class UsageLimiter:
    """Simple per-IP limiter.

    - RATE_LIMIT_PER_IP: max requests per rolling minute.
    - DAILY_QUOTA_PER_IP: max requests per UTC day.

    In Phase 3.5 you can replace this with Redis-based atomic counters.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._state: Dict[str, _IpState] = {}

    def _client_ip(self, request: Request) -> str:
        # If behind a proxy, set/validate X-Forwarded-For in your ingress.
        xff = request.headers.get("x-forwarded-for")
        if xff:
            return xff.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def enforce(self, request: Request, *, cost: int = 1) -> None:
        """Raise HTTPException(429) if over limits."""

        ip = self._client_ip(request)
        now = time.time()
        today = date.today()

        with self._lock:
            st = self._state.get(ip)
            if st is None:
                st = _IpState(minute_start=now, minute_count=0, day=today, day_count=0)
                self._state[ip] = st

            # reset minute window
            if now - st.minute_start >= 60:
                st.minute_start = now
                st.minute_count = 0

            # reset day
            if st.day != today:
                st.day = today
                st.day_count = 0

            # enforce
            if st.minute_count + cost > settings.RATE_LIMIT_PER_IP:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "rate_limited",
                        "message": "Too many requests from this IP. Try again shortly.",
                        "limit_per_minute": settings.RATE_LIMIT_PER_IP,
                    },
                )

            if st.day_count + cost > settings.DAILY_QUOTA_PER_IP:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "daily_quota_exceeded",
                        "message": "Daily quota exceeded for this IP. Try again tomorrow.",
                        "daily_quota": settings.DAILY_QUOTA_PER_IP,
                    },
                )

            st.minute_count += cost
            st.day_count += cost


usage_limiter = UsageLimiter()
