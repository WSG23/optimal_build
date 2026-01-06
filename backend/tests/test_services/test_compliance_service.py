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


class TestBuildResult:
    """Tests for _build_result helper function."""

    def test_build_result_with_complete_record(self):
        """Test _build_result builds response from complete property record."""
        from datetime import datetime, timezone
        from unittest.mock import patch
        from uuid import uuid4

        from app.services.compliance import _build_result

        mock_record = MagicMock()
        mock_record.id = uuid4()
        mock_record.bca_compliance_status = ComplianceStatus.PASSED
        mock_record.ura_compliance_status = ComplianceStatus.PENDING
        mock_record.compliance_notes = "All checks passed"
        mock_record.compliance_last_checked = datetime.now(timezone.utc)
        mock_record.compliance_data = {"score": 95}
        mock_record.updated_at = datetime.now(timezone.utc)

        with patch(
            "app.services.compliance.SingaporePropertySchema.model_validate"
        ) as mock_validate:
            mock_validate.return_value = MagicMock()

            result = _build_result(mock_record)

            assert result is not None
            assert result.response.property_id == mock_record.id
            assert result.response.metadata == {"jurisdiction": "SG"}

    def test_build_result_with_none_compliance_data(self):
        """Test _build_result handles None compliance_data."""
        from datetime import datetime, timezone
        from unittest.mock import patch
        from uuid import uuid4

        from app.services.compliance import _build_result

        mock_record = MagicMock()
        mock_record.id = uuid4()
        mock_record.bca_compliance_status = None
        mock_record.ura_compliance_status = None
        mock_record.compliance_notes = None
        mock_record.compliance_last_checked = None
        mock_record.compliance_data = None
        mock_record.updated_at = datetime.now(timezone.utc)

        with patch(
            "app.services.compliance.SingaporePropertySchema.model_validate"
        ) as mock_validate:
            mock_validate.return_value = MagicMock()

            result = _build_result(mock_record)

            assert result is not None
            # compliance_data should default to {} - access via attribute
            assert result.response.compliance.data == {}

    def test_build_result_extracts_status_values(self):
        """Test _build_result correctly extracts status values."""
        from datetime import datetime, timezone
        from unittest.mock import patch
        from uuid import uuid4

        from app.services.compliance import _build_result

        mock_record = MagicMock()
        mock_record.id = uuid4()
        mock_record.bca_compliance_status = ComplianceStatus.FAILED
        mock_record.ura_compliance_status = ComplianceStatus.PASSED
        mock_record.compliance_notes = "BCA failed due to height"
        mock_record.compliance_last_checked = datetime.now(timezone.utc)
        mock_record.compliance_data = {}
        mock_record.updated_at = datetime.now(timezone.utc)

        with patch(
            "app.services.compliance.SingaporePropertySchema.model_validate"
        ) as mock_validate:
            mock_validate.return_value = MagicMock()

            result = _build_result(mock_record)

            # Access via attributes since compliance is PropertyComplianceSummary
            assert result.response.compliance.bca_status == "failed"
            assert result.response.compliance.ura_status == "passed"
            assert result.response.compliance.notes == "BCA failed due to height"


class TestComplianceServiceRunForProperty:
    """Tests for ComplianceService.run_for_property."""

    @pytest.mark.asyncio
    async def test_run_for_property_success(self):
        """Test run_for_property returns result for valid property."""
        from datetime import datetime, timezone
        from unittest.mock import AsyncMock, MagicMock, patch
        from uuid import uuid4

        from app.services.compliance import ComplianceService

        property_id = uuid4()

        # Create mock record
        mock_record = MagicMock()
        mock_record.id = property_id
        mock_record.bca_compliance_status = ComplianceStatus.PASSED
        mock_record.ura_compliance_status = ComplianceStatus.PASSED
        mock_record.compliance_notes = None
        mock_record.compliance_last_checked = datetime.now(timezone.utc)
        mock_record.compliance_data = {}
        mock_record.updated_at = datetime.now(timezone.utc)

        # Create mock session
        mock_session = AsyncMock()
        mock_session.get.return_value = mock_record

        # Create mock session factory
        mock_factory = MagicMock()
        mock_factory.return_value.__aenter__.return_value = mock_session

        service = ComplianceService(mock_factory)

        with patch("app.services.compliance.update_property_compliance") as mock_update:
            mock_update.return_value = mock_record
            with patch(
                "app.services.compliance.SingaporePropertySchema.model_validate"
            ) as mock_validate:
                mock_validate.return_value = MagicMock()

                result = await service.run_for_property(property_id)

                assert result is not None
                mock_session.get.assert_called_once()
                mock_update.assert_called_once_with(mock_record, mock_session)
                mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_for_property_not_found(self):
        """Test run_for_property raises ValueError for missing property."""
        from unittest.mock import AsyncMock, MagicMock
        from uuid import uuid4

        from app.services.compliance import ComplianceService

        property_id = uuid4()

        # Mock session returning None
        mock_session = AsyncMock()
        mock_session.get.return_value = None

        mock_factory = MagicMock()
        mock_factory.return_value.__aenter__.return_value = mock_session

        service = ComplianceService(mock_factory)

        with pytest.raises(ValueError, match=f"Property {property_id} not found"):
            await service.run_for_property(property_id)


