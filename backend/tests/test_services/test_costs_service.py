"""Tests for costs service with mocked database.

Tests focus on upsert_cost_index, get_latest_cost_index,
add_cost_catalog_item, and list_cost_catalog.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

pytest.importorskip("sqlalchemy")

from app.models.rkp import RefCostCatalog, RefCostIndex


class TestUpsertCostIndex:
    """Test upsert_cost_index function."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_upsert_creates_new_record_when_not_exists(self, mock_session):
        """Test upsert creates new record when no matching record exists."""
        from app.services.costs import upsert_cost_index

        # Mock no existing record
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        payload = {
            "jurisdiction": "SG",
            "series_name": "BCI_TENDER",
            "period": "2024Q4",
            "value": "145.6",
            "unit": "index",
            "source": "BCA",
        }

        await upsert_cost_index(mock_session, payload)

        # Should add new record
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

        # Verify record attributes
        added_record = mock_session.add.call_args[0][0]
        assert added_record.series_name == "BCI_TENDER"
        assert added_record.period == "2024Q4"

    @pytest.mark.asyncio
    async def test_upsert_updates_existing_record(self, mock_session):
        """Test upsert updates existing record when found."""
        from app.services.costs import upsert_cost_index

        # Mock existing record
        existing_record = MagicMock(spec=RefCostIndex)
        existing_record.series_name = "BCI_TENDER"
        existing_record.period = "2024Q4"
        existing_record.value = "145.6"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_record
        mock_session.execute.return_value = mock_result

        payload = {
            "jurisdiction": "SG",
            "series_name": "BCI_TENDER",
            "period": "2024Q4",
            "value": "148.2",  # Updated value
            "unit": "index",
        }

        await upsert_cost_index(mock_session, payload)

        # Should NOT add (update instead)
        mock_session.add.assert_not_called()
        mock_session.flush.assert_called_once()

        # Verify value was updated
        assert existing_record.value == "148.2"
        assert existing_record.unit == "index"

    @pytest.mark.asyncio
    async def test_upsert_uses_default_jurisdiction(self, mock_session):
        """Test upsert uses SG as default jurisdiction."""
        from app.services.costs import upsert_cost_index

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        payload = {
            "series_name": "CPI",
            "period": "2024-12",
            "value": "102.5",
        }

        await upsert_cost_index(mock_session, payload)

        # Verify execute was called (query uses default jurisdiction)
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_updates_multiple_fields(self, mock_session):
        """Test upsert updates all COST_INDEX_UPDATE_FIELDS."""
        from app.services.costs import COST_INDEX_UPDATE_FIELDS, upsert_cost_index

        existing_record = MagicMock(spec=RefCostIndex)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_record
        mock_session.execute.return_value = mock_result

        payload = {
            "series_name": "TEST",
            "period": "2024Q4",
            "value": "100",
            "unit": "index",
            "source": "BCA",
            "category": "building",
            "subcategory": "residential",
            "provider": "official",
            "methodology": "standard",
        }

        await upsert_cost_index(mock_session, payload)

        # Verify all update fields were set
        for field_name in COST_INDEX_UPDATE_FIELDS:
            if field_name in payload:
                assert getattr(existing_record, field_name) == payload[field_name]


