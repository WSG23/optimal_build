"""Pydantic schemas for property resources."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.singapore_property import ComplianceStatus, SingaporeProperty


class PropertyComplianceSummary(BaseModel):
    """Aggregated compliance outcome for a property."""

    bca_status: str | None = None
    ura_status: str | None = None
    notes: str | None = None
    last_checked: datetime | None = None
    data: dict[str, Any] = Field(default_factory=dict)


class SingaporePropertySchema(BaseModel):
    """Reduced representation of a :class:`SingaporeProperty` instance."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    property_name: str
    address: str
    zoning: str | None = None
    planning_area: str | None = None
    compliance: PropertyComplianceSummary | None = None
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="before")
    @classmethod
    def _from_orm(cls, value: Any) -> Any:
        if isinstance(value, SingaporeProperty):
            compliance = PropertyComplianceSummary(
                bca_status=_as_string(value.bca_compliance_status),
                ura_status=_as_string(value.ura_compliance_status),
                notes=value.compliance_notes,
                last_checked=value.compliance_last_checked,
                data=value.compliance_data or {},
            )
            return {
                "id": value.id,
                "property_name": value.property_name,
                "address": value.address,
                "zoning": _as_string(value.zoning),
                "planning_area": value.planning_area,
                "compliance": compliance,
                "created_at": value.created_at,
                "updated_at": value.updated_at,
            }
        return value


def _as_string(obj: Any) -> str | None:
    if obj is None:
        return None
    if isinstance(obj, ComplianceStatus):
        return obj.value
    if hasattr(obj, "value"):
        return str(obj.value)
    return str(obj)


__all__ = ["PropertyComplianceSummary", "SingaporePropertySchema"]
