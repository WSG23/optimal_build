"""Service for managing notifications."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from backend._compat.datetime import utcnow

from app.models.notification import (
    Notification,
    NotificationPriority,
    NotificationType,
)
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession


class NotificationService:
    """Service for managing user notifications."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def create_notification(
        self,
        user_id: UUID,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        project_id: Optional[UUID] = None,
        related_entity_type: Optional[str] = None,
        related_entity_id: Optional[UUID] = None,
        expires_at: Optional[datetime] = None,
    ) -> Notification:
        """Create a new notification for a user."""
        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            priority=priority,
            project_id=project_id,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            expires_at=expires_at,
        )
        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)
        return notification

    async def get_notifications(
        self,
        user_id: UUID,
        unread_only: bool = False,
        notification_type: Optional[NotificationType] = None,
        project_id: Optional[UUID] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Notification], int, int]:
        """
        Get notifications for a user with pagination.

        Returns:
            Tuple of (notifications, total_count, unread_count)
        """
        # Base query
        query = select(Notification).where(Notification.user_id == user_id)

        # Apply filters
        if unread_only:
            query = query.where(Notification.is_read.is_(False))
        if notification_type:
            query = query.where(Notification.notification_type == notification_type)
        if project_id:
            query = query.where(Notification.project_id == project_id)

        # Exclude expired notifications
        now = utcnow()
        query = query.where(
            (Notification.expires_at.is_(None)) | (Notification.expires_at > now)
        )

        # Order by created_at descending (newest first)
        query = query.order_by(Notification.created_at.desc())

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total_count = total_result.scalar() or 0

        # Get unread count
        unread_query = (
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user_id)
            .where(Notification.is_read.is_(False))
            .where(
                (Notification.expires_at.is_(None)) | (Notification.expires_at > now)
            )
        )
        unread_result = await self.db.execute(unread_query)
        unread_count = unread_result.scalar() or 0

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        notifications = list(result.scalars().all())

        return notifications, total_count, unread_count

    async def get_notification_by_id(
        self, notification_id: UUID, user_id: UUID
    ) -> Optional[Notification]:
        """Get a specific notification by ID (only if owned by user)."""
        query = select(Notification).where(
            Notification.id == notification_id, Notification.user_id == user_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def mark_as_read(self, notification_id: UUID, user_id: UUID) -> bool:
        """Mark a notification as read."""
        notification = await self.get_notification_by_id(notification_id, user_id)
        if notification:
            notification.mark_as_read()
            self.db.add(notification)
            await self.db.commit()
            return True
        return False

    async def mark_all_as_read(self, user_id: UUID) -> int:
        """Mark all notifications as read for a user."""
        now = utcnow()
        stmt = (
            update(Notification)
            .where(Notification.user_id == user_id)
            .where(Notification.is_read.is_(False))
            .values(is_read=True, read_at=now)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount

    async def mark_bulk_as_read(
        self, notification_ids: list[UUID], user_id: UUID
    ) -> int:
        """Mark multiple notifications as read."""
        now = utcnow()
        stmt = (
            update(Notification)
            .where(Notification.id.in_(notification_ids))
            .where(Notification.user_id == user_id)
            .where(Notification.is_read.is_(False))
            .values(is_read=True, read_at=now)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount

    async def delete_notification(self, notification_id: UUID, user_id: UUID) -> bool:
        """Delete a notification (only if owned by user)."""
        stmt = delete(Notification).where(
            Notification.id == notification_id, Notification.user_id == user_id
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0

    async def delete_expired_notifications(self) -> int:
        """Delete all expired notifications (cleanup task)."""
        now = utcnow()
        stmt = delete(Notification).where(
            Notification.expires_at.is_not(None), Notification.expires_at < now
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount

    async def get_unread_count(self, user_id: UUID) -> int:
        """Get the count of unread notifications for a user."""
        now = utcnow()
        query = (
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user_id)
            .where(Notification.is_read.is_(False))
            .where(
                (Notification.expires_at.is_(None)) | (Notification.expires_at > now)
            )
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    # Convenience methods for creating specific notification types

    async def notify_team_invitation(
        self,
        user_id: UUID,
        project_id: UUID,
        project_name: str,
        inviter_name: str,
        invitation_id: UUID,
    ) -> Notification:
        """Create a notification for a team invitation."""
        return await self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.TEAM_INVITATION,
            title="Team Invitation",
            message=f"{inviter_name} has invited you to join project '{project_name}'",
            priority=NotificationPriority.HIGH,
            project_id=project_id,
            related_entity_type="team_invitation",
            related_entity_id=invitation_id,
        )

    async def notify_team_member_joined(
        self,
        user_id: UUID,
        project_id: UUID,
        project_name: str,
        new_member_name: str,
    ) -> Notification:
        """Create a notification when a team member joins."""
        return await self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.TEAM_MEMBER_JOINED,
            title="New Team Member",
            message=f"{new_member_name} has joined project '{project_name}'",
            priority=NotificationPriority.NORMAL,
            project_id=project_id,
        )

    async def notify_workflow_step_assigned(
        self,
        user_id: UUID,
        project_id: UUID,
        workflow_name: str,
        step_name: str,
        workflow_id: UUID,
    ) -> Notification:
        """Create a notification when a workflow step is assigned."""
        return await self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.WORKFLOW_STEP_ASSIGNED,
            title="Action Required",
            message=f"You have been assigned to '{step_name}' in workflow '{workflow_name}'",
            priority=NotificationPriority.HIGH,
            project_id=project_id,
            related_entity_type="workflow",
            related_entity_id=workflow_id,
        )

    async def notify_approval_needed(
        self,
        user_id: UUID,
        project_id: UUID,
        workflow_name: str,
        step_name: str,
        workflow_id: UUID,
    ) -> Notification:
        """Create a notification when approval is needed."""
        return await self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.WORKFLOW_APPROVAL_NEEDED,
            title="Approval Required",
            message=f"Your approval is needed for '{step_name}' in workflow '{workflow_name}'",
            priority=NotificationPriority.URGENT,
            project_id=project_id,
            related_entity_type="workflow",
            related_entity_id=workflow_id,
        )

    async def notify_regulatory_status_change(
        self,
        user_id: UUID,
        project_id: UUID,
        submission_title: str,
        new_status: str,
        submission_id: UUID,
    ) -> Notification:
        """Create a notification for regulatory submission status change."""
        return await self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.REGULATORY_STATUS_CHANGE,
            title="Regulatory Update",
            message=f"Submission '{submission_title}' status changed to: {new_status}",
            priority=NotificationPriority.HIGH,
            project_id=project_id,
            related_entity_type="regulatory_submission",
            related_entity_id=submission_id,
        )
