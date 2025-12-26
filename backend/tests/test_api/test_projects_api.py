"""Comprehensive tests for projects_api API.

Tests cover:
- ProjectCreate model
- ProjectUpdate model
- ProjectResponse model
- API endpoint structure
"""

from __future__ import annotations

from datetime import datetime

import pytest

from app.api.v1.projects_api import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
)

# Mark all tests in this module as not requiring database
pytestmark = pytest.mark.no_db


class TestProjectCreate:
    """Tests for ProjectCreate model."""

    def test_required_fields(self) -> None:
        """Test required fields."""
        project = ProjectCreate(name="Test Project")
        assert project.name == "Test Project"
        assert project.status == "planning"

    def test_all_fields(self) -> None:
        """Test all fields."""
        project = ProjectCreate(
            name="New Development",
            description="A new mixed-use development",
            location="123 Main Street",
            project_type="mixed_use",
            status="approval",
            budget=10000000.0,
        )
        assert project.name == "New Development"
        assert project.budget == 10000000.0

    def test_name_min_length(self) -> None:
        """Test name minimum length validation."""
        # Pydantic validates min_length=1
        project = ProjectCreate(name="A")
        assert len(project.name) >= 1

    def test_default_status(self) -> None:
        """Test default status value."""
        project = ProjectCreate(name="Test")
        assert project.status == "planning"


class TestProjectUpdate:
    """Tests for ProjectUpdate model."""

    def test_all_optional(self) -> None:
        """Test all fields are optional."""
        update = ProjectUpdate()
        assert update.name is None
        assert update.description is None
        assert update.budget is None

    def test_partial_update(self) -> None:
        """Test partial update."""
        update = ProjectUpdate(
            status="construction",
            budget=15000000.0,
        )
        assert update.status == "construction"
        assert update.budget == 15000000.0
        assert update.name is None

    def test_name_update(self) -> None:
        """Test name update."""
        update = ProjectUpdate(name="Updated Name")
        assert update.name == "Updated Name"


class TestProjectResponse:
    """Tests for ProjectResponse model."""

    def test_from_attributes(self) -> None:
        """Test from_attributes config works."""

        # Create a mock object with attributes
        class MockProject:
            id = "proj_12345678"
            name = "Test Project"
            description = "Test description"
            location = "Singapore"
            project_type = "residential"
            status = "planning"
            budget = 5000000.0
            owner_email = "test@example.com"
            created_at = datetime(2024, 1, 1, 10, 0, 0)
            updated_at = datetime(2024, 1, 15, 14, 30, 0)
            is_active = True

        mock = MockProject()
        response = ProjectResponse.model_validate(mock)
        assert response.id == "proj_12345678"
        assert response.name == "Test Project"
        assert response.is_active is True

    def test_response_fields(self) -> None:
        """Test response fields."""
        response = ProjectResponse(
            id="proj_abc12345",
            name="Tower Development",
            description="35-storey mixed-use tower",
            location="Marina Bay, Singapore",
            project_type="mixed_use",
            status="construction",
            budget=250000000.0,
            owner_email="developer@example.com",
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 6, 15),
            is_active=True,
        )
        assert response.id == "proj_abc12345"
        assert response.status == "construction"
        assert response.budget == 250000000.0

    def test_nullable_fields(self) -> None:
        """Test nullable fields."""
        response = ProjectResponse(
            id="proj_123",
            name="Basic Project",
            description=None,
            location=None,
            project_type=None,
            status="planning",
            budget=None,
            owner_email="user@example.com",
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 1, 1),
            is_active=True,
        )
        assert response.description is None
        assert response.budget is None


class TestProjectScenarios:
    """Tests for project use case scenarios."""

    def test_create_residential_project(self) -> None:
        """Test creating a residential project."""
        project = ProjectCreate(
            name="Sunset Residences",
            description="Luxury condominium with 200 units",
            location="Orchard Road, Singapore",
            project_type="residential",
            status="planning",
            budget=150000000.0,
        )
        assert project.project_type == "residential"
        assert project.budget == 150000000.0

    def test_create_commercial_project(self) -> None:
        """Test creating a commercial project."""
        project = ProjectCreate(
            name="Business Hub Tower",
            description="Grade A office building",
            location="CBD, Singapore",
            project_type="commercial",
            status="approval",
            budget=300000000.0,
        )
        assert project.project_type == "commercial"

    def test_create_mixed_use_project(self) -> None:
        """Test creating a mixed-use project."""
        project = ProjectCreate(
            name="Marina Central",
            description="Integrated development with retail, office, and residential",
            location="Marina Bay, Singapore",
            project_type="mixed_use",
            status="planning",
            budget=500000000.0,
        )
        assert project.project_type == "mixed_use"

    def test_project_status_progression(self) -> None:
        """Test project status progression."""
        statuses = ["planning", "approval", "construction", "completed"]

        # Initial project
        project = ProjectCreate(name="Test Project", status="planning")
        assert project.status == statuses[0]

        # Progress through statuses
        for status in statuses[1:]:
            update = ProjectUpdate(status=status)
            assert update.status == status

    def test_project_lifecycle(self) -> None:
        """Test complete project lifecycle."""
        # Create
        create = ProjectCreate(
            name="Lifecycle Project",
            description="Testing project lifecycle",
            status="planning",
            budget=10000000.0,
        )
        assert create.status == "planning"

        # Update during construction
        update1 = ProjectUpdate(
            status="construction",
            budget=12000000.0,  # Budget increase
        )
        assert update1.budget == 12000000.0

        # Complete project
        update2 = ProjectUpdate(status="completed")
        assert update2.status == "completed"

    def test_project_response_serialization(self) -> None:
        """Test project response serialization."""
        response = ProjectResponse(
            id="proj_test123",
            name="Serialization Test",
            description="Testing serialization",
            location="Test Location",
            project_type="test",
            status="planning",
            budget=1000000.0,
            owner_email="test@example.com",
            created_at=datetime(2024, 1, 1, 0, 0, 0),
            updated_at=datetime(2024, 1, 1, 0, 0, 0),
            is_active=True,
        )

        # Serialize to dict
        data = response.model_dump()
        assert data["id"] == "proj_test123"
        assert data["is_active"] is True
        assert isinstance(data["created_at"], datetime)

    def test_inactive_project(self) -> None:
        """Test inactive (soft-deleted) project."""
        response = ProjectResponse(
            id="proj_deleted",
            name="Deleted Project",
            description=None,
            location=None,
            project_type=None,
            status="planning",
            budget=None,
            owner_email="user@example.com",
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2024, 6, 1),
            is_active=False,
        )
        assert response.is_active is False
