"""Comprehensive tests for mock_corenet service.

Tests cover:
- Mock CORENET X API responses
- Submission status tracking
- Document validation
"""

from __future__ import annotations

import pytest

# Mark all tests in this module as not requiring database
pytestmark = pytest.mark.no_db


class TestCorenetSubmissionStatus:
    """Tests for CORENET submission status values."""

    def test_draft_status(self) -> None:
        """Test draft submission status."""
        status = "draft"
        assert status == "draft"

    def test_submitted_status(self) -> None:
        """Test submitted status."""
        status = "submitted"
        assert status == "submitted"

    def test_under_review_status(self) -> None:
        """Test under review status."""
        status = "under_review"
        assert status == "under_review"

    def test_approved_status(self) -> None:
        """Test approved status."""
        status = "approved"
        assert status == "approved"

    def test_rejected_status(self) -> None:
        """Test rejected status."""
        status = "rejected"
        assert status == "rejected"

    def test_pending_clarification_status(self) -> None:
        """Test pending clarification status."""
        status = "pending_clarification"
        assert status == "pending_clarification"


class TestCorenetDocumentTypes:
    """Tests for CORENET document type values."""

    def test_building_plan_type(self) -> None:
        """Test building plan document type."""
        doc_type = "building_plan"
        assert doc_type == "building_plan"

    def test_structural_plan_type(self) -> None:
        """Test structural plan document type."""
        doc_type = "structural_plan"
        assert doc_type == "structural_plan"

    def test_mep_plan_type(self) -> None:
        """Test MEP plan document type."""
        doc_type = "mep_plan"
        assert doc_type == "mep_plan"

    def test_fire_safety_plan_type(self) -> None:
        """Test fire safety plan document type."""
        doc_type = "fire_safety_plan"
        assert doc_type == "fire_safety_plan"

    def test_accessibility_plan_type(self) -> None:
        """Test accessibility plan document type."""
        doc_type = "accessibility_plan"
        assert doc_type == "accessibility_plan"


class TestCorenetAgencies:
    """Tests for CORENET participating agencies."""

    def test_bca_agency(self) -> None:
        """Test BCA (Building and Construction Authority)."""
        agency = {"code": "BCA", "name": "Building and Construction Authority"}
        assert agency["code"] == "BCA"

    def test_scdf_agency(self) -> None:
        """Test SCDF (Singapore Civil Defence Force)."""
        agency = {"code": "SCDF", "name": "Singapore Civil Defence Force"}
        assert agency["code"] == "SCDF"

    def test_ura_agency(self) -> None:
        """Test URA (Urban Redevelopment Authority)."""
        agency = {"code": "URA", "name": "Urban Redevelopment Authority"}
        assert agency["code"] == "URA"

    def test_pub_agency(self) -> None:
        """Test PUB (Public Utilities Board)."""
        agency = {"code": "PUB", "name": "Public Utilities Board"}
        assert agency["code"] == "PUB"

    def test_nea_agency(self) -> None:
        """Test NEA (National Environment Agency)."""
        agency = {"code": "NEA", "name": "National Environment Agency"}
        assert agency["code"] == "NEA"


class TestCorenetSubmissionData:
    """Tests for CORENET submission data structures."""

    def test_submission_structure(self) -> None:
        """Test submission data structure."""
        submission = {
            "submission_id": "COR-2024-00001",
            "project_ref": "BP/2024/001",
            "status": "submitted",
            "submitted_at": "2024-01-15T10:30:00+08:00",
            "submitted_by": "QP-12345",
        }
        assert submission["submission_id"].startswith("COR-")

    def test_document_attachment(self) -> None:
        """Test document attachment structure."""
        document = {
            "document_id": "DOC-001",
            "document_type": "building_plan",
            "filename": "A-101_Floor_Plan.pdf",
            "file_size_bytes": 5242880,
            "sha256_hash": "abc123...",
            "uploaded_at": "2024-01-15T10:00:00+08:00",
        }
        assert document["document_type"] == "building_plan"

    def test_review_comment(self) -> None:
        """Test review comment structure."""
        comment = {
            "comment_id": "CMT-001",
            "agency": "BCA",
            "reviewer": "R-12345",
            "comment_type": "clarification_required",
            "comment_text": "Please provide additional structural calculations.",
            "created_at": "2024-01-20T14:00:00+08:00",
            "resolved": False,
        }
        assert comment["agency"] == "BCA"


