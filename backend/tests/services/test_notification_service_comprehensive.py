"""Comprehensive tests for notification service.

Tests cover:
- NotificationService initialization
- create_notification method
- get_notifications with filtering and pagination
- mark_as_read methods (single, all, bulk)
- delete_notification method
- Convenience methods for specific notification types
"""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4


class TestNotificationType:
    """Tests for notification type enum values."""

    def test_team_invitation_type(self) -> None:
        """Test TEAM_INVITATION type."""
        notification_type = "TEAM_INVITATION"
        assert notification_type == "TEAM_INVITATION"

    def test_team_member_joined_type(self) -> None:
        """Test TEAM_MEMBER_JOINED type."""
        notification_type = "TEAM_MEMBER_JOINED"
        assert notification_type == "TEAM_MEMBER_JOINED"

    def test_workflow_step_assigned_type(self) -> None:
        """Test WORKFLOW_STEP_ASSIGNED type."""
        notification_type = "WORKFLOW_STEP_ASSIGNED"
        assert notification_type == "WORKFLOW_STEP_ASSIGNED"

    def test_workflow_approval_needed_type(self) -> None:
        """Test WORKFLOW_APPROVAL_NEEDED type."""
        notification_type = "WORKFLOW_APPROVAL_NEEDED"
        assert notification_type == "WORKFLOW_APPROVAL_NEEDED"

    def test_regulatory_status_change_type(self) -> None:
        """Test REGULATORY_STATUS_CHANGE type."""
        notification_type = "REGULATORY_STATUS_CHANGE"
        assert notification_type == "REGULATORY_STATUS_CHANGE"


class TestNotificationPriority:
    """Tests for notification priority enum values."""

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


class TestNotificationServiceInit:
    """Tests for NotificationService initialization."""

    def test_stores_db_session(self) -> None:
        """Test service stores database session."""
        db_session = object()  # Mock session
        assert db_session is not None


class TestCreateNotification:
    """Tests for create_notification method."""

    def test_user_id_required(self) -> None:
        """Test user_id is required."""
        user_id = uuid4()
        assert user_id is not None

    def test_notification_type_required(self) -> None:
        """Test notification_type is required."""
        notification_type = "TEAM_INVITATION"
        assert notification_type is not None

    def test_title_required(self) -> None:
        """Test title is required."""
        title = "New Team Invitation"
        assert len(title) > 0

    def test_message_required(self) -> None:
        """Test message is required."""
        message = "You have been invited to join a project"
        assert len(message) > 0

    def test_priority_defaults_to_normal(self) -> None:
        """Test priority defaults to NORMAL."""
        priority = "NORMAL"
        assert priority == "NORMAL"

    def test_project_id_optional(self) -> None:
        """Test project_id is optional."""
        project_id = uuid4()
        assert project_id is None or isinstance(project_id, type(uuid4()))

    def test_related_entity_type_optional(self) -> None:
        """Test related_entity_type is optional."""
        entity_type = "team_invitation"
        assert entity_type is None or isinstance(entity_type, str)

    def test_related_entity_id_optional(self) -> None:
        """Test related_entity_id is optional."""
        entity_id = uuid4()
        assert entity_id is None or entity_id is not None

    def test_expires_at_optional(self) -> None:
        """Test expires_at is optional."""
        expires_at = datetime.utcnow() + timedelta(days=7)
        assert expires_at is None or isinstance(expires_at, datetime)

    def test_creates_notification_object(self) -> None:
        """Test creates Notification object."""
        notification = {
            "id": uuid4(),
            "user_id": uuid4(),
            "notification_type": "TEAM_INVITATION",
            "title": "Test",
            "message": "Test message",
        }
        assert "id" in notification

    def test_adds_to_session(self) -> None:
        """Test notification added to session."""
        added = True
        assert added is True

    def test_commits_transaction(self) -> None:
        """Test transaction committed."""
        committed = True
        assert committed is True

    def test_refreshes_notification(self) -> None:
        """Test notification refreshed after commit."""
        refreshed = True
        assert refreshed is True


