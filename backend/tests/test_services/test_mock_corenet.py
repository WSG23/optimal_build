"""Tests for mock_corenet service.

Tests focus on MockCorenetService methods.
"""

from __future__ import annotations

import pytest

pytest.importorskip("sqlalchemy")

from app.models.regulatory import AgencyCode, SubmissionStatus


class TestMockCorenetSubmitToAgency:
    """Test MockCorenetService.submit_to_agency."""

    @pytest.fixture
    def corenet_service(self):
        """Create MockCorenetService instance with no delay."""
        from app.services.mock_corenet import MockCorenetService

        service = MockCorenetService()
        service.mock_delay_ms = 0  # No delay for tests
        return service

    @pytest.mark.asyncio
    async def test_submit_to_agency_returns_success(self, corenet_service):
        """Test submit_to_agency returns success response."""
        result = await corenet_service.submit_to_agency(
            agency_code="URA",
            submission_type="development_application",
            project_ref="TEST-001",
            payload={"project_name": "Test Project"},
        )

        assert result["success"] is True
        assert "transaction_id" in result
        assert result["status"] == "received"
        assert "timestamp" in result
        assert "message" in result
        assert "URA" in result["message"]

    @pytest.mark.asyncio
    async def test_submit_to_agency_generates_ura_ref_format(self, corenet_service):
        """Test submit_to_agency generates URA-style reference number."""
        result = await corenet_service.submit_to_agency(
            agency_code=AgencyCode.URA,
            submission_type="planning_permission",
            project_ref="TEST-002",
            payload={},
        )

        # URA format: ES{yymmdd}-{rand}K
        ref = result["transaction_id"]
        assert ref.startswith("ES")
        assert ref.endswith("K")

    @pytest.mark.asyncio
    async def test_submit_to_agency_generates_bca_ref_format(self, corenet_service):
        """Test submit_to_agency generates BCA-style reference number."""
        result = await corenet_service.submit_to_agency(
            agency_code=AgencyCode.BCA,
            submission_type="building_plan",
            project_ref="TEST-003",
            payload={},
        )

        # BCA format: A{yymmdd}-{rand}-BP
        ref = result["transaction_id"]
        assert ref.startswith("A")
        assert ref.endswith("-BP")

    @pytest.mark.asyncio
    async def test_submit_to_agency_generates_other_agency_ref_format(
        self, corenet_service
    ):
        """Test submit_to_agency generates generic reference for other agencies."""
        result = await corenet_service.submit_to_agency(
            agency_code="OTHER",
            submission_type="other_submission",
            project_ref="TEST-004",
            payload={},
        )

        # Other format: {agency}-{yymmdd}-{rand}
        ref = result["transaction_id"]
        assert ref.startswith("OTHER-")


class TestMockCorenetCheckStatus:
    """Test MockCorenetService.check_status."""

    @pytest.fixture
    def corenet_service(self):
        """Create MockCorenetService instance with no delay."""
        from app.services.mock_corenet import MockCorenetService

        service = MockCorenetService()
        service.mock_delay_ms = 0  # No delay for tests
        return service

    @pytest.mark.asyncio
    async def test_check_status_returns_status_info(self, corenet_service):
        """Test check_status returns status information."""
        result = await corenet_service.check_status(
            agency_code="URA", reference_no="ES240101-1234K"
        )

        assert result["reference_no"] == "ES240101-1234K"
        assert result["agency_code"] == "URA"
        assert "external_status" in result
        assert "mapped_status" in result
        assert "remarks" in result
        assert "last_updated" in result

    @pytest.mark.asyncio
    async def test_check_status_auto_approves_ref_ending_00(self, corenet_service):
        """Test check_status auto-approves refs ending in 00."""
        result = await corenet_service.check_status(
            agency_code="URA", reference_no="ES240101-1200"
        )

        assert result["external_status"] == "approved"
        assert "Auto-approved" in result["remarks"]

    @pytest.mark.asyncio
    async def test_check_status_auto_rejects_ref_ending_99(self, corenet_service):
        """Test check_status auto-rejects refs ending in 99."""
        # Reference must END with "99" (not have 99 in middle)
        result = await corenet_service.check_status(
            agency_code="BCA", reference_no="A240101-1299"
        )

        assert result["external_status"] == "rejected"
        # The rejection message mentions demo purposes
        assert "demo" in result["remarks"].lower()


