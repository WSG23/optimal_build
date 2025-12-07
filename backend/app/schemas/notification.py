"""Pydantic schemas for notification API."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.notification import NotificationPriority, NotificationType


class NotificationBase(BaseModel):
    """Base notification schema."""

    notification_type: NotificationType
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    priority: NotificationPriority = NotificationPriority.NORMAL


class NotificationCreate(NotificationBase):
    """Schema for creating a notification."""

    user_id: UUID
    project_id: Optional[UUID] = None
    related_entity_type: Optional[str] = Field(None, max_length=50)
    related_entity_id: Optional[UUID] = None
    expires_at: Optional[datetime] = None


class NotificationRead(NotificationBase):
    """Schema for reading a notification."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    project_id: Optional[UUID] = None
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[UUID] = None
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime
    expires_at: Optional[datetime] = None


class NotificationUpdate(BaseModel):
    """Schema for updating a notification (mark as read)."""

    is_read: bool


class NotificationBulkUpdate(BaseModel):
    """Schema for bulk updating notifications."""

    notification_ids: list[UUID]
    is_read: bool


class NotificationCount(BaseModel):
    """Schema for notification counts."""

    total: int
    unread: int


class NotificationList(BaseModel):
    """Schema for paginated notification list."""

    notifications: list[NotificationRead]
    total: int
    unread_count: int
    page: int
    page_size: int
    has_more: bool
