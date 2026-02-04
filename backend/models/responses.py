from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class SeverityLevel(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class ConfidenceLevel(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class DetectedViolation(BaseModel):
    violation_type: str
    description: str
    severity: SeverityLevel
    confidence: ConfidenceLevel
    location: str
    affected_parties: List[str]


class LawReference(BaseModel):
    """Reference into Person-A source catalog.

    Mirrors `legal_references` entries in Person-A JSON.
    """

    source_id: str | None = None
    citation: str | None = None
    interpretation: str | None = None
    confidence: str | None = None


class PenaltyProfile(BaseModel):
    """Penalty profile object from Person-A JSON."""

    penalty_profile_id: str | None = None
    law_name: str | None = None
    section: str | None = None
    penalty_type: str | None = None
    min_bdt: Optional[int] = None
    max_bdt: Optional[int] = None
    notes: str | None = None


class ViolationWithLaw(BaseModel):
    violation: DetectedViolation
    laws: List[LawReference]
    penalties: List[PenaltyProfile] = []
    recommended_actions: List[str]


class FlaggedViolationWithLaw(BaseModel):
    """A violation hypothesis that must be confirmed by a human inspector.

    We still attach law citations and penalty profiles to help reviewers, but these are
    conditional until verification.
    """

    violation: DetectedViolation
    laws: List[LawReference]
    penalties: List[PenaltyProfile] = []
    recommended_actions: List[str]

    flag_reason: str
    requires_human_verification: bool = True
    assumption_note: str | None = None


class AnalysisResponse(BaseModel):
    success: bool
    image_id: str
    timestamp: str
    violations_found: int
    violations: List[ViolationWithLaw]

    # New: sensitive/uncertain detections
    flagged_found: int = 0
    flagged_for_review: List[FlaggedViolationWithLaw] = []

    # New: image quality hint for UI
    image_quality: str | None = None

    # New: pre-aggregated UI counts/priorities (optional)
    ui_summary: dict | None = None
    disclaimer: str
