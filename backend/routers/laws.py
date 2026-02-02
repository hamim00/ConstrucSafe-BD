from fastapi import APIRouter, HTTPException
from backend.services.law_matcher import LawMatcher

router = APIRouter(tags=["Laws"])
law_matcher = LawMatcher()


@router.get("/laws/violations")
async def get_supported_violations():
    """Get list of all detectable violation types."""
    return {"violations": law_matcher.get_all_violation_types()}


@router.get("/laws/violations/{violation_id}")
async def get_violation_laws(violation_id: str):
    """Get laws and penalties for a specific violation."""
    result = law_matcher.get_violation_details(violation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Violation type not found")
    return result


@router.get("/laws/authorities/{authority_id}")
async def get_authority_info(authority_id: str):
    """Get contact info for an enforcement authority."""
    result = law_matcher.get_authority_info(authority_id)
    if not result:
        raise HTTPException(status_code=404, detail="Authority not found")
    return result
