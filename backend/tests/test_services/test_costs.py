"""Tests for cost index and catalog services."""

from __future__ import annotations

from decimal import Decimal

import pytest

pytest.importorskip("sqlalchemy")

from sqlalchemy.ext.asyncio import AsyncSession

from app.services import costs


class TestUpsertCostIndex:
    """Tests for upsert_cost_index function."""

    @pytest.mark.asyncio
    async def test_upsert_creates_new_cost_index(self, session: AsyncSession) -> None:
        """Test upsert creates new cost index when none exists."""
        payload = {
            "jurisdiction": "SG",
            "series_name": "BCA Cost Index",
            "category": "material",
            "period": "2024-Q1",
            "value": Decimal("150.5"),
            "unit": "index",
        }

        result = await costs.upsert_cost_index(session, payload)
        await session.commit()

        assert result.id is not None
        assert result.series_name == "BCA Cost Index"
        assert result.jurisdiction == "SG"
        assert result.period == "2024-Q1"
        assert result.value == Decimal("150.5")
        assert result.unit == "index"
        assert result.category == "material"

    @pytest.mark.asyncio
    async def test_upsert_creates_with_default_jurisdiction(
        self, session: AsyncSession
    ) -> None:
        """Test upsert defaults jurisdiction to SG when not provided."""
        payload = {
            "series_name": "Steel Price Index",
            "category": "material",
            "period": "2024-Q2",
            "value": Decimal("200.0"),
            "unit": "index",
        }

        result = await costs.upsert_cost_index(session, payload)
        await session.commit()

        assert result.jurisdiction == "SG"

    @pytest.mark.asyncio
    async def test_upsert_updates_existing_cost_index(
        self, session: AsyncSession
    ) -> None:
        """Test upsert updates existing cost index."""
        initial_payload = {
            "jurisdiction": "SG",
            "series_name": "Concrete Cost Index",
            "category": "material",
            "period": "2024-Q1",
            "value": Decimal("100.0"),
            "unit": "index",
            "provider": "BCA",
        }

        result1 = await costs.upsert_cost_index(session, initial_payload)
        await session.commit()
        original_id = result1.id

        update_payload = {
            "jurisdiction": "SG",
            "series_name": "Concrete Cost Index",
            "category": "material",
            "period": "2024-Q1",
            "value": Decimal("105.5"),
            "unit": "index",
            "provider": "BCA Updated",
            "source": "official_report",
            "methodology": "weighted average",
        }

        result2 = await costs.upsert_cost_index(session, update_payload)
        await session.commit()

        assert result2.id == original_id
        assert result2.value == Decimal("105.5")
        assert result2.provider == "BCA Updated"
        assert result2.source == "official_report"
        assert result2.methodology == "weighted average"

    @pytest.mark.asyncio
    async def test_upsert_updates_only_provided_fields(
        self, session: AsyncSession
    ) -> None:
        """Test upsert only updates fields present in payload."""
        initial_payload = {
            "jurisdiction": "SG",
            "series_name": "Labor Cost Index",
            "category": "labor",
            "subcategory": "skilled",
            "period": "2024-Q1",
            "value": Decimal("120.0"),
            "unit": "SGD/hour",
            "source": "original_source",
            "provider": "internal",
        }

        _ = await costs.upsert_cost_index(session, initial_payload)
        await session.commit()

        update_payload = {
            "jurisdiction": "SG",
            "series_name": "Labor Cost Index",
            "category": "labor",
            "period": "2024-Q1",
            "value": Decimal("125.0"),
        }

        result2 = await costs.upsert_cost_index(session, update_payload)
        await session.commit()

        assert result2.value == Decimal("125.0")
        assert result2.source == "original_source"  # unchanged
        assert result2.subcategory == "skilled"  # unchanged

    @pytest.mark.asyncio
    async def test_upsert_updates_all_updatable_fields(
        self, session: AsyncSession
    ) -> None:
        """Test upsert can update all COST_INDEX_UPDATE_FIELDS."""
        initial_payload = {
            "jurisdiction": "SG",
            "series_name": "Equipment Cost Index",
            "category": "equipment",
            "period": "2024-Q1",
            "value": Decimal("150.0"),
            "unit": "SGD/day",
        }

        await costs.upsert_cost_index(session, initial_payload)
        await session.commit()

        update_payload = {
            "jurisdiction": "SG",
            "series_name": "Equipment Cost Index",
            "category": "equipment",
            "period": "2024-Q1",
            "value": Decimal("155.0"),
            "unit": "SGD/hour",
            "source": "vendor_data",
            "subcategory": "heavy_machinery",
            "provider": "external_vendor",
            "methodology": "market_survey",
        }

        result = await costs.upsert_cost_index(session, update_payload)
        await session.commit()

        assert result.value == Decimal("155.0")
        assert result.unit == "SGD/hour"
        assert result.source == "vendor_data"
        assert result.subcategory == "heavy_machinery"
        assert result.provider == "external_vendor"
        assert result.methodology == "market_survey"

    @pytest.mark.asyncio
    async def test_upsert_distinguishes_by_jurisdiction_series_period(session) -> None:
        """Test upsert treats same series in different jurisdictions/periods as distinct."""
        payload_sg = {
            "jurisdiction": "SG",
            "series_name": "BCA Cost Index",
            "category": "material",
            "period": "2024-Q1",
            "value": Decimal("150.0"),
            "unit": "index",
        }

        payload_other_jurisdiction = {
            "jurisdiction": "MY",
            "series_name": "BCA Cost Index",
            "category": "material",
            "period": "2024-Q1",
            "value": Decimal("160.0"),
            "unit": "index",
        }

        payload_other_period = {
            "jurisdiction": "SG",
            "series_name": "BCA Cost Index",
            "category": "material",
            "period": "2024-Q2",
            "value": Decimal("155.0"),
            "unit": "index",
        }

        result1 = await costs.upsert_cost_index(session, payload_sg)
        result2 = await costs.upsert_cost_index(session, payload_other_jurisdiction)
        result3 = await costs.upsert_cost_index(session, payload_other_period)
        await session.commit()

        assert result1.id != result2.id
        assert result1.id != result3.id
        assert result2.id != result3.id


