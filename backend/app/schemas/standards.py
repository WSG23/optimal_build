"""Pydantic schemas for standards APIs."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, Optional

from pydantic import BaseModel


class MaterialStandard(BaseModel):
    """Material standard response payload."""

    id: int
    standard_code: str
    material_type: str
    standard_body: str
    property_key: str
    value: str
    unit: Optional[str]
    context: Optional[Dict[str, Any]]
    section: Optional[str]
    applicability: Optional[Dict[str, Any]]
    edition: Optional[str]
    effective_date: Optional[date]
    license_ref: Optional[str]
    provenance: Optional[Dict[str, Any]]
    source_document: Optional[str]

    class Config:
        """Pydantic configuration."""

        from_attributes = True
