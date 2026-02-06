from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


@dataclass(frozen=True)
class AppConfig:
    # Default points at Railway backend
    base_url: str = os.getenv("CONSTRUCSAFE_API_BASE_URL", "https://construcsafe-bd-production.up.railway.app")
    request_timeout_s: int = int(os.getenv("CONSTRUCSAFE_HTTP_TIMEOUT_S", "60"))


CONFIG = AppConfig()
