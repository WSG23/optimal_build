"""Pydantic schemas for notification API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.notification import NotificationPriority, NotificationType


class NotificationBase(BaseModel):
    """Base notification schema."""

    notification_type: NotificationType
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    priority: NotificationPriority = NotificationPriority.NORMAL
    related_entity_type: str | None = None
    related_entity_id: UUID | None = None
    action_url: str | None = None


class NotificationCreate(NotificationBase):
    """Schema for creating a notification."""

    user_id: UUID


class NotificationResponse(NotificationBase):
    """Schema for notification response."""

    id: UUID
    user_id: UUID
    is_read: bool
    is_dismissed: bool
    created_at: datetime
    read_at: datetime | None
    dismissed_at: datetime | None

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Paginated list of notifications."""

    items: list[NotificationResponse]
    total: int
    unread_count: int
    page: int
    page_size: int
    has_more: bool


class NotificationMarkReadRequest(BaseModel):
    """Request to mark notifications as read."""

    notification_ids: list[UUID] = Field(default_factory=list)
    mark_all: bool = False


class NotificationMarkReadResponse(BaseModel):
    """Response after marking notifications as read."""

    marked_count: int


class NotificationDismissRequest(BaseModel):
    """Request to dismiss notifications."""

    notification_ids: list[UUID] = Field(default_factory=list)
    dismiss_all: bool = False


class NotificationDismissResponse(BaseModel):
    """Response after dismissing notifications."""

    dismissed_count: int


class NotificationCountResponse(BaseModel):
    """Response with notification counts."""

    total: int
    unread: int
    by_type: dict[str, int]


class EmailLogResponse(BaseModel):
    """Schema for email log response."""

    id: UUID
    recipient_email: str
    subject: str
    template_name: str | None
    status: str
    error_message: str | None
    notification_id: UUID | None
    created_at: datetime
    sent_at: datetime | None

    class Config:
        from_attributes = True
