from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union


JsonObj = Dict[str, Any]
JsonCollection = Union[List[Any], Dict[str, Any], None]


@dataclass(frozen=True)
class ClauseMatch:
    # This shape matches what your analyze.py expects (attribute access)
    violation_id: str
    title: str
    score: float
    source_catalog_id: Optional[str] = None
    clause_id: Optional[str] = None
    citation: Optional[str] = None
    section: Optional[str] = None
    pdf_page: Optional[int] = None
    gazette_page: Optional[int] = None
    confidence: Optional[str] = None


class LawMatcher:
    """
    Loads Person-A JSON (backend/data/laws.json) and provides:
      - exact violation_id lookups (laws/penalties)
      - BNBC clause library text search (top_k matches)

    Supports variations:
      - authorities: list[dict] OR dict[str, dict]
      - penalty_profiles: list[dict] OR dict[str, dict]  (your current case: dict)

    Compatibility methods for older routers:
      - list_violations()
      - get_authority()
      - match_violation_text()
      - get_laws_for_violation()
      - get_violation()
    """

    def __init__(self, laws_file: str = "data/laws.json", laws_path: Optional[str] = None):
        filepath = laws_path or laws_file
        self._raw: JsonObj = self._load_laws(filepath)

        # Index violations (canonical + micro)
        self._violations_index: Dict[str, JsonObj] = {}
        for v in self._iter_dict_items(self._raw.get("canonical_violations")):
            vid = v.get("violation_id")
            if isinstance(vid, str) and vid.strip():
                self._violations_index[vid.strip()] = v

        for v in self._iter_dict_items(self._raw.get("micro_violations")):
            vid = v.get("violation_id")
            if isinstance(vid, str) and vid.strip():
                self._violations_index[vid.strip()] = v

        # Authorities
        self._authorities_index: Dict[str, JsonObj] = {}
        for a in self._iter_dict_items(self._raw.get("authorities")):
            aid = a.get("authority_id")
            if isinstance(aid, str) and aid.strip():
                self._authorities_index[aid.strip()] = a

        # Penalty profiles (list or dict)
        self._penalties_index: Dict[str, JsonObj] = {}
        pp = self._raw.get("penalty_profiles")
        for p in self._iter_dict_items(pp):
            pid = p.get("penalty_profile_id")
            if isinstance(pid, str) and pid.strip():
                self._penalties_index[pid.strip()] = p
        if isinstance(pp, dict):
            for k, v in pp.items():
                if isinstance(k, str) and k.strip() and isinstance(v, dict):
                    self._penalties_index.setdefault(k.strip(), v)

        # BNBC clause library
        self._clause_library: List[JsonObj] = []
        cl = self._raw.get("bnbc_clause_library")
        if isinstance(cl, list):
            self._clause_library = [x for x in cl if isinstance(x, dict)]

        # Tokenization helpers
        self._word_re = re.compile(r"[a-z0-9]+")

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------

    def _load_laws(self, filepath: str) -> JsonObj:
        p = Path(filepath)
        if not p.is_absolute():
            base = Path(__file__).parent.parent  # backend/
            p = base / filepath

        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("laws.json root must be a JSON object")
        return data

    def _iter_dict_items(self, value: JsonCollection) -> Iterable[JsonObj]:
        if isinstance(value, list):
            for x in value:
                if isinstance(x, dict):
                    yield x
            return
        if isinstance(value, dict):
            for x in value.values():
                if isinstance(x, dict):
                    yield x
            return
        return

    def _tokenize(self, text: str) -> List[str]:
        if not text:
            return []
        return self._word_re.findall(text.lower())

    # ---------------------------------------------------------------------
    # Core APIs
    # ---------------------------------------------------------------------

    def get_all_violation_types(self) -> List[str]:
        return sorted(self._violations_index.keys())

    def get_violation_details(self, violation_id: str) -> Optional[JsonObj]:
        if not violation_id:
            return None
        return self._violations_index.get(violation_id.strip())

    def get_authority_info(self, authority_id: str) -> Optional[JsonObj]:
        if not authority_id:
            return None
        return self._authorities_index.get(authority_id.strip())

    def match_violation(self, query: str, top_k: Optional[int] = None) -> Optional[Union[JsonObj, List[ClauseMatch]]]:
        """
        Dual-mode matcher.

        Mode A (exact violation lookup):
            match_violation("PPE_HELMET_MISSING") -> dict law bundle
            Triggered when top_k is None.

        Mode B (text search over BNBC clause library):
            match_violation("no guardrail on scaffold", top_k=3) -> List[ClauseMatch]
        """
        if top_k is None:
            return self._match_violation_id(query)

        # Text search mode
        k = int(top_k) if isinstance(top_k, int) else 3
        k = max(1, min(k, 20))
        return self._match_clause_text(query, top_k=k)

    # ---------------------------------------------------------------------
    # Mode A: Exact violation_id -> normalized bundle
    # ---------------------------------------------------------------------

    def _match_violation_id(self, violation_type: str) -> Optional[JsonObj]:
        if not violation_type:
            return None
        key = violation_type.strip()
        v = self._violations_index.get(key)
        if not v:
            return None

        laws: List[JsonObj] = []
        for lr in (v.get("legal_references") or []):
            if isinstance(lr, dict):
                laws.append(
                    {
                        "source_id": lr.get("source_id"),
                        "citation": lr.get("citation"),
                        "interpretation": lr.get("interpretation"),
                        "confidence": lr.get("confidence"),
                    }
                )

        penalties: List[JsonObj] = []
        for item in (v.get("penalty_profiles") or []):
            if isinstance(item, str):
                p = self._penalties_index.get(item.strip())
                if p:
                    penalties.append(p)
            elif isinstance(item, dict):
                penalties.append(item)

        recommended: List[str] = []
        enf = v.get("enforcement")
        if isinstance(enf, dict):
            pa = enf.get("primary_authority")
            if isinstance(pa, str) and pa.strip():
                recommended.append(f"Notify/coordinate with: {pa.strip()}")

        return {
            "violation_id": v.get("violation_id"),
            "display_name_en": v.get("display_name_en"),
            "display_name_bn": v.get("display_name_bn"),
            "category": v.get("category"),
            "severity": v.get("severity"),
            "laws": laws,
            "penalties": penalties,
            "recommended_actions": recommended,
        }

    # ---------------------------------------------------------------------
    # Mode B: Text search over BNBC clause library -> ClauseMatch[]
    # ---------------------------------------------------------------------

    def _match_clause_text(self, text: str, top_k: int = 3) -> List[ClauseMatch]:
        q_tokens = set(self._tokenize(text))
        if not q_tokens:
            return []

        scored: List[ClauseMatch] = []

        for clause in self._clause_library:
            title = clause.get("title") or ""
            keywords = clause.get("keywords") or []
            mapped_ids = clause.get("mapped_violation_ids") or []

            # Build token bag from title + keywords
            t_tokens = set(self._tokenize(str(title)))
            if isinstance(keywords, list):
                for kw in keywords:
                    if isinstance(kw, str):
                        t_tokens.update(self._tokenize(kw))

            if not t_tokens:
                continue

            # Simple overlap score
            overlap = q_tokens.intersection(t_tokens)
            if not overlap:
                continue

            # Jaccard-ish score (bounded 0..1)
            score = len(overlap) / max(1, len(q_tokens.union(t_tokens)))

            # Clause may map to multiple violation IDs; emit one match per mapped id
            if isinstance(mapped_ids, list) and mapped_ids:
                for vid in mapped_ids[:5]:  # avoid exploding
                    if isinstance(vid, str) and vid.strip():
                        scored.append(
                            ClauseMatch(
                                violation_id=vid.strip(),
                                title=str(title),
                                score=float(score),
                                source_catalog_id=clause.get("source_id"),
                                clause_id=clause.get("clause_id"),
                                citation=clause.get("citation"),
                                section=clause.get("section"),
                                pdf_page=clause.get("pdf_page"),
                                gazette_page=clause.get("gazette_page"),
                                confidence=clause.get("confidence"),
                            )
                        )
            else:
                # fallback: unknown mapped id
                scored.append(
                    ClauseMatch(
                        violation_id="",
                        title=str(title),
                        score=float(score),
                        source_catalog_id=clause.get("source_id"),
                        clause_id=clause.get("clause_id"),
                        citation=clause.get("citation"),
                        section=clause.get("section"),
                        pdf_page=clause.get("pdf_page"),
                        gazette_page=clause.get("gazette_page"),
                        confidence=clause.get("confidence"),
                    )
                )

        scored.sort(key=lambda m: m.score, reverse=True)
        return scored[:top_k]

    # ---------------------------------------------------------------------
    # Compatibility layer (for older routers / older code)
    # ---------------------------------------------------------------------

    def list_violations(self) -> List[JsonObj]:
        out: List[JsonObj] = []
        for vid, v in self._violations_index.items():
            out.append(
                {
                    "violation_id": vid,
                    "display_name_en": v.get("display_name_en"),
                    "display_name_bn": v.get("display_name_bn"),
                    "category": v.get("category"),
                    "severity": v.get("severity"),
                }
            )
        out.sort(key=lambda x: str(x.get("violation_id", "")))
        return out

    def get_authority(self, authority_id: str) -> Optional[JsonObj]:
        return self.get_authority_info(authority_id)

    def match_violation_text(self, text: str, top_k: int = 3) -> List[ClauseMatch]:
        # Explicit text-mode API
        return self._match_clause_text(text, top_k=max(1, min(int(top_k), 20)))

    def get_laws_for_violation(self, violation_type: str) -> Optional[JsonObj]:
        # Alias used in older task doc and earlier phases
        return self._match_violation_id(violation_type)

    def get_violation(self, violation_id: str) -> Optional[JsonObj]:
        """
        Some analyze.py versions call matcher.get_violation(vid) then read record['title'].
        We provide a stable 'title' mapping to display_name_en.
        """
        v = self.get_violation_details(violation_id)
        if not v:
            return None
        return {
            "violation_id": v.get("violation_id"),
            "title": v.get("display_name_en") or v.get("display_name_bn") or v.get("violation_id"),
            "display_name_en": v.get("display_name_en"),
            "display_name_bn": v.get("display_name_bn"),
            "category": v.get("category"),
            "severity": v.get("severity"),
        }