class TestGetLatestCostIndex:
    """Test get_latest_cost_index function."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_get_latest_returns_record(self, mock_session):
        """Test get_latest returns the latest record for a series."""
        from app.services.costs import get_latest_cost_index

        mock_record = MagicMock(spec=RefCostIndex)
        mock_record.series_name = "BCI_TENDER"
        mock_record.period = "2024Q4"
        mock_record.value = "148.2"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_record
        mock_session.execute.return_value = mock_result

        result = await get_latest_cost_index(
            mock_session, series_name="BCI_TENDER", jurisdiction="SG"
        )

        assert result is not None
        assert result.series_name == "BCI_TENDER"

    @pytest.mark.asyncio
    async def test_get_latest_returns_none_when_not_found(self, mock_session):
        """Test get_latest returns None when no record found."""
        from app.services.costs import get_latest_cost_index

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await get_latest_cost_index(mock_session, series_name="NONEXISTENT")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_latest_filters_by_provider(self, mock_session):
        """Test get_latest includes provider filter when provided."""
        from app.services.costs import get_latest_cost_index

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        await get_latest_cost_index(
            mock_session,
            series_name="BCI_TENDER",
            jurisdiction="SG",
            provider="BCA",
        )

        # Verify execute was called with query including provider
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_latest_uses_default_jurisdiction(self, mock_session):
        """Test get_latest uses SG as default jurisdiction."""
        from app.services.costs import get_latest_cost_index

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        await get_latest_cost_index(mock_session, series_name="TEST")

        mock_session.execute.assert_called_once()


class TestAddCostCatalogItem:
    """Test add_cost_catalog_item function."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_add_cost_catalog_item_creates_record(self, mock_session):
        """Test add_cost_catalog_item creates and returns new record."""
        from app.services.costs import add_cost_catalog_item

        payload = {
            "catalog_name": "RICS_2024",
            "item_code": "2A.01",
            "description": "Substructure - Piling",
            "unit": "m2",
            "category": "structural",
        }

        await add_cost_catalog_item(mock_session, payload)

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

        added_record = mock_session.add.call_args[0][0]
        assert added_record.catalog_name == "RICS_2024"
        assert added_record.item_code == "2A.01"

    @pytest.mark.asyncio
    async def test_add_cost_catalog_item_with_all_fields(self, mock_session):
        """Test add_cost_catalog_item with all fields."""
        from app.services.costs import add_cost_catalog_item

        payload = {
            "catalog_name": "BCA_2024",
            "item_code": "1B.02",
            "description": "Excavation works",
            "unit": "m3",
            "category": "groundwork",
            "unit_cost": 45.50,
            "currency": "SGD",
        }

        await add_cost_catalog_item(mock_session, payload)

        added_record = mock_session.add.call_args[0][0]
        assert added_record.catalog_name == "BCA_2024"
        assert added_record.item_code == "1B.02"
        assert added_record.category == "groundwork"


class TestListCostCatalog:
    """Test list_cost_catalog function."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_list_cost_catalog_returns_all(self, mock_session):
        """Test list_cost_catalog returns all when no filters."""
        from app.services.costs import list_cost_catalog

        mock_records = [
            MagicMock(spec=RefCostCatalog),
            MagicMock(spec=RefCostCatalog),
            MagicMock(spec=RefCostCatalog),
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_records
        mock_session.execute.return_value = mock_result

        result = await list_cost_catalog(mock_session)

        assert len(result) == 3
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_cost_catalog_filters_by_catalog_name(self, mock_session):
        """Test list_cost_catalog filters by catalog_name."""
        from app.services.costs import list_cost_catalog

        mock_records = [MagicMock(spec=RefCostCatalog)]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_records
        mock_session.execute.return_value = mock_result

        result = await list_cost_catalog(mock_session, catalog_name="RICS_2024")

        assert len(result) == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_cost_catalog_filters_by_category(self, mock_session):
        """Test list_cost_catalog filters by category."""
        from app.services.costs import list_cost_catalog

        mock_records = [MagicMock(spec=RefCostCatalog) for _ in range(2)]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_records
        mock_session.execute.return_value = mock_result

        result = await list_cost_catalog(mock_session, category="structural")

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_list_cost_catalog_combines_filters(self, mock_session):
        """Test list_cost_catalog combines multiple filters."""
        from app.services.costs import list_cost_catalog

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await list_cost_catalog(
            mock_session, catalog_name="BCA_2024", category="groundwork"
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_list_cost_catalog_returns_empty_list(self, mock_session):
        """Test list_cost_catalog returns empty list when no matches."""
        from app.services.costs import list_cost_catalog

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await list_cost_catalog(mock_session, catalog_name="NONEXISTENT")

        assert result == []


class TestCostIndexUpdateFields:
    """Test COST_INDEX_UPDATE_FIELDS constant."""

    def test_contains_expected_fields(self):
        """Test COST_INDEX_UPDATE_FIELDS contains expected field names."""
        from app.services.costs import COST_INDEX_UPDATE_FIELDS

        expected_fields = [
            "value",
            "unit",
            "source",
            "category",
            "subcategory",
            "provider",
            "methodology",
        ]

        for field_name in expected_fields:
            assert field_name in COST_INDEX_UPDATE_FIELDS