class TestComplianceServiceRunBatch:
    """Tests for ComplianceService.run_batch."""

    @pytest.mark.asyncio
    async def test_run_batch_with_no_property_ids(self):
        """Test run_batch processes properties with limit when no IDs provided."""
        from datetime import datetime, timezone
        from unittest.mock import AsyncMock, MagicMock, patch
        from uuid import uuid4

        from app.services.compliance import ComplianceService

        # Create mock records
        mock_records = []
        for _ in range(3):
            mock_record = MagicMock()
            mock_record.id = uuid4()
            mock_record.bca_compliance_status = ComplianceStatus.PENDING
            mock_record.ura_compliance_status = ComplianceStatus.PENDING
            mock_record.compliance_notes = None
            mock_record.compliance_last_checked = None
            mock_record.compliance_data = None
            mock_record.updated_at = datetime.now(timezone.utc)
            mock_records.append(mock_record)

        # Mock session
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_records

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        mock_factory = MagicMock()
        mock_factory.return_value.__aenter__.return_value = mock_session

        service = ComplianceService(mock_factory)

        with patch("app.services.compliance.update_property_compliance") as mock_update:
            mock_update.side_effect = mock_records
            with patch(
                "app.services.compliance.SingaporePropertySchema.model_validate"
            ) as mock_validate:
                mock_validate.return_value = MagicMock()

                results = await service.run_batch(limit=100)

                assert len(results) == 3
                assert mock_update.call_count == 3
                mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_batch_with_specific_property_ids(self):
        """Test run_batch processes only specified property IDs."""
        from datetime import datetime, timezone
        from unittest.mock import AsyncMock, MagicMock, patch
        from uuid import uuid4

        from app.services.compliance import ComplianceService

        property_ids = [uuid4(), uuid4()]

        mock_records = []
        for pid in property_ids:
            mock_record = MagicMock()
            mock_record.id = pid
            mock_record.bca_compliance_status = ComplianceStatus.PASSED
            mock_record.ura_compliance_status = ComplianceStatus.PASSED
            mock_record.compliance_notes = None
            mock_record.compliance_last_checked = datetime.now(timezone.utc)
            mock_record.compliance_data = {}
            mock_record.updated_at = datetime.now(timezone.utc)
            mock_records.append(mock_record)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_records

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        mock_factory = MagicMock()
        mock_factory.return_value.__aenter__.return_value = mock_session

        service = ComplianceService(mock_factory)

        with patch("app.services.compliance.update_property_compliance") as mock_update:
            mock_update.side_effect = mock_records
            with patch(
                "app.services.compliance.SingaporePropertySchema.model_validate"
            ) as mock_validate:
                mock_validate.return_value = MagicMock()

                results = await service.run_batch(property_ids=property_ids)

                assert len(results) == 2

    @pytest.mark.asyncio
    async def test_run_batch_empty_results(self):
        """Test run_batch returns empty list when no properties found."""
        from unittest.mock import AsyncMock, MagicMock

        from app.services.compliance import ComplianceService

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        mock_factory = MagicMock()
        mock_factory.return_value.__aenter__.return_value = mock_session

        service = ComplianceService(mock_factory)

        results = await service.run_batch()

        assert results == []
        mock_session.commit.assert_called_once()


class TestComplianceServiceInit:
    """Tests for ComplianceService initialization."""

    def test_init_stores_session_factory(self):
        """Test ComplianceService stores session factory."""
        from unittest.mock import MagicMock

        from app.services.compliance import ComplianceService

        mock_factory = MagicMock()
        service = ComplianceService(mock_factory)

        assert service._session_factory == mock_factory
