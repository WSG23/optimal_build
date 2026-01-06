"""Tests for notification_service with mocked database.

Tests focus on NotificationService methods with mocked AsyncSession.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

pytest.importorskip("sqlalchemy")

from app.models.notification import (
    NotificationPriority,
    NotificationType,
)


class TestNotificationServiceCreate:
    """Test NotificationService.create_notification."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        return session

    @pytest.fixture
    def notification_service(self, mock_session):
        """Create NotificationService with mock session."""
        from app.services.notification.notification_service import NotificationService

        return NotificationService(mock_session)

    @pytest.mark.asyncio
    async def test_create_notification_adds_to_session(
        self, notification_service, mock_session
    ):
        """Test create_notification adds notification to session."""
        user_id = uuid4()

        await notification_service.create_notification(
            user_id=user_id,
            notification_type=NotificationType.TEAM_INVITE,
            title="Test Notification",
            message="This is a test",
        )

        assert mock_session.add.called
        assert mock_session.commit.called
        assert mock_session.refresh.called

    @pytest.mark.asyncio
    async def test_create_notification_with_all_fields(
        self, notification_service, mock_session
    ):
        """Test create_notification with all optional fields."""
        user_id = uuid4()
        entity_id = uuid4()

        await notification_service.create_notification(
            user_id=user_id,
            notification_type=NotificationType.WORKFLOW_APPROVED,
            title="Workflow Approved",
            message="Your workflow was approved",
            priority=NotificationPriority.HIGH,
            related_entity_type="workflow",
            related_entity_id=entity_id,
            action_url="/workflows/123",
        )

        # Verify notification was added
        call_args = mock_session.add.call_args
        notification = call_args[0][0]
        assert notification.user_id == user_id
        assert notification.notification_type == NotificationType.WORKFLOW_APPROVED
        assert notification.title == "Workflow Approved"
        assert notification.priority == NotificationPriority.HIGH
        assert notification.related_entity_type == "workflow"
        assert notification.related_entity_id == entity_id
        assert notification.action_url == "/workflows/123"


class TestNotificationServiceMarkAsRead:
    """Test NotificationService.mark_as_read."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        return session

    @pytest.fixture
    def notification_service(self, mock_session):
        """Create NotificationService with mock session."""
        from app.services.notification.notification_service import NotificationService

        return NotificationService(mock_session)

    @pytest.mark.asyncio
    async def test_mark_as_read_empty_list_returns_zero(
        self, notification_service, mock_session
    ):
        """Test mark_as_read with empty list returns 0."""
        user_id = uuid4()

        result = await notification_service.mark_as_read([], user_id)

        assert result == 0
        assert not mock_session.execute.called

    @pytest.mark.asyncio
    async def test_mark_as_read_updates_notifications(
        self, notification_service, mock_session
    ):
        """Test mark_as_read updates unread notifications."""
        user_id = uuid4()
        notification_ids = [uuid4(), uuid4()]

        # Mock unread notifications
        mock_notification1 = MagicMock()
        mock_notification1.is_read = False
        mock_notification2 = MagicMock()
        mock_notification2.is_read = False

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            mock_notification1,
            mock_notification2,
        ]
        mock_session.execute.return_value = mock_result

        result = await notification_service.mark_as_read(notification_ids, user_id)

        assert result == 2
        assert mock_notification1.is_read is True
        assert mock_notification2.is_read is True
        assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_mark_as_read_no_matching_returns_zero(
        self, notification_service, mock_session
    ):
        """Test mark_as_read with no matching notifications returns 0."""
        user_id = uuid4()
        notification_ids = [uuid4()]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await notification_service.mark_as_read(notification_ids, user_id)

        assert result == 0


class TestNotificationServiceDismiss:
    """Test NotificationService dismiss methods."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        return session

    @pytest.fixture
    def notification_service(self, mock_session):
        """Create NotificationService with mock session."""
        from app.services.notification.notification_service import NotificationService

        return NotificationService(mock_session)

    @pytest.mark.asyncio
    async def test_dismiss_notifications_empty_list_returns_zero(
        self, notification_service, mock_session
    ):
        """Test dismiss_notifications with empty list returns 0."""
        user_id = uuid4()

        result = await notification_service.dismiss_notifications([], user_id)

        assert result == 0
        assert not mock_session.execute.called

    @pytest.mark.asyncio
    async def test_dismiss_notifications_updates_notifications(
        self, notification_service, mock_session
    ):
        """Test dismiss_notifications updates non-dismissed notifications."""
        user_id = uuid4()
        notification_ids = [uuid4()]

        mock_notification = MagicMock()
        mock_notification.is_dismissed = False

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_notification]
        mock_session.execute.return_value = mock_result

        result = await notification_service.dismiss_notifications(
            notification_ids, user_id
        )

        assert result == 1
        assert mock_notification.is_dismissed is True
        assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_dismiss_all_updates_all_undismissed(
        self, notification_service, mock_session
    ):
        """Test dismiss_all updates all undismissed notifications."""
        user_id = uuid4()

        mock_notifications = [MagicMock(is_dismissed=False) for _ in range(3)]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_notifications
        mock_session.execute.return_value = mock_result

        result = await notification_service.dismiss_all(user_id)

        assert result == 3
        for n in mock_notifications:
            assert n.is_dismissed is True


