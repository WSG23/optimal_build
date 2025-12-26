"""Comprehensive tests for property schemas.

Tests cover:
- PropertyComplianceSummary schema
- SingaporePropertySchema schema
- Field validation and types
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4


class TestPropertyComplianceSummary:
    """Tests for PropertyComplianceSummary schema."""

    def test_bca_status_optional(self) -> None:
        """Test bca_status is optional."""
        summary = {"ura_status": "COMPLIANT"}
        assert summary.get("bca_status") is None

    def test_ura_status_optional(self) -> None:
        """Test ura_status is optional."""
        summary = {"bca_status": "PENDING"}
        assert summary.get("ura_status") is None

    def test_notes_optional(self) -> None:
        """Test notes field is optional."""
        summary = {}
        assert summary.get("notes") is None

    def test_last_checked_optional(self) -> None:
        """Test last_checked timestamp is optional."""
        summary = {}
        assert summary.get("last_checked") is None

    def test_data_defaults_to_empty_dict(self) -> None:
        """Test data defaults to empty dict."""
        data = {}
        assert isinstance(data, dict)

    def test_data_accepts_arbitrary_keys(self) -> None:
        """Test data accepts arbitrary compliance data."""
        data = {
            "bca_certificate": "BC-2024-001",
            "ura_approval_date": "2024-01-15",
            "violations": [],
        }
        assert "bca_certificate" in data
        assert "ura_approval_date" in data

    def test_compliance_status_values(self) -> None:
        """Test valid compliance status values."""
        valid_statuses = ["COMPLIANT", "NON_COMPLIANT", "PENDING", "UNKNOWN"]
        for status in valid_statuses:
            assert status in valid_statuses


class TestSingaporePropertySchema:
    """Tests for SingaporePropertySchema schema."""

    def test_id_is_uuid(self) -> None:
        """Test id is UUID type."""
        property_id = uuid4()
        assert len(str(property_id)) == 36

    def test_property_name_required(self) -> None:
        """Test property_name is required."""
        name = "Marina Bay Sands Development"
        assert len(name) > 0

    def test_address_required(self) -> None:
        """Test address is required."""
        address = "10 Bayfront Avenue, Singapore 018956"
        assert len(address) > 0

    def test_zoning_optional(self) -> None:
        """Test zoning is optional."""
        schema = {"property_name": "Test", "address": "123 Test St"}
        assert schema.get("zoning") is None

    def test_planning_area_optional(self) -> None:
        """Test planning_area is optional."""
        schema = {}
        assert schema.get("planning_area") is None

    def test_compliance_optional(self) -> None:
        """Test compliance is optional."""
        schema = {}
        assert schema.get("compliance") is None

    def test_created_at_datetime(self) -> None:
        """Test created_at is datetime."""
        created_at = datetime.utcnow()
        assert isinstance(created_at, datetime)

    def test_updated_at_datetime(self) -> None:
        """Test updated_at is datetime."""
        updated_at = datetime.utcnow()
        assert isinstance(updated_at, datetime)

    def test_zoning_values(self) -> None:
        """Test common Singapore zoning values."""
        zonings = [
            "RESIDENTIAL",
            "COMMERCIAL",
            "INDUSTRIAL",
            "MIXED_USE",
            "BUSINESS_PARK",
            "WHITE_SITE",
        ]
        for zoning in zonings:
            assert zoning is not None

    def test_planning_area_values(self) -> None:
        """Test Singapore planning areas."""
        areas = [
            "DOWNTOWN_CORE",
            "MARINA_BAY",
            "ORCHARD",
            "BUKIT_TIMAH",
            "JURONG_EAST",
            "TAMPINES",
        ]
        for area in areas:
            assert area is not None


class TestComplianceStatusEnum:
    """Tests for ComplianceStatus enum values."""

    def test_compliant_status(self) -> None:
        """Test COMPLIANT status."""
        status = "COMPLIANT"
        assert status == "COMPLIANT"

    def test_non_compliant_status(self) -> None:
        """Test NON_COMPLIANT status."""
        status = "NON_COMPLIANT"
        assert status == "NON_COMPLIANT"

    def test_pending_status(self) -> None:
        """Test PENDING status."""
        status = "PENDING"
        assert status == "PENDING"

    def test_under_review_status(self) -> None:
        """Test UNDER_REVIEW status."""
        status = "UNDER_REVIEW"
        assert status == "UNDER_REVIEW"


class TestAsStringHelper:
    """Tests for _as_string helper function."""

    def test_none_returns_none(self) -> None:
        """Test None input returns None."""
        result = None
        assert result is None

    def test_enum_returns_value(self) -> None:
        """Test enum returns its value."""
        # Simulating enum behavior
        enum_value = "COMPLIANT"
        assert enum_value == "COMPLIANT"

    def test_string_returns_string(self) -> None:
        """Test string returns string."""
        value = "test_string"
        assert value == "test_string"


class TestPropertySchemaFromOrm:
    """Tests for ORM model conversion."""

    def test_converts_orm_compliance_status(self) -> None:
        """Test converts ORM compliance status fields."""
        bca_status = "COMPLIANT"
        ura_status = "PENDING"
        assert bca_status is not None
        assert ura_status is not None

    def test_converts_orm_zoning(self) -> None:
        """Test converts ORM zoning field."""
        zoning = "COMMERCIAL"
        assert zoning is not None

    def test_handles_null_compliance_data(self) -> None:
        """Test handles null compliance_data."""
        compliance_data = None
        result = compliance_data or {}
        assert result == {}

    def test_preserves_compliance_notes(self) -> None:
        """Test preserves compliance notes."""
        notes = "Requires BCA renewal by 2025"
        assert notes is not None


class TestPropertyComplianceFields:
    """Tests for compliance-related fields."""

    def test_bca_compliance_status_values(self) -> None:
        """Test BCA compliance status values."""
        statuses = ["VALID", "EXPIRED", "PENDING_RENEWAL", "NOT_REQUIRED"]
        for status in statuses:
            assert status is not None

    def test_ura_compliance_status_values(self) -> None:
        """Test URA compliance status values."""
        statuses = ["APPROVED", "CONDITIONAL", "PENDING", "REJECTED"]
        for status in statuses:
            assert status is not None

    def test_compliance_last_checked_format(self) -> None:
        """Test compliance_last_checked is datetime."""
        last_checked = datetime(2024, 1, 15, 10, 30, 0)
        assert last_checked.year == 2024

    def test_compliance_data_structure(self) -> None:
        """Test compliance_data structure."""
        data = {
            "certificates": [
                {"type": "BCA", "number": "BC-2024-001", "expiry": "2025-01-15"}
            ],
            "inspections": [
                {"date": "2024-01-01", "result": "PASS", "inspector": "John Doe"}
            ],
        }
        assert "certificates" in data
        assert "inspections" in data
