"""Models supporting the agent advisory workflow."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID as UUIDType, uuid4

from app.models.base import BaseModel
from app.models.types import FlexibleJSONB
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class AgentAdvisoryFeedback(BaseModel):
    """Feedback captured from agents during advisory workflows."""

    __tablename__ = "agent_advisory_feedback"

    id: Mapped[UUIDType] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    property_id: Mapped[UUIDType] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    submitted_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    channel: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    sentiment: Mapped[str] = mapped_column(String(16), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[dict] = mapped_column(FlexibleJSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    property = relationship("Property", backref="advisory_feedback")


__all__ = ["AgentAdvisoryFeedback"]
