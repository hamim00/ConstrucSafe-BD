from __future__ import annotations

from datetime import datetime, timezone
import inspect
import io
import logging
import traceback
import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, UploadFile, File, HTTPException, Query

from backend.services.vision_analyzer import VisionAnalyzer
from backend.services.law_matcher import LawMatcher, ClauseMatch
from backend.models.responses import (
    AnalysisResponse,
    DetectedViolation,
    LawReference,
    PenaltyProfile,
    ViolationWithLaw,
)
from backend.utils.image_processing import validate_image, resize_image

try:
    from PIL import Image
except Exception:  # pragma: no cover
    Image = None  # type: ignore


logger = logging.getLogger("constructsafe.analyze")
router = APIRouter(tags=["Analysis"])


def _make_law_matcher() -> LawMatcher:
    sig = inspect.signature(LawMatcher.__init__)
    params = list(sig.parameters.keys())

    if "laws_path" in params:
        return LawMatcher(laws_path="data/laws.json")  # type: ignore[arg-type]
    if "laws_file" in params:
        return LawMatcher(laws_file="data/laws.json")  # type: ignore[arg-type]

    try:
        return LawMatcher()  # type: ignore[call-arg]
    except TypeError:
        return LawMatcher("data/laws.json")  # type: ignore[call-arg]


def _resize_bytes_for_model(image_bytes: bytes) -> bytes:
    # resize_image may accept bytes or PIL.Image depending on your version
    try:
        return resize_image(image_bytes)  # type: ignore[arg-type]
    except TypeError:
        if Image is None:
            raise HTTPException(
                status_code=500,
                detail="PIL/Pillow is required for image processing but is not installed. Run: pip install pillow",
            )
        img = Image.open(io.BytesIO(image_bytes))
        return resize_image(img)  # type: ignore[arg-type]


async def _run_vision(vision: VisionAnalyzer, image_bytes: bytes, mode: str) -> Dict[str, Any]:
    # VisionAnalyzer may expose analyze_image(...) or analyze(...)
    if hasattr(vision, "analyze_image"):
        fn = getattr(vision, "analyze_image")
        return await fn(image_bytes, mode=mode)  # type: ignore[misc]
    if hasattr(vision, "analyze"):
        fn = getattr(vision, "analyze")
        try:
            return await fn(image_bytes, mime_type="image/jpeg")  # type: ignore[misc]
        except TypeError:
            return await fn(image_bytes)  # type: ignore[misc]
    raise HTTPException(status_code=500, detail="VisionAnalyzer has no analyze method.")


def _clause_matches_to_law_refs(matches: List[ClauseMatch]) -> List[LawReference]:
    out: List[LawReference] = []
    for m in matches:
        interpretation_parts = [m.title]
        if m.section:
            interpretation_parts.append(f"Section: {m.section}")
        if m.pdf_page is not None:
            interpretation_parts.append(f"PDF page: {m.pdf_page}")
        if m.gazette_page is not None:
            interpretation_parts.append(f"Gazette page: {m.gazette_page}")
        interpretation = " | ".join([p for p in interpretation_parts if p])

        out.append(
            LawReference(
                source_id=m.source_catalog_id,
                citation=m.citation or m.title,
                interpretation=interpretation,
                confidence=str(round(float(m.score), 4)),
            )
        )
    return out


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_image(
    file: UploadFile = File(...),
    include_laws: bool = Query(True),
    mode: str = Query("fast", pattern="^(fast|accurate)$"),
) -> AnalysisResponse:
    try:
        vision_analyzer = VisionAnalyzer()
        law_matcher = _make_law_matcher()

        image_bytes = await file.read()
        filename = file.filename or "upload.jpg"

        # Validate
        if not validate_image(image_bytes, filename):
            raise HTTPException(status_code=400, detail="Invalid image format or size")

        # Resize/normalize
        processed_bytes = _resize_bytes_for_model(image_bytes)

        # Vision
        result = await _run_vision(vision_analyzer, processed_bytes, mode=mode)

        if not isinstance(result, dict) or not result.get("success", False):
            err = "Unknown error"
            if isinstance(result, dict):
                err = str(result.get("error") or err)
            raise HTTPException(status_code=503, detail=f"Vision analysis unavailable: {err}")

        raw_violations = result.get("violations", [])
        if not isinstance(raw_violations, list):
            raw_violations = []

        violations_out: List[ViolationWithLaw] = []

        for v in raw_violations:
            if not isinstance(v, dict):
                continue

            dv = DetectedViolation(**v)

            laws: List[LawReference] = []
            penalties: List[PenaltyProfile] = []
            actions: List[str] = []

            if include_laws:
                exact = law_matcher.match_violation(dv.violation_type)

                if isinstance(exact, dict):
                    laws = [LawReference(**lr) for lr in (exact.get("laws") or [])]
                    penalties = [PenaltyProfile(**p) for p in (exact.get("penalties") or [])]
                    actions = exact.get("recommended_actions") or []
                else:
                    query_text = dv.description or dv.violation_type
                    matches = law_matcher.match_violation(query_text, top_k=3)

                    if isinstance(matches, list) and matches and isinstance(matches[0], ClauseMatch):
                        laws = _clause_matches_to_law_refs(matches)

            violations_out.append(
                ViolationWithLaw(
                    violation=dv,
                    laws=laws,
                    penalties=penalties,
                    recommended_actions=actions,
                )
            )

        return AnalysisResponse(
            success=True,
            image_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            violations_found=len(violations_out),
            violations=violations_out,
            disclaimer="⚠️ AI-assisted analysis. Verify with qualified safety professionals and official authorities.",
        )

    except HTTPException:
        raise
    except Exception as e:
        # Log full traceback to terminal
        logger.error("Analyze failed: %s\n%s", e, traceback.format_exc())
        # Return a JSON error instead of bare 'Internal Server Error'
        raise HTTPException(status_code=500, detail=f"Analyze crashed: {type(e).__name__}: {e}")
