"""Pydantic schemas for overlay workflows."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, field_validator


class OverlayDecisionRecord(BaseModel):
    """Decision metadata associated with an overlay suggestion."""

    id: int
    decision: str
    decided_by: Optional[str] = None
    decided_at: datetime
    notes: Optional[str] = None

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class OverlaySuggestion(BaseModel):
    """Overlay suggestion payload returned by the API."""

    id: int
    project_id: int
    source_geometry_id: int
    code: str
    title: str
    rationale: Optional[str] = None
    severity: Optional[str] = None
    status: str
    engine_version: Optional[str] = None
    engine_payload: Dict[str, Any]
    score: Optional[float] = None
    geometry_checksum: str
    created_at: datetime
    updated_at: datetime
    decided_at: Optional[datetime] = None
    decided_by: Optional[str] = None
    decision_notes: Optional[str] = None
    decision: Optional[OverlayDecisionRecord] = None

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class OverlayDecisionPayload(BaseModel):
    """Request payload for approving or rejecting an overlay suggestion."""

    suggestion_id: int
    decision: str
    decided_by: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("decision")
    @classmethod
    def _ensure_decision_present(cls, value: str) -> str:
        """Ensure a non-empty decision value is supplied."""

        if not value or not value.strip():
            raise ValueError("decision must not be empty")
        return value


__all__ = [
    "OverlayDecisionPayload",
    "OverlayDecisionRecord",
    "OverlaySuggestion",
]
