"""Tests for notification API endpoints (Phase 2E)."""

from __future__ import annotations

from uuid import uuid4

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")

from backend._compat.datetime import utcnow

from app.api import deps
from app.main import app
from app.models.notification import (
    Notification,
    NotificationPriority,
    NotificationType,
)
from app.models.projects import Project, ProjectPhase, ProjectType
from app.models.users import User
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


# Mock identity for authenticated user
async def mock_user_identity():
    """Mock identity for authenticated user."""
    return deps.RequestIdentity(
        role="developer",
        user_id="00000000-0000-0000-0000-000000000001",
        email="user@example.com",
    )


@pytest.fixture(autouse=True)
def override_auth():
    """Override authentication dependencies for testing."""
    app.dependency_overrides[deps.get_identity] = mock_user_identity
    yield
    app.dependency_overrides = {}


async def test_list_notifications_empty(client: AsyncClient, db_session) -> None:
    """Test listing notifications when user has none."""
    user_id = uuid4()
    user = User(
        id=user_id,
        email="user@example.com",
        username="testuser_" + str(uuid4())[:8],
        full_name="Test User",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    # Update mock to use actual user ID
    async def mock_with_user():
        return deps.RequestIdentity(
            role="developer",
            user_id=str(user_id),
            email="user@example.com",
        )

    app.dependency_overrides[deps.get_identity] = mock_with_user

    response = await client.get("/api/v1/notifications")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["unread_count"] == 0
    assert data["notifications"] == []


async def test_list_notifications_with_data(client: AsyncClient, db_session) -> None:
    """Test listing notifications with existing notifications."""
    user_id = uuid4()
    user = User(
        id=user_id,
        email="user@example.com",
        username="testuser_" + str(uuid4())[:8],
        full_name="Test User",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(user)

    project = Project(
        id=uuid4(),
        project_name="Notification Test Project",
        project_code="NOTIF-TEST-1",
        project_type=ProjectType.NEW_DEVELOPMENT,
        current_phase=ProjectPhase.CONCEPT,
        owner_email="owner@example.com",
    )
    db_session.add(project)
    await db_session.commit()

    # Update mock to use actual user ID
    async def mock_with_user():
        return deps.RequestIdentity(
            role="developer",
            user_id=str(user_id),
            email="user@example.com",
        )

    app.dependency_overrides[deps.get_identity] = mock_with_user

    # Create test notifications
    notification1 = Notification(
        id=uuid4(),
        user_id=user_id,
        notification_type=NotificationType.TEAM_INVITATION,
        title="Team Invitation",
        message="You have been invited to join a project",
        priority=NotificationPriority.HIGH,
        project_id=project.id,
        is_read=False,
        created_at=utcnow(),
    )
    notification2 = Notification(
        id=uuid4(),
        user_id=user_id,
        notification_type=NotificationType.WORKFLOW_STEP_ASSIGNED,
        title="New Assignment",
        message="You have been assigned a workflow step",
        priority=NotificationPriority.NORMAL,
        is_read=True,
        created_at=utcnow(),
    )
    db_session.add_all([notification1, notification2])
    await db_session.commit()

    response = await client.get("/api/v1/notifications")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert data["unread_count"] == 1
    assert len(data["notifications"]) == 2


async def test_list_notifications_unread_only(client: AsyncClient, db_session) -> None:
    """Test filtering notifications to unread only."""
    user_id = uuid4()
    user = User(
        id=user_id,
        email="user@example.com",
        username="testuser_" + str(uuid4())[:8],
        full_name="Test User",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    async def mock_with_user():
        return deps.RequestIdentity(
            role="developer",
            user_id=str(user_id),
            email="user@example.com",
        )

    app.dependency_overrides[deps.get_identity] = mock_with_user

    # Create one read and one unread notification
    notification1 = Notification(
        id=uuid4(),
        user_id=user_id,
        notification_type=NotificationType.SYSTEM_ANNOUNCEMENT,
        title="System Update",
        message="System maintenance scheduled",
        is_read=False,
        created_at=utcnow(),
    )
    notification2 = Notification(
        id=uuid4(),
        user_id=user_id,
        notification_type=NotificationType.PROJECT_UPDATE,
        title="Project Update",
        message="Project status changed",
        is_read=True,
        created_at=utcnow(),
    )
    db_session.add_all([notification1, notification2])
    await db_session.commit()

    response = await client.get("/api/v1/notifications?unread_only=true")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["notifications"]) == 1
    assert data["notifications"][0]["is_read"] is False


async def test_get_notification_count(client: AsyncClient, db_session) -> None:
    """Test getting notification counts."""
    user_id = uuid4()
    user = User(
        id=user_id,
        email="user@example.com",
        username="testuser_" + str(uuid4())[:8],
        full_name="Test User",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    async def mock_with_user():
        return deps.RequestIdentity(
            role="developer",
            user_id=str(user_id),
            email="user@example.com",
        )

    app.dependency_overrides[deps.get_identity] = mock_with_user

    # Create notifications
    for i in range(5):
        notification = Notification(
            id=uuid4(),
            user_id=user_id,
            notification_type=NotificationType.PROJECT_UPDATE,
            title=f"Update {i}",
            message=f"Project update {i}",
            is_read=(i < 2),  # First 2 are read
            created_at=utcnow(),
        )
        db_session.add(notification)
    await db_session.commit()

    response = await client.get("/api/v1/notifications/count")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert data["unread"] == 3


async def test_get_notification_by_id(client: AsyncClient, db_session) -> None:
    """Test getting a specific notification by ID."""
    user_id = uuid4()
    user = User(
        id=user_id,
        email="user@example.com",
        username="testuser_" + str(uuid4())[:8],
        full_name="Test User",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    async def mock_with_user():
        return deps.RequestIdentity(
            role="developer",
            user_id=str(user_id),
            email="user@example.com",
        )

    app.dependency_overrides[deps.get_identity] = mock_with_user

    notification = Notification(
        id=uuid4(),
        user_id=user_id,
        notification_type=NotificationType.WORKFLOW_APPROVAL_NEEDED,
        title="Approval Required",
        message="Your approval is needed",
        priority=NotificationPriority.URGENT,
        is_read=False,
        created_at=utcnow(),
    )
    db_session.add(notification)
    await db_session.commit()

    response = await client.get(f"/api/v1/notifications/{notification.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(notification.id)
    assert data["title"] == "Approval Required"
    assert data["priority"] == "urgent"


async def test_get_notification_not_found(client: AsyncClient, db_session) -> None:
    """Test getting a non-existent notification returns 404."""
    user_id = uuid4()
    user = User(
        id=user_id,
        email="user@example.com",
        username="testuser_" + str(uuid4())[:8],
        full_name="Test User",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    async def mock_with_user():
        return deps.RequestIdentity(
            role="developer",
            user_id=str(user_id),
            email="user@example.com",
        )

    app.dependency_overrides[deps.get_identity] = mock_with_user

    fake_id = uuid4()
    response = await client.get(f"/api/v1/notifications/{fake_id}")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


async def test_mark_notification_as_read(client: AsyncClient, db_session) -> None:
    """Test marking a notification as read."""
    user_id = uuid4()
    user = User(
        id=user_id,
        email="user@example.com",
        username="testuser_" + str(uuid4())[:8],
        full_name="Test User",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    async def mock_with_user():
        return deps.RequestIdentity(
            role="developer",
            user_id=str(user_id),
            email="user@example.com",
        )

    app.dependency_overrides[deps.get_identity] = mock_with_user

    notification = Notification(
        id=uuid4(),
        user_id=user_id,
        notification_type=NotificationType.TEAM_MEMBER_JOINED,
        title="New Member",
        message="A new member joined the project",
        is_read=False,
        created_at=utcnow(),
    )
    db_session.add(notification)
    await db_session.commit()

    response = await client.patch(f"/api/v1/notifications/{notification.id}/read")
    assert response.status_code == 200
    data = response.json()
    assert data["is_read"] is True
    assert data["read_at"] is not None


async def test_mark_all_as_read(client: AsyncClient, db_session) -> None:
    """Test marking all notifications as read."""
    user_id = uuid4()
    user = User(
        id=user_id,
        email="user@example.com",
        username="testuser_" + str(uuid4())[:8],
        full_name="Test User",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    async def mock_with_user():
        return deps.RequestIdentity(
            role="developer",
            user_id=str(user_id),
            email="user@example.com",
        )

    app.dependency_overrides[deps.get_identity] = mock_with_user

    # Create multiple unread notifications
    for i in range(3):
        notification = Notification(
            id=uuid4(),
            user_id=user_id,
            notification_type=NotificationType.PROJECT_UPDATE,
            title=f"Update {i}",
            message=f"Project update {i}",
            is_read=False,
            created_at=utcnow(),
        )
        db_session.add(notification)
    await db_session.commit()

    response = await client.post("/api/v1/notifications/read-all")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 3


async def test_delete_notification(client: AsyncClient, db_session) -> None:
    """Test deleting a notification."""
    user_id = uuid4()
    user = User(
        id=user_id,
        email="user@example.com",
        username="testuser_" + str(uuid4())[:8],
        full_name="Test User",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    async def mock_with_user():
        return deps.RequestIdentity(
            role="developer",
            user_id=str(user_id),
            email="user@example.com",
        )

    app.dependency_overrides[deps.get_identity] = mock_with_user

    notification = Notification(
        id=uuid4(),
        user_id=user_id,
        notification_type=NotificationType.SYSTEM_ANNOUNCEMENT,
        title="Old Announcement",
        message="This is an old announcement",
        is_read=True,
        created_at=utcnow(),
    )
    db_session.add(notification)
    await db_session.commit()

    response = await client.delete(f"/api/v1/notifications/{notification.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["deleted"] is True

    # Verify it's deleted
    response = await client.get(f"/api/v1/notifications/{notification.id}")
    assert response.status_code == 404


async def test_delete_notification_not_found(client: AsyncClient, db_session) -> None:
    """Test deleting a non-existent notification returns 404."""
    user_id = uuid4()
    user = User(
        id=user_id,
        email="user@example.com",
        username="testuser_" + str(uuid4())[:8],
        full_name="Test User",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    async def mock_with_user():
        return deps.RequestIdentity(
            role="developer",
            user_id=str(user_id),
            email="user@example.com",
        )

    app.dependency_overrides[deps.get_identity] = mock_with_user

    fake_id = uuid4()
    response = await client.delete(f"/api/v1/notifications/{fake_id}")
    assert response.status_code == 404
