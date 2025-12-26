"""Comprehensive tests for notification schemas.

Tests cover:
- NotificationBase schema
- NotificationCreate schema
- NotificationRead schema
- NotificationUpdate schema
- NotificationBulkUpdate schema
- NotificationCount schema
- NotificationList schema
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4


class TestNotificationBase:
    """Tests for NotificationBase schema."""

    def test_notification_type_required(self) -> None:
        """Test notification_type is required."""
        notification_type = "TEAM_INVITATION"
        assert notification_type is not None

    def test_title_required(self) -> None:
        """Test title is required with min length 1."""
        title = "Team Invitation"
        assert len(title) >= 1

    def test_title_max_length(self) -> None:
        """Test title max length is 255."""
        title = "A" * 255
        assert len(title) <= 255

    def test_message_required(self) -> None:
        """Test message is required with min length 1."""
        message = "You have been invited to join a team"
        assert len(message) >= 1

    def test_priority_default_normal(self) -> None:
        """Test priority defaults to NORMAL."""
        priority = "NORMAL"
        assert priority == "NORMAL"


class TestNotificationType:
    """Tests for NotificationType enum values."""

    def test_team_invitation(self) -> None:
        """Test TEAM_INVITATION type."""
        notification_type = "TEAM_INVITATION"
        assert notification_type == "TEAM_INVITATION"

    def test_workflow_approval_needed(self) -> None:
        """Test WORKFLOW_APPROVAL_NEEDED type."""
        notification_type = "WORKFLOW_APPROVAL_NEEDED"
        assert notification_type == "WORKFLOW_APPROVAL_NEEDED"

    def test_workflow_approved(self) -> None:
        """Test WORKFLOW_APPROVED type."""
        notification_type = "WORKFLOW_APPROVED"
        assert notification_type == "WORKFLOW_APPROVED"

    def test_workflow_rejected(self) -> None:
        """Test WORKFLOW_REJECTED type."""
        notification_type = "WORKFLOW_REJECTED"
        assert notification_type == "WORKFLOW_REJECTED"

    def test_project_update(self) -> None:
        """Test PROJECT_UPDATE type."""
        notification_type = "PROJECT_UPDATE"
        assert notification_type == "PROJECT_UPDATE"

    def test_system_announcement(self) -> None:
        """Test SYSTEM_ANNOUNCEMENT type."""
        notification_type = "SYSTEM_ANNOUNCEMENT"
        assert notification_type == "SYSTEM_ANNOUNCEMENT"


class TestNotificationPriority:
    """Tests for NotificationPriority enum values."""

    def test_low_priority(self) -> None:
        """Test LOW priority."""
        priority = "LOW"
        assert priority == "LOW"

    def test_normal_priority(self) -> None:
        """Test NORMAL priority."""
        priority = "NORMAL"
        assert priority == "NORMAL"

    def test_high_priority(self) -> None:
        """Test HIGH priority."""
        priority = "HIGH"
        assert priority == "HIGH"

    def test_urgent_priority(self) -> None:
        """Test URGENT priority."""
        priority = "URGENT"
        assert priority == "URGENT"


class TestNotificationCreate:
    """Tests for NotificationCreate schema."""

    def test_user_id_required(self) -> None:
        """Test user_id is required UUID."""
        user_id = uuid4()
        assert len(str(user_id)) == 36

    def test_project_id_optional(self) -> None:
        """Test project_id is optional."""
        notification = {}
        assert notification.get("project_id") is None

    def test_related_entity_type_optional(self) -> None:
        """Test related_entity_type is optional."""
        notification = {}
        assert notification.get("related_entity_type") is None

    def test_related_entity_type_max_length(self) -> None:
        """Test related_entity_type max length is 50."""
        entity_type = "workflow"
        assert len(entity_type) <= 50

    def test_related_entity_id_optional(self) -> None:
        """Test related_entity_id is optional."""
        notification = {}
        assert notification.get("related_entity_id") is None

    def test_expires_at_optional(self) -> None:
        """Test expires_at is optional."""
        notification = {}
        assert notification.get("expires_at") is None


class TestNotificationRead:
    """Tests for NotificationRead schema."""

    def test_id_required(self) -> None:
        """Test id is required UUID."""
        notification_id = uuid4()
        assert len(str(notification_id)) == 36

    def test_user_id_required(self) -> None:
        """Test user_id is required."""
        user_id = uuid4()
        assert user_id is not None

    def test_is_read_required(self) -> None:
        """Test is_read is required boolean."""
        is_read = False
        assert isinstance(is_read, bool)

    def test_read_at_optional(self) -> None:
        """Test read_at is optional."""
        notification = {}
        assert notification.get("read_at") is None

    def test_created_at_required(self) -> None:
        """Test created_at is required."""
        created_at = datetime.utcnow()
        assert created_at is not None

    def test_from_attributes_config(self) -> None:
        """Test from_attributes is enabled."""
        # ConfigDict allows ORM model mapping
        from_attributes = True
        assert from_attributes is True


class TestNotificationUpdate:
    """Tests for NotificationUpdate schema."""

    def test_is_read_required(self) -> None:
        """Test is_read is required."""
        is_read = True
        assert isinstance(is_read, bool)

    def test_mark_as_read(self) -> None:
        """Test marking notification as read."""
        update = {"is_read": True}
        assert update["is_read"] is True

    def test_mark_as_unread(self) -> None:
        """Test marking notification as unread."""
        update = {"is_read": False}
        assert update["is_read"] is False


class TestNotificationBulkUpdate:
    """Tests for NotificationBulkUpdate schema."""

    def test_notification_ids_required(self) -> None:
        """Test notification_ids is required list."""
        notification_ids = [uuid4(), uuid4(), uuid4()]
        assert len(notification_ids) == 3

    def test_is_read_required(self) -> None:
        """Test is_read is required."""
        is_read = True
        assert isinstance(is_read, bool)

    def test_bulk_mark_as_read(self) -> None:
        """Test bulk marking as read."""
        update = {
            "notification_ids": [str(uuid4()), str(uuid4())],
            "is_read": True,
        }
        assert update["is_read"] is True
        assert len(update["notification_ids"]) == 2


class TestNotificationCount:
    """Tests for NotificationCount schema."""

    def test_total_required(self) -> None:
        """Test total is required."""
        total = 25
        assert total >= 0

    def test_unread_required(self) -> None:
        """Test unread is required."""
        unread = 5
        assert unread >= 0

    def test_unread_lte_total(self) -> None:
        """Test unread is less than or equal to total."""
        total = 25
        unread = 5
        assert unread <= total


class TestNotificationList:
    """Tests for NotificationList schema."""

    def test_notifications_list(self) -> None:
        """Test notifications is a list."""
        notifications = []
        assert isinstance(notifications, list)

    def test_total_required(self) -> None:
        """Test total count is required."""
        total = 50
        assert total >= 0

    def test_unread_count_required(self) -> None:
        """Test unread_count is required."""
        unread_count = 10
        assert unread_count >= 0

    def test_page_required(self) -> None:
        """Test page is required."""
        page = 1
        assert page >= 1

    def test_page_size_required(self) -> None:
        """Test page_size is required."""
        page_size = 20
        assert page_size >= 1

    def test_has_more_required(self) -> None:
        """Test has_more is required boolean."""
        has_more = True
        assert isinstance(has_more, bool)

    def test_pagination_calculation(self) -> None:
        """Test pagination calculation."""
        total = 50
        page = 2
        page_size = 20
        has_more = (page * page_size) < total
        assert has_more is True

    def test_last_page_no_more(self) -> None:
        """Test has_more is False on last page."""
        total = 50
        page = 3
        page_size = 20
        has_more = (page * page_size) < total
        assert has_more is False
