"""Pydantic schemas for standards APIs."""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict


class MaterialStandard(BaseModel):
    """Material standard response payload."""

    id: int
    standard_code: str
    material_type: str
    standard_body: str
    property_key: str
    value: str
    unit: str | None
    context: dict[str, Any] | None
    section: str | None
    applicability: dict[str, Any] | None
    edition: str | None
    effective_date: date | None
    license_ref: str | None
    provenance: dict[str, Any] | None
    source_document: str | None

    model_config = ConfigDict(from_attributes=True)
