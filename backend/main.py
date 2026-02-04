from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
import backend.routers.analyze as analyze
import backend.routers.laws as laws
import backend.routers.reports as reports


def _parse_cors_origins() -> list[str]:
    raw = (os.getenv("CORS_ALLOW_ORIGINS", "*") or "").strip()
    if not raw or raw == "*":
        return ["*"]
    return [x.strip() for x in raw.split(",") if x.strip()]


# ✅ Uvicorn expects this name: app
app = FastAPI(title=settings.APP_NAME, version=getattr(settings, "APP_VERSION", "1.0.0"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "version": getattr(settings, "APP_VERSION", "1.0.0")}


# ✅ Mount routers under /api/v1
app.include_router(analyze.router, prefix="/api/v1")
app.include_router(laws.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
