"""API endpoints for notifications."""

from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core.database import get_session
from app.models.notification import NotificationType
from app.schemas.notification import (
    NotificationBulkUpdate,
    NotificationCount,
    NotificationList,
    NotificationRead,
)
from app.services.notification import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationList)
async def list_notifications(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    unread_only: bool = Query(False, description="Filter to unread only"),
    notification_type: Optional[NotificationType] = Query(
        None, description="Filter by notification type"
    ),
    project_id: Optional[UUID] = Query(None, description="Filter by project"),
    db: AsyncSession = Depends(get_session),
    identity: deps.RequestIdentity = Depends(deps.get_identity),
) -> Any:
    """
    List notifications for the current user with pagination.
    """
    if not identity.user_id:
        raise HTTPException(
            status_code=401, detail="Authentication required to view notifications"
        )

    service = NotificationService(db)
    user_id = UUID(identity.user_id)

    notifications, total, unread_count = await service.get_notifications(
        user_id=user_id,
        unread_only=unread_only,
        notification_type=notification_type,
        project_id=project_id,
        page=page,
        page_size=page_size,
    )

    has_more = (page * page_size) < total

    return NotificationList(
        notifications=[NotificationRead.model_validate(n) for n in notifications],
        total=total,
        unread_count=unread_count,
        page=page,
        page_size=page_size,
        has_more=has_more,
    )


@router.get("/count", response_model=NotificationCount)
async def get_notification_count(
    db: AsyncSession = Depends(get_session),
    identity: deps.RequestIdentity = Depends(deps.get_identity),
) -> Any:
    """
    Get notification counts (total and unread) for the current user.
    """
    if not identity.user_id:
        raise HTTPException(
            status_code=401, detail="Authentication required to view notifications"
        )

    service = NotificationService(db)
    user_id = UUID(identity.user_id)

    _, total, unread = await service.get_notifications(
        user_id=user_id, page=1, page_size=1
    )

    return NotificationCount(total=total, unread=unread)


@router.get("/{notification_id}", response_model=NotificationRead)
async def get_notification(
    notification_id: UUID,
    db: AsyncSession = Depends(get_session),
    identity: deps.RequestIdentity = Depends(deps.get_identity),
) -> Any:
    """
    Get a specific notification by ID.
    """
    if not identity.user_id:
        raise HTTPException(
            status_code=401, detail="Authentication required to view notification"
        )

    service = NotificationService(db)
    user_id = UUID(identity.user_id)

    notification = await service.get_notification_by_id(notification_id, user_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    return NotificationRead.model_validate(notification)


@router.patch("/{notification_id}/read", response_model=NotificationRead)
async def mark_notification_as_read(
    notification_id: UUID,
    db: AsyncSession = Depends(get_session),
    identity: deps.RequestIdentity = Depends(deps.get_identity),
) -> Any:
    """
    Mark a specific notification as read.
    """
    if not identity.user_id:
        raise HTTPException(
            status_code=401, detail="Authentication required to update notification"
        )

    service = NotificationService(db)
    user_id = UUID(identity.user_id)

    success = await service.mark_as_read(notification_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification = await service.get_notification_by_id(notification_id, user_id)
    return NotificationRead.model_validate(notification)


@router.post("/read-all", response_model=dict)
async def mark_all_notifications_as_read(
    db: AsyncSession = Depends(get_session),
    identity: deps.RequestIdentity = Depends(deps.get_identity),
) -> Any:
    """
    Mark all notifications as read for the current user.
    """
    if not identity.user_id:
        raise HTTPException(
            status_code=401, detail="Authentication required to update notifications"
        )

    service = NotificationService(db)
    user_id = UUID(identity.user_id)

    count = await service.mark_all_as_read(user_id)

    return {"message": f"Marked {count} notifications as read", "count": count}


@router.post("/read-bulk", response_model=dict)
async def mark_bulk_notifications_as_read(
    bulk_update: NotificationBulkUpdate,
    db: AsyncSession = Depends(get_session),
    identity: deps.RequestIdentity = Depends(deps.get_identity),
) -> Any:
    """
    Mark multiple notifications as read.
    """
    if not identity.user_id:
        raise HTTPException(
            status_code=401, detail="Authentication required to update notifications"
        )

    service = NotificationService(db)
    user_id = UUID(identity.user_id)

    count = await service.mark_bulk_as_read(bulk_update.notification_ids, user_id)

    return {"message": f"Marked {count} notifications as read", "count": count}


@router.delete("/{notification_id}", response_model=dict)
async def delete_notification(
    notification_id: UUID,
    db: AsyncSession = Depends(get_session),
    identity: deps.RequestIdentity = Depends(deps.get_identity),
) -> Any:
    """
    Delete a specific notification.
    """
    if not identity.user_id:
        raise HTTPException(
            status_code=401, detail="Authentication required to delete notification"
        )

    service = NotificationService(db)
    user_id = UUID(identity.user_id)

    success = await service.delete_notification(notification_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")

    return {"message": "Notification deleted", "deleted": True}
