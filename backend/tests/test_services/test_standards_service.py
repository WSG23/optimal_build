"""Tests for standards service with mocked database.

Tests focus on upsert_material_standard and lookup_material_standards.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

pytest.importorskip("sqlalchemy")

from app.models.rkp import RefMaterialStandard


class TestUpsertMaterialStandard:
    """Test upsert_material_standard function."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_upsert_creates_new_record_when_not_exists(self, mock_session):
        """Test upsert creates new record when no matching record exists."""
        from app.services.standards import upsert_material_standard

        # Mock no existing record
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        payload = {
            "standard_code": "ASTM-A36",
            "material_type": "steel",
            "property_key": "yield_strength",
            "value": "250",
            "unit": "MPa",
            "standard_body": "ASTM",
        }

        await upsert_material_standard(mock_session, payload)

        # Should add new record
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

        # Verify record attributes
        added_record = mock_session.add.call_args[0][0]
        assert added_record.standard_code == "ASTM-A36"
        assert added_record.material_type == "steel"
        assert added_record.property_key == "yield_strength"

    @pytest.mark.asyncio
    async def test_upsert_updates_existing_record(self, mock_session):
        """Test upsert updates existing record when found."""
        from app.services.standards import upsert_material_standard

        # Mock existing record
        existing_record = MagicMock(spec=RefMaterialStandard)
        existing_record.standard_code = "ASTM-A36"
        existing_record.material_type = "steel"
        existing_record.property_key = "yield_strength"
        existing_record.value = "250"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_record
        mock_session.execute.return_value = mock_result

        payload = {
            "standard_code": "ASTM-A36",
            "material_type": "steel",
            "property_key": "yield_strength",
            "value": "275",  # Updated value
            "unit": "MPa",
        }

        await upsert_material_standard(mock_session, payload)

        # Should NOT add (update instead)
        mock_session.add.assert_not_called()
        mock_session.flush.assert_called_once()

        # Verify value was updated
        assert existing_record.value == "275"
        assert existing_record.unit == "MPa"

    @pytest.mark.asyncio
    async def test_upsert_with_section_filter(self, mock_session):
        """Test upsert includes section in filter when provided."""
        from app.services.standards import upsert_material_standard

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        payload = {
            "standard_code": "ISO-9001",
            "material_type": "general",
            "property_key": "quality",
            "section": "Section 4.1",
        }

        await upsert_material_standard(mock_session, payload)

        # Verify execute was called with query including section filter
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_with_edition_filter(self, mock_session):
        """Test upsert includes edition in filter when provided."""
        from app.services.standards import upsert_material_standard

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        payload = {
            "standard_code": "EN-1090",
            "material_type": "steel",
            "property_key": "fabrication",
            "edition": "2018",
        }

        await upsert_material_standard(mock_session, payload)

        mock_session.execute.assert_called_once()


class TestLookupMaterialStandards:
    """Test lookup_material_standards function."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_lookup_returns_all_when_no_filters(self, mock_session):
        """Test lookup returns all standards when no filters provided."""
        from app.services.standards import lookup_material_standards

        mock_records = [
            MagicMock(spec=RefMaterialStandard),
            MagicMock(spec=RefMaterialStandard),
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_records
        mock_session.execute.return_value = mock_result

        result = await lookup_material_standards(mock_session)

        assert len(result) == 2
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_lookup_filters_by_standard_code(self, mock_session):
        """Test lookup filters by standard_code when provided."""
        from app.services.standards import lookup_material_standards

        mock_records = [MagicMock(spec=RefMaterialStandard)]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_records
        mock_session.execute.return_value = mock_result

        result = await lookup_material_standards(mock_session, standard_code="ASTM-A36")

        assert len(result) == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_lookup_filters_by_standard_body(self, mock_session):
        """Test lookup filters by standard_body when provided."""
        from app.services.standards import lookup_material_standards

        mock_records = [MagicMock(spec=RefMaterialStandard) for _ in range(3)]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_records
        mock_session.execute.return_value = mock_result

        result = await lookup_material_standards(mock_session, standard_body="ASTM")

        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_lookup_filters_by_material_type(self, mock_session):
        """Test lookup filters by material_type when provided."""
        from app.services.standards import lookup_material_standards

        mock_records = [MagicMock(spec=RefMaterialStandard) for _ in range(2)]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_records
        mock_session.execute.return_value = mock_result

        result = await lookup_material_standards(mock_session, material_type="steel")

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_lookup_filters_by_section(self, mock_session):
        """Test lookup filters by section when provided."""
        from app.services.standards import lookup_material_standards

        mock_records = []
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_records
        mock_session.execute.return_value = mock_result

        result = await lookup_material_standards(mock_session, section="4.1")

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_lookup_with_multiple_filters(self, mock_session):
        """Test lookup combines multiple filters."""
        from app.services.standards import lookup_material_standards

        mock_records = [MagicMock(spec=RefMaterialStandard)]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_records
        mock_session.execute.return_value = mock_result

        result = await lookup_material_standards(
            mock_session,
            standard_code="ASTM-A36",
            standard_body="ASTM",
            material_type="steel",
            section="Table 1",
        )

        assert len(result) == 1


class TestStandardUpdateFields:
    """Test STANDARD_UPDATE_FIELDS constant."""

    def test_standard_update_fields_contains_expected_fields(self):
        """Test STANDARD_UPDATE_FIELDS contains expected field names."""
        from app.services.standards import STANDARD_UPDATE_FIELDS

        expected_fields = [
            "value",
            "unit",
            "context",
            "section",
            "applicability",
            "edition",
            "effective_date",
            "license_ref",
            "provenance",
            "source_document",
            "standard_body",
        ]

        for field in expected_fields:
            assert field in STANDARD_UPDATE_FIELDS
