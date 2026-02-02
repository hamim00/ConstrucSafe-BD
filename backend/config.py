from __future__ import annotations

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API key")
    GEMINI_MODEL: str = Field(default="gemini-1.5-flash")

    MAX_IMAGE_SIZE_MB: int = Field(default=10, ge=1, le=50)

    ALLOWED_EXTENSIONS: List[str] = Field(default_factory=lambda: ["jpg", "jpeg", "png", "webp"])
    CORS_ALLOW_ORIGINS: List[str] = Field(default_factory=lambda: ["*"])

    @field_validator("ALLOWED_EXTENSIONS", mode="before")
    @classmethod
    def _parse_extensions(cls, v):
        if v is None:
            return ["jpg", "jpeg", "png", "webp"]
        if isinstance(v, str):
            return [x.strip().lower() for x in v.split(",") if x.strip()]
        return v

    @field_validator("CORS_ALLOW_ORIGINS", mode="before")
    @classmethod
    def _parse_origins(cls, v):
        if v is None:
            return ["*"]
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v


settings = Settings()
