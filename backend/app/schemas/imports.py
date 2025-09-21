"""Pydantic schemas for import and parse workflows."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DetectedFloor(BaseModel):
    """Summary of a detected floor and its units."""

    name: str = Field(..., description="Human readable floor name")
    unit_ids: List[str] = Field(default_factory=list, description="Units located on this floor")


class ImportResult(BaseModel):
    """Response payload returned after uploading a CAD/BIM model."""

    import_id: str
    filename: str
    content_type: Optional[str]
    size_bytes: int
    storage_path: str
    vector_storage_path: Optional[str] = Field(
        default=None, description="URI of stored vectorised geometry derived from the upload"
    )
    uploaded_at: datetime
    layer_metadata: List[Dict[str, Any]]
    detected_floors: List[DetectedFloor]
    detected_units: List[str]
    vector_summary: Optional[Dict[str, Any]] = Field(
        default=None, description="Summary of extracted vector paths and inferred walls"
    )
    parse_status: str

    class Config:
        """Model configuration."""

        from_attributes = True


class ParseStatusResponse(BaseModel):
    """Status for a parse job associated with an import."""

    import_id: str
    status: str
    requested_at: Optional[datetime]
    completed_at: Optional[datetime]
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    job_id: Optional[str] = None

    class Config:
        """Model configuration."""

        from_attributes = True


__all__ = ["DetectedFloor", "ImportResult", "ParseStatusResponse"]
