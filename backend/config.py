from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# Load .env reliably from project root (…/ConstructSafe-BD/.env)
try:
    from dotenv import load_dotenv
    _ROOT = Path(__file__).resolve().parents[1]  # backend/.. -> project root
    load_dotenv(dotenv_path=_ROOT / ".env", override=False)
except Exception:
    # If python-dotenv isn't installed, env vars must be provided by the shell/OS
    pass


def _getenv(key: str, default: str = "") -> str:
    v = os.getenv(key)
    if v is None:
        return default
    v = str(v).strip()
    return v if v else default


def _getenv_int(key: str, default: int) -> int:
    v = os.getenv(key)
    if v is None:
        return default
    v = str(v).strip()
    if not v:
        return default
    try:
        return int(v)
    except ValueError:
        return default


def _getenv_list(key: str, default_csv: str) -> list[str]:
    raw = _getenv(key, default_csv).strip()
    if not raw:
        return []
    return [x.strip().lower() for x in raw.split(",") if x.strip()]


@dataclass(frozen=True)
class Settings:
    APP_NAME: str = _getenv("APP_NAME", "ConstructSafe-BD")
    APP_VERSION: str = _getenv("APP_VERSION", "1.0.0")
    APP_ENV: str = _getenv("APP_ENV", "dev")

    # OpenAI
    OPENAI_API_KEY: str = _getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL_FAST: str = _getenv("OPENAI_MODEL_FAST", "gpt-4o-mini")
    OPENAI_MODEL_ACCURATE: str = _getenv("OPENAI_MODEL_ACCURATE", "gpt-4o")

    # Compatibility names
    OPENAI_MODEL: str = _getenv("OPENAI_MODEL", _getenv("OPENAI_MODEL_FAST", "gpt-4o-mini"))
    OPENAI_VISION_MODEL: str = _getenv("OPENAI_VISION_MODEL", _getenv("OPENAI_MODEL_FAST", "gpt-4o-mini"))
    OPENAI_TEXT_MODEL: str = _getenv("OPENAI_TEXT_MODEL", _getenv("OPENAI_MODEL_FAST", "gpt-4o-mini"))

    # Image constraints
    MAX_IMAGE_SIZE_MB: int = _getenv_int("MAX_IMAGE_SIZE_MB", 10)
    ALLOWED_EXTENSIONS: list[str] = field(
        default_factory=lambda: _getenv_list("ALLOWED_EXTENSIONS", "jpg,jpeg,png,webp,jfif")
    )

    # CORS
    CORS_ALLOW_ORIGINS: str = _getenv("CORS_ALLOW_ORIGINS", "*")

    # Limits
    RATE_LIMIT_PER_IP: int = _getenv_int("RATE_LIMIT_PER_IP", 10)
    DAILY_QUOTA_PER_IP: int = _getenv_int("DAILY_QUOTA_PER_IP", 50)
    RATE_LIMIT_PER_MINUTE: int = _getenv_int("RATE_LIMIT_PER_MINUTE", 60)
    DAILY_TOKEN_LIMIT: int = _getenv_int("DAILY_TOKEN_LIMIT", 200000)

    # Cache
    CACHE_TTL_SECONDS: int = _getenv_int("CACHE_TTL_SECONDS", 3600)
    REDIS_URL: str = _getenv("REDIS_URL", "")

    # Data paths
    LAWS_JSON_PATH: str = _getenv("LAWS_JSON_PATH", "backend/data/laws.json")


settings = Settings()
