"""Tests for team management API endpoints (Phase 2E)."""

from __future__ import annotations

from datetime import timedelta
from uuid import UUID, uuid4

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")

from backend._compat.datetime import utcnow

from app.api import deps
from app.main import app
from app.models.projects import Project, ProjectPhase, ProjectType
from app.models.notification import EmailLog, Notification, NotificationType
from app.models.team import InvitationStatus, TeamInvitation, TeamMember
from app.models.users import User, UserRole
from httpx import AsyncClient
from sqlalchemy import select


pytestmark = pytest.mark.asyncio

VIEWER_ID = "00000000-0000-0000-0000-000000000001"
REVIEWER_ID = "00000000-0000-0000-0000-000000000002"
USER_ID = "00000000-0000-0000-0000-000000000003"


async def mock_viewer_identity():
    """Mock identity for viewer role."""
    return deps.RequestIdentity(
        role="viewer",
        user_id=VIEWER_ID,
        email="viewer@example.com",
    )


async def mock_reviewer_identity():
    """Mock identity for reviewer role."""
    return deps.RequestIdentity(
        role="reviewer",
        user_id=REVIEWER_ID,
        email="reviewer@example.com",
    )


async def mock_user_identity():
    """Mock identity for authenticated user."""
    return deps.RequestIdentity(
        role="developer",
        user_id=USER_ID,
        email="user@example.com",
    )


@pytest.fixture(autouse=True)
def override_auth():
    """Override authentication dependencies for testing."""
    app.dependency_overrides[deps.require_viewer] = mock_viewer_identity
    app.dependency_overrides[deps.require_reviewer] = mock_reviewer_identity
    app.dependency_overrides[deps.get_identity] = mock_user_identity
    yield
    app.dependency_overrides = {}


