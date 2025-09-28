"""Pydantic schemas for overlay workflows."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


class OverlayDecisionRecord(BaseModel):
    """Decision metadata associated with an overlay suggestion."""

    id: int
    decision: str
    decided_by: str | None = None
    decided_at: datetime
    notes: str | None = None

    model_config = ConfigDict(from_attributes=True)


class OverlaySuggestion(BaseModel):
    """Overlay suggestion payload returned by the API."""

    id: int
    project_id: int
    source_geometry_id: int
    code: str
    type: str | None = None
    title: str
    rationale: str | None = None
    severity: str | None = None
    status: str
    engine_version: str | None = None
    engine_payload: dict[str, Any]
    target_ids: list[str] = []
    props: dict[str, Any] = {}
    rule_refs: list[str] = []
    score: float | None = None
    geometry_checksum: str
    created_at: datetime
    updated_at: datetime
    decided_at: datetime | None = None
    decided_by: str | None = None
    decision_notes: str | None = None
    decision: OverlayDecisionRecord | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("target_ids", mode="before")
    @classmethod
    def _ensure_target_ids(cls, value: object) -> list[str]:
        """Coerce target identifiers to a list of strings."""

        if value is None:
            return []
        if isinstance(value, (list, tuple, set)):
            return [str(item) for item in value if item not in (None, "")]
        return [str(value)]

    @field_validator("props", mode="before")
    @classmethod
    def _ensure_props(cls, value: object) -> dict[str, Any]:
        """Ensure a dictionary of properties is always returned."""

        if isinstance(value, dict):
            return dict(value)
        return {}

    @field_validator("rule_refs", mode="before")
    @classmethod
    def _ensure_rule_refs(cls, value: object) -> list[str]:
        """Coerce rule references to a list of strings."""

        if value is None:
            return []
        if isinstance(value, (list, tuple, set)):
            return [str(item) for item in value if item not in (None, "")]
        return [str(value)]


class OverlayDecisionPayload(BaseModel):
    """Request payload for approving or rejecting an overlay suggestion."""

    suggestion_id: int
    decision: str
    decided_by: str | None = None
    notes: str | None = None

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
