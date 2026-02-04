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
    # This shape matches what analyze.py expects (attribute access)
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

    Compatibility methods:
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

        # Authorities (normalize weird keys like "ju   urisdiction")
        self._authorities_index: Dict[str, JsonObj] = {}
        for a in self._iter_dict_items(self._raw.get("authorities")):
            if not isinstance(a, dict):
                continue
            a_norm = self._normalize_authority(a)
            aid = a_norm.get("authority_id")
            if isinstance(aid, str) and aid.strip():
                self._authorities_index[aid.strip()] = a_norm

        # Penalty profiles (list or dict) -> normalize into response-friendly shape
        self._penalties_index: Dict[str, JsonObj] = {}
        pp = self._raw.get("penalty_profiles")

        # 1) penalty_profiles is a list[dict] with penalty_profile_id
        for p in self._iter_dict_items(pp):
            pid = p.get("penalty_profile_id")
            if isinstance(pid, str) and pid.strip():
                self._penalties_index[pid.strip()] = self._normalize_penalty_profile(pid.strip(), p)

        # 2) penalty_profiles is a dict keyed by id (your current structure)
        if isinstance(pp, dict):
            for k, v in pp.items():
                if isinstance(k, str) and k.strip() and isinstance(v, dict):
                    self._penalties_index[k.strip()] = self._normalize_penalty_profile(k.strip(), v)

        # BNBC clause library
        self._clause_library: List[JsonObj] = []
        cl = self._raw.get("bnbc_clause_library")
        if isinstance(cl, list):
            self._clause_library = [x for x in cl if isinstance(x, dict)]

        # Tokenization helper
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

    @staticmethod
    def _normalize_authority(a: JsonObj) -> JsonObj:
        """
        Fix common data issues like a key containing extra spaces:
        e.g. "ju   urisdiction" -> "jurisdiction"
        """
        out = dict(a)

        if "jurisdiction" not in out:
            for k in list(out.keys()):
                if isinstance(k, str) and "".join(k.split()) == "jurisdiction":
                    out["jurisdiction"] = out.get(k)
                    break

        return out

    @staticmethod
    def _safe_int(x: Any) -> Optional[int]:
        try:
            if x is None:
                return None
            if isinstance(x, bool):
                return None
            return int(x)
        except Exception:
            return None

    def _normalize_penalty_profile(self, penalty_profile_id: str, p: JsonObj) -> JsonObj:
        """
        Convert internal penalty profile shapes (your laws.json structure) into the
        response model shape expected by PenaltyProfile:
          - penalty_profile_id
          - law_name
          - section
          - penalty_type
          - min_bdt
          - max_bdt
          - notes
        """
        law_name = p.get("law_name") or p.get("law")
        section = p.get("section")

        # Try to extract fine range from various shapes
        min_bdt = (
            p.get("min_bdt")
            or p.get("fine_min_bdt")
            or (p.get("first_offense") or {}).get("fine_min_bdt")
        )
        max_bdt = (
            p.get("max_bdt")
            or p.get("fine_max_bdt")
            or (p.get("first_offense") or {}).get("fine_max_bdt")
        )

        # Imprisonment hints (if present) — kept in notes
        first = p.get("first_offense") if isinstance(p.get("first_offense"), dict) else {}
        subsequent = p.get("subsequent_offense") if isinstance(p.get("subsequent_offense"), dict) else {}

        first_impr = first.get("imprisonment_max_months") if isinstance(first, dict) else None
        sub_impr = subsequent.get("imprisonment_max_months") if isinstance(subsequent, dict) else None

        penalty_type = p.get("penalty_type")
        if not isinstance(penalty_type, str) or not penalty_type.strip():
            if first_impr is not None or sub_impr is not None:
                penalty_type = "fine_or_imprisonment"
            else:
                penalty_type = "fine"

        # Build a useful notes string
        notes = p.get("notes") or p.get("summary")
        notes_parts: List[str] = []
        if isinstance(notes, str) and notes.strip():
            notes_parts.append(notes.strip())

        fmax = self._safe_int((first or {}).get("fine_max_bdt"))
        smax = self._safe_int((subsequent or {}).get("fine_max_bdt"))
        if fmax is not None or first_impr is not None:
            notes_parts.append(
                f"First offense: fine up to {fmax} BDT; imprisonment up to {self._safe_int(first_impr)} months."
                if first_impr is not None
                else f"First offense: fine up to {fmax} BDT."
            )
        if smax is not None or sub_impr is not None:
            notes_parts.append(
                f"Subsequent offense: fine up to {smax} BDT; imprisonment up to {self._safe_int(sub_impr)} months."
                if sub_impr is not None
                else f"Subsequent offense: fine up to {smax} BDT."
            )

        out_notes = " ".join([x for x in notes_parts if x])

        return {
            "penalty_profile_id": penalty_profile_id,
            "law_name": law_name,
            "section": section,
            "penalty_type": penalty_type,
            "min_bdt": self._safe_int(min_bdt),
            "max_bdt": self._safe_int(max_bdt),
            "notes": out_notes or None,
        }

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
        a = self._authorities_index.get(authority_id.strip())
        if not a:
            return None
        return self._normalize_authority(a)

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
                pid = item.strip()
                p = self._penalties_index.get(pid)
                if p:
                    penalties.append(p)
            elif isinstance(item, dict):
                pid = item.get("penalty_profile_id")
                if isinstance(pid, str) and pid.strip():
                    penalties.append(self._normalize_penalty_profile(pid.strip(), item))
                else:
                    # Best effort: keep but coerce into a stable shape
                    penalties.append(self._normalize_penalty_profile("UNKNOWN", item))

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

            t_tokens = set(self._tokenize(str(title)))
            if isinstance(keywords, list):
                for kw in keywords:
                    if isinstance(kw, str):
                        t_tokens.update(self._tokenize(kw))

            if not t_tokens:
                continue

            overlap = q_tokens.intersection(t_tokens)
            if not overlap:
                continue

            score = len(overlap) / max(1, len(q_tokens.union(t_tokens)))

            if isinstance(mapped_ids, list) and mapped_ids:
                for vid in mapped_ids[:5]:
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
    # Compatibility layer
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
        return self._match_clause_text(text, top_k=max(1, min(int(top_k), 20)))

    def get_laws_for_violation(self, violation_type: str) -> Optional[JsonObj]:
        return self._match_violation_id(violation_type)

    def get_violation(self, violation_id: str) -> Optional[JsonObj]:
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
