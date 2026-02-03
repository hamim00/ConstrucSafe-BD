from __future__ import annotations

import asyncio
import json
import os
import re
from typing import Any, Dict, Optional

import google.generativeai as genai
from google.generativeai.types import GenerationConfig

try:
    from backend.prompts.construction import CONSTRUCTION_VIOLATIONS_PROMPT
except ImportError:
    from prompts.construction import CONSTRUCTION_VIOLATIONS_PROMPT


class VisionAnalyzer:
    def __init__(self, model_name: str = "gemini-1.5-flash") -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is missing. Set it in .env or environment variables.")

        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model_name)

        self._gen_cfg = GenerationConfig(
            temperature=0.2,
            max_output_tokens=2048,
        )

    @staticmethod
    def _extract_json(text: str) -> Dict[str, Any]:
        """
        The model might wrap JSON in markdown or extra text.
        We extract the first JSON object.
        """
        if not text:
            return {}

        # Try direct parse
        try:
            return json.loads(text)
        except Exception:
            pass

        # Strip markdown fences
        cleaned = re.sub(r"```(?:json)?", "", text, flags=re.IGNORECASE).replace("```", "").strip()

        # Try direct parse again
        try:
            return json.loads(cleaned)
        except Exception:
            pass

        # Find first {...}
        m = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not m:
            return {}

        try:
            return json.loads(m.group(0))
        except Exception:
            return {}

    async def analyze(self, image_bytes: bytes, mime_type: str) -> Dict[str, Any]:
        """
        Returns a dict matching the prompt schema.
        """
        parts = [
            {"mime_type": mime_type, "data": image_bytes},
            {"text": CONSTRUCTION_VIOLATIONS_PROMPT},
        ]

        # Offload blocking call
        resp = await asyncio.to_thread(
            self._model.generate_content,
            parts,
            generation_config=self._gen_cfg,
        )

        # google-generativeai response typically has .text
        text_out: Optional[str] = getattr(resp, "text", None)
        if not text_out:
            return {"violations": [], "notes": "Model returned empty response."}

        parsed = self._extract_json(text_out)
        if not parsed:
            # fallback: return raw text to debug
            return {"violations": [], "notes": "Failed to parse model JSON.", "raw_model_text": text_out}

        return parsed
