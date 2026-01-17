"""Tests for projects API endpoints."""

from __future__ import annotations

import uuid

import pytest


@pytest.mark.asyncio
async def test_create_project_success(client):
    """Test creating a new project with valid data."""
    payload = {
        "name": "Test Project",
        "description": "A test project description",
        "location": "Singapore",
        "project_type": "new_development",
        "status": "planning",
        "budget": 1000000.0,
    }
    response = await client.post("/api/v1/projects/create", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == payload["name"]
    assert body["description"] == payload["description"]
    assert body["project_type"] == payload["project_type"]
    assert body["status"] == "concept"  # planning maps to concept phase
    assert body["budget"] == payload["budget"]
    assert body["is_active"] is True
    assert "id" in body
    assert "created_at" in body
    assert "updated_at" in body


@pytest.mark.asyncio
async def test_create_project_minimal(client):
    """Test creating a project with minimal required fields."""
    payload = {
        "name": "Minimal Project",
    }
    response = await client.post("/api/v1/projects/create", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Minimal Project"
    assert body["description"] is None
    assert body["is_active"] is True


@pytest.mark.asyncio
async def test_create_project_invalid_type_falls_back(client):
    """Test that invalid project type falls back to new_development."""
    payload = {
        "name": "Invalid Type Project",
        "project_type": "invalid_type",
    }
    response = await client.post("/api/v1/projects/create", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["project_type"] == "new_development"


@pytest.mark.asyncio
async def test_create_project_different_statuses(client):
    """Test creating projects with different status values."""
    status_to_phase = {
        "planning": "concept",
        "approval": "approval",
        "construction": "construction",
        "completed": "operation",
    }
    for status, expected_phase in status_to_phase.items():
        payload = {
            "name": f"Project {status}",
            "status": status,
        }
        response = await client.post("/api/v1/projects/create", json=payload)
        assert response.status_code == 201
        body = response.json()
        assert body["status"] == expected_phase


@pytest.mark.asyncio
async def test_list_projects_empty(client):
    """Test listing projects when none exist."""
    response = await client.get("/api/v1/projects/list")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)


@pytest.mark.asyncio
async def test_list_projects_with_pagination(client):
    """Test listing projects with pagination parameters."""
    # Create some projects
    for i in range(5):
        payload = {"name": f"Project {i}"}
        await client.post("/api/v1/projects/create", json=payload)

    # Test with skip and limit
    response = await client.get("/api/v1/projects/list?skip=0&limit=2")
    assert response.status_code == 200
    body = response.json()
    assert len(body) <= 2

    # Test skip
    response = await client.get("/api/v1/projects/list?skip=3&limit=10")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_project_success(client):
    """Test getting a specific project by ID."""
    # Create a project
    create_response = await client.post(
        "/api/v1/projects/create",
        json={"name": "Get Test Project", "description": "Test description"},
    )
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    # Get the project
    response = await client.get(f"/api/v1/projects/{project_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == project_id
    assert body["name"] == "Get Test Project"
    assert body["description"] == "Test description"


@pytest.mark.asyncio
async def test_get_project_invalid_uuid(client):
    """Test getting a project with invalid UUID format."""
    response = await client.get("/api/v1/projects/not-a-uuid")
    assert response.status_code == 400
    body = response.json()
    assert "Invalid project ID format" in body["detail"]


@pytest.mark.asyncio
async def test_get_project_not_found(client):
    """Test getting a project that doesn't exist."""
    fake_uuid = str(uuid.uuid4())
    response = await client.get(f"/api/v1/projects/{fake_uuid}")
    assert response.status_code == 404
    body = response.json()
    assert body["detail"] == "Project not found"


@pytest.mark.asyncio
async def test_update_project_success(client):
    """Test updating a project with valid data."""
    # Create a project
    create_response = await client.post(
        "/api/v1/projects/create",
        json={"name": "Original Name", "description": "Original description"},
    )
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    # Update the project
    update_payload = {
        "name": "Updated Name",
        "description": "Updated description",
        "budget": 2000000.0,
    }
    response = await client.put(f"/api/v1/projects/{project_id}", json=update_payload)
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Updated Name"
    assert body["description"] == "Updated description"
    assert body["budget"] == 2000000.0


@pytest.mark.asyncio
async def test_update_project_partial(client):
    """Test partial update of a project."""
    # Create a project
    create_response = await client.post(
        "/api/v1/projects/create",
        json={"name": "Partial Update", "description": "Original description"},
    )
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    # Update only name
    response = await client.put(
        f"/api/v1/projects/{project_id}",
        json={"name": "New Name Only"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "New Name Only"
    assert body["description"] == "Original description"


@pytest.mark.asyncio
async def test_update_project_status_changes_phase(client):
    """Test that updating status changes the project phase."""
    # Create a project
    create_response = await client.post(
        "/api/v1/projects/create",
        json={"name": "Status Update Test"},
    )
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    # Update status to construction
    response = await client.put(
        f"/api/v1/projects/{project_id}",
        json={"status": "construction"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "construction"


@pytest.mark.asyncio
async def test_update_project_invalid_uuid(client):
    """Test updating a project with invalid UUID format."""
    response = await client.put(
        "/api/v1/projects/not-a-uuid",
        json={"name": "Updated"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_update_project_not_found(client):
    """Test updating a project that doesn't exist."""
    fake_uuid = str(uuid.uuid4())
    response = await client.put(
        f"/api/v1/projects/{fake_uuid}",
        json={"name": "Updated"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_project_type(client):
    """Test updating project type."""
    # Create a project
    create_response = await client.post(
        "/api/v1/projects/create",
        json={"name": "Type Update Test", "project_type": "new_development"},
    )
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    # Update project type - note: invalid types are ignored
    response = await client.put(
        f"/api/v1/projects/{project_id}",
        json={"project_type": "redevelopment"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_project_success(client):
    """Test soft deleting a project."""
    # Create a project
    create_response = await client.post(
        "/api/v1/projects/create",
        json={"name": "Delete Test Project"},
    )
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    # Delete the project
    response = await client.delete(f"/api/v1/projects/{project_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Project deleted successfully"
    assert body["project_id"] == project_id

    # Verify project is no longer accessible (soft deleted)
    get_response = await client.get(f"/api/v1/projects/{project_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_project_invalid_uuid(client):
    """Test deleting a project with invalid UUID format."""
    response = await client.delete("/api/v1/projects/not-a-uuid")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_delete_project_not_found(client):
    """Test deleting a project that doesn't exist."""
    fake_uuid = str(uuid.uuid4())
    response = await client.delete(f"/api/v1/projects/{fake_uuid}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_project_stats(client):
    """Test getting project statistics."""
    # Create some projects with different phases
    await client.post(
        "/api/v1/projects/create",
        json={"name": "Planning Project", "status": "planning", "budget": 1000000},
    )
    await client.post(
        "/api/v1/projects/create",
        json={"name": "Construction Project", "status": "construction", "budget": 2000000},
    )
    await client.post(
        "/api/v1/projects/create",
        json={"name": "Completed Project", "status": "completed", "budget": 3000000},
    )

    response = await client.get("/api/v1/projects/stats/summary")
    assert response.status_code == 200
    body = response.json()
    assert "total_projects" in body
    assert "total_budget" in body
    assert "active_projects" in body
    assert "completed_projects" in body
    assert "status_breakdown" in body
    assert "type_breakdown" in body
    assert "recent_projects" in body
    assert isinstance(body["recent_projects"], list)


@pytest.mark.asyncio
async def test_get_project_progress(client):
    """Test getting project progress details."""
    # Create a project
    create_response = await client.post(
        "/api/v1/projects/create",
        json={"name": "Progress Test Project", "status": "construction"},
    )
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    # Get progress
    response = await client.get(f"/api/v1/projects/{project_id}/progress")
    assert response.status_code == 200
    body = response.json()
    assert "project" in body
    assert body["project"]["id"] == project_id
    assert body["project"]["name"] == "Progress Test Project"
    assert "phases" in body
    assert isinstance(body["phases"], list)
    assert "workflow_summary" in body
    assert "total_steps" in body["workflow_summary"]
    assert "approved_steps" in body["workflow_summary"]
    assert "pending_steps" in body["workflow_summary"]
    assert "pending_approvals" in body
    assert "team_activity" in body


@pytest.mark.asyncio
async def test_get_project_progress_not_found(client):
    """Test getting progress for non-existent project."""
    fake_uuid = str(uuid.uuid4())
    response = await client.get(f"/api/v1/projects/{fake_uuid}/progress")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_project_progress_invalid_uuid(client):
    """Test getting progress with invalid UUID."""
    response = await client.get("/api/v1/projects/invalid-uuid/progress")
    # The normalise_project_id function may raise different errors
    assert response.status_code in (400, 422)


@pytest.mark.asyncio
async def test_project_response_conversion():
    """Test the _project_to_response helper function."""
    from datetime import datetime, timezone
    from unittest.mock import MagicMock

    from app.api.v1.projects_api import _project_to_response
    from app.models.projects import ProjectPhase, ProjectType

    mock_project = MagicMock()
    mock_project.id = uuid.uuid4()
    mock_project.project_name = "Test Project"
    mock_project.description = "Description"
    mock_project.project_type = ProjectType.NEW_DEVELOPMENT
    mock_project.current_phase = ProjectPhase.CONSTRUCTION
    mock_project.estimated_cost_sgd = 1000000.0
    mock_project.owner_email = "owner@example.com"
    mock_project.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    mock_project.updated_at = datetime(2024, 1, 2, tzinfo=timezone.utc)
    mock_project.is_active = True

    response = _project_to_response(mock_project)

    assert response.id == str(mock_project.id)
    assert response.name == "Test Project"
    assert response.description == "Description"
    assert response.project_type == "new_development"
    assert response.status == "construction"
    assert response.budget == 1000000.0
    assert response.owner_email == "owner@example.com"
    assert response.is_active is True


@pytest.mark.asyncio
async def test_generate_project_code():
    """Test project code generation."""
    from app.api.v1.projects_api import _generate_project_code

    code = _generate_project_code()
    assert code.startswith("PROJ-")
    assert len(code) == 13  # PROJ- (5) + 8 hex chars


@pytest.mark.asyncio
async def test_phase_display_name():
    """Test phase display name conversion."""
    from app.api.v1.projects_api import _phase_display_name
    from app.models.projects import ProjectPhase

    assert _phase_display_name(ProjectPhase.CONCEPT) == "Concept"
    assert _phase_display_name(ProjectPhase.CONSTRUCTION) == "Construction"
    assert _phase_display_name(ProjectPhase.TESTING_COMMISSIONING) == "Testing Commissioning"


@pytest.mark.asyncio
async def test_phase_status_from_development():
    """Test development phase status mapping."""
    from app.api.v1.projects_api import _phase_status_from_development
    from app.models.development_phase import PhaseStatus

    assert _phase_status_from_development(None) == "not_started"
    assert _phase_status_from_development(PhaseStatus.NOT_STARTED) == "not_started"
    assert _phase_status_from_development(PhaseStatus.IN_PROGRESS) == "in_progress"
    assert _phase_status_from_development(PhaseStatus.COMPLETED) == "completed"
    assert _phase_status_from_development(PhaseStatus.DELAYED) == "delayed"
    assert _phase_status_from_development(PhaseStatus.ON_HOLD) == "delayed"


@pytest.mark.asyncio
async def test_workflow_step_status():
    """Test workflow step status conversion."""
    from app.api.v1.projects_api import _workflow_step_status
    from app.models.workflow import StepStatus

    assert _workflow_step_status(None) == StepStatus.PENDING.value
    assert _workflow_step_status("") == StepStatus.PENDING.value
    assert _workflow_step_status("APPROVED") == "approved"
    assert _workflow_step_status("Pending") == "pending"


# Dashboard endpoint tests
@pytest.mark.asyncio
async def test_get_project_dashboard_success(client):
    """Test getting dashboard data for a project."""
    # Create a project with budget
    create_response = await client.post(
        "/api/v1/projects/create",
        json={
            "name": "Dashboard Test Project",
            "status": "construction",
            "budget": 42500000.0,
        },
    )
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    # Get dashboard
    response = await client.get(f"/api/v1/projects/{project_id}/dashboard")
    assert response.status_code == 200
    body = response.json()

    # Verify project info
    assert body["project_id"] == project_id
    assert body["project_name"] == "Dashboard Test Project"
    assert body["status"] == "construction"

    # Verify KPIs structure
    assert "kpis" in body
    assert isinstance(body["kpis"], list)
    assert len(body["kpis"]) == 4

    kpi_labels = [kpi["label"] for kpi in body["kpis"]]
    assert "Total GFA" in kpi_labels
    assert "Development Cost" in kpi_labels
    assert "Projected Revenue" in kpi_labels
    assert "IRR" in kpi_labels

    # The development cost KPI should have the budget value
    dev_cost_kpi = next(kpi for kpi in body["kpis"] if kpi["label"] == "Development Cost")
    assert dev_cost_kpi["raw_value"] == 42500000.0
    assert dev_cost_kpi["value"] == "$42.5M"

    # Verify modules structure
    assert "modules" in body
    assert isinstance(body["modules"], list)
    assert len(body["modules"]) == 6

    module_keys = [m["key"] for m in body["modules"]]
    assert "capture" in module_keys
    assert "feasibility" in module_keys
    assert "finance" in module_keys
    assert "phases" in module_keys
    assert "team" in module_keys
    assert "regulatory" in module_keys


@pytest.mark.asyncio
async def test_get_project_dashboard_not_found(client):
    """Test getting dashboard for non-existent project."""
    fake_uuid = str(uuid.uuid4())
    response = await client.get(f"/api/v1/projects/{fake_uuid}/dashboard")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_project_dashboard_invalid_uuid(client):
    """Test getting dashboard with invalid UUID."""
    response = await client.get("/api/v1/projects/invalid-uuid/dashboard")
    assert response.status_code in (400, 422)


@pytest.mark.asyncio
async def test_get_project_dashboard_no_finance_data(client):
    """Test dashboard returns placeholder values when no finance data exists."""
    # Create a minimal project without budget
    create_response = await client.post(
        "/api/v1/projects/create",
        json={"name": "Minimal Dashboard Project"},
    )
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    # Get dashboard
    response = await client.get(f"/api/v1/projects/{project_id}/dashboard")
    assert response.status_code == 200
    body = response.json()

    # KPIs should have placeholder values
    for kpi in body["kpis"]:
        if kpi["label"] in ("Total GFA", "Projected Revenue", "IRR"):
            assert kpi["value"] == "—"
            assert kpi["raw_value"] is None

    # Development Cost should also be placeholder without budget
    dev_cost_kpi = next(kpi for kpi in body["kpis"] if kpi["label"] == "Development Cost")
    assert dev_cost_kpi["value"] == "—"


@pytest.mark.asyncio
async def test_format_currency():
    """Test currency formatting helper."""
    from app.api.v1.projects_api import _format_currency

    assert _format_currency(500) == "$500"
    assert _format_currency(1500) == "$1.5K"
    assert _format_currency(42500000) == "$42.5M"
    assert _format_currency(1500000000) == "$1.5B"


@pytest.mark.asyncio
async def test_format_area():
    """Test area formatting helper."""
    from app.api.v1.projects_api import _format_area

    assert _format_area(15400) == "15,400 m²"
    assert _format_area(1000000) == "1,000,000 m²"


@pytest.mark.asyncio
async def test_format_percentage():
    """Test percentage formatting helper."""
    from app.api.v1.projects_api import _format_percentage

    assert _format_percentage(18.4) == "18.4%"
    assert _format_percentage(0.5) == "0.5%"
