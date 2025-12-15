"""Notification models for in-app and email notifications."""

import uuid
from enum import Enum

from backend._compat.datetime import utcnow

from app.models.base import UUID, BaseModel
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship


class NotificationType(str, Enum):
    """Types of notifications."""

    # Team notifications
    TEAM_INVITE = "team_invite"
    TEAM_INVITE_ACCEPTED = "team_invite_accepted"
    TEAM_MEMBER_JOINED = "team_member_joined"
    TEAM_MEMBER_LEFT = "team_member_left"

    # Workflow notifications
    WORKFLOW_CREATED = "workflow_created"
    WORKFLOW_APPROVAL_PENDING = "workflow_approval_pending"
    WORKFLOW_APPROVED = "workflow_approved"
    WORKFLOW_REJECTED = "workflow_rejected"
    WORKFLOW_STEP_COMPLETED = "workflow_step_completed"

    # Regulatory notifications
    SUBMISSION_STATUS_CHANGED = "submission_status_changed"
    SUBMISSION_APPROVED = "submission_approved"
    SUBMISSION_REJECTED = "submission_rejected"
    SUBMISSION_RFI = "submission_rfi"

    # General
    SYSTEM = "system"
    REMINDER = "reminder"


class NotificationPriority(str, Enum):
    """Priority levels for notifications."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Notification(BaseModel):
    """In-app notification for users."""

    __tablename__ = "notifications"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(), ForeignKey("users.id"), nullable=False, index=True)

    # Notification content
    notification_type = Column(
        SQLEnum(NotificationType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    priority = Column(
        SQLEnum(NotificationPriority, values_callable=lambda x: [e.value for e in x]),
        default=NotificationPriority.NORMAL,
        nullable=False,
    )

    # Related entity for deep linking
    related_entity_type = Column(
        String(50), nullable=True
    )  # e.g., 'project', 'workflow', 'submission'
    related_entity_id = Column(UUID(), nullable=True)

    # Action URL for one-click navigation
    action_url = Column(String(500), nullable=True)

    # Status tracking
    is_read = Column(Boolean, default=False, nullable=False)
    is_dismissed = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=utcnow, nullable=False, index=True)
    read_at = Column(DateTime, nullable=True)
    dismissed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", backref="notifications")

    def mark_as_read(self) -> None:
        """Mark the notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = utcnow()

    def dismiss(self) -> None:
        """Dismiss the notification."""
        if not self.is_dismissed:
            self.is_dismissed = True
            self.dismissed_at = utcnow()


class EmailLog(BaseModel):
    """Log of sent emails for audit and debugging."""

    __tablename__ = "email_logs"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    recipient_email = Column(String(255), nullable=False, index=True)
    subject = Column(String(500), nullable=False)
    template_name = Column(String(100), nullable=True)

    # Status
    status = Column(
        String(50), default="pending", nullable=False
    )  # pending, sent, failed
    error_message = Column(Text, nullable=True)

    # Related notification
    notification_id = Column(UUID(), ForeignKey("notifications.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=utcnow, nullable=False)
    sent_at = Column(DateTime, nullable=True)

    # Relationships
    notification = relationship("Notification", backref="email_logs")
