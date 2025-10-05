"""Schemas for compliance assessment APIs."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict
from uuid import UUID

from app.schemas.property import PropertyComplianceSummary
from pydantic import BaseModel, Field


class ComplianceCheckRequest(BaseModel):
    """Payload requesting a property compliance refresh."""

    property_id: UUID
    refresh_geometry: bool = False


class ComplianceCheckResponse(BaseModel):
    """Response emitted after running compliance checks."""

    property_id: UUID
    compliance: PropertyComplianceSummary
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "ComplianceCheckRequest",
    "ComplianceCheckResponse",
]
