from __future__ import annotations

import base64
import json
from typing import Any, Dict, List

from backend.config import settings
from backend.services.law_matcher import LawMatcher
from backend.utils.image_processing import assess_image_quality


# ---- Prompt imports (supports both older/newer layouts) ----
# New layout:
#   backend/prompts/construction.py  => SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
# Old layout:
#   backend/prompt/construction.py   => systemPrompt, userPromptTemplate
try:
    from backend.prompts.construction import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
except Exception:  # pragma: no cover
    try:
        from backend.prompt.construction import systemPrompt as SYSTEM_PROMPT  # type: ignore
        from backend.prompt.construction import userPromptTemplate as USER_PROMPT_TEMPLATE  # type: ignore
    except Exception:  # pragma: no cover
        # Last-resort fallback (keeps server from crashing if prompt module path is wrong)
        SYSTEM_PROMPT = "You are a construction safety compliance analyst. Output valid JSON only."
        USER_PROMPT_TEMPLATE = (
            "Analyze the image for safety violations. Allowed IDs: {allowed_ids_json}. "
            "Return at most {max_items}. Quality: {quality_hint}."
        )


# Sensitive violations require extra caution (high-stakes claims)
SENSITIVE_VIOLATIONS = {
    "CHILD_LABOUR_ON_SITE",
    "CHILD_LABOUR_HAZARDOUS_TASK",
    "UNDERAGE_HOIST_OPERATOR",
}

# Curated high-visual-detectability list (keeps prompt small and reduces hallucination risk).
# IMPORTANT: IDs must exist in laws.json.
PRIORITY_VIOLATIONS = [
    # PPE
    "PPE_HELMET_MISSING", "PPE_HELMET_NOT_USED", "PPE_HELMET_DAMAGED",
    "PPE_HIVIS_VEST_MISSING", "PPE_HV_MISSING",
    "PPE_GLOVES_MISSING", "PPE_SHOES_MISSING",
    "PPE_EYE_PROTECTION_MISSING", "PPE_EAR_PROTECTION_MISSING",

    # Fall protection
    "FALL_HARNESS_MISSING", "FALL_HARNESS_NOT_USED", "HEIGHT_NO_HARNESS",
    "FALL_GUARDRAIL_MISSING", "NO_GUARDRAIL_OPEN_EDGE",
    "SCAFFOLDING_UNSAFE_NO_GUARDRAIL", "SCAFFOLDING_UNSAFE_NO_TOEBOARD",
    "SAFETY_NET_MISSING", "FALL_NET_MISSING",

    # Excavation / barricades
    "EXCAVATION_NO_BARRICADE", "EXCAVATION_UNPROTECTED",
    "EXCAVATION_NO_SHORING", "EXCAVATION_NO_SIGNAGE",

    # Public safety / site boundary
    "SITE_BARRICADE_MISSING", "SITE_FENCING_MISSING",
    "ROAD_OBSTRUCTION_MATERIALS", "ROAD_OBSTRUCTION_DEBRIS",
    "NO_WARNING_SIGNS",

    # Scaffolding stability
    "SCAFFOLDING_UNSAFE_NO_BRACING", "SCAFFOLDING_UNSAFE_OVERLOADED",
    "SCAFFOLDING_UNSAFE_INCOMPLETE_PLANKS", "SCAFFOLD_UNSECURED",

    # Electrical / fire
    "ELECTRICAL_HAZARD_EXPOSED_WIRING", "ELECTRICAL_DANGLING_CABLES",
    "FIRE_EXTINGUISHER_MISSING", "FIRE_EXIT_BLOCKED",

    # Sensitive
    "CHILD_LABOUR_ON_SITE", "CHILD_LABOUR_HAZARDOUS_TASK", "UNDERAGE_HOIST_OPERATOR",
]


