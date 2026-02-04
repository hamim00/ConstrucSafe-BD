from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from backend.services.law_matcher import LawMatcher

# IMPORTANT: router prefix ensures /api/v1/laws/... always exists
router = APIRouter(prefix="/laws", tags=["Laws"])

# Make sure LawMatcher can load your JSON
law_matcher = LawMatcher(laws_file="data/laws.json")


@router.get("/violations")
async def get_supported_violations():
    """Get list of all detectable violation types."""
    # If your frontend needs more details, use law_matcher.list_violations()
    return {"violations": law_matcher.get_all_violation_types()}


@router.get("/violations/{violation_id}")
async def get_violation_details(violation_id: str):
    """Get full details for a specific violation."""
    result = law_matcher.get_violation_details(violation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Violation type not found")
    return result


@router.get("/authorities/{authority_id}")
async def get_authority_info(authority_id: str):
    """Get contact info for an enforcement authority."""
    result = law_matcher.get_authority_info(authority_id)
    if not result:
        raise HTTPException(status_code=404, detail="Authority not found")
    return result


@router.get("/match-text")
async def match_text(
    text: str = Query(..., description="Free text to search against BNBC clause library"),
    top_k: int = Query(3, ge=1, le=20),
):
    """Text search → top_k clause matches."""
    matches = law_matcher.match_violation_text(text, top_k=top_k)
    return {"query": text, "top_k": top_k, "matches": [m.__dict__ for m in matches]}
