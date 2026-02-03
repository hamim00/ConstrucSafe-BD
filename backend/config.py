from __future__ import annotations

from typing import ClassVar, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",          # <- unknown env vars are ignored
        "case_sensitive": False,
    }

    APP_NAME: str = "ConstructSafe-BD API"
    API_PREFIX: str = "/api/v1"

    # Keep only simple scalar fields here to avoid env JSON parsing traps
    MAX_IMAGE_SIZE_MB: int = 10

    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"


settings = Settings()
