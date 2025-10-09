"""Pydantic schemas for import and parse workflows."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DetectedFloor(BaseModel):
    """Summary of a detected floor and its units."""

    name: str = Field(..., description="Human readable floor name")
    unit_ids: list[str] = Field(
        default_factory=list, description="Units located on this floor"
    )


class ImportResult(BaseModel):
    """Response payload returned after uploading a CAD/BIM model."""

    import_id: str
    filename: str
    content_type: str | None
    size_bytes: int
    storage_path: str
    vector_storage_path: str | None = Field(
        default=None,
        description="URI of stored vectorised geometry derived from the upload",
    )
    uploaded_at: datetime
    layer_metadata: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Layer metadata detected during upload or derived from vectorization",
    )
    detected_floors: list[DetectedFloor] = Field(
        default_factory=list,
        description="Floors detected during upload for quick-look summaries",
    )
    detected_units: list[str] = Field(
        default_factory=list,
        description="Unit identifiers detected during upload",
    )
    vector_summary: dict[str, Any] | None = Field(
        default=None, description="Summary of extracted vector paths and inferred walls"
    )
    zone_code: str | None = Field(
        default=None, description="Zoning code associated with the import"
    )
    metric_overrides: dict[str, Any] | None = Field(
        default=None,
        description="Reviewer-supplied metric overrides for rule evaluation",
    )
    parse_status: str

    model_config = ConfigDict(from_attributes=True)


class ParseStatusResponse(BaseModel):
    """Status for a parse job associated with an import."""

    import_id: str
    status: str
    requested_at: datetime | None
    completed_at: datetime | None
    result: dict[str, Any] | None = None
    error: str | None = None
    job_id: str | None = None

    model_config = ConfigDict(from_attributes=True)


__all__ = ["DetectedFloor", "ImportResult", "ParseStatusResponse"]
