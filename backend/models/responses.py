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
    law_name: str
    section: str
    description: str
    penalty_min_bdt: Optional[int] = None
    penalty_max_bdt: Optional[int] = None
    authority: str


class ViolationWithLaw(BaseModel):
    violation: DetectedViolation
    laws: List[LawReference]
    recommended_actions: List[str]


class AnalysisResponse(BaseModel):
    success: bool
    image_id: str
    timestamp: str
    violations_found: int
    violations: List[ViolationWithLaw]
    disclaimer: str
