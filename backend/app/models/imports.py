"""Models for tracking CAD/BIM imports."""

from __future__ import annotations

from uuid import uuid4

from app.models.base import BaseModel
from app.models.types import FlexibleJSONB
from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func


class ImportRecord(BaseModel):
    """Persisted import metadata for uploaded design files."""

    __tablename__ = "imports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id = Column(Integer, index=True)
    filename = Column(String(255), nullable=False)
    content_type = Column(String(100))
    size_bytes = Column(Integer, nullable=False)
    storage_path = Column(Text, nullable=False)
    zone_code = Column(String(50))
    uploaded_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    layer_metadata = Column(FlexibleJSONB, default=list)
    detected_floors = Column(FlexibleJSONB, default=list)
    detected_units = Column(FlexibleJSONB, default=list)
    vector_storage_path = Column(Text)
    vector_summary = Column(FlexibleJSONB)
    metric_overrides = Column(FlexibleJSONB, default=dict)

    parse_status = Column(String(32), nullable=False, default="pending")
    parse_requested_at = Column(DateTime(timezone=True))
    parse_completed_at = Column(DateTime(timezone=True))
    parse_error = Column(Text)
    parse_result = Column(FlexibleJSONB)


__all__ = ["ImportRecord"]