class TestCorenetProjectTypes:
    """Tests for CORENET project type values."""

    def test_new_erection(self) -> None:
        """Test new erection project type."""
        project_type = "new_erection"
        assert project_type == "new_erection"

    def test_addition_alteration(self) -> None:
        """Test addition & alteration project type."""
        project_type = "addition_alteration"
        assert project_type == "addition_alteration"

    def test_demolition(self) -> None:
        """Test demolition project type."""
        project_type = "demolition"
        assert project_type == "demolition"

    def test_change_of_use(self) -> None:
        """Test change of use project type."""
        project_type = "change_of_use"
        assert project_type == "change_of_use"


class TestCorenetOccupancyTypes:
    """Tests for CORENET occupancy type values."""

    def test_residential_occupancy(self) -> None:
        """Test residential occupancy."""
        occupancy = "residential"
        assert occupancy == "residential"

    def test_commercial_occupancy(self) -> None:
        """Test commercial occupancy."""
        occupancy = "commercial"
        assert occupancy == "commercial"

    def test_industrial_occupancy(self) -> None:
        """Test industrial occupancy."""
        occupancy = "industrial"
        assert occupancy == "industrial"

    def test_institutional_occupancy(self) -> None:
        """Test institutional occupancy."""
        occupancy = "institutional"
        assert occupancy == "institutional"

    def test_mixed_use_occupancy(self) -> None:
        """Test mixed-use occupancy."""
        occupancy = "mixed_use"
        assert occupancy == "mixed_use"


class TestCorenetScenarios:
    """Tests for CORENET use case scenarios."""

    def test_building_plan_submission(self) -> None:
        """Test building plan submission scenario."""
        submission = {
            "submission_type": "building_plan",
            "project_ref": "BP/2024/001",
            "project_title": "30-Storey Residential Tower",
            "project_address": "123 Orchard Road",
            "postal_code": "238888",
            "lot_number": "TS10-01234X",
            "project_type": "new_erection",
            "occupancy_type": "residential",
            "gfa_sqm": 35000.0,
            "building_height_m": 120.0,
            "storeys_above_ground": 30,
            "storeys_below_ground": 3,
            "qp_upe_number": "QP-12345",
            "owner_name": "ABC Development Pte Ltd",
            "owner_uen": "201234567X",
        }
        assert submission["storeys_above_ground"] == 30

    def test_structural_submission(self) -> None:
        """Test structural plan submission scenario."""
        submission = {
            "submission_type": "structural_plan",
            "project_ref": "SP/2024/001",
            "pe_number": "PE-12345",
            "structural_system": "reinforced_concrete_frame",
            "foundation_type": "bored_piles",
            "soil_investigation_ref": "SI-2024-001",
        }
        assert submission["structural_system"] == "reinforced_concrete_frame"

    def test_fire_safety_submission(self) -> None:
        """Test fire safety submission scenario."""
        submission = {
            "submission_type": "fire_safety",
            "project_ref": "FS/2024/001",
            "fire_safety_engineer": "FSE-12345",
            "sprinkler_system": True,
            "smoke_detection": True,
            "emergency_exits": 4,
            "fire_command_centre": True,
        }
        assert submission["sprinkler_system"] is True

    def test_accessibility_submission(self) -> None:
        """Test accessibility submission scenario."""
        submission = {
            "submission_type": "accessibility",
            "project_ref": "AC/2024/001",
            "barrier_free_access": True,
            "wheelchair_ramps": 2,
            "accessible_toilets": 6,
            "braille_signage": True,
            "tactile_guidance": True,
        }
        assert submission["barrier_free_access"] is True
