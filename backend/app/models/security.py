"""Security incident tracking models."""

from __future__ import annotations

import uuid
from enum import Enum

from backend._compat.datetime import utcnow
from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.models.base import UUID, BaseModel


class SecurityTicketStatus(str, Enum):
    """Status for security tickets."""

    OPEN = "open"
    LOCKED = "locked"
    RESOLVED_HARMFUL = "resolved_harmful"
    RESOLVED_MALFUNCTION = "resolved_malfunction"
    RESOLVED_NORMAL = "resolved_normal"
    DISMISSED = "dismissed"


class SecurityTicket(BaseModel):
    """Security incident ticket tied to a project/facility."""

    __tablename__ = "security_tickets"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(), ForeignKey("projects.id"), nullable=True, index=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(
        SQLEnum(SecurityTicketStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=SecurityTicketStatus.OPEN,
    )
    location = Column(String(255), nullable=False)
    category = Column(String(255), nullable=False)

    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    project = relationship("Project", back_populates="security_tickets")


__all__ = ["SecurityTicket", "SecurityTicketStatus"]
