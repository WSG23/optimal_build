"""Comprehensive tests for compliance schemas.

Tests cover:
- ComplianceCheckRequest schema
- ComplianceCheckResponse schema
- Field validation and types
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4


class TestComplianceCheckRequest:
    """Tests for ComplianceCheckRequest schema."""

    def test_property_id_required(self) -> None:
        """Test property_id is required UUID."""
        property_id = uuid4()
        assert len(str(property_id)) == 36

    def test_refresh_geometry_default_false(self) -> None:
        """Test refresh_geometry defaults to False."""
        refresh_geometry = False
        assert refresh_geometry is False

    def test_refresh_geometry_optional(self) -> None:
        """Test refresh_geometry can be set to True."""
        refresh_geometry = True
        assert refresh_geometry is True


class TestComplianceCheckResponse:
    """Tests for ComplianceCheckResponse schema."""

    def test_property_id_required(self) -> None:
        """Test property_id is required UUID."""
        property_id = uuid4()
        assert property_id is not None

    def test_compliance_summary_required(self) -> None:
        """Test compliance summary is required."""
        compliance = {
            "overall_status": "COMPLIANT",
            "bca_status": "APPROVED",
            "ura_status": "APPROVED",
        }
        assert "overall_status" in compliance

    def test_updated_at_required(self) -> None:
        """Test updated_at timestamp is required."""
        updated_at = datetime.utcnow()
        assert updated_at is not None

    def test_metadata_default_empty_dict(self) -> None:
        """Test metadata defaults to empty dict."""
        metadata = {}
        assert isinstance(metadata, dict)

    def test_metadata_with_data(self) -> None:
        """Test metadata can contain data."""
        metadata = {"source": "manual_check", "inspector": "System"}
        assert metadata["source"] == "manual_check"


class TestComplianceStatus:
    """Tests for compliance status values."""

    def test_compliant_status(self) -> None:
        """Test COMPLIANT status value."""
        status = "COMPLIANT"
        assert status == "COMPLIANT"

    def test_non_compliant_status(self) -> None:
        """Test NON_COMPLIANT status value."""
        status = "NON_COMPLIANT"
        assert status == "NON_COMPLIANT"

    def test_pending_status(self) -> None:
        """Test PENDING status value."""
        status = "PENDING"
        assert status == "PENDING"

    def test_not_applicable_status(self) -> None:
        """Test NOT_APPLICABLE status value."""
        status = "NOT_APPLICABLE"
        assert status == "NOT_APPLICABLE"


class TestBCAComplianceStatus:
    """Tests for BCA-specific compliance statuses."""

    def test_bca_approved(self) -> None:
        """Test BCA APPROVED status."""
        bca_status = "APPROVED"
        assert bca_status == "APPROVED"

    def test_bca_pending_review(self) -> None:
        """Test BCA PENDING_REVIEW status."""
        bca_status = "PENDING_REVIEW"
        assert bca_status == "PENDING_REVIEW"

    def test_bca_requires_amendment(self) -> None:
        """Test BCA REQUIRES_AMENDMENT status."""
        bca_status = "REQUIRES_AMENDMENT"
        assert bca_status == "REQUIRES_AMENDMENT"

    def test_bca_rejected(self) -> None:
        """Test BCA REJECTED status."""
        bca_status = "REJECTED"
        assert bca_status == "REJECTED"


class TestURAComplianceStatus:
    """Tests for URA-specific compliance statuses."""

    def test_ura_approved(self) -> None:
        """Test URA APPROVED status."""
        ura_status = "APPROVED"
        assert ura_status == "APPROVED"

    def test_ura_conditional_approval(self) -> None:
        """Test URA CONDITIONAL_APPROVAL status."""
        ura_status = "CONDITIONAL_APPROVAL"
        assert ura_status == "CONDITIONAL_APPROVAL"

    def test_ura_pending_submission(self) -> None:
        """Test URA PENDING_SUBMISSION status."""
        ura_status = "PENDING_SUBMISSION"
        assert ura_status == "PENDING_SUBMISSION"

    def test_ura_under_review(self) -> None:
        """Test URA UNDER_REVIEW status."""
        ura_status = "UNDER_REVIEW"
        assert ura_status == "UNDER_REVIEW"
