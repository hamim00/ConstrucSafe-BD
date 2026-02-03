from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class LawMatch:
    violation_id: str
    title: str
    score: float
    source_catalog_id: Optional[str] = None
    authority_id: Optional[str] = None
    penalty_profile_id: Optional[str] = None
    fine_range: Optional[Tuple[Optional[float], Optional[float]]] = None


class LawMatcher:
    """
    Matches text -> violation candidates using Person A laws.json structure:
      - canonical_violations
      - micro_violations
      - penalty_profiles
      - authorities
      - source_catalog
    """

    def __init__(self, laws_path: str) -> None:
        if not os.path.exists(laws_path):
            raise FileNotFoundError(f"laws.json not found at: {laws_path}")

        with open(laws_path, "r", encoding="utf-8") as f:
            self.laws: Dict[str, Any] = json.load(f)

        self._violations_index: List[Dict[str, Any]] = self._build_index()

    def _build_index(self) -> List[Dict[str, Any]]:
        canonical = self.laws.get("canonical_violations", [])
        micro = self.laws.get("micro_violations", [])

        index: List[Dict[str, Any]] = []

        for v in canonical:
            index.append({
                "violation_id": v.get("violation_id"),
                "title": v.get("title", ""),
                "keywords": v.get("keywords", []),
                "source_catalog_id": v.get("source_catalog_id"),
                "authority_id": v.get("authority_id"),
                "penalty_profile_id": v.get("penalty_profile_id"),
            })

        for v in micro:
            index.append({
                "violation_id": v.get("micro_violation_id"),
                "title": v.get("title", ""),
                "keywords": v.get("keywords", []),
                "source_catalog_id": v.get("source_catalog_id"),
                "authority_id": v.get("authority_id"),
                "penalty_profile_id": v.get("penalty_profile_id"),
            })

        # remove any entries missing IDs
        index = [x for x in index if isinstance(x.get("violation_id"), str) and x["violation_id"]]
        return index

    @staticmethod
    def _normalize(text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r"[^a-z0-9\s\-_/]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text

    @staticmethod
    def _similarity(a: str, b: str) -> float:
        return SequenceMatcher(None, a, b).ratio()

    def _penalty_fine_range(self, penalty_profile_id: Optional[str]) -> Optional[Tuple[Optional[float], Optional[float]]]:
        if not penalty_profile_id:
            return None
        for p in self.laws.get("penalty_profiles", []):
            if p.get("penalty_profile_id") == penalty_profile_id:
                # try to pull numeric fine range if available
                fine = p.get("fine_bdt", None)
                if isinstance(fine, dict):
                    mn = fine.get("min")
                    mx = fine.get("max")
                    mn_val = float(mn) if isinstance(mn, (int, float)) else None
                    mx_val = float(mx) if isinstance(mx, (int, float)) else None
                    return (mn_val, mx_val)
                return None
        return None

    def match_violation(self, text: str, top_k: int = 3) -> List[LawMatch]:
        """
        Public method (used by analyze.py). Returns top_k matches.
        """
        return self.match_text(text=text, top_k=top_k)

    def match_text(self, text: str, top_k: int = 3) -> List[LawMatch]:
        if not text or not isinstance(text, str):
            return []

        q = self._normalize(text)

        scored: List[Tuple[float, Dict[str, Any]]] = []
        for v in self._violations_index:
            title = self._normalize(v.get("title", ""))
            keywords = [self._normalize(k) for k in (v.get("keywords") or []) if isinstance(k, str)]

            # scoring: exact keyword hit > title similarity
            kw_hit = any(k and (k in q or q in k) for k in keywords)
            sim = self._similarity(q, title) if title else 0.0
            score = (0.65 if kw_hit else 0.0) + (0.35 * sim)

            if score > 0.25:  # low threshold, we’ll keep top_k
                scored.append((score, v))

        scored.sort(key=lambda x: x[0], reverse=True)
        results: List[LawMatch] = []

        for score, v in scored[:top_k]:
            penalty_profile_id = v.get("penalty_profile_id")
            results.append(
                LawMatch(
                    violation_id=str(v["violation_id"]),
                    title=str(v.get("title", "")),
                    score=float(score),
                    source_catalog_id=v.get("source_catalog_id"),
                    authority_id=v.get("authority_id"),
                    penalty_profile_id=penalty_profile_id,
                    fine_range=self._penalty_fine_range(penalty_profile_id),
                )
            )

        return results

    # Optional helpers used by /laws routes
    def list_violations(self) -> List[Dict[str, Any]]:
        return self._violations_index

    def get_violation(self, violation_id: str) -> Optional[Dict[str, Any]]:
        for v in self._violations_index:
            if v.get("violation_id") == violation_id:
                return v
        return None

    def get_authority(self, authority_id: str) -> Optional[Dict[str, Any]]:
        for a in self.laws.get("authorities", []):
            if a.get("authority_id") == authority_id:
                return a
        return None