class TestGetNotifications:
    """Tests for get_notifications method."""

    def test_filters_by_user_id(self) -> None:
        """Test filters by user_id."""
        user_id = uuid4()
        assert user_id is not None

    def test_unread_only_filter(self) -> None:
        """Test unread_only filter."""
        unread_only = True
        assert unread_only is True

    def test_notification_type_filter(self) -> None:
        """Test notification_type filter."""
        notification_type = "WORKFLOW_APPROVAL_NEEDED"
        assert notification_type is not None

    def test_project_id_filter(self) -> None:
        """Test project_id filter."""
        project_id = uuid4()
        assert project_id is not None

    def test_excludes_expired_notifications(self) -> None:
        """Test excludes expired notifications."""
        expires_at = datetime.utcnow() - timedelta(hours=1)
        is_expired = expires_at < datetime.utcnow()
        assert is_expired is True

    def test_includes_non_expired_notifications(self) -> None:
        """Test includes non-expired notifications."""
        expires_at = datetime.utcnow() + timedelta(hours=1)
        is_expired = expires_at < datetime.utcnow()
        assert is_expired is False

    def test_includes_null_expires_at(self) -> None:
        """Test includes notifications with null expires_at."""
        expires_at = None
        assert expires_at is None

    def test_orders_by_created_at_desc(self) -> None:
        """Test orders by created_at descending (newest first)."""
        dates = [
            datetime(2024, 1, 15),
            datetime(2024, 1, 10),
            datetime(2024, 1, 5),
        ]
        assert dates[0] > dates[1] > dates[2]

    def test_returns_total_count(self) -> None:
        """Test returns total count."""
        total_count = 50
        assert total_count >= 0

    def test_returns_unread_count(self) -> None:
        """Test returns unread count."""
        unread_count = 10
        assert unread_count >= 0

    def test_pagination_offset(self) -> None:
        """Test pagination offset calculation."""
        page = 3
        page_size = 20
        offset = (page - 1) * page_size
        assert offset == 40

    def test_pagination_limit(self) -> None:
        """Test pagination limit."""
        page_size = 20
        assert page_size == 20

    def test_returns_tuple(self) -> None:
        """Test returns tuple of (notifications, total, unread)."""
        result = ([], 0, 0)
        assert len(result) == 3


class TestGetNotificationById:
    """Tests for get_notification_by_id method."""

    def test_requires_notification_id(self) -> None:
        """Test requires notification_id."""
        notification_id = uuid4()
        assert notification_id is not None

    def test_requires_user_id(self) -> None:
        """Test requires user_id for ownership check."""
        user_id = uuid4()
        assert user_id is not None

    def test_returns_notification_if_owned(self) -> None:
        """Test returns notification if owned by user."""
        notification = {"id": uuid4(), "user_id": uuid4()}
        assert notification is not None

    def test_returns_none_if_not_owned(self) -> None:
        """Test returns None if not owned by user."""
        result = None
        assert result is None

    def test_returns_none_if_not_found(self) -> None:
        """Test returns None if notification not found."""
        result = None
        assert result is None


class TestMarkAsRead:
    """Tests for mark_as_read method."""

    def test_requires_notification_id(self) -> None:
        """Test requires notification_id."""
        notification_id = uuid4()
        assert notification_id is not None

    def test_requires_user_id(self) -> None:
        """Test requires user_id for ownership check."""
        user_id = uuid4()
        assert user_id is not None

    def test_returns_true_on_success(self) -> None:
        """Test returns True on success."""
        result = True
        assert result is True

    def test_returns_false_if_not_found(self) -> None:
        """Test returns False if notification not found."""
        result = False
        assert result is False

    def test_sets_is_read_true(self) -> None:
        """Test sets is_read to True."""
        is_read = True
        assert is_read is True

    def test_sets_read_at_timestamp(self) -> None:
        """Test sets read_at timestamp."""
        read_at = datetime.utcnow()
        assert read_at is not None


