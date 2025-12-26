"""Comprehensive tests for developers_checklists API.

Tests cover:
- ChecklistItemResponse model
- ChecklistItemsResponse model
- ChecklistSummaryResponse model
- ChecklistTemplateResponse model
- ChecklistTemplateBaseRequest model
- ChecklistTemplateCreateRequest model
- ChecklistTemplateUpdateRequest model
- ChecklistTemplateBulkImportRequest model
- ChecklistTemplateBulkImportResponse model
- UpdateChecklistStatusRequest model
- ChecklistProgressResponse model
"""

from __future__ import annotations

import pytest

from app.api.v1.developers_checklists import (
    ChecklistItemResponse,
    ChecklistItemsResponse,
    ChecklistSummaryResponse,
    ChecklistTemplateResponse,
    ChecklistTemplateBaseRequest,
    ChecklistTemplateCreateRequest,
    ChecklistTemplateUpdateRequest,
    ChecklistTemplateBulkImportRequest,
    ChecklistTemplateBulkImportResponse,
    UpdateChecklistStatusRequest,
    ChecklistProgressResponse,
)

# Mark all tests in this module as not requiring database
pytestmark = pytest.mark.no_db


class TestChecklistItemResponse:
    """Tests for ChecklistItemResponse model."""

    def test_required_fields(self) -> None:
        """Test required fields."""
        response = ChecklistItemResponse(
            id="item-123",
            property_id="prop-456",
            development_scenario="new_development",
            category="Legal",
            item_title="Title Search",
            priority="high",
            status="pending",
            metadata={},
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
            item_description=None,
            assigned_to=None,
            due_date=None,
            completed_date=None,
            completed_by=None,
            notes=None,
        )
        assert response.id == "item-123"
        assert response.property_id == "prop-456"
        assert response.development_scenario == "new_development"
        assert response.category == "Legal"
        assert response.status == "pending"

    def test_optional_fields(self) -> None:
        """Test optional fields."""
        response = ChecklistItemResponse(
            id="item-123",
            property_id="prop-456",
            development_scenario="heritage_property",
            category="Heritage",
            item_title="Conservation Approval",
            priority="high",
            status="in_progress",
            metadata={"heritage_grade": "II"},
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-02T00:00:00Z",
            item_description="Submit conservation approval application",
            assigned_to="user-789",
            due_date="2024-03-01",
            completed_date=None,
            completed_by=None,
            notes="Pending heritage board review",
            requires_professional=True,
            professional_type="heritage_consultant",
            typical_duration_days=30,
            display_order=1,
        )
        assert response.item_description is not None
        assert response.requires_professional is True
        assert response.professional_type == "heritage_consultant"


class TestChecklistItemsResponse:
    """Tests for ChecklistItemsResponse envelope model."""

    def test_items_list(self) -> None:
        """Test items list structure."""
        item = ChecklistItemResponse(
            id="item-1",
            property_id="prop-1",
            development_scenario="new_development",
            category="Legal",
            item_title="Title Search",
            priority="high",
            status="pending",
            metadata={},
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
            item_description=None,
            assigned_to=None,
            due_date=None,
            completed_date=None,
            completed_by=None,
            notes=None,
        )
        response = ChecklistItemsResponse(items=[item], total=1)
        assert len(response.items) == 1
        assert response.total == 1

    def test_empty_items(self) -> None:
        """Test empty items list."""
        response = ChecklistItemsResponse(items=[], total=0)
        assert len(response.items) == 0
        assert response.total == 0


class TestChecklistSummaryResponse:
    """Tests for ChecklistSummaryResponse model."""

    def test_summary_fields(self) -> None:
        """Test summary fields."""
        response = ChecklistSummaryResponse(
            property_id="prop-123",
            total=20,
            completed=10,
            in_progress=5,
            pending=3,
            not_applicable=2,
            completion_percentage=50,
            by_category_status={
                "Legal": {"completed": 3, "pending": 2},
                "Technical": {"completed": 5, "in_progress": 3},
            },
        )
        assert response.total == 20
        assert response.completed == 10
        assert response.completion_percentage == 50
        assert "Legal" in response.by_category_status

    def test_all_completed(self) -> None:
        """Test all items completed."""
        response = ChecklistSummaryResponse(
            property_id="prop-123",
            total=10,
            completed=10,
            in_progress=0,
            pending=0,
            not_applicable=0,
            completion_percentage=100,
            by_category_status={},
        )
        assert response.completion_percentage == 100


