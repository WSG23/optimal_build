"""Pydantic schemas for security dashboard APIs."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.security import SecurityTicketStatus


class SecurityTicketResponse(BaseModel):
    """Security ticket payload."""

    id: UUID
    project_id: UUID | None = None
    title: str
    description: str
    status: SecurityTicketStatus
    location: str
    category: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SecurityTicketUpdate(BaseModel):
    """Update payload for a security ticket."""

    status: SecurityTicketStatus = Field(..., description="Updated ticket status")


class ThreatData(BaseModel):
    """Threat score data."""

    entity_id: str | None = None
    headline_score: int = Field(..., ge=0, le=100)


class SecurityOverviewResponse(BaseModel):
    """Security dashboard overview payload."""

    facility_label: str | None = None
    project_id: UUID | None = None
    tickets: list[SecurityTicketResponse] = Field(default_factory=list)
    threat: ThreatData
