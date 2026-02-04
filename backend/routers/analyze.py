from __future__ import annotations

from datetime import datetime, timezone
import inspect
import io
import logging
import traceback
import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Request

from backend.services.vision_analyzer import VisionAnalyzer
from backend.services.law_matcher import LawMatcher, ClauseMatch
from backend.services.cache_store import cache_store
from backend.services.usage_limiter import usage_limiter
from backend.models.responses import (
    AnalysisResponse,
    DetectedViolation,
    LawReference,
    PenaltyProfile,
    ViolationWithLaw,
    FlaggedViolationWithLaw,
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


def _val(x: Any) -> Any:
    """Enum-safe value extractor."""
    return getattr(x, "value", x)


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_image(
    request: Request,
    file: UploadFile = File(...),
    include_laws: bool = Query(True),
    mode: str = Query("fast", pattern="^(fast|accurate)$"),
) -> AnalysisResponse:
    try:
        usage_limiter.enforce(request, cost=2 if mode == "accurate" else 1)

        vision_analyzer = VisionAnalyzer()
        law_matcher = _make_law_matcher()

        image_bytes = await file.read()
        filename = file.filename or "upload.jpg"

        if not validate_image(image_bytes, filename):
            raise HTTPException(status_code=400, detail="Invalid image format or size")

        processed_bytes = _resize_bytes_for_model(image_bytes)

        cache_key = cache_store.make_key(processed_bytes, mode=mode, include_laws=include_laws)
        cached = cache_store.get(cache_key)
        if isinstance(cached, dict) and cached.get("success") is True:
            return AnalysisResponse(**cached)

        result = await _run_vision(vision_analyzer, processed_bytes, mode=mode)

        if not isinstance(result, dict) or not result.get("success", False):
            err = "Unknown error"
            if isinstance(result, dict):
                err = str(result.get("error") or err)
            raise HTTPException(status_code=503, detail=f"Vision analysis unavailable: {err}")

        raw_violations = result.get("violations", [])
        if not isinstance(raw_violations, list):
            raw_violations = []

        raw_flagged = result.get("flagged_for_review", [])
        if not isinstance(raw_flagged, list):
            raw_flagged = []

        image_quality = result.get("image_quality")
        if not isinstance(image_quality, str):
            image_quality = None

        violations_out: List[ViolationWithLaw] = []
        flagged_out: List[FlaggedViolationWithLaw] = []

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

        for v in raw_flagged:
            if not isinstance(v, dict):
                continue

            dv_data: Dict[str, Any] = {
                "violation_type": v.get("violation_type"),
                "description": v.get("description"),
                "severity": v.get("severity"),
                "confidence": v.get("confidence"),
                "location": v.get("location"),
                "affected_parties": v.get("affected_parties"),
            }
            dv = DetectedViolation(**dv_data)

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

            flagged_out.append(
                FlaggedViolationWithLaw(
                    violation=dv,
                    laws=laws,
                    penalties=penalties,
                    recommended_actions=actions,
                    flag_reason=str(v.get("flag_reason") or "Requires manual review."),
                    requires_human_verification=bool(v.get("requires_human_verification", True)),
                    assumption_note=(
                        str(v.get("assumption_note"))
                        if isinstance(v.get("assumption_note"), str)
                        else "This is an AI-assisted hypothesis. If confirmed by a human inspector, the attached laws and penalties would apply."
                    ),
                )
            )

        # UI summary (enum-safe)
        def _sev_rank(s: Any) -> int:
            sv = str(_val(s))
            return {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(sv, 0)

        def _conf_rank(c: Any) -> int:
            cv = str(_val(c))
            return {"high": 3, "medium": 2, "low": 1}.get(cv, 0)

        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for vw in violations_out:
            sev = str(_val(vw.violation.severity))
            if sev in severity_counts:
                severity_counts[sev] += 1

        top = sorted(
            [vw.violation for vw in violations_out],
            key=lambda x: (_sev_rank(x.severity), _conf_rank(x.confidence)),
            reverse=True,
        )[:4]

        ui_summary = {
            "critical_count": severity_counts["critical"],
            "high_count": severity_counts["high"],
            "medium_count": severity_counts["medium"],
            "low_count": severity_counts["low"],
            "top_priorities": [
                {
                    "violation_type": t.violation_type,
                    "severity": str(_val(t.severity)),
                    "confidence": str(_val(t.confidence)),
                    "location": t.location,
                }
                for t in top
            ],
            "flagged_for_review_count": len(flagged_out),
        }

        response = AnalysisResponse(
            success=True,
            image_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            violations_found=len(violations_out),
            violations=violations_out,
            flagged_found=len(flagged_out),
            flagged_for_review=flagged_out,
            image_quality=image_quality,
            ui_summary=ui_summary,
            disclaimer=(
                "⚠️ AI-assisted analysis. Confirm with qualified safety professionals and official authorities. "
                "Items under 'flagged_for_review' are hypotheses that require human verification; attached laws/penalties are conditional until confirmed."
            ),
        )

        cache_store.set(cache_key, response.model_dump())
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Analyze failed: %s\n%s", e, traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Analyze crashed: {type(e).__name__}: {e}")
