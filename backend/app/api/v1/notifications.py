"""API endpoints for notifications."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_db
from app.models.notification import NotificationType
from app.schemas.notification import (
    NotificationCountResponse,
    NotificationDismissRequest,
    NotificationDismissResponse,
    NotificationListResponse,
    NotificationMarkReadRequest,
    NotificationMarkReadResponse,
    NotificationResponse,
)
from app.services.notification import NotificationService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/notifications", tags=["notifications"])


def get_user_id_from_header(
    x_user_id: str = Query(None, alias="X-User-Id"),
) -> UUID:
    """Get user ID from header or query parameter.

    In production, this would be extracted from JWT token.
    For now, we accept it as a header/query param for demo purposes.
    """
    if not x_user_id:
        raise HTTPException(
            status_code=401,
            detail="X-User-Id header required",
        )
    try:
        return UUID(x_user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail="Invalid user ID format",
        ) from e


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    db: AsyncSession = Depends(get_db),
    user_id: str | None = Query(None, alias="user_id"),
    include_dismissed: bool = Query(False),
    notification_type: NotificationType | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> NotificationListResponse:
    """List notifications for a user.

    Args:
        user_id: User ID to get notifications for
        include_dismissed: Include dismissed notifications
        notification_type: Filter by notification type
        page: Page number (1-indexed)
        page_size: Number of items per page

    Returns:
        Paginated list of notifications with counts
    """
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    try:
        user_uuid = UUID(user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid user_id format") from e

    service = NotificationService(db)
    notifications, total, unread = await service.get_user_notifications(
        user_id=user_uuid,
        include_dismissed=include_dismissed,
        notification_type=notification_type,
        page=page,
        page_size=page_size,
    )

    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in notifications],
        total=total,
        unread_count=unread,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.get("/count", response_model=NotificationCountResponse)
async def get_notification_counts(
    db: AsyncSession = Depends(get_db),
    user_id: str | None = Query(None, alias="user_id"),
) -> NotificationCountResponse:
    """Get notification counts for a user.

    Returns:
        Total, unread, and by-type notification counts
    """
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    try:
        user_uuid = UUID(user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid user_id format") from e

    service = NotificationService(db)
    counts = await service.get_notification_counts(user_uuid)

    return NotificationCountResponse(**counts)


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str | None = Query(None, alias="user_id"),
) -> NotificationResponse:
    """Get a specific notification by ID."""
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    try:
        user_uuid = UUID(user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid user_id format") from e

    service = NotificationService(db)
    notification = await service.get_notification_by_id(notification_id, user_uuid)

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    return NotificationResponse.model_validate(notification)


@router.post("/mark-read", response_model=NotificationMarkReadResponse)
async def mark_notifications_read(
    request: NotificationMarkReadRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str | None = Query(None, alias="user_id"),
) -> NotificationMarkReadResponse:
    """Mark notifications as read.

    Args:
        request: Contains notification_ids to mark or mark_all flag

    Returns:
        Count of marked notifications
    """
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    try:
        user_uuid = UUID(user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid user_id format") from e

    service = NotificationService(db)

    if request.mark_all:
        count = await service.mark_all_as_read(user_uuid)
    else:
        count = await service.mark_as_read(request.notification_ids, user_uuid)

    return NotificationMarkReadResponse(marked_count=count)


@router.post("/dismiss", response_model=NotificationDismissResponse)
async def dismiss_notifications(
    request: NotificationDismissRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str | None = Query(None, alias="user_id"),
) -> NotificationDismissResponse:
    """Dismiss notifications.

    Args:
        request: Contains notification_ids to dismiss or dismiss_all flag

    Returns:
        Count of dismissed notifications
    """
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    try:
        user_uuid = UUID(user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid user_id format") from e

    service = NotificationService(db)

    if request.dismiss_all:
        count = await service.dismiss_all(user_uuid)
    else:
        count = await service.dismiss_notifications(request.notification_ids, user_uuid)

    return NotificationDismissResponse(dismissed_count=count)


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str | None = Query(None, alias="user_id"),
) -> dict:
    """Delete a notification permanently."""
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    try:
        user_uuid = UUID(user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid user_id format") from e

    service = NotificationService(db)
    deleted = await service.delete_notification(notification_id, user_uuid)

    if not deleted:
        raise HTTPException(status_code=404, detail="Notification not found")

    return {"success": True, "message": "Notification deleted"}