class TestChecklistTemplateResponse:
    """Tests for ChecklistTemplateResponse model."""

    def test_template_fields(self) -> None:
        """Test template fields with aliases."""
        response = ChecklistTemplateResponse(
            id="tmpl-123",
            developmentScenario="new_development",
            category="Legal",
            itemTitle="Title Search",
            priority="high",
            requiresProfessional=True,
            displayOrder=1,
            createdAt="2024-01-01T00:00:00Z",
            updatedAt="2024-01-01T00:00:00Z",
            itemDescription="Conduct title search",
            typicalDurationDays=5,
            professionalType="lawyer",
        )
        assert response.development_scenario == "new_development"
        assert response.item_title == "Title Search"
        assert response.requires_professional is True

    def test_optional_fields_none(self) -> None:
        """Test optional fields as None."""
        response = ChecklistTemplateResponse(
            id="tmpl-123",
            developmentScenario="existing_building",
            category="Technical",
            itemTitle="Building Inspection",
            priority="medium",
            requiresProfessional=False,
            displayOrder=5,
            createdAt="2024-01-01T00:00:00Z",
            updatedAt="2024-01-01T00:00:00Z",
        )
        assert response.item_description is None
        assert response.typical_duration_days is None


class TestChecklistTemplateBaseRequest:
    """Tests for ChecklistTemplateBaseRequest model."""

    def test_required_fields(self) -> None:
        """Test required fields."""
        request = ChecklistTemplateBaseRequest(
            developmentScenario="heritage_property",
            category="Heritage",
            itemTitle="Heritage Impact Assessment",
            priority="high",
        )
        assert request.development_scenario == "heritage_property"
        assert request.category == "Heritage"
        assert request.priority == "high"

    def test_optional_fields(self) -> None:
        """Test optional fields."""
        request = ChecklistTemplateBaseRequest(
            developmentScenario="new_development",
            category="Planning",
            itemTitle="Development Application",
            priority="high",
            itemDescription="Submit DA to council",
            typicalDurationDays=60,
            requiresProfessional=True,
            professionalType="town_planner",
            displayOrder=2,
        )
        assert request.typical_duration_days == 60
        assert request.professional_type == "town_planner"


class TestChecklistTemplateCreateRequest:
    """Tests for ChecklistTemplateCreateRequest model."""

    def test_inherits_base(self) -> None:
        """Test inherits from base request."""
        request = ChecklistTemplateCreateRequest(
            developmentScenario="new_development",
            category="Legal",
            itemTitle="Contract Review",
            priority="medium",
        )
        assert request.development_scenario == "new_development"
        assert request.item_title == "Contract Review"


class TestChecklistTemplateUpdateRequest:
    """Tests for ChecklistTemplateUpdateRequest model."""

    def test_all_optional(self) -> None:
        """Test all fields are optional."""
        request = ChecklistTemplateUpdateRequest()
        assert request.development_scenario is None
        assert request.category is None
        assert request.item_title is None

    def test_partial_update(self) -> None:
        """Test partial update."""
        request = ChecklistTemplateUpdateRequest(
            priority="high",
            typicalDurationDays=10,
        )
        assert request.priority == "high"
        assert request.typical_duration_days == 10
        assert request.category is None


class TestChecklistTemplateBulkImportRequest:
    """Tests for ChecklistTemplateBulkImportRequest model."""

    def test_empty_templates(self) -> None:
        """Test empty templates list."""
        request = ChecklistTemplateBulkImportRequest()
        assert request.templates == []
        assert request.replace_existing is False

    def test_with_templates(self) -> None:
        """Test with templates."""
        template = ChecklistTemplateBaseRequest(
            developmentScenario="new_development",
            category="Legal",
            itemTitle="Title Search",
            priority="high",
        )
        request = ChecklistTemplateBulkImportRequest(
            templates=[template],
            replaceExisting=True,
        )
        assert len(request.templates) == 1
        assert request.replace_existing is True