class TestGetLatestCostIndex:
    """Tests for get_latest_cost_index function."""

    @pytest.mark.asyncio
    async def test_get_latest_returns_highest_period(
        self, session: AsyncSession
    ) -> None:
        """Test get_latest returns the cost index with highest period."""
        payloads = [
            {
                "jurisdiction": "SG",
                "series_name": "BCA Index",
                "category": "material",
                "period": "2024-Q1",
                "value": Decimal("150.0"),
                "unit": "index",
            },
            {
                "jurisdiction": "SG",
                "series_name": "BCA Index",
                "category": "material",
                "period": "2024-Q2",
                "value": Decimal("155.0"),
                "unit": "index",
            },
            {
                "jurisdiction": "SG",
                "series_name": "BCA Index",
                "category": "material",
                "period": "2024-Q3",
                "value": Decimal("160.0"),
                "unit": "index",
            },
        ]

        for payload in payloads:
            await costs.upsert_cost_index(session, payload)
        await session.commit()

        result = await costs.get_latest_cost_index(session, series_name="BCA Index")

        assert result is not None
        assert result.period == "2024-Q3"
        assert result.value == Decimal("160.0")

    @pytest.mark.asyncio
    async def test_get_latest_returns_none_when_not_found(
        self, session: AsyncSession
    ) -> None:
        """Test get_latest returns None when series not found."""
        result = await costs.get_latest_cost_index(
            session, series_name="Nonexistent Index"
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_get_latest_with_jurisdiction_filter(
        self, session: AsyncSession
    ) -> None:
        """Test get_latest respects jurisdiction filter."""
        payloads = [
            {
                "jurisdiction": "SG",
                "series_name": "Labor Index",
                "category": "labor",
                "period": "2024-Q1",
                "value": Decimal("100.0"),
                "unit": "index",
            },
            {
                "jurisdiction": "MY",
                "series_name": "Labor Index",
                "category": "labor",
                "period": "2024-Q2",
                "value": Decimal("110.0"),
                "unit": "index",
            },
        ]

        for payload in payloads:
            await costs.upsert_cost_index(session, payload)
        await session.commit()

        result_sg = await costs.get_latest_cost_index(
            session, series_name="Labor Index", jurisdiction="SG"
        )
        result_my = await costs.get_latest_cost_index(
            session, series_name="Labor Index", jurisdiction="MY"
        )

        assert result_sg is not None
        assert result_sg.jurisdiction == "SG"
        assert result_sg.period == "2024-Q1"

        assert result_my is not None
        assert result_my.jurisdiction == "MY"
        assert result_my.period == "2024-Q2"

    @pytest.mark.asyncio
    async def test_get_latest_with_provider_filter(self, session: AsyncSession) -> None:
        """Test get_latest respects provider filter."""
        payloads = [
            {
                "jurisdiction": "SG",
                "series_name": "Steel Index",
                "category": "material",
                "period": "2024-Q1",
                "value": Decimal("200.0"),
                "unit": "index",
                "provider": "BCA",
            },
            {
                "jurisdiction": "SG",
                "series_name": "Steel Index",
                "category": "material",
                "period": "2024-Q2",
                "value": Decimal("210.0"),
                "unit": "index",
                "provider": "internal",
            },
            {
                "jurisdiction": "SG",
                "series_name": "Steel Index",
                "category": "material",
                "period": "2024-Q1",
                "value": Decimal("205.0"),
                "unit": "index",
                "provider": "external",
            },
        ]

        for payload in payloads:
            await costs.upsert_cost_index(session, payload)
        await session.commit()

        result_bca = await costs.get_latest_cost_index(
            session, series_name="Steel Index", provider="BCA"
        )
        result_internal = await costs.get_latest_cost_index(
            session, series_name="Steel Index", provider="internal"
        )

        assert result_bca is not None
        assert result_bca.provider == "BCA"
        assert result_bca.period == "2024-Q1"

        assert result_internal is not None
        assert result_internal.provider == "internal"
        assert result_internal.period == "2024-Q2"

    @pytest.mark.asyncio
    async def test_get_latest_with_all_filters(self, session: AsyncSession) -> None:
        """Test get_latest with jurisdiction, series, and provider filters."""
        payloads = [
            {
                "jurisdiction": "SG",
                "series_name": "Concrete Index",
                "category": "material",
                "period": "2024-Q1",
                "value": Decimal("150.0"),
                "unit": "index",
                "provider": "BCA",
            },
            {
                "jurisdiction": "SG",
                "series_name": "Concrete Index",
                "category": "material",
                "period": "2024-Q2",
                "value": Decimal("155.0"),
                "unit": "index",
                "provider": "BCA",
            },
            {
                "jurisdiction": "MY",
                "series_name": "Concrete Index",
                "category": "material",
                "period": "2024-Q1",
                "value": Decimal("160.0"),
                "unit": "index",
                "provider": "BCA",
            },
        ]

        for payload in payloads:
            await costs.upsert_cost_index(session, payload)
        await session.commit()

        result = await costs.get_latest_cost_index(
            session,
            series_name="Concrete Index",
            jurisdiction="SG",
            provider="BCA",
        )

        assert result is not None
        assert result.jurisdiction == "SG"
        assert result.period == "2024-Q2"
        assert result.value == Decimal("155.0")

    @pytest.mark.asyncio
    async def test_get_latest_provider_filter_excludes_non_matching(session) -> None:
        """Test get_latest provider filter excludes providers not matching."""
        payloads = [
            {
                "jurisdiction": "SG",
                "series_name": "Index",
                "category": "material",
                "period": "2024-Q1",
                "value": Decimal("100.0"),
                "unit": "index",
                "provider": "BCA",
            },
            {
                "jurisdiction": "SG",
                "series_name": "Index",
                "category": "material",
                "period": "2024-Q2",
                "value": Decimal("110.0"),
                "unit": "index",
                "provider": "internal",
            },
        ]

        for payload in payloads:
            await costs.upsert_cost_index(session, payload)
        await session.commit()

        result = await costs.get_latest_cost_index(
            session, series_name="Index", provider="BCA"
        )

        assert result is not None
        assert result.provider == "BCA"
        assert result.period == "2024-Q1"


class TestAddCostCatalogItem:
    """Tests for add_cost_catalog_item function."""

    @pytest.mark.asyncio
    async def test_add_catalog_item_creates_entry(self, session: AsyncSession) -> None:
        """Test add_cost_catalog_item creates new catalog entry."""
        payload = {
            "jurisdiction": "SG",
            "catalog_name": "BCA Cost Index",
            "category": "structural",
            "item_code": "STR001",
            "description": "Reinforced concrete beams",
            "unit": "m3",
            "unit_cost": Decimal("150.50"),
            "currency": "SGD",
        }

        result = await costs.add_cost_catalog_item(session, payload)
        await session.commit()

        assert result.id is not None
        assert result.catalog_name == "BCA Cost Index"
        assert result.item_code == "STR001"
        assert result.category == "structural"
        assert result.description == "Reinforced concrete beams"
        assert result.unit == "m3"
        assert result.unit_cost == Decimal("150.50")

    @pytest.mark.asyncio
    async def test_add_catalog_item_with_all_fields(
        self, session: AsyncSession
    ) -> None:
        """Test add_cost_catalog_item with all optional fields."""
        from datetime import date

        payload = {
            "jurisdiction": "SG",
            "catalog_name": "Updated Catalog",
            "category": "mechanical",
            "item_code": "MEC002",
            "description": "HVAC system installation",
            "unit": "lump sum",
            "unit_cost": Decimal("5000.00"),
            "currency": "SGD",
            "effective_date": date(2024, 1, 1),
            "item_metadata": {"supplier": "ABC Corp", "warranty_months": 24},
            "source": "vendor_quote",
        }

        result = await costs.add_cost_catalog_item(session, payload)
        await session.commit()

        assert result.id is not None
        assert result.catalog_name == "Updated Catalog"
        assert result.item_code == "MEC002"
        assert result.category == "mechanical"
        assert result.unit_cost == Decimal("5000.00")
        assert result.effective_date == date(2024, 1, 1)
        assert result.item_metadata == {"supplier": "ABC Corp", "warranty_months": 24}
        assert result.source == "vendor_quote"

    @pytest.mark.asyncio
    async def test_add_catalog_item_with_minimal_fields(
        self, session: AsyncSession
    ) -> None:
        """Test add_cost_catalog_item with minimal required fields."""
        payload = {
            "jurisdiction": "SG",
            "catalog_name": "Minimal Catalog",
            "item_code": "MIN001",
        }

        result = await costs.add_cost_catalog_item(session, payload)
        await session.commit()

        assert result.id is not None
        assert result.catalog_name == "Minimal Catalog"
        assert result.item_code == "MIN001"

    @pytest.mark.asyncio
    async def test_add_multiple_catalog_items(self, session: AsyncSession) -> None:
        """Test adding multiple distinct catalog items."""
        payloads = [
            {
                "jurisdiction": "SG",
                "catalog_name": "Catalog A",
                "category": "A",
                "item_code": "A001",
                "unit_cost": Decimal("100.0"),
            },
            {
                "jurisdiction": "SG",
                "catalog_name": "Catalog A",
                "category": "B",
                "item_code": "A002",
                "unit_cost": Decimal("200.0"),
            },
            {
                "jurisdiction": "SG",
                "catalog_name": "Catalog B",
                "category": "A",
                "item_code": "B001",
                "unit_cost": Decimal("300.0"),
            },
        ]

        results = []
        for payload in payloads:
            result = await costs.add_cost_catalog_item(session, payload)
            results.append(result)

        await session.commit()

        assert len(results) == 3
        assert all(r.id is not None for r in results)
        assert results[0].item_code == "A001"
        assert results[1].item_code == "A002"
        assert results[2].item_code == "B001"


class TestListCostCatalog:
    """Tests for list_cost_catalog function."""

    @pytest.mark.asyncio
    async def test_list_catalog_returns_all_items(self, session: AsyncSession) -> None:
        """Test list_cost_catalog returns all items when no filters applied."""
        payloads = [
            {
                "jurisdiction": "SG",
                "catalog_name": "Catalog A",
                "category": "structural",
                "item_code": "ITEM001",
            },
            {
                "jurisdiction": "SG",
                "catalog_name": "Catalog B",
                "category": "mechanical",
                "item_code": "ITEM002",
            },
            {
                "jurisdiction": "SG",
                "catalog_name": "Catalog A",
                "category": "electrical",
                "item_code": "ITEM003",
            },
        ]

        for payload in payloads:
            await costs.add_cost_catalog_item(session, payload)
        await session.commit()

        results = await costs.list_cost_catalog(session)

        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_list_catalog_filters_by_catalog_name(
        self, session: AsyncSession
    ) -> None:
        """Test list_cost_catalog filters by catalog_name."""
        payloads = [
            {
                "jurisdiction": "SG",
                "catalog_name": "BCA Index",
                "category": "structural",
                "item_code": "STR001",
            },
            {
                "jurisdiction": "SG",
                "catalog_name": "BCA Index",
                "category": "mechanical",
                "item_code": "MEC001",
            },
            {
                "jurisdiction": "SG",
                "catalog_name": "Other Index",
                "category": "structural",
                "item_code": "STR002",
            },
        ]

        for payload in payloads:
            await costs.add_cost_catalog_item(session, payload)
        await session.commit()

        results = await costs.list_cost_catalog(session, catalog_name="BCA Index")

        assert len(results) == 2
        assert all(r.catalog_name == "BCA Index" for r in results)

    @pytest.mark.asyncio
    async def test_list_catalog_filters_by_category(
        self, session: AsyncSession
    ) -> None:
        """Test list_cost_catalog filters by category."""
        payloads = [
            {
                "jurisdiction": "SG",
                "catalog_name": "Catalog A",
                "category": "structural",
                "item_code": "STR001",
            },
            {
                "jurisdiction": "SG",
                "catalog_name": "Catalog A",
                "category": "mechanical",
                "item_code": "MEC001",
            },
            {
                "jurisdiction": "SG",
                "catalog_name": "Catalog B",
                "category": "structural",
                "item_code": "STR002",
            },
        ]

        for payload in payloads:
            await costs.add_cost_catalog_item(session, payload)
        await session.commit()

        results = await costs.list_cost_catalog(session, category="structural")

        assert len(results) == 2
        assert all(r.category == "structural" for r in results)

    @pytest.mark.asyncio
    async def test_list_catalog_filters_by_both_name_and_category(session) -> None:
        """Test list_cost_catalog with both catalog_name and category filters."""
        payloads = [
            {
                "jurisdiction": "SG",
                "catalog_name": "BCA Index",
                "category": "structural",
                "item_code": "STR001",
            },
            {
                "jurisdiction": "SG",
                "catalog_name": "BCA Index",
                "category": "mechanical",
                "item_code": "MEC001",
            },
            {
                "jurisdiction": "SG",
                "catalog_name": "Other Index",
                "category": "structural",
                "item_code": "STR002",
            },
        ]

        for payload in payloads:
            await costs.add_cost_catalog_item(session, payload)
        await session.commit()

        results = await costs.list_cost_catalog(
            session, catalog_name="BCA Index", category="structural"
        )

        assert len(results) == 1
        assert results[0].item_code == "STR001"
        assert results[0].catalog_name == "BCA Index"
        assert results[0].category == "structural"

    @pytest.mark.asyncio
    async def test_list_catalog_returns_empty_when_no_matches(
        self, session: AsyncSession
    ) -> None:
        """Test list_cost_catalog returns empty list when no items match filters."""
        results = await costs.list_cost_catalog(
            session, catalog_name="Nonexistent Catalog"
        )

        assert results == []

    @pytest.mark.asyncio
    async def test_list_catalog_returns_empty_when_no_items(
        self, session: AsyncSession
    ) -> None:
        """Test list_cost_catalog returns empty list when database is empty."""
        results = await costs.list_cost_catalog(session)

        assert results == []

    @pytest.mark.asyncio
    async def test_list_catalog_ordered_by_item_code(
        self, session: AsyncSession
    ) -> None:
        """Test list_cost_catalog returns items ordered by item_code."""
        payloads = [
            {
                "jurisdiction": "SG",
                "catalog_name": "Catalog",
                "item_code": "ZZZ",
            },
            {
                "jurisdiction": "SG",
                "catalog_name": "Catalog",
                "item_code": "AAA",
            },
            {
                "jurisdiction": "SG",
                "catalog_name": "Catalog",
                "item_code": "MMM",
            },
        ]

        for payload in payloads:
            await costs.add_cost_catalog_item(session, payload)
        await session.commit()

        results = await costs.list_cost_catalog(session)

        assert len(results) == 3
        assert results[0].item_code == "AAA"
        assert results[1].item_code == "MMM"
        assert results[2].item_code == "ZZZ"

    @pytest.mark.asyncio
    async def test_list_catalog_with_category_filter_empty(
        self, session: AsyncSession
    ) -> None:
        """Test list_cost_catalog with category filter returns empty when no matches."""
        payloads = [
            {
                "jurisdiction": "SG",
                "catalog_name": "Catalog",
                "category": "structural",
                "item_code": "STR001",
            },
        ]

        for payload in payloads:
            await costs.add_cost_catalog_item(session, payload)
        await session.commit()

        results = await costs.list_cost_catalog(session, category="nonexistent")

        assert results == []
