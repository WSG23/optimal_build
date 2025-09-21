"""Project audit logging models."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import BaseModel
from app.models.types import FlexibleJSONB


class ProjectAuditLog(BaseModel):
    """Discrete audit events captured for ROI analytics."""

    __tablename__ = "project_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    baseline_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    automated_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    accepted_suggestions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata: Mapped[dict] = mapped_column(FlexibleJSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        index=True,
    )


__all__ = ["ProjectAuditLog"]
