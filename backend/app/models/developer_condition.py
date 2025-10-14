"""Models for developer condition assessments."""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text, func

from app.models.base import UUID, Base


class DeveloperConditionAssessmentRecord(Base):
    """Persisted condition assessment captured via developer inspection."""

    __tablename__ = "developer_condition_assessments"

    id = Column(UUID(), primary_key=True, default=uuid4)
    property_id = Column(
        UUID(),
        nullable=False,
        index=True,
    )
    scenario = Column(String(50), nullable=True, index=True)
    overall_rating = Column(String(10), nullable=False)
    overall_score = Column(Integer, nullable=False)
    risk_level = Column(String(20), nullable=False)
    summary = Column(Text, nullable=False)
    scenario_context = Column(Text, nullable=True)
    systems = Column(JSON, nullable=False, server_default="[]", default=list)
    recommended_actions = Column(
        JSON, nullable=False, server_default="[]", default=list
    )
    recorded_by = Column(
        UUID(),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    recorded_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


__all__ = ["DeveloperConditionAssessmentRecord"]