async def test_list_team_members_empty(client: AsyncClient, db_session) -> None:
    """Test listing team members for a project with no members."""
    project = Project(
        id=uuid4(),
        project_name="Team Test Project",
        project_code="TEAM-TEST-1",
        project_type=ProjectType.NEW_DEVELOPMENT,
        current_phase=ProjectPhase.CONCEPT,
        owner_email="owner@example.com",
    )
    db_session.add(project)
    await db_session.commit()

    response = await client.get(f"/api/v1/team/members?project_id={project.id}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


async def test_list_team_members_with_members(client: AsyncClient, db_session) -> None:
    """Test listing team members for a project with existing members."""
    project = Project(
        id=uuid4(),
        project_name="Team Test Project",
        project_code="TEAM-TEST-2",
        project_type=ProjectType.NEW_DEVELOPMENT,
        current_phase=ProjectPhase.CONCEPT,
        owner_email="owner@example.com",
    )
    db_session.add(project)

    user = User(
        id=uuid4(),
        email="member@example.com",
        username="member_" + str(uuid4())[:8],
        full_name="Team Member",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(project)
    await db_session.refresh(user)

    member = TeamMember(
        id=uuid4(),
        project_id=project.id,
        user_id=user.id,
        role=UserRole.CONSULTANT,
        is_active=True,
        joined_at=utcnow(),
    )
    db_session.add(member)
    await db_session.commit()

    response = await client.get(f"/api/v1/team/members?project_id={project.id}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["role"] == "consultant"


async def test_invite_member_success(client: AsyncClient, db_session) -> None:
    """Test inviting a new member to a project."""
    project = Project(
        id=uuid4(),
        project_name="Team Test Project",
        project_code="TEAM-TEST-3",
        project_type=ProjectType.NEW_DEVELOPMENT,
        current_phase=ProjectPhase.CONCEPT,
        owner_email="owner@example.com",
    )
    db_session.add(project)

    # Create inviter user with the mock reviewer identity
    inviter = User(
        id=UUID(REVIEWER_ID),
        email="reviewer@example.com",
        username="reviewer_" + str(uuid4())[:8],
        full_name="Reviewer User",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(inviter)

    invitee = User(
        id=uuid4(),
        email="newmember@example.com",
        username="invitee_" + str(uuid4())[:8],
        full_name="Invitee User",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(invitee)
    await db_session.commit()

    payload = {
        "email": "newmember@example.com",
        "role": "viewer",
    }

    response = await client.post(
        f"/api/v1/team/invite?project_id={project.id}",
        json=payload,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newmember@example.com"
    assert data["role"] == "viewer"
    assert data["status"] == "pending"
    assert "token" in data

    notifications = await db_session.execute(
        select(Notification).where(
            Notification.user_id == invitee.id,
            Notification.notification_type == NotificationType.TEAM_INVITE,
        )
    )
    assert notifications.scalars().first() is not None

    email_logs = await db_session.execute(
        select(EmailLog).where(EmailLog.recipient_email == "newmember@example.com")
    )
    assert email_logs.scalars().first() is not None


async def test_invite_member_invalid_email(client: AsyncClient, db_session) -> None:
    """Test inviting a member with invalid email format."""
    project = Project(
        id=uuid4(),
        project_name="Team Test Project",
        project_code="TEAM-TEST-4",
        project_type=ProjectType.NEW_DEVELOPMENT,
        current_phase=ProjectPhase.CONCEPT,
        owner_email="owner@example.com",
    )
    db_session.add(project)
    await db_session.commit()

    payload = {
        "email": "not-an-email",
        "role": "viewer",
    }

    response = await client.post(
        f"/api/v1/team/invite?project_id={project.id}",
        json=payload,
    )
    assert response.status_code == 422  # Validation error


async def test_accept_invitation_success(client: AsyncClient, db_session) -> None:
    """Test accepting a valid invitation."""
    project = Project(
        id=uuid4(),
        project_name="Team Test Project",
        project_code="TEAM-TEST-5",
        project_type=ProjectType.NEW_DEVELOPMENT,
        current_phase=ProjectPhase.CONCEPT,
        owner_email="owner@example.com",
    )
    db_session.add(project)

    inviter = User(
        id=uuid4(),
        email="inviter@example.com",
        username="inviter_" + str(uuid4())[:8],
        full_name="Inviter User",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(inviter)

    user = User(
        id=UUID(USER_ID),
        email="user@example.com",
        username="user_" + str(uuid4())[:8],
        full_name="Invited User",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(inviter)
    await db_session.refresh(project)

    invitation = TeamInvitation(
        id=uuid4(),
        project_id=project.id,
        email="user@example.com",
        role=UserRole.VIEWER,
        token="valid-token-123",
        status=InvitationStatus.PENDING,
        invited_by_id=inviter.id,
        expires_at=utcnow() + timedelta(days=7),
    )
    db_session.add(invitation)
    await db_session.commit()

    response = await client.post("/api/v1/team/invitations/valid-token-123/accept")
    assert response.status_code == 200


async def test_accept_invitation_invalid_token(client: AsyncClient) -> None:
    """Test accepting an invitation with invalid token."""
    response = await client.post("/api/v1/team/invitations/invalid-token/accept")
    assert response.status_code == 400
    assert "Invalid or expired" in response.json()["detail"]


async def test_remove_member_success(client: AsyncClient, db_session) -> None:
    """Test removing a member from a project."""
    project = Project(
        id=uuid4(),
        project_name="Team Test Project",
        project_code="TEAM-TEST-6",
        project_type=ProjectType.NEW_DEVELOPMENT,
        current_phase=ProjectPhase.CONCEPT,
        owner_email="owner@example.com",
    )
    db_session.add(project)

    user = User(
        id=uuid4(),
        email="removeme@example.com",
        username="removeme_" + str(uuid4())[:8],
        full_name="Remove Me",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(project)
    await db_session.refresh(user)

    member = TeamMember(
        id=uuid4(),
        project_id=project.id,
        user_id=user.id,
        role=UserRole.VIEWER,
        is_active=True,
        joined_at=utcnow(),
    )
    db_session.add(member)
    await db_session.commit()

    response = await client.delete(
        f"/api/v1/team/members/{user.id}?project_id={project.id}"
    )
    assert response.status_code == 200
    assert response.json() is True


async def test_remove_member_not_found(client: AsyncClient, db_session) -> None:
    """Test removing a non-existent member."""
    project = Project(
        id=uuid4(),
        project_name="Team Test Project",
        project_code="TEAM-TEST-7",
        project_type=ProjectType.NEW_DEVELOPMENT,
        current_phase=ProjectPhase.CONCEPT,
        owner_email="owner@example.com",
    )
    db_session.add(project)
    await db_session.commit()

    fake_user_id = uuid4()
    response = await client.delete(
        f"/api/v1/team/members/{fake_user_id}?project_id={project.id}"
    )
    assert response.status_code == 404
    assert "Member not found" in response.json()["detail"]
