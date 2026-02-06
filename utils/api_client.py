from __future__ import annotations

import mimetypes
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests

from utils.config import CONFIG


@dataclass
class APIError(Exception):
    message: str
    status_code: Optional[int] = None
    payload: Optional[dict] = None


class ConstructSafeAPIClient:
    def __init__(self, base_url: str | None = None, timeout_s: int | None = None) -> None:
        self.base_url = (base_url or CONFIG.base_url).rstrip("/")
        self.timeout_s = timeout_s or CONFIG.request_timeout_s
        self.session = requests.Session()

    def _url(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return self.base_url + path

    def health(self) -> Dict[str, Any]:
        r = self.session.get(self._url("/health"), timeout=self.timeout_s)
        r.raise_for_status()
        return r.json()

    def analyze_image(self, image_bytes: bytes, filename: str, *, include_laws: bool = True, mode: str = "fast") -> Dict[str, Any]:
        mime, _ = mimetypes.guess_type(filename)
        mime = mime or "application/octet-stream"

        files = {"file": (filename, image_bytes, mime)}
        params = {"include_laws": str(include_laws).lower(), "mode": mode}

        try:
            r = self.session.post(self._url("/api/v1/analyze"), params=params, files=files, timeout=self.timeout_s)
            if r.status_code >= 400:
                # API uses FastAPI HTTPException with 'detail'
                try:
                    payload = r.json()
                except Exception:
                    payload = {"detail": r.text}
                return {"success": False, "error": payload.get("detail", payload), "status_code": r.status_code}
            return r.json()
        except requests.RequestException as e:
            return {"success": False, "error": str(e), "status_code": None}

    def list_violations(self) -> List[str]:
        r = self.session.get(self._url("/api/v1/laws/violations"), timeout=self.timeout_s)
        r.raise_for_status()
        data = r.json()
        return data.get("violations", [])

    def get_violation_details(self, violation_id: str) -> Dict[str, Any]:
        r = self.session.get(self._url(f"/api/v1/laws/violations/{violation_id}"), timeout=self.timeout_s)
        r.raise_for_status()
        return r.json()

    def get_authority(self, authority_id: str) -> Dict[str, Any]:
        r = self.session.get(self._url(f"/api/v1/laws/authorities/{authority_id}"), timeout=self.timeout_s)
        r.raise_for_status()
        return r.json()

    def match_text(self, text: str, top_k: int = 5) -> Dict[str, Any]:
        params = {"text": text, "top_k": int(top_k)}
        r = self.session.get(self._url("/api/v1/laws/match-text"), params=params, timeout=self.timeout_s)
        r.raise_for_status()
        return r.json()
