from __future__ import annotations

import os
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from backend.services.law_matcher import LawMatcher

router = APIRouter(prefix="/api/v1/laws", tags=["laws"])

_LAWS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "laws.json")
_LAWS_PATH = os.path.abspath(_LAWS_PATH)

law_matcher = LawMatcher(_LAWS_PATH)


@router.get("/violations")
def list_violations() -> Dict[str, Any]:
    """
    Returns a flat list of violations indexed from Person A laws.json:
    canonical_violations + micro_violations.
    """
    return {"violations": law_matcher.list_violations()}


@router.get("/violations/{violation_id}")
def get_violation(violation_id: str) -> Dict[str, Any]:
    v = law_matcher.get_violation(violation_id)
    if not v:
        raise HTTPException(status_code=404, detail="Violation not found")
    return {"violation": v}


@router.get("/authorities/{authority_id}")
def get_authority(authority_id: str) -> Dict[str, Any]:
    a = law_matcher.get_authority(authority_id)
    if not a:
        raise HTTPException(status_code=404, detail="Authority not found")
    return {"authority": a}
