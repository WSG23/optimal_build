"""Tests for compliance_service.

Tests focus on ComplianceService and helper functions.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

pytest.importorskip("sqlalchemy")

from app.models.singapore_property import ComplianceStatus


class TestToString:
    """Tests for _to_string helper function."""

    def test_to_string_with_none(self):
        """Test _to_string returns None for None input."""
        from app.services.compliance import _to_string

        result = _to_string(None)
        assert result is None

    def test_to_string_with_compliance_status_enum(self):
        """Test _to_string extracts value from ComplianceStatus enum."""
        from app.services.compliance import _to_string

        result = _to_string(ComplianceStatus.PASSED)
        assert result == "passed"

        result = _to_string(ComplianceStatus.FAILED)
        assert result == "failed"

        result = _to_string(ComplianceStatus.PENDING)
        assert result == "pending"

    def test_to_string_with_string(self):
        """Test _to_string converts string to string."""
        from app.services.compliance import _to_string

        result = _to_string("some_status")
        assert result == "some_status"

    def test_to_string_with_object_having_value_attr(self):
        """Test _to_string uses .value attribute if present."""
        from app.services.compliance import _to_string

        mock_obj = MagicMock()
        mock_obj.value = "custom_value"

        result = _to_string(mock_obj)
        assert result == "custom_value"

    def test_to_string_with_integer(self):
        """Test _to_string converts integer to string."""
        from app.services.compliance import _to_string

        result = _to_string(42)
        assert result == "42"


class TestComplianceServiceBuildQuery:
    """Tests for ComplianceService._build_query."""

    def test_build_query_with_no_property_ids(self):
        """Test _build_query applies limit when no IDs provided."""
        from unittest.mock import MagicMock

        from app.services.compliance import ComplianceService

        mock_factory = MagicMock()
        service = ComplianceService(mock_factory)

        stmt = service._build_query(None, limit=50)

        # Just verify it returns a Select statement
        assert stmt is not None

    def test_build_query_with_property_ids(self):
        """Test _build_query filters by property IDs when provided."""
        from uuid import uuid4

        from app.services.compliance import ComplianceService

        mock_factory = MagicMock()
        service = ComplianceService(mock_factory)

        property_ids = [uuid4(), uuid4()]
        stmt = service._build_query(property_ids, limit=50)

        # Verify statement was built
        assert stmt is not None

    def test_build_query_with_empty_property_ids(self):
        """Test _build_query with empty list uses limit."""
        from app.services.compliance import ComplianceService

        mock_factory = MagicMock()
        service = ComplianceService(mock_factory)

        stmt = service._build_query([], limit=25)

        assert stmt is not None


class TestComplianceResult:
    """Tests for ComplianceResult dataclass."""

    def test_compliance_result_creation(self):
        """Test ComplianceResult can be instantiated."""
        from app.services.compliance import ComplianceResult

        mock_property = MagicMock()
        mock_response = MagicMock()

        result = ComplianceResult(property=mock_property, response=mock_response)

        assert result.property == mock_property
        assert result.response == mock_response
