from __future__ import annotations

from pydantic import BaseModel, Field


class ReportRequest(BaseModel):
    """Request body for PDF report generation."""
    analysis: dict = Field(..., description="The analysis JSON (same shape as /analyze response)")
    title: str = Field(default="ConstrucSafe BD Report")
