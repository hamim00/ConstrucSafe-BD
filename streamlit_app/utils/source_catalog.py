from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional


@lru_cache(maxsize=1)
def _load_catalog() -> Dict[str, Dict[str, Any]]:
    """Load a small local catalog mapping source_id -> metadata (title, portal)."""
    p = Path(__file__).resolve().parents[1] / "assets" / "source_catalog.json"
    if not p.exists():
        return {}

    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}

    out: Dict[str, Dict[str, Any]] = {}
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                sid = item.get("source_id")
                if isinstance(sid, str) and sid.strip():
                    out[sid.strip()] = item
    return out


def source_title(source_id: str) -> str:
    if not source_id:
        return "Unknown source"
    item = _load_catalog().get(source_id, {})
    title = item.get("title")
    return str(title).strip() if isinstance(title, str) and title.strip() else source_id


def source_portal_url(source_id: str) -> Optional[str]:
    item = _load_catalog().get(source_id, {})
    portal = item.get("official_portal")
    if isinstance(portal, str) and portal.strip():
        p = portal.strip()
        if p.startswith("http://") or p.startswith("https://"):
            return p
        return "https://" + p
    return None
