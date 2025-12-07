"""Notification models for team coordination."""

import uuid
from enum import Enum

from backend._compat.datetime import utcnow

from app.models.base import UUID, BaseModel
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import relationship


class NotificationType(str, Enum):
    """Types of notifications."""

    # Team-related
    TEAM_INVITATION = "team_invitation"
    TEAM_MEMBER_JOINED = "team_member_joined"
    TEAM_MEMBER_REMOVED = "team_member_removed"

    # Workflow-related
    WORKFLOW_CREATED = "workflow_created"
    WORKFLOW_STEP_ASSIGNED = "workflow_step_assigned"
    WORKFLOW_STEP_COMPLETED = "workflow_step_completed"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_APPROVAL_NEEDED = "workflow_approval_needed"
    WORKFLOW_REJECTED = "workflow_rejected"

    # Project-related
    PROJECT_UPDATE = "project_update"
    PROJECT_MILESTONE = "project_milestone"

    # Regulatory-related
    REGULATORY_STATUS_CHANGE = "regulatory_status_change"
    REGULATORY_RFI = "regulatory_rfi"

    # System
    SYSTEM_ANNOUNCEMENT = "system_announcement"


class NotificationPriority(str, Enum):
    """Priority levels for notifications."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Notification(BaseModel):
    """Notification model for in-app notifications."""

    __tablename__ = "notifications"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)

    # Recipient
    user_id = Column(UUID(), ForeignKey("users.id"), nullable=False, index=True)

    # Notification content
    notification_type = Column(
        SQLEnum(NotificationType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
    )
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    priority = Column(
        SQLEnum(NotificationPriority, values_callable=lambda x: [e.value for e in x]),
        default=NotificationPriority.NORMAL,
        nullable=False,
    )

    # Context links (optional - for navigation)
    project_id = Column(UUID(), ForeignKey("projects.id"), nullable=True, index=True)
    related_entity_type = Column(
        String(50), nullable=True
    )  # e.g., "workflow", "team_invitation"
    related_entity_id = Column(UUID(), nullable=True)

    # Status
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=utcnow, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=True)  # Optional expiration

    # Relationships
    user = relationship("User", backref="notifications")
    project = relationship("Project", backref="notifications")

    def mark_as_read(self) -> None:
        """Mark the notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = utcnow()

    def is_expired(self) -> bool:
        """Check if notification has expired."""
        if self.expires_at is None:
            return False
        now = utcnow()
        expires = self.expires_at
        # Handle timezone differences
        if expires.tzinfo is None and now.tzinfo is not None:
            now = now.replace(tzinfo=None)
        return now > expires

    def __repr__(self) -> str:
        return f"<Notification {self.id} type={self.notification_type} user={self.user_id}>"
