"""Audit logging models for tracking workflow instrumentation."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import BaseModel
from app.models.types import FlexibleJSONB


JSONType = FlexibleJSONB


class AuditLog(BaseModel):
    """Recorded metrics emitted by automation workflows."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    baseline_seconds: Mapped[float | None] = mapped_column(Float)
    actual_seconds: Mapped[float | None] = mapped_column(Float)
    context: Mapped[dict] = mapped_column(JSONType, default=dict)
    hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    prev_hash: Mapped[str | None] = mapped_column(String(64))
    signature: Mapped[str] = mapped_column(String(128), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    __table_args__ = (
        Index("idx_audit_logs_project_event", "project_id", "event_type"),
        Index("idx_audit_logs_project_version", "project_id", "version"),
        UniqueConstraint("project_id", "version", name="uq_audit_logs_project_version"),
    )


__all__ = ["AuditLog"]
