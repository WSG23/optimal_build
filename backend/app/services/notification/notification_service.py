"""Service for managing in-app notifications."""

import logging
from uuid import UUID

from backend._compat.datetime import utcnow

from app.models.notification import (
    EmailLog,
    Notification,
    NotificationPriority,
    NotificationType,
)
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


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
        related_entity_type: str | None = None,
        related_entity_id: UUID | None = None,
        action_url: str | None = None,
    ) -> Notification:
        """Create a new notification for a user."""
        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            priority=priority,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            action_url=action_url,
        )

        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)

        logger.info(
            f"Created notification {notification.id} for user {user_id}: {title}"
        )
        return notification

    async def get_user_notifications(
        self,
        user_id: UUID,
        include_dismissed: bool = False,
        notification_type: NotificationType | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Notification], int, int]:
        """Get notifications for a user with pagination.

        Returns:
            Tuple of (notifications, total_count, unread_count)
        """
        # Base query
        conditions = [Notification.user_id == user_id]
        if not include_dismissed:
            conditions.append(Notification.is_dismissed.is_(False))
        if notification_type:
            conditions.append(Notification.notification_type == notification_type)

        # Get total count
        count_query = (
            select(func.count()).select_from(Notification).where(and_(*conditions))
        )
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Get unread count
        unread_query = (
            select(func.count())
            .select_from(Notification)
            .where(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read.is_(False),
                    Notification.is_dismissed.is_(False),
                )
            )
        )
        unread_result = await self.db.execute(unread_query)
        unread = unread_result.scalar() or 0

        # Get paginated notifications
        offset = (page - 1) * page_size
        query = (
            select(Notification)
            .where(and_(*conditions))
            .order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.db.execute(query)
        notifications = list(result.scalars().all())

        return notifications, total, unread

    async def get_notification_by_id(
        self, notification_id: UUID, user_id: UUID
    ) -> Notification | None:
        """Get a specific notification for a user."""
        query = select(Notification).where(
            and_(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def mark_as_read(self, notification_ids: list[UUID], user_id: UUID) -> int:
        """Mark notifications as read. Returns count of marked notifications."""
        if not notification_ids:
            return 0

        query = select(Notification).where(
            and_(
                Notification.id.in_(notification_ids),
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
        )
        result = await self.db.execute(query)
        notifications = list(result.scalars().all())

        count = 0
        now = utcnow()
        for notification in notifications:
            notification.is_read = True
            notification.read_at = now
            self.db.add(notification)
            count += 1

        if count > 0:
            await self.db.commit()

        return count

    async def mark_all_as_read(self, user_id: UUID) -> int:
        """Mark all unread notifications as read for a user."""
        query = select(Notification).where(
            and_(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
        )
        result = await self.db.execute(query)
        notifications = list(result.scalars().all())

        count = 0
        now = utcnow()
        for notification in notifications:
            notification.is_read = True
            notification.read_at = now
            self.db.add(notification)
            count += 1

        if count > 0:
            await self.db.commit()

        return count

    async def dismiss_notifications(
        self, notification_ids: list[UUID], user_id: UUID
    ) -> int:
        """Dismiss notifications. Returns count of dismissed notifications."""
        if not notification_ids:
            return 0

        query = select(Notification).where(
            and_(
                Notification.id.in_(notification_ids),
                Notification.user_id == user_id,
                Notification.is_dismissed.is_(False),
            )
        )
        result = await self.db.execute(query)
        notifications = list(result.scalars().all())

        count = 0
        now = utcnow()
        for notification in notifications:
            notification.is_dismissed = True
            notification.dismissed_at = now
            self.db.add(notification)
            count += 1

        if count > 0:
            await self.db.commit()

        return count

    async def dismiss_all(self, user_id: UUID) -> int:
        """Dismiss all notifications for a user."""
        query = select(Notification).where(
            and_(
                Notification.user_id == user_id,
                Notification.is_dismissed.is_(False),
            )
        )
        result = await self.db.execute(query)
        notifications = list(result.scalars().all())

        count = 0
        now = utcnow()
        for notification in notifications:
            notification.is_dismissed = True
            notification.dismissed_at = now
            self.db.add(notification)
            count += 1

        if count > 0:
            await self.db.commit()

        return count

    async def get_notification_counts(self, user_id: UUID) -> dict:
        """Get notification counts by type for a user."""
        # Total count
        total_query = (
            select(func.count())
            .select_from(Notification)
            .where(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_dismissed.is_(False),
                )
            )
        )
        total_result = await self.db.execute(total_query)
        total = total_result.scalar() or 0

        # Unread count
        unread_query = (
            select(func.count())
            .select_from(Notification)
            .where(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read.is_(False),
                    Notification.is_dismissed.is_(False),
                )
            )
        )
        unread_result = await self.db.execute(unread_query)
        unread = unread_result.scalar() or 0

        # Counts by type
        type_query = (
            select(
                Notification.notification_type,
                func.count().label("count"),
            )
            .where(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_dismissed.is_(False),
                )
            )
            .group_by(Notification.notification_type)
        )
        type_result = await self.db.execute(type_query)
        by_type = {
            row.notification_type.value: row.count for row in type_result.fetchall()
        }

        return {
            "total": total,
            "unread": unread,
            "by_type": by_type,
        }

    async def delete_notification(self, notification_id: UUID, user_id: UUID) -> bool:
        """Delete a notification. Returns True if deleted."""
        notification = await self.get_notification_by_id(notification_id, user_id)
        if notification:
            await self.db.delete(notification)
            await self.db.commit()
            return True
        return False

    # --- Convenience methods for creating specific notification types ---

    async def notify_team_invite(
        self,
        user_id: UUID,
        project_name: str,
        inviter_name: str,
        project_id: UUID,
    ) -> Notification:
        """Create a team invitation notification."""
        return await self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.TEAM_INVITE,
            title="Team Invitation",
            message=f"{inviter_name} invited you to join project '{project_name}'",
            priority=NotificationPriority.HIGH,
            related_entity_type="project",
            related_entity_id=project_id,
            action_url=f"/projects/{project_id}/team",
        )

    async def notify_workflow_approval_pending(
        self,
        user_id: UUID,
        workflow_title: str,
        step_name: str,
        workflow_id: UUID,
        project_id: UUID,
    ) -> Notification:
        """Create a workflow approval pending notification."""
        return await self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.WORKFLOW_APPROVAL_PENDING,
            title="Approval Required",
            message=f"Your approval is required for '{step_name}' in workflow '{workflow_title}'",
            priority=NotificationPriority.HIGH,
            related_entity_type="workflow",
            related_entity_id=workflow_id,
            action_url=f"/projects/{project_id}/workflows/{workflow_id}",
        )

    async def notify_workflow_approved(
        self,
        user_id: UUID,
        workflow_title: str,
        approver_name: str,
        workflow_id: UUID,
        project_id: UUID,
    ) -> Notification:
        """Create a workflow approved notification."""
        return await self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.WORKFLOW_APPROVED,
            title="Workflow Approved",
            message=f"'{workflow_title}' was approved by {approver_name}",
            priority=NotificationPriority.NORMAL,
            related_entity_type="workflow",
            related_entity_id=workflow_id,
            action_url=f"/projects/{project_id}/workflows/{workflow_id}",
        )

    async def notify_workflow_rejected(
        self,
        user_id: UUID,
        workflow_title: str,
        rejector_name: str,
        reason: str | None,
        workflow_id: UUID,
        project_id: UUID,
    ) -> Notification:
        """Create a workflow rejected notification."""
        message = f"'{workflow_title}' was rejected by {rejector_name}"
        if reason:
            message += f": {reason}"
        return await self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.WORKFLOW_REJECTED,
            title="Workflow Rejected",
            message=message,
            priority=NotificationPriority.HIGH,
            related_entity_type="workflow",
            related_entity_id=workflow_id,
            action_url=f"/projects/{project_id}/workflows/{workflow_id}",
        )

    async def notify_submission_status_changed(
        self,
        user_id: UUID,
        submission_title: str,
        new_status: str,
        submission_id: UUID,
        project_id: UUID,
    ) -> Notification:
        """Create a regulatory submission status change notification."""
        return await self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.SUBMISSION_STATUS_CHANGED,
            title="Submission Status Update",
            message=f"Submission '{submission_title}' status changed to {new_status}",
            priority=NotificationPriority.NORMAL,
            related_entity_type="submission",
            related_entity_id=submission_id,
            action_url=f"/projects/{project_id}/regulatory",
        )

    async def log_email(
        self,
        recipient_email: str,
        subject: str,
        template_name: str | None = None,
        notification_id: UUID | None = None,
        status: str = "pending",
        error_message: str | None = None,
    ) -> EmailLog:
        """Log an email send attempt."""
        email_log = EmailLog(
            recipient_email=recipient_email,
            subject=subject,
            template_name=template_name,
            notification_id=notification_id,
            status=status,
            error_message=error_message,
        )

        self.db.add(email_log)
        await self.db.commit()
        await self.db.refresh(email_log)

        return email_log

    async def update_email_log_status(
        self,
        email_log_id: UUID,
        status: str,
        error_message: str | None = None,
    ) -> EmailLog | None:
        """Update the status of an email log."""
        query = select(EmailLog).where(EmailLog.id == email_log_id)
        result = await self.db.execute(query)
        email_log = result.scalar_one_or_none()

        if email_log:
            email_log.status = status
            if status == "sent":
                email_log.sent_at = utcnow()
            if error_message:
                email_log.error_message = error_message
            self.db.add(email_log)
            await self.db.commit()
            await self.db.refresh(email_log)

        return email_log