class TestChecklistTemplateBulkImportResponse:
    """Tests for ChecklistTemplateBulkImportResponse model."""

    def test_import_results(self) -> None:
        """Test import results."""
        response = ChecklistTemplateBulkImportResponse(
            created=10,
            updated=5,
            deleted=2,
        )
        assert response.created == 10
        assert response.updated == 5
        assert response.deleted == 2


class TestUpdateChecklistStatusRequest:
    """Tests for UpdateChecklistStatusRequest model."""

    def test_status_only(self) -> None:
        """Test status only."""
        request = UpdateChecklistStatusRequest(status="completed")
        assert request.status == "completed"
        assert request.notes is None

    def test_status_with_notes(self) -> None:
        """Test status with notes."""
        request = UpdateChecklistStatusRequest(
            status="in_progress",
            notes="Working on this item",
        )
        assert request.status == "in_progress"
        assert request.notes == "Working on this item"


class TestChecklistProgressResponse:
    """Tests for ChecklistProgressResponse model."""

    def test_progress_fields(self) -> None:
        """Test progress fields with aliases."""
        response = ChecklistProgressResponse(
            total=50,
            completed=25,
            inProgress=10,
            pending=10,
            notApplicable=5,
            completionPercentage=50,
        )
        assert response.total == 50
        assert response.in_progress == 10
        assert response.not_applicable == 5
        assert response.completion_percentage == 50


class TestChecklistScenarios:
    """Tests for checklist use case scenarios."""

    def test_new_development_checklist(self) -> None:
        """Test new development checklist scenario."""
        items = [
            ChecklistItemResponse(
                id=f"item-{i}",
                property_id="prop-123",
                development_scenario="new_development",
                category=cat,
                item_title=f"Task {i}",
                priority="high" if i < 3 else "medium",
                status="pending",
                metadata={},
                created_at="2024-01-01T00:00:00Z",
                updated_at="2024-01-01T00:00:00Z",
                item_description=None,
                assigned_to=None,
                due_date=None,
                completed_date=None,
                completed_by=None,
                notes=None,
            )
            for i, cat in enumerate(
                ["Legal", "Planning", "Technical", "Finance", "Heritage"]
            )
        ]
        response = ChecklistItemsResponse(items=items, total=5)
        assert response.total == 5
        categories = {item.category for item in response.items}
        assert "Legal" in categories
        assert "Planning" in categories

    def test_heritage_property_checklist(self) -> None:
        """Test heritage property checklist scenario."""
        item = ChecklistItemResponse(
            id="heritage-item-1",
            property_id="heritage-prop-1",
            development_scenario="heritage_property",
            category="Heritage",
            item_title="Heritage Impact Assessment",
            priority="high",
            status="in_progress",
            metadata={"heritage_grade": "I", "listed": True},
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-15T00:00:00Z",
            item_description="Prepare HIA for planning submission",
            assigned_to="heritage-consultant-1",
            due_date="2024-03-01",
            completed_date=None,
            completed_by=None,
            notes="Awaiting heritage officer review",
            requires_professional=True,
            professional_type="heritage_consultant",
            typical_duration_days=45,
            display_order=1,
        )
        assert item.development_scenario == "heritage_property"
        assert item.requires_professional is True
        assert item.professional_type == "heritage_consultant"

    def test_checklist_completion_workflow(self) -> None:
        """Test checklist completion workflow."""
        # Start with pending
        update1 = UpdateChecklistStatusRequest(status="in_progress")
        assert update1.status == "in_progress"

        # Mark as completed
        update2 = UpdateChecklistStatusRequest(
            status="completed",
            notes="All requirements satisfied",
        )
        assert update2.status == "completed"
        assert update2.notes is not None

    def test_bulk_template_import(self) -> None:
        """Test bulk template import scenario."""
        templates = [
            ChecklistTemplateBaseRequest(
                developmentScenario=scenario,
                category="Legal",
                itemTitle=f"Legal Task {i}",
                priority="high",
            )
            for i, scenario in enumerate(
                ["new_development", "heritage_property", "existing_building"]
            )
        ]
        request = ChecklistTemplateBulkImportRequest(
            templates=templates,
            replaceExisting=False,
        )
        assert len(request.templates) == 3

        # Simulate response
        response = ChecklistTemplateBulkImportResponse(
            created=3,
            updated=0,
            deleted=0,
        )
        assert response.created == 3
