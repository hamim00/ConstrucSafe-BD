from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class LawMatcher:
    """Loads Person-A JSON and provides lookups.

    NOTE: Person A's file uses keys:
    - canonical_violations, micro_violations (not 'violations')
    - authorities
    - penalty_profiles
    - source_catalog (list)
    """

    def __init__(self, laws_file: str = "data/laws.json"):
        self._raw = self._load_laws(laws_file)

        self._violations_index: Dict[str, Dict[str, Any]] = {}
        for v in self._raw.get("canonical_violations", []) + self._raw.get("micro_violations", []):
            vid = v.get("violation_id")
            if vid:
                self._violations_index[vid] = v

        self._authorities_index: Dict[str, Dict[str, Any]] = {
            a.get("authority_id"): a for a in self._raw.get("authorities", []) if a.get("authority_id")
        }

    def _load_laws(self, filepath: str) -> Dict[str, Any]:
        base = Path(__file__).parent.parent
        with open(base / filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_all_violation_types(self) -> List[str]:
        return sorted(self._violations_index.keys())

    def get_authority_info(self, authority_id: str) -> Optional[Dict[str, Any]]:
        return self._authorities_index.get(authority_id)

    def get_violation_details(self, violation_id: str) -> Optional[Dict[str, Any]]:
        v = self._violations_index.get(violation_id)
        if not v:
            return None
        # In Phase 3 we expand this with penalties + law name mapping
        return v
