"""Preview job models for developer visualisation pipeline."""

from __future__ import annotations

import uuid
from enum import Enum

from sqlalchemy import Column, DateTime, ForeignKey, Index, JSON, String
from sqlalchemy.types import Enum as SQLEnum
from sqlalchemy.orm import relationship

from backend._compat.datetime import utcnow

from app.models.base import BaseModel, MetadataProxy, UUID


def _enum_values(enum_cls: type[Enum]) -> list[str]:
    return [member.value for member in enum_cls]


class PreviewJobStatus(str, Enum):
    """Status values for preview generation jobs."""

    QUEUED = "queued"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    EXPIRED = "expired"


class PreviewJob(BaseModel):
    """Represents a preview generation job for a property scenario."""

    __tablename__ = "preview_jobs"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(), ForeignKey("properties.id"), nullable=False)
    scenario = Column(String(80), nullable=False, default="base")
    status = Column(
        SQLEnum(
            PreviewJobStatus,
            name="preview_job_status",
            values_callable=_enum_values,
        ),
        nullable=False,
        default=PreviewJobStatus.QUEUED,
    )
    requested_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    started_at = Column(DateTime(timezone=True))
    finished_at = Column(DateTime(timezone=True))
    asset_version = Column(String(64))
    preview_url = Column(String(500))
    thumbnail_url = Column(String(500))
    payload_checksum = Column(String(128))
    message = Column(String(500))
    metadata_json = Column(JSON, nullable=False, default=dict)

    metadata = MetadataProxy()

    property = relationship("Property", backref="preview_jobs")

    __table_args__ = (Index("ix_preview_jobs_property", "property_id"),)


__all__ = ["PreviewJob", "PreviewJobStatus"]