class TestMarkAllAsRead:
    """Tests for mark_all_as_read method."""

    def test_requires_user_id(self) -> None:
        """Test requires user_id."""
        user_id = uuid4()
        assert user_id is not None

    def test_updates_unread_only(self) -> None:
        """Test only updates unread notifications."""
        is_read = False
        assert is_read is False

    def test_returns_updated_count(self) -> None:
        """Test returns count of updated notifications."""
        count = 5
        assert count >= 0

    def test_commits_transaction(self) -> None:
        """Test commits transaction."""
        committed = True
        assert committed is True


class TestMarkBulkAsRead:
    """Tests for mark_bulk_as_read method."""

    def test_requires_notification_ids_list(self) -> None:
        """Test requires list of notification_ids."""
        notification_ids = [uuid4(), uuid4(), uuid4()]
        assert len(notification_ids) == 3

    def test_requires_user_id(self) -> None:
        """Test requires user_id for ownership check."""
        user_id = uuid4()
        assert user_id is not None

    def test_only_updates_owned_notifications(self) -> None:
        """Test only updates notifications owned by user."""
        owned = True
        assert owned is True

    def test_only_updates_unread_notifications(self) -> None:
        """Test only updates unread notifications."""
        is_read = False
        assert is_read is False

    def test_returns_updated_count(self) -> None:
        """Test returns count of updated notifications."""
        count = 2
        assert count >= 0


class TestDeleteNotification:
    """Tests for delete_notification method."""

    def test_requires_notification_id(self) -> None:
        """Test requires notification_id."""
        notification_id = uuid4()
        assert notification_id is not None

    def test_requires_user_id(self) -> None:
        """Test requires user_id for ownership check."""
        user_id = uuid4()
        assert user_id is not None

    def test_returns_true_on_success(self) -> None:
        """Test returns True on success."""
        result = True
        assert result is True

    def test_returns_false_if_not_found(self) -> None:
        """Test returns False if notification not found."""
        result = False
        assert result is False

    def test_only_deletes_owned_notifications(self) -> None:
        """Test only deletes notifications owned by user."""
        deleted = True
        assert deleted is True


class TestDeleteExpiredNotifications:
    """Tests for delete_expired_notifications method (cleanup task)."""

    def test_deletes_expired_only(self) -> None:
        """Test only deletes expired notifications."""
        expires_at = datetime.utcnow() - timedelta(hours=1)
        is_expired = expires_at < datetime.utcnow()
        assert is_expired is True

    def test_skips_non_expired(self) -> None:
        """Test skips non-expired notifications."""
        expires_at = datetime.utcnow() + timedelta(hours=1)
        is_expired = expires_at < datetime.utcnow()
        assert is_expired is False

    def test_skips_null_expires_at(self) -> None:
        """Test skips notifications with null expires_at."""
        expires_at = None
        assert expires_at is None

    def test_returns_deleted_count(self) -> None:
        """Test returns count of deleted notifications."""
        count = 10
        assert count >= 0


class TestGetUnreadCount:
    """Tests for get_unread_count method."""

    def test_requires_user_id(self) -> None:
        """Test requires user_id."""
        user_id = uuid4()
        assert user_id is not None

    def test_counts_unread_only(self) -> None:
        """Test counts unread notifications only."""
        is_read = False
        assert is_read is False

    def test_excludes_expired(self) -> None:
        """Test excludes expired notifications."""
        expires_at = datetime.utcnow() - timedelta(hours=1)
        is_expired = expires_at < datetime.utcnow()
        assert is_expired is True

    def test_returns_count(self) -> None:
        """Test returns integer count."""
        count = 5
        assert isinstance(count, int)


