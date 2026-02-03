from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from backend.services.law_matcher import LawMatcher
from backend.utils.image_processing import resize_for_model, validate_image

if TYPE_CHECKING:
    from backend.services.vision_analyzer import VisionAnalyzer

router = APIRouter(prefix="/api/v1", tags=["analyze"])

_LAWS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "laws.json")
_LAWS_PATH = os.path.abspath(_LAWS_PATH)

matcher = LawMatcher(_LAWS_PATH)

# Lazy singleton (avoid constructing Gemini client during import)
_vision: Optional["VisionAnalyzer"] = None


def _get_vision() -> "VisionAnalyzer":
    """
    Create VisionAnalyzer only when /analyze is called.
    Prevents server startup from failing if GEMINI_API_KEY is missing.
    """
    global _vision
    if _vision is None:
        from backend.services.vision_analyzer import VisionAnalyzer  # runtime import
        _vision = VisionAnalyzer()
    return _vision


@router.post("/analyze")
async def analyze_image(
    file: UploadFile = File(...),
    include_laws: bool = Query(default=False),
) -> Dict[str, Any]:
    data = await file.read()
    safe_name = file.filename or "upload.jpg"

    validated = validate_image(data=data, filename=safe_name)
    img = resize_for_model(validated.image, max_side=1024)

    # Re-encode to JPEG for consistent model input
    import io

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    jpeg_bytes = buf.getvalue()

    # Lazy init Gemini client
    try:
        vision = _get_vision()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    model_out = await vision.analyze(jpeg_bytes, mime_type="image/jpeg")

    violations: List[Dict[str, Any]] = model_out.get("violations", [])
    if not isinstance(violations, list):
        violations = []

    if include_laws:
        for v in violations:
            vid = v.get("violation_id")
            title = v.get("title", "")

            if isinstance(vid, str) and vid.strip():
                record = matcher.get_violation(vid)
                if record:
                    matches = matcher.match_violation(str(record.get("title", "")), top_k=3)
                else:
                    matches = matcher.match_violation(str(title), top_k=3)
            else:
                matches = matcher.match_violation(str(title), top_k=3)

            v["law_matches"] = [
                {
                    "violation_id": m.violation_id,
                    "title": m.title,
                    "score": m.score,
                    "source_catalog_id": m.source_catalog_id,
                    "authority_id": m.authority_id,
                    "penalty_profile_id": m.penalty_profile_id,
                    "fine_range": m.fine_range,
                }
                for m in matches
            ]

    return {
        "image": {"filename": safe_name, "format": validated.format, "size": validated.size},
        "model_output": model_out,
        "violations": violations,
        "include_laws": include_laws,
    }
