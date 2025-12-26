"""Tests for Construction Management API (Phase 2G)."""

from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.construction import (
    Contractor,
    ContractorType,
    DrawdownRequest,
    DrawdownStatus,
    InspectionStatus,
    QualityInspection,
    SafetyIncident,
    SeverityLevel,
)
from app.models.projects import Project, ProjectType, ProjectPhase
from app.models.users import User


@pytest.fixture
async def test_user(session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        id=uuid4(),
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password="hashed",
        is_active=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.fixture
async def test_project(session: AsyncSession, test_user: User) -> Project:
    """Create a test project."""
    project = Project(
        id=uuid4(),
        project_name="Test Construction Project",
        project_code="TEST-CONST-001",
        project_type=ProjectType.NEW_DEVELOPMENT,
        current_phase=ProjectPhase.CONSTRUCTION,
        owner_id=test_user.id,
    )
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


@pytest.fixture
async def test_contractor(session: AsyncSession, test_project: Project) -> Contractor:
    """Create a test contractor."""
    contractor = Contractor(
        id=uuid4(),
        project_id=test_project.id,
        company_name="ABC Construction Pte Ltd",
        contractor_type=ContractorType.GENERAL_CONTRACTOR,
        contact_person="John Tan",
        email="john@abc-construction.sg",
        phone="+65 9123 4567",
        contract_value=Decimal("15000000.00"),
        is_active=True,
    )
    session.add(contractor)
    await session.commit()
    await session.refresh(contractor)
    return contractor


class TestContractorAPI:
    """Tests for contractor management endpoints."""

    async def test_create_contractor(
        self, client: AsyncClient, test_project: Project
    ) -> None:
        """Test creating a new contractor."""
        payload = {
            "project_id": str(test_project.id),
            "company_name": "New Construction Co",
            "contractor_type": "sub_contractor",
            "contact_person": "Jane Lee",
            "email": "jane@newco.sg",
            "phone": "+65 9234 5678",
        }

        response = await client.post(
            f"/api/v1/projects/{test_project.id}/contractors", json=payload
        )

        assert response.status_code == 201
        data = response.json()
        assert data["company_name"] == "New Construction Co"
        assert data["contractor_type"] == "sub_contractor"
        assert data["contact_person"] == "Jane Lee"

    async def test_list_contractors(
        self, client: AsyncClient, test_project: Project, test_contractor: Contractor
    ) -> None:
        """Test listing contractors for a project."""
        response = await client.get(f"/api/v1/projects/{test_project.id}/contractors")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(c["id"] == str(test_contractor.id) for c in data)

    async def test_list_contractors_by_type(
        self, client: AsyncClient, test_project: Project, test_contractor: Contractor
    ) -> None:
        """Test filtering contractors by type."""
        response = await client.get(
            f"/api/v1/projects/{test_project.id}/contractors?type=general_contractor"
        )

        assert response.status_code == 200
        data = response.json()
        assert all(c["contractor_type"] == "general_contractor" for c in data)

    async def test_update_contractor(
        self, client: AsyncClient, test_contractor: Contractor
    ) -> None:
        """Test updating contractor details."""
        payload = {
            "contact_person": "Updated Contact",
            "email": "updated@abc-construction.sg",
        }

        response = await client.patch(
            f"/api/v1/projects/contractors/{test_contractor.id}", json=payload
        )

        assert response.status_code == 200
        data = response.json()
        assert data["contact_person"] == "Updated Contact"
        assert data["email"] == "updated@abc-construction.sg"


class TestQualityInspectionAPI:
    """Tests for quality inspection endpoints."""

    async def test_create_inspection(
        self, client: AsyncClient, test_project: Project
    ) -> None:
        """Test logging a new quality inspection."""
        payload = {
            "project_id": str(test_project.id),
            "inspection_date": "2024-12-20",
            "inspector_name": "Michael Chen",
            "location": "Level 5 Structural Slab",
            "status": "passed",
            "notes": "All concrete works satisfactory",
        }

        response = await client.post(
            f"/api/v1/projects/{test_project.id}/inspections", json=payload
        )

        assert response.status_code == 201
        data = response.json()
        assert data["inspector_name"] == "Michael Chen"
        assert data["status"] == "passed"

    async def test_list_inspections(
        self, client: AsyncClient, session: AsyncSession, test_project: Project
    ) -> None:
        """Test listing inspections for a project."""
        # Create a test inspection
        inspection = QualityInspection(
            id=uuid4(),
            project_id=test_project.id,
            inspection_date=date(2024, 12, 20),
            inspector_name="Test Inspector",
            location="Test Location",
            status=InspectionStatus.SCHEDULED,
        )
        session.add(inspection)
        await session.commit()

        response = await client.get(f"/api/v1/projects/{test_project.id}/inspections")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    async def test_update_inspection(
        self, client: AsyncClient, session: AsyncSession, test_project: Project
    ) -> None:
        """Test updating inspection status."""
        # Create a test inspection
        inspection = QualityInspection(
            id=uuid4(),
            project_id=test_project.id,
            inspection_date=date(2024, 12, 20),
            inspector_name="Test Inspector",
            location="Test Location",
            status=InspectionStatus.SCHEDULED,
        )
        session.add(inspection)
        await session.commit()

        payload = {
            "status": "passed",
            "notes": "Inspection completed successfully",
        }

        response = await client.patch(
            f"/api/v1/projects/inspections/{inspection.id}", json=payload
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "passed"
        assert data["notes"] == "Inspection completed successfully"


class TestSafetyIncidentAPI:
    """Tests for safety incident endpoints."""

    async def test_create_incident(
        self, client: AsyncClient, test_project: Project
    ) -> None:
        """Test reporting a new safety incident."""
        payload = {
            "project_id": str(test_project.id),
            "incident_date": "2024-12-18T10:30:00Z",
            "severity": "near_miss",
            "title": "Unsecured scaffolding",
            "description": "Worker noticed loose scaffolding bracket",
            "location": "Level 3 East Wing",
            "reported_by": "Ahmad bin Hassan",
        }

        response = await client.post(
            f"/api/v1/projects/{test_project.id}/incidents", json=payload
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Unsecured scaffolding"
        assert data["severity"] == "near_miss"
        assert data["is_resolved"] is False

    async def test_list_incidents(
        self, client: AsyncClient, session: AsyncSession, test_project: Project
    ) -> None:
        """Test listing safety incidents."""
        # Create a test incident
        incident = SafetyIncident(
            id=uuid4(),
            project_id=test_project.id,
            incident_date=datetime(2024, 12, 18, 10, 30),
            severity=SeverityLevel.MINOR,
            title="Test Incident",
            location="Test Location",
            is_resolved=False,
        )
        session.add(incident)
        await session.commit()

        response = await client.get(f"/api/v1/projects/{test_project.id}/incidents")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    async def test_list_unresolved_incidents(
        self, client: AsyncClient, session: AsyncSession, test_project: Project
    ) -> None:
        """Test filtering for unresolved incidents only."""
        # Create resolved and unresolved incidents
        resolved = SafetyIncident(
            id=uuid4(),
            project_id=test_project.id,
            incident_date=datetime(2024, 12, 17),
            severity=SeverityLevel.MINOR,
            title="Resolved Incident",
            is_resolved=True,
        )
        unresolved = SafetyIncident(
            id=uuid4(),
            project_id=test_project.id,
            incident_date=datetime(2024, 12, 18),
            severity=SeverityLevel.MODERATE,
            title="Unresolved Incident",
            is_resolved=False,
        )
        session.add_all([resolved, unresolved])
        await session.commit()

        response = await client.get(
            f"/api/v1/projects/{test_project.id}/incidents?unresolved=true"
        )

        assert response.status_code == 200
        data = response.json()
        assert all(i["is_resolved"] is False for i in data)


class TestDrawdownAPI:
    """Tests for drawdown request endpoints."""

    async def test_create_drawdown(
        self, client: AsyncClient, test_project: Project
    ) -> None:
        """Test creating a new drawdown request."""
        payload = {
            "project_id": str(test_project.id),
            "request_name": "Drawdown #1 - Foundation Works",
            "request_date": "2024-11-01",
            "amount_requested": 2500000.00,
            "notes": "Foundation complete as per QS certification",
        }

        response = await client.post(
            f"/api/v1/projects/{test_project.id}/drawdowns", json=payload
        )

        assert response.status_code == 201
        data = response.json()
        assert data["request_name"] == "Drawdown #1 - Foundation Works"
        assert data["status"] == "draft"

    async def test_list_drawdowns(
        self, client: AsyncClient, session: AsyncSession, test_project: Project
    ) -> None:
        """Test listing drawdown requests."""
        # Create a test drawdown
        drawdown = DrawdownRequest(
            id=uuid4(),
            project_id=test_project.id,
            request_name="Test Drawdown",
            request_date=date(2024, 11, 1),
            amount_requested=Decimal("1000000.00"),
            status=DrawdownStatus.DRAFT,
        )
        session.add(drawdown)
        await session.commit()

        response = await client.get(f"/api/v1/projects/{test_project.id}/drawdowns")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    async def test_approve_drawdown(
        self, client: AsyncClient, session: AsyncSession, test_project: Project
    ) -> None:
        """Test approving a drawdown request."""
        # Create a submitted drawdown
        drawdown = DrawdownRequest(
            id=uuid4(),
            project_id=test_project.id,
            request_name="Drawdown for Approval",
            request_date=date(2024, 12, 1),
            amount_requested=Decimal("2000000.00"),
            status=DrawdownStatus.SUBMITTED,
        )
        session.add(drawdown)
        await session.commit()

        response = await client.post(
            f"/api/v1/projects/drawdowns/{drawdown.id}/approve"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved_architect"
        assert float(data["amount_approved"]) == 2000000.00

    async def test_approve_drawdown_partial_amount(
        self, client: AsyncClient, session: AsyncSession, test_project: Project
    ) -> None:
        """Test approving a drawdown with a partial amount."""
        # Create a submitted drawdown
        drawdown = DrawdownRequest(
            id=uuid4(),
            project_id=test_project.id,
            request_name="Drawdown for Partial Approval",
            request_date=date(2024, 12, 5),
            amount_requested=Decimal("3000000.00"),
            status=DrawdownStatus.SUBMITTED,
        )
        session.add(drawdown)
        await session.commit()

        response = await client.post(
            f"/api/v1/projects/drawdowns/{drawdown.id}/approve?approved_amount=2500000"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved_architect"
        assert float(data["amount_approved"]) == 2500000.00

    async def test_update_drawdown(
        self, client: AsyncClient, session: AsyncSession, test_project: Project
    ) -> None:
        """Test updating a drawdown request."""
        # Create a draft drawdown
        drawdown = DrawdownRequest(
            id=uuid4(),
            project_id=test_project.id,
            request_name="Draft Drawdown",
            request_date=date(2024, 12, 10),
            amount_requested=Decimal("1500000.00"),
            status=DrawdownStatus.DRAFT,
        )
        session.add(drawdown)
        await session.commit()

        payload = {
            "request_name": "Updated Drawdown Name",
            "status": "submitted",
        }

        response = await client.patch(
            f"/api/v1/projects/drawdowns/{drawdown.id}", json=payload
        )

        assert response.status_code == 200
        data = response.json()
        assert data["request_name"] == "Updated Drawdown Name"
        assert data["status"] == "submitted"


class TestProjectIDMismatch:
    """Tests for project ID validation."""

    async def test_contractor_project_id_mismatch(
        self, client: AsyncClient, test_project: Project
    ) -> None:
        """Test that mismatched project IDs are rejected."""
        other_project_id = uuid4()
        payload = {
            "project_id": str(other_project_id),  # Different from URL
            "company_name": "New Construction Co",
            "contractor_type": "sub_contractor",
        }

        response = await client.post(
            f"/api/v1/projects/{test_project.id}/contractors", json=payload
        )

        assert response.status_code == 400
        assert "mismatch" in response.json()["detail"].lower()