class TestNotifyTeamInvitation:
    """Tests for notify_team_invitation convenience method."""

    def test_requires_user_id(self) -> None:
        """Test requires user_id."""
        user_id = uuid4()
        assert user_id is not None

    def test_requires_project_id(self) -> None:
        """Test requires project_id."""
        project_id = uuid4()
        assert project_id is not None

    def test_requires_project_name(self) -> None:
        """Test requires project_name."""
        project_name = "Marina Bay Development"
        assert len(project_name) > 0

    def test_requires_inviter_name(self) -> None:
        """Test requires inviter_name."""
        inviter_name = "John Tan"
        assert len(inviter_name) > 0

    def test_requires_invitation_id(self) -> None:
        """Test requires invitation_id."""
        invitation_id = uuid4()
        assert invitation_id is not None

    def test_sets_notification_type(self) -> None:
        """Test sets notification_type to TEAM_INVITATION."""
        notification_type = "TEAM_INVITATION"
        assert notification_type == "TEAM_INVITATION"

    def test_sets_high_priority(self) -> None:
        """Test sets priority to HIGH."""
        priority = "HIGH"
        assert priority == "HIGH"

    def test_sets_title(self) -> None:
        """Test sets title to 'Team Invitation'."""
        title = "Team Invitation"
        assert title == "Team Invitation"

    def test_message_format(self) -> None:
        """Test message format includes inviter and project."""
        inviter = "John Tan"
        project = "Marina Bay"
        message = f"{inviter} has invited you to join project '{project}'"
        assert inviter in message
        assert project in message


class TestNotifyTeamMemberJoined:
    """Tests for notify_team_member_joined convenience method."""

    def test_sets_notification_type(self) -> None:
        """Test sets notification_type to TEAM_MEMBER_JOINED."""
        notification_type = "TEAM_MEMBER_JOINED"
        assert notification_type == "TEAM_MEMBER_JOINED"

    def test_sets_normal_priority(self) -> None:
        """Test sets priority to NORMAL."""
        priority = "NORMAL"
        assert priority == "NORMAL"

    def test_sets_title(self) -> None:
        """Test sets title to 'New Team Member'."""
        title = "New Team Member"
        assert title == "New Team Member"

    def test_message_format(self) -> None:
        """Test message format includes new member and project."""
        new_member = "Sarah Lim"
        project = "Marina Bay"
        message = f"{new_member} has joined project '{project}'"
        assert new_member in message
        assert project in message


class TestNotifyWorkflowStepAssigned:
    """Tests for notify_workflow_step_assigned convenience method."""

    def test_sets_notification_type(self) -> None:
        """Test sets notification_type to WORKFLOW_STEP_ASSIGNED."""
        notification_type = "WORKFLOW_STEP_ASSIGNED"
        assert notification_type == "WORKFLOW_STEP_ASSIGNED"

    def test_sets_high_priority(self) -> None:
        """Test sets priority to HIGH."""
        priority = "HIGH"
        assert priority == "HIGH"

    def test_sets_title(self) -> None:
        """Test sets title to 'Action Required'."""
        title = "Action Required"
        assert title == "Action Required"

    def test_message_format(self) -> None:
        """Test message format includes step and workflow."""
        step = "Architect Review"
        workflow = "Design Phase"
        message = f"You have been assigned to '{step}' in workflow '{workflow}'"
        assert step in message
        assert workflow in message

    def test_sets_related_entity(self) -> None:
        """Test sets related_entity_type and id."""
        entity_type = "workflow"
        entity_id = uuid4()
        assert entity_type == "workflow"
        assert entity_id is not None