class TestMapExternalStatus:
    """Test MockCorenetService._map_external_status."""

    @pytest.fixture
    def corenet_service(self):
        """Create MockCorenetService instance."""
        from app.services.mock_corenet import MockCorenetService

        return MockCorenetService()

    def test_map_approved_status(self, corenet_service):
        """Test mapping approved status."""
        result = corenet_service._map_external_status("approved")
        assert result == SubmissionStatus.APPROVED

    def test_map_approved_status_case_insensitive(self, corenet_service):
        """Test mapping handles case insensitivity."""
        result = corenet_service._map_external_status("APPROVED")
        assert result == SubmissionStatus.APPROVED

        result = corenet_service._map_external_status("Approved")
        assert result == SubmissionStatus.APPROVED

    def test_map_rejected_status(self, corenet_service):
        """Test mapping rejected status."""
        result = corenet_service._map_external_status("rejected")
        assert result == SubmissionStatus.REJECTED

    def test_map_rfi_status(self, corenet_service):
        """Test mapping RFI status."""
        result = corenet_service._map_external_status("rfi")
        assert result == SubmissionStatus.RFI

    def test_map_clarification_status(self, corenet_service):
        """Test mapping clarification status to RFI."""
        result = corenet_service._map_external_status("clarification needed")
        assert result == SubmissionStatus.RFI

    def test_map_processing_status(self, corenet_service):
        """Test mapping processing status to IN_REVIEW."""
        result = corenet_service._map_external_status("processing")
        assert result == SubmissionStatus.IN_REVIEW

    def test_map_received_status(self, corenet_service):
        """Test mapping received status to IN_REVIEW."""
        result = corenet_service._map_external_status("received")
        assert result == SubmissionStatus.IN_REVIEW

    def test_map_unknown_status_defaults_to_submitted(self, corenet_service):
        """Test mapping unknown status defaults to SUBMITTED."""
        result = corenet_service._map_external_status("unknown_status")
        assert result == SubmissionStatus.SUBMITTED


class TestGenerateRefNo:
    """Test MockCorenetService._generate_ref_no."""

    @pytest.fixture
    def corenet_service(self):
        """Create MockCorenetService instance."""
        from app.services.mock_corenet import MockCorenetService

        return MockCorenetService()

    def test_generate_ura_ref(self, corenet_service):
        """Test generating URA reference number."""
        ref = corenet_service._generate_ref_no(AgencyCode.URA, "dev_app")

        assert ref.startswith("ES")
        assert ref.endswith("K")
        # Should have date in middle and random number
        assert len(ref) > 10

    def test_generate_bca_ref(self, corenet_service):
        """Test generating BCA reference number."""
        ref = corenet_service._generate_ref_no(AgencyCode.BCA, "building_plan")

        assert ref.startswith("A")
        assert ref.endswith("-BP")

    def test_generate_other_agency_ref(self, corenet_service):
        """Test generating other agency reference number."""
        ref = corenet_service._generate_ref_no("SCDF", "fire_safety")

        assert ref.startswith("SCDF-")

    def test_generate_ref_is_unique(self, corenet_service):
        """Test that generated refs are unique."""
        refs = [corenet_service._generate_ref_no("URA", "test") for _ in range(10)]
        # Should have some uniqueness (at least 5 unique out of 10)
        unique_refs = set(refs)
        assert len(unique_refs) >= 5
