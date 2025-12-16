"""Tests for approval workflow API endpoints (Phase 2E)."""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")

from backend._compat.datetime import utcnow

from app.api import deps
from app.main import app
from app.models.notification import Notification, NotificationType
from app.models.projects import Project, ProjectPhase, ProjectType
from app.models.team import TeamMember
from app.models.users import User, UserRole
from app.models.workflow import (
    ApprovalStep,
    ApprovalWorkflow,
    StepStatus,
    WorkflowStatus,
)
from httpx import AsyncClient
from sqlalchemy import select


pytestmark = pytest.mark.asyncio

VIEWER_ID = "00000000-0000-0000-0000-000000000001"
REVIEWER_ID = "00000000-0000-0000-0000-000000000002"
APPROVER_ID = "00000000-0000-0000-0000-000000000003"


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


async def mock_approver_identity():
    """Mock identity for approver."""
    return deps.RequestIdentity(
        role="developer",
        user_id=APPROVER_ID,
        email="approver@example.com",
    )


@pytest.fixture(autouse=True)
def override_auth():
    """Override authentication dependencies for testing."""
    app.dependency_overrides[deps.require_viewer] = mock_viewer_identity
    app.dependency_overrides[deps.require_reviewer] = mock_reviewer_identity
    app.dependency_overrides[deps.get_identity] = mock_approver_identity
    yield
    app.dependency_overrides = {}