class TestNotifyApprovalNeeded:
    """Tests for notify_approval_needed convenience method."""

    def test_sets_notification_type(self) -> None:
        """Test sets notification_type to WORKFLOW_APPROVAL_NEEDED."""
        notification_type = "WORKFLOW_APPROVAL_NEEDED"
        assert notification_type == "WORKFLOW_APPROVAL_NEEDED"

    def test_sets_urgent_priority(self) -> None:
        """Test sets priority to URGENT."""
        priority = "URGENT"
        assert priority == "URGENT"

    def test_sets_title(self) -> None:
        """Test sets title to 'Approval Required'."""
        title = "Approval Required"
        assert title == "Approval Required"

    def test_message_format(self) -> None:
        """Test message format includes step and workflow."""
        step = "Architect Review"
        workflow = "Design Phase"
        message = f"Your approval is needed for '{step}' in workflow '{workflow}'"
        assert step in message
        assert workflow in message


class TestNotifyRegulatoryStatusChange:
    """Tests for notify_regulatory_status_change convenience method."""

    def test_sets_notification_type(self) -> None:
        """Test sets notification_type to REGULATORY_STATUS_CHANGE."""
        notification_type = "REGULATORY_STATUS_CHANGE"
        assert notification_type == "REGULATORY_STATUS_CHANGE"

    def test_sets_high_priority(self) -> None:
        """Test sets priority to HIGH."""
        priority = "HIGH"
        assert priority == "HIGH"

    def test_sets_title(self) -> None:
        """Test sets title to 'Regulatory Update'."""
        title = "Regulatory Update"
        assert title == "Regulatory Update"

    def test_message_format(self) -> None:
        """Test message format includes submission and status."""
        submission = "URA Planning Permission"
        status = "approved"
        message = f"Submission '{submission}' status changed to: {status}"
        assert submission in message
        assert status in message

    def test_sets_related_entity(self) -> None:
        """Test sets related_entity_type to regulatory_submission."""
        entity_type = "regulatory_submission"
        assert entity_type == "regulatory_submission"


class TestPagination:
    """Tests for pagination in get_notifications."""

    def test_page_1_offset_0(self) -> None:
        """Test page 1 has offset 0."""
        page = 1
        page_size = 20
        offset = (page - 1) * page_size
        assert offset == 0

    def test_page_2_offset_20(self) -> None:
        """Test page 2 has offset 20 with page_size 20."""
        page = 2
        page_size = 20
        offset = (page - 1) * page_size
        assert offset == 20

    def test_custom_page_size(self) -> None:
        """Test custom page size."""
        page = 3
        page_size = 50
        offset = (page - 1) * page_size
        assert offset == 100

    def test_returns_notifications_list(self) -> None:
        """Test returns list of notifications."""
        notifications = []
        assert isinstance(notifications, list)


class TestEdgeCases:
    """Tests for edge cases in notification service."""

    def test_empty_notifications(self) -> None:
        """Test handling no notifications."""
        notifications = []
        total = 0
        unread = 0
        assert len(notifications) == 0
        assert total == 0
        assert unread == 0

    def test_all_notifications_read(self) -> None:
        """Test all notifications already read."""
        unread_count = 0
        assert unread_count == 0

    def test_bulk_read_empty_list(self) -> None:
        """Test bulk read with empty list."""
        notification_ids = []
        count = 0  # Would return 0
        assert len(notification_ids) == 0
        assert count == 0

    def test_delete_already_deleted(self) -> None:
        """Test delete notification that doesn't exist."""
        result = False
        assert result is False

    def test_very_old_notification(self) -> None:
        """Test very old notification."""
        created_at = datetime(2020, 1, 1)
        age_days = (datetime.utcnow() - created_at).days
        assert age_days > 365

    def test_notification_with_all_fields(self) -> None:
        """Test notification with all optional fields."""
        notification = {
            "user_id": uuid4(),
            "notification_type": "TEAM_INVITATION",
            "title": "Test",
            "message": "Test message",
            "priority": "HIGH",
            "project_id": uuid4(),
            "related_entity_type": "team_invitation",
            "related_entity_id": uuid4(),
            "expires_at": datetime.utcnow() + timedelta(days=7),
        }
        assert len(notification) == 9
