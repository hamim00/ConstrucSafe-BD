from __future__ import annotations

import base64
import json
from typing import Any, Dict, List

from backend.config import settings
from backend.services.law_matcher import LawMatcher


class VisionAnalyzer:
    """
    Returns dict:
    {
      "success": bool,
      "violations": [DetectedViolation-compatible dicts],
      "error": str|None
    }

    DetectedViolation fields (based on your validation errors):
      - violation_type: str (must match your known IDs)
      - severity: required (keep to low/medium/high to be safe)
      - confidence: enum required => 'low'|'medium'|'high'
      - location: required str
      - affected_parties: required list[str]
      - description: str
      - bbox: optional
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
        self.allowed_ids: List[str] = self.law_matcher.get_all_violation_types()

    async def analyze_image(self, image_bytes: bytes, mode: str = "fast") -> Dict[str, Any]:
        if not self.api_key:
            return {
                "success": False,
                "violations": [],
                "error": "OpenAI not configured (missing OPENAI_API_KEY)",
            }

        model = self.model_fast if mode == "fast" else self.model_accurate

        # Use numeric threshold internally, but DO NOT return it as 'confidence'
        min_score: float = 0.30 if mode == "fast" else 0.35
        max_items: int = 10 if mode == "fast" else 15

        prompt = self._build_prompt(min_score=min_score, max_items=max_items)

        try:
            from openai import AsyncOpenAI  # type: ignore

            client = AsyncOpenAI(api_key=self.api_key)
            b64 = base64.b64encode(image_bytes).decode("utf-8")

            resp = await client.chat.completions.create(
                model=model,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": "You are a strict construction safety compliance analyst. Output JSON only.",
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                            },
                        ],
                    },
                ],
            )

            content = resp.choices[0].message.content or "{}"

            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                return {"success": False, "violations": [], "error": "Model did not return valid JSON."}

            violations_raw = data.get("violations", [])
            if not isinstance(violations_raw, list):
                violations_raw = []

            cleaned: List[Dict[str, Any]] = []

            for v in violations_raw:
                if not isinstance(v, dict):
                    continue

                vt_any = v.get("violation_type")
                if not isinstance(vt_any, str):
                    continue
                vt = vt_any.strip()
                if vt not in self.allowed_ids:
                    continue  # strict ID check

                # numeric score internal only
                score_any = v.get("confidence_score", v.get("confidence", 0.0))
                score = self._parse_score(score_any)
                if score < min_score:
                    continue

                confidence_level = self._confidence_level_from_score(score)

                # severity: keep in low/medium/high to avoid enum mismatch
                sev_any = v.get("severity")
                if isinstance(sev_any, str) and sev_any.strip():
                    severity = sev_any.strip().lower()
                else:
                    severity = self._severity_from_score(score)

                if severity not in {"low", "medium", "high"}:
                    severity = self._severity_from_score(score)

                desc_any = v.get("description", "")
                description = desc_any.strip() if isinstance(desc_any, str) else ""

                # Append numeric score to description for debugging visibility (optional)
                if description:
                    description = f"{description} (score={score:.2f})"
                else:
                    description = f"(score={score:.2f})"

                loc_any = v.get("location", "unknown")
                location = loc_any.strip() if isinstance(loc_any, str) and loc_any.strip() else "unknown"

                ap_any = v.get("affected_parties", ["workers"])
                affected_parties = self._parse_affected_parties(ap_any)

                cleaned.append(
                    {
                        "violation_type": vt,
                        "severity": severity,                 # low/medium/high
                        "confidence": confidence_level,       # REQUIRED ENUM: low/medium/high
                        "description": description,
                        "location": location,
                        "affected_parties": affected_parties,
                        "bbox": None,
                    }
                )

                if len(cleaned) >= max_items:
                    break

            return {"success": True, "violations": cleaned, "error": None}

        except Exception as e:
            return {"success": False, "violations": [], "error": f"{type(e).__name__}: {e}"}

    def _build_prompt(self, min_score: float, max_items: int) -> str:
        allowed = ", ".join(self.allowed_ids)

        # IMPORTANT: 'confidence' must be low/medium/high (enum)
        # We ask the model for a numeric "confidence_score" but we'll map it ourselves.
        return (
            "Analyze the image for construction safety violations.\n\n"
            "CRITICAL RULES:\n"
            "- Output MUST be valid JSON only (no markdown).\n"
            "- Only use violation_type values from this allowed list (exact match):\n"
            f"  [{allowed}]\n"
            f"- Return up to {max_items} violations.\n"
            "- If unsure, omit (do NOT guess).\n"
            "- Evidence must be directly visible in the image.\n\n"
            "Return schema (include ALL fields):\n"
            "{\n"
            '  "violations": [\n'
            "    {\n"
            '      "violation_type": "EXACT_ALLOWED_ID",\n'
            '      "severity": "low|medium|high",\n'
            f'      "confidence_score": 0.0,  \n'
            '      "description": "Short evidence from the image",\n'
            '      "location": "where in the scene (e.g., excavation edge / near walkway / unknown)",\n'
            '      "affected_parties": ["workers","public"]\n'
            "    }\n"
            "  ]\n"
            "}\n\n"
            f"Only include items with confidence_score >= {min_score}.\n"
        )

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

        # clamp
        if s < 0.0:
            s = 0.0
        if s > 1.0:
            s = 1.0
        return s

    @staticmethod
    def _confidence_level_from_score(score: float) -> str:
        # MUST match your enum: low/medium/high
        if score >= 0.80:
            return "high"
        if score >= 0.55:
            return "medium"
        return "low"

    @staticmethod
    def _severity_from_score(score: float) -> str:
        # Keep aligned with low/medium/high to avoid enum mismatch
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