async def test_create_workflow_success(client: AsyncClient, db_session) -> None:
    """Test creating a new approval workflow."""
    project = Project(
        id=uuid4(),
        project_name="Workflow Test Project",
        project_code="WF-TEST-1",
        project_type=ProjectType.NEW_DEVELOPMENT,
        current_phase=ProjectPhase.CONCEPT,
        owner_email="owner@example.com",
    )
    db_session.add(project)

    creator = User(
        id=UUID(REVIEWER_ID),
        email="reviewer@example.com",
        username="reviewer_" + str(uuid4())[:8],
        full_name="Reviewer User",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(creator)
    await db_session.commit()

    payload = {
        "title": "Design Approval",
        "description": "Approval workflow for design phase",
        "workflow_type": "design_review",
        "steps": [
            {"name": "Consultant Review", "required_role": "consultant"},
            {"name": "Developer Review", "required_role": "developer"},
            {"name": "Final Approval", "required_role": "admin"},
        ],
    }

    response = await client.post(
        f"/api/v1/workflow/?project_id={project.id}",
        json=payload,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Design Approval"
    assert data["workflow_type"] == "design_review"
    assert data["status"] == "in_progress"
    assert len(data["steps"]) == 3


async def test_list_workflows_returns_created_workflows(
    client: AsyncClient, db_session
) -> None:
    project = Project(
        id=uuid4(),
        project_name="Workflow List Project",
        project_code="WF-LIST-1",
        project_type=ProjectType.NEW_DEVELOPMENT,
        current_phase=ProjectPhase.CONCEPT,
        owner_email="owner@example.com",
    )
    db_session.add(project)

    creator = User(
        id=UUID(REVIEWER_ID),
        email="reviewer@example.com",
        username="reviewer_" + str(uuid4())[:8],
        full_name="Reviewer User",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(creator)
    await db_session.commit()

    payload = {
        "title": "Budget Approval",
        "workflow_type": "budget_approval",
        "steps": [{"name": "Developer Review", "required_role": "developer"}],
    }
    create_response = await client.post(
        f"/api/v1/workflow/?project_id={project.id}",
        json=payload,
    )
    assert create_response.status_code == 200

    list_response = await client.get(f"/api/v1/workflow/?project_id={project.id}")
    assert list_response.status_code == 200
    workflows = list_response.json()
    assert isinstance(workflows, list)
    assert len(workflows) == 1
    assert workflows[0]["title"] == "Budget Approval"
    assert workflows[0]["project_id"] == str(project.id)


async def test_create_workflow_empty_steps(client: AsyncClient, db_session) -> None:
    """Test creating a workflow with no steps."""
    project = Project(
        id=uuid4(),
        project_name="Workflow Test Project",
        project_code="WF-TEST-2",
        project_type=ProjectType.NEW_DEVELOPMENT,
        current_phase=ProjectPhase.CONCEPT,
        owner_email="owner@example.com",
    )
    db_session.add(project)
    await db_session.commit()

    reviewer = User(
        id=UUID(REVIEWER_ID),
        email="reviewer@example.com",
        username="reviewer_" + str(uuid4())[:8],
        full_name="Reviewer User",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(reviewer)
    await db_session.commit()

    payload = {
        "title": "Empty Workflow",
        "workflow_type": "review",
        "steps": [],
    }

    response = await client.post(
        f"/api/v1/workflow/?project_id={project.id}",
        json=payload,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Empty Workflow"
    assert data["workflow_type"] == "review"
    assert data["steps"] == []


async def test_get_workflow_success(client: AsyncClient, db_session) -> None:
    """Test getting workflow details."""
    project = Project(
        id=uuid4(),
        project_name="Workflow Test Project",
        project_code="WF-TEST-3",
        project_type=ProjectType.NEW_DEVELOPMENT,
        current_phase=ProjectPhase.CONCEPT,
        owner_email="owner@example.com",
    )
    db_session.add(project)

    creator = User(
        id=uuid4(),
        email="creator@example.com",
        username="creator_" + str(uuid4())[:8],
        full_name="Creator User",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(creator)
    await db_session.commit()
    await db_session.refresh(project)
    await db_session.refresh(creator)

    workflow = ApprovalWorkflow(
        id=uuid4(),
        project_id=project.id,
        title="Test Workflow",
        description="Test description",
        workflow_type="feasibility_signoff",
        status=WorkflowStatus.IN_PROGRESS,
        created_by_id=creator.id,
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    db_session.add(workflow)
    await db_session.commit()
    await db_session.refresh(workflow)

    step = ApprovalStep(
        id=uuid4(),
        workflow_id=workflow.id,
        name="Step 1",
        sequence_order=1,
        required_role=UserRole.DEVELOPER,
        status=StepStatus.PENDING,
    )
    db_session.add(step)
    await db_session.commit()

    response = await client.get(f"/api/v1/workflow/{workflow.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Workflow"
    assert data["status"] == "in_progress"
    assert len(data["steps"]) == 1
    assert data["steps"][0]["name"] == "Step 1"


async def test_get_workflow_not_found(client: AsyncClient) -> None:
    """Test getting a non-existent workflow."""
    fake_workflow_id = uuid4()
    response = await client.get(f"/api/v1/workflow/{fake_workflow_id}")
    assert response.status_code == 404
    assert "Workflow not found" in response.json()["detail"]


async def test_approve_step_success(client: AsyncClient, db_session) -> None:
    """Test approving a workflow step."""
    project = Project(
        id=uuid4(),
        project_name="Workflow Test Project",
        project_code="WF-TEST-4",
        project_type=ProjectType.NEW_DEVELOPMENT,
        current_phase=ProjectPhase.CONCEPT,
        owner_email="owner@example.com",
    )
    db_session.add(project)

    approver = User(
        id=UUID(APPROVER_ID),
        email="approver@example.com",
        username="approver_" + str(uuid4())[:8],
        full_name="Approver User",
        hashed_password="hashed",
        role=UserRole.DEVELOPER,
        is_active=True,
    )
    db_session.add(approver)

    creator = User(
        id=uuid4(),
        email="creator@example.com",
        username="creator_" + str(uuid4())[:8],
        full_name="Creator User",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(creator)
    await db_session.commit()
    await db_session.refresh(project)
    await db_session.refresh(creator)

    reviewer = User(
        id=UUID(REVIEWER_ID),
        email="reviewer@example.com",
        username="reviewer_" + str(uuid4())[:8],
        full_name="Reviewer User",
        hashed_password="hashed",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(reviewer)
    await db_session.commit()

    workflow = ApprovalWorkflow(
        id=uuid4(),
        project_id=project.id,
        title="Approval Workflow",
        workflow_type="review",
        status=WorkflowStatus.IN_PROGRESS,
        created_by_id=creator.id,
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    db_session.add(workflow)
    await db_session.commit()
    await db_session.refresh(workflow)

    step = ApprovalStep(
        id=uuid4(),
        workflow_id=workflow.id,
        name="Approval Step",
        sequence_order=1,
        required_role=UserRole.DEVELOPER,
        status=StepStatus.IN_REVIEW,
    )
    db_session.add(step)
    db_session.add(
        TeamMember(
            id=uuid4(),
            project_id=project.id,
            user_id=approver.id,
            role=UserRole.DEVELOPER,
            is_active=True,
            joined_at=utcnow(),
        )
    )
    await db_session.commit()

    payload = {
        "approved": True,
        "comments": "Looks good, approved!",
    }

    response = await client.post(
        f"/api/v1/workflow/steps/{step.id}/approve",
        json=payload,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["steps"][0]["status"] == "approved"

    result = await db_session.execute(
        select(Notification).where(
            Notification.user_id == creator.id,
            Notification.notification_type == NotificationType.WORKFLOW_APPROVED,
        )
    )
    assert result.scalars().first() is not None


async def test_reject_step_success(client: AsyncClient, db_session) -> None:
    """Test rejecting a workflow step."""
    project = Project(
        id=uuid4(),
        project_name="Workflow Test Project",
        project_code="WF-TEST-5",
        project_type=ProjectType.NEW_DEVELOPMENT,
        current_phase=ProjectPhase.CONCEPT,
        owner_email="owner@example.com",
    )
    db_session.add(project)

    approver = User(
        id=UUID(APPROVER_ID),
        email="approver@example.com",
        username="approver_" + str(uuid4())[:8],
        full_name="Approver User",
        hashed_password="hashed",
        role=UserRole.DEVELOPER,
        is_active=True,
    )
    db_session.add(approver)

    creator = User(
        id=uuid4(),
        email="creator@example.com",
        username="creator_" + str(uuid4())[:8],
        full_name="Creator User",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(creator)
    await db_session.commit()
    await db_session.refresh(project)
    await db_session.refresh(creator)

    workflow = ApprovalWorkflow(
        id=uuid4(),
        project_id=project.id,
        title="Rejection Workflow",
        workflow_type="review",
        status=WorkflowStatus.IN_PROGRESS,
        created_by_id=creator.id,
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    db_session.add(workflow)
    await db_session.commit()
    await db_session.refresh(workflow)

    step = ApprovalStep(
        id=uuid4(),
        workflow_id=workflow.id,
        name="Review Step",
        sequence_order=1,
        required_role=UserRole.DEVELOPER,
        status=StepStatus.IN_REVIEW,
    )
    db_session.add(step)
    db_session.add(
        TeamMember(
            id=uuid4(),
            project_id=project.id,
            user_id=approver.id,
            role=UserRole.DEVELOPER,
            is_active=True,
            joined_at=utcnow(),
        )
    )
    await db_session.commit()

    payload = {
        "approved": False,
        "comments": "Needs revisions before approval.",
    }

    response = await client.post(
        f"/api/v1/workflow/steps/{step.id}/approve",
        json=payload,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"


async def test_approve_step_requires_role(client: AsyncClient, db_session) -> None:
    """Approving should be forbidden when the user lacks the required role."""
    project = Project(
        id=uuid4(),
        project_name="Workflow Test Project",
        project_code="WF-TEST-ROLE",
        project_type=ProjectType.NEW_DEVELOPMENT,
        current_phase=ProjectPhase.CONCEPT,
        owner_email="owner@example.com",
    )
    db_session.add(project)

    approver = User(
        id=UUID(APPROVER_ID),
        email="approver@example.com",
        username="approver_" + str(uuid4())[:8],
        full_name="Approver User",
        hashed_password="hashed",
        role=UserRole.DEVELOPER,
        is_active=True,
    )
    creator = User(
        id=uuid4(),
        email="creator@example.com",
        username="creator_" + str(uuid4())[:8],
        full_name="Creator User",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add_all([approver, creator])
    await db_session.commit()
    await db_session.refresh(project)
    await db_session.refresh(creator)

    workflow = ApprovalWorkflow(
        id=uuid4(),
        project_id=project.id,
        title="Role-Gated Workflow",
        workflow_type="review",
        status=WorkflowStatus.IN_PROGRESS,
        created_by_id=creator.id,
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    db_session.add(workflow)
    await db_session.commit()
    await db_session.refresh(workflow)

    step = ApprovalStep(
        id=uuid4(),
        workflow_id=workflow.id,
        name="Consultant-only Step",
        sequence_order=1,
        required_role=UserRole.CONSULTANT,
        status=StepStatus.IN_REVIEW,
    )
    db_session.add(step)
    db_session.add(
        TeamMember(
            id=uuid4(),
            project_id=project.id,
            user_id=approver.id,
            role=UserRole.DEVELOPER,
            is_active=True,
            joined_at=utcnow(),
        )
    )
    await db_session.commit()

    response = await client.post(
        f"/api/v1/workflow/steps/{step.id}/approve",
        json={"approved": True, "comments": "Trying to approve"},
    )
    assert response.status_code == 403


async def test_approve_step_invalid_step_id(client: AsyncClient) -> None:
    """Test approving a non-existent step."""
    fake_step_id = uuid4()
    payload = {
        "approved": True,
        "comments": "Trying to approve non-existent step",
    }

    response = await client.post(
        f"/api/v1/workflow/steps/{fake_step_id}/approve",
        json=payload,
    )
    assert response.status_code == 400
    assert "Step not found" in response.json()["detail"]


async def test_workflow_multi_step_progression(client: AsyncClient, db_session) -> None:
    """Test workflow with multiple steps progresses correctly."""
    project = Project(
        id=uuid4(),
        project_name="Workflow Test Project",
        project_code="WF-TEST-6",
        project_type=ProjectType.NEW_DEVELOPMENT,
        current_phase=ProjectPhase.CONCEPT,
        owner_email="owner@example.com",
    )
    db_session.add(project)

    creator = User(
        id=uuid4(),
        email="creator@example.com",
        username="creator_" + str(uuid4())[:8],
        full_name="Creator User",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(creator)
    await db_session.commit()
    await db_session.refresh(project)
    await db_session.refresh(creator)

    workflow = ApprovalWorkflow(
        id=uuid4(),
        project_id=project.id,
        title="Multi-Step Workflow",
        workflow_type="comprehensive_review",
        status=WorkflowStatus.IN_PROGRESS,
        created_by_id=creator.id,
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    db_session.add(workflow)
    await db_session.commit()
    await db_session.refresh(workflow)

    step1 = ApprovalStep(
        id=uuid4(),
        workflow_id=workflow.id,
        name="Step 1: Initial Review",
        sequence_order=1,
        status=StepStatus.IN_REVIEW,
    )
    step2 = ApprovalStep(
        id=uuid4(),
        workflow_id=workflow.id,
        name="Step 2: Technical Review",
        sequence_order=2,
        status=StepStatus.PENDING,
    )
    step3 = ApprovalStep(
        id=uuid4(),
        workflow_id=workflow.id,
        name="Step 3: Final Approval",
        sequence_order=3,
        status=StepStatus.PENDING,
    )
    db_session.add_all([step1, step2, step3])
    await db_session.commit()

    # Verify workflow has 3 steps
    response = await client.get(f"/api/v1/workflow/{workflow.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["steps"]) == 3
    assert data["steps"][0]["status"] == "in_review"
    assert data["steps"][1]["status"] == "pending"
    assert data["steps"][2]["status"] == "pending"