class VisionAnalyzer:
    """OpenAI vision-based analyzer.

    Returns:
      {
        "success": bool,
        "violations": [DetectedViolation-compatible dicts],
        "flagged_for_review": [FlaggedViolation-compatible dicts],
        "image_quality": "good|moderate|poor|unknown",
        "error": str|None,
      }
    """

    def __init__(self) -> None:
        self.api_key: str = getattr(settings, "OPENAI_API_KEY", "") or ""

        self.model_fast: str = (
            getattr(settings, "OPENAI_MODEL_FAST", "")
            or getattr(settings, "OPENAI_VISION_MODEL", "")
            or "gpt-4o-mini"
        )
        self.model_accurate: str = (
            getattr(settings, "OPENAI_MODEL_ACCURATE", "")
            or getattr(settings, "OPENAI_VISION_MODEL", "")
            or "gpt-4o"
        )

        self.law_matcher = LawMatcher(laws_file="data/laws.json")
        all_ids = set(self.law_matcher.get_all_violation_types())

        curated = [v for v in PRIORITY_VIOLATIONS if v in all_ids]
        self.allowed_ids: List[str] = curated if curated else sorted(all_ids)

    async def analyze_image(self, image_bytes: bytes, mode: str = "fast") -> Dict[str, Any]:
        if not self.api_key:
            return {
                "success": False,
                "violations": [],
                "flagged_for_review": [],
                "image_quality": "unknown",
                "error": "OpenAI not configured (missing OPENAI_API_KEY)",
            }

        model = self.model_fast if mode == "fast" else self.model_accurate

        # Image quality heuristic
        q = assess_image_quality(image_bytes)
        image_quality = str(q.get("quality") or "unknown")
        warnings = q.get("warnings") or []
        metrics = q.get("metrics") or {}

        # Adjust thresholds based on quality
        quality_multiplier = {
            "good": 1.0,
            "moderate": 1.10,
            "poor": 1.25,
        }.get(image_quality, 1.10)

        # Base thresholds by mode
        base_standard = 0.50 if mode == "fast" else 0.45
        base_critical = 0.70
        base_sensitive = 0.90

        max_items = 6 if mode == "fast" else 12

        prompt = self._build_prompt(
            max_items=max_items,
            quality_hint=self._format_quality_hint(image_quality, warnings, metrics),
        )

        try:
            from openai import AsyncOpenAI  # type: ignore

            client = AsyncOpenAI(api_key=self.api_key)
            b64 = base64.b64encode(image_bytes).decode("utf-8")

            resp = await client.chat.completions.create(
                model=model,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                        ],
                    },
                ],
            )

            content = resp.choices[0].message.content or "{}"
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "violations": [],
                    "flagged_for_review": [],
                    "image_quality": image_quality,
                    "error": "Model did not return valid JSON.",
                }

            raw = data.get("violations", [])
            if not isinstance(raw, list):
                raw = []

            confirmed: List[Dict[str, Any]] = []
            flagged: List[Dict[str, Any]] = []

            for v in raw:
                if not isinstance(v, dict):
                    continue

                vt_any = v.get("violation_type")
                if not isinstance(vt_any, str):
                    continue
                vt = vt_any.strip()
                if vt not in self.allowed_ids:
                    continue

                score = self._parse_score(v.get("confidence_score", v.get("confidence", 0.0)))

                severity = self._normalize_severity(v.get("severity"))
                if severity not in {"low", "medium", "high", "critical"}:
                    severity = self._severity_from_score(score)

                # Threshold based on type
                if vt in SENSITIVE_VIOLATIONS:
                    threshold = min(base_sensitive * quality_multiplier, 0.99)
                elif severity == "critical":
                    threshold = min(base_critical * quality_multiplier, 0.99)
                else:
                    threshold = min(base_standard * quality_multiplier, 0.99)

                desc_any = v.get("description", "")
                description = desc_any.strip() if isinstance(desc_any, str) else ""
                loc_any = v.get("location", "unknown")
                location = loc_any.strip() if isinstance(loc_any, str) and loc_any.strip() else "unknown"
                ap = self._parse_affected_parties(v.get("affected_parties", ["workers"]))

                record: Dict[str, Any] = {
                    "violation_type": vt,
                    "severity": severity,
                    "confidence": self._confidence_level_from_score(score),
                    "description": description or "(no description)",
                    "location": location,
                    "affected_parties": ap,
                }

                if score >= threshold:
                    confirmed.append(record)
                elif vt in SENSITIVE_VIOLATIONS and score >= 0.50:
                    # Flag sensitive items for manual verification (router will attach laws + penalties)
                    flagged.append(
                        {
                            **record,
                            "flag_reason": (
                                f"Potential {vt} detected with {score:.0%} model confidence. "
                                f"Image quality={image_quality}. Requires human verification before confirmation."
                            ),
                            "requires_human_verification": True,
                            "assumption_note": (
                                "This is an AI-assisted hypothesis. If a human inspector confirms this violation, "
                                "the attached law citations and penalties would apply."
                            ),
                            "raw_confidence_score": round(score, 4),
                        }
                    )

                if len(confirmed) >= max_items:
                    break

            return {
                "success": True,
                "violations": confirmed,
                "flagged_for_review": flagged,
                "image_quality": image_quality,
                "error": None,
            }

        except Exception as e:
            return {
                "success": False,
                "violations": [],
                "flagged_for_review": [],
                "image_quality": image_quality,
                "error": f"{type(e).__name__}: {e}",
            }

    def _build_prompt(self, *, max_items: int, quality_hint: str) -> str:
        allowed_ids_json = json.dumps(self.allowed_ids, ensure_ascii=False, indent=2)
        return USER_PROMPT_TEMPLATE.format(
            allowed_ids_json=allowed_ids_json,
            max_items=max_items,
            quality_hint=quality_hint,
        )

    @staticmethod
    def _format_quality_hint(image_quality: str, warnings: List[str], metrics: Dict[str, Any]) -> str:
        parts = [f"quality={image_quality}"]
        if warnings:
            parts.append(f"warnings={warnings}")
        short_metrics = {
            k: metrics.get(k)
            for k in ["width", "height", "brightness_mean", "contrast_std", "edge_variance"]
            if k in metrics
        }
        if short_metrics:
            parts.append(f"metrics={short_metrics}")
        return " | ".join(parts)

    @staticmethod
    def _parse_score(x: Any) -> float:
        if isinstance(x, (int, float)):
            s = float(x)
        elif isinstance(x, str):
            try:
                s = float(x.strip())
            except ValueError:
                s = 0.0
        else:
            s = 0.0
        return max(0.0, min(1.0, s))

    @staticmethod
    def _confidence_level_from_score(score: float) -> str:
        if score >= 0.80:
            return "high"
        if score >= 0.55:
            return "medium"
        return "low"

    @staticmethod
    def _normalize_severity(sev: Any) -> str:
        if isinstance(sev, str):
            s = sev.strip().lower()
            if s in {"critical", "high", "medium", "low"}:
                return s
        return "medium"

    @staticmethod
    def _severity_from_score(score: float) -> str:
        if score >= 0.90:
            return "critical"
        if score >= 0.80:
            return "high"
        if score >= 0.55:
            return "medium"
        return "low"

    @staticmethod
    def _parse_affected_parties(x: Any) -> List[str]:
        if isinstance(x, list):
            out = [str(i).strip().lower() for i in x if str(i).strip()]
            return out if out else ["workers"]
        if isinstance(x, str) and x.strip():
            parts = [p.strip().lower() for p in x.split(",") if p.strip()]
            return parts if parts else ["workers"]
        return ["workers"]