class TestNotificationServiceConvenienceMethods:
    """Test NotificationService convenience methods."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        return session

    @pytest.fixture
    def notification_service(self, mock_session):
        """Create NotificationService with mock session."""
        from app.services.notification.notification_service import NotificationService

        return NotificationService(mock_session)

    @pytest.mark.asyncio
    async def test_notify_team_invite_creates_correct_notification(
        self, notification_service, mock_session
    ):
        """Test notify_team_invite creates team invite notification."""
        user_id = uuid4()
        project_id = uuid4()

        await notification_service.notify_team_invite(
            user_id=user_id,
            project_name="Test Project",
            inviter_name="John Doe",
            project_id=project_id,
        )

        call_args = mock_session.add.call_args
        notification = call_args[0][0]
        assert notification.notification_type == NotificationType.TEAM_INVITE
        assert notification.title == "Team Invitation"
        assert "John Doe" in notification.message
        assert "Test Project" in notification.message
        assert notification.priority == NotificationPriority.HIGH
        assert notification.related_entity_type == "project"
        assert notification.related_entity_id == project_id

    @pytest.mark.asyncio
    async def test_notify_workflow_approval_pending(
        self, notification_service, mock_session
    ):
        """Test notify_workflow_approval_pending creates correct notification."""
        user_id = uuid4()
        workflow_id = uuid4()
        project_id = uuid4()

        await notification_service.notify_workflow_approval_pending(
            user_id=user_id,
            workflow_title="Budget Approval",
            step_name="Manager Review",
            workflow_id=workflow_id,
            project_id=project_id,
        )

        call_args = mock_session.add.call_args
        notification = call_args[0][0]
        assert (
            notification.notification_type == NotificationType.WORKFLOW_APPROVAL_PENDING
        )
        assert notification.title == "Approval Required"
        assert "Manager Review" in notification.message
        assert notification.priority == NotificationPriority.HIGH

    @pytest.mark.asyncio
    async def test_notify_workflow_approved(self, notification_service, mock_session):
        """Test notify_workflow_approved creates correct notification."""
        user_id = uuid4()
        workflow_id = uuid4()
        project_id = uuid4()

        await notification_service.notify_workflow_approved(
            user_id=user_id,
            workflow_title="Budget Approval",
            approver_name="Jane Smith",
            workflow_id=workflow_id,
            project_id=project_id,
        )

        call_args = mock_session.add.call_args
        notification = call_args[0][0]
        assert notification.notification_type == NotificationType.WORKFLOW_APPROVED
        assert notification.title == "Workflow Approved"
        assert "Jane Smith" in notification.message
        assert notification.priority == NotificationPriority.NORMAL

    @pytest.mark.asyncio
    async def test_notify_workflow_rejected_with_reason(
        self, notification_service, mock_session
    ):
        """Test notify_workflow_rejected includes rejection reason."""
        user_id = uuid4()
        workflow_id = uuid4()
        project_id = uuid4()

        await notification_service.notify_workflow_rejected(
            user_id=user_id,
            workflow_title="Budget Approval",
            rejector_name="Bob Manager",
            reason="Budget exceeds limit",
            workflow_id=workflow_id,
            project_id=project_id,
        )

        call_args = mock_session.add.call_args
        notification = call_args[0][0]
        assert notification.notification_type == NotificationType.WORKFLOW_REJECTED
        assert "Budget exceeds limit" in notification.message
        assert notification.priority == NotificationPriority.HIGH

    @pytest.mark.asyncio
    async def test_notify_workflow_rejected_without_reason(
        self, notification_service, mock_session
    ):
        """Test notify_workflow_rejected works without reason."""
        user_id = uuid4()
        workflow_id = uuid4()
        project_id = uuid4()

        await notification_service.notify_workflow_rejected(
            user_id=user_id,
            workflow_title="Budget Approval",
            rejector_name="Bob Manager",
            reason=None,
            workflow_id=workflow_id,
            project_id=project_id,
        )

        call_args = mock_session.add.call_args
        notification = call_args[0][0]
        assert "Bob Manager" in notification.message
        assert ":" not in notification.message  # No reason appended

    @pytest.mark.asyncio
    async def test_notify_submission_status_changed(
        self, notification_service, mock_session
    ):
        """Test notify_submission_status_changed creates correct notification."""
        user_id = uuid4()
        submission_id = uuid4()
        project_id = uuid4()

        await notification_service.notify_submission_status_changed(
            user_id=user_id,
            submission_title="Building Permit Application",
            new_status="Approved",
            submission_id=submission_id,
            project_id=project_id,
        )

        call_args = mock_session.add.call_args
        notification = call_args[0][0]
        assert (
            notification.notification_type == NotificationType.SUBMISSION_STATUS_CHANGED
        )
        assert notification.title == "Submission Status Update"
        assert "Approved" in notification.message


class TestNotificationServiceEmailLog:
    """Test NotificationService email logging methods."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        return session

    @pytest.fixture
    def notification_service(self, mock_session):
        """Create NotificationService with mock session."""
        from app.services.notification.notification_service import NotificationService

        return NotificationService(mock_session)

    @pytest.mark.asyncio
    async def test_log_email_creates_email_log(
        self, notification_service, mock_session
    ):
        """Test log_email creates email log record."""
        await notification_service.log_email(
            recipient_email="test@example.com",
            subject="Test Subject",
            template_name="welcome_email",
            status="pending",
        )

        assert mock_session.add.called
        assert mock_session.commit.called
        call_args = mock_session.add.call_args
        email_log = call_args[0][0]
        assert email_log.recipient_email == "test@example.com"
        assert email_log.subject == "Test Subject"
        assert email_log.template_name == "welcome_email"
        assert email_log.status == "pending"

    @pytest.mark.asyncio
    async def test_update_email_log_status_success(
        self, notification_service, mock_session
    ):
        """Test update_email_log_status updates existing log."""
        email_log_id = uuid4()
        mock_email_log = MagicMock()
        mock_email_log.status = "pending"
        mock_email_log.sent_at = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_email_log
        mock_session.execute.return_value = mock_result

        result = await notification_service.update_email_log_status(
            email_log_id=email_log_id, status="sent"
        )

        assert result == mock_email_log
        assert mock_email_log.status == "sent"
        assert mock_email_log.sent_at is not None
        assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_update_email_log_status_with_error(
        self, notification_service, mock_session
    ):
        """Test update_email_log_status records error message."""
        email_log_id = uuid4()
        mock_email_log = MagicMock()
        mock_email_log.status = "pending"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_email_log
        mock_session.execute.return_value = mock_result

        await notification_service.update_email_log_status(
            email_log_id=email_log_id,
            status="failed",
            error_message="SMTP connection error",
        )

        assert mock_email_log.status == "failed"
        assert mock_email_log.error_message == "SMTP connection error"

    @pytest.mark.asyncio
    async def test_update_email_log_status_not_found(
        self, notification_service, mock_session
    ):
        """Test update_email_log_status returns None when not found."""
        email_log_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await notification_service.update_email_log_status(
            email_log_id=email_log_id, status="sent"
        )

        assert result is None


class TestNotificationServiceMarkAllAsRead:
    """Test NotificationService.mark_all_as_read."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        return session

    @pytest.fixture
    def notification_service(self, mock_session):
        """Create NotificationService with mock session."""
        from app.services.notification.notification_service import NotificationService

        return NotificationService(mock_session)

    @pytest.mark.asyncio
    async def test_mark_all_as_read_updates_all_unread(
        self, notification_service, mock_session
    ):
        """Test mark_all_as_read marks all unread notifications as read."""
        user_id = uuid4()

        mock_notifications = [MagicMock(is_read=False) for _ in range(5)]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_notifications
        mock_session.execute.return_value = mock_result

        result = await notification_service.mark_all_as_read(user_id)

        assert result == 5
        for n in mock_notifications:
            assert n.is_read is True
            assert n.read_at is not None

    @pytest.mark.asyncio
    async def test_mark_all_as_read_no_unread_returns_zero(
        self, notification_service, mock_session
    ):
        """Test mark_all_as_read with no unread notifications returns 0."""
        user_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await notification_service.mark_all_as_read(user_id)

        assert result == 0
        # Commit not called when count is 0
        assert not mock_session.commit.called
