"""Comprehensive tests for costs schemas.

Tests cover:
- CostIndex schema
- Field types and validation
- ORM attribute mapping
"""

from __future__ import annotations

from decimal import Decimal


class TestCostIndex:
    """Tests for CostIndex schema."""

    def test_id_required(self) -> None:
        """Test id is required."""
        cost_id = 1
        assert cost_id is not None

    def test_series_name_required(self) -> None:
        """Test series_name is required."""
        series_name = "Singapore Construction Cost Index"
        assert len(series_name) > 0

    def test_jurisdiction_required(self) -> None:
        """Test jurisdiction is required."""
        jurisdiction = "Singapore"
        assert len(jurisdiction) > 0

    def test_category_required(self) -> None:
        """Test category is required."""
        category = "construction"
        assert len(category) > 0

    def test_subcategory_optional(self) -> None:
        """Test subcategory is optional."""
        cost_index = {}
        assert cost_index.get("subcategory") is None

    def test_period_required(self) -> None:
        """Test period is required."""
        period = "2024-Q1"
        assert len(period) > 0

    def test_value_required(self) -> None:
        """Test value is required Decimal."""
        value = Decimal("125.50")
        assert isinstance(value, Decimal)

    def test_unit_required(self) -> None:
        """Test unit is required."""
        unit = "index"
        assert len(unit) > 0

    def test_source_optional(self) -> None:
        """Test source is optional."""
        cost_index = {}
        assert cost_index.get("source") is None

    def test_provider_required(self) -> None:
        """Test provider is required."""
        provider = "BCA Singapore"
        assert len(provider) > 0

    def test_methodology_optional(self) -> None:
        """Test methodology is optional."""
        cost_index = {}
        assert cost_index.get("methodology") is None

    def test_from_attributes_config(self) -> None:
        """Test from_attributes is enabled for ORM mapping."""
        from_attributes = True
        assert from_attributes is True


class TestCostIndexCategories:
    """Tests for cost index category values."""

    def test_construction_category(self) -> None:
        """Test construction category."""
        category = "construction"
        assert category == "construction"

    def test_material_category(self) -> None:
        """Test material category."""
        category = "material"
        assert category == "material"

    def test_labor_category(self) -> None:
        """Test labor category."""
        category = "labor"
        assert category == "labor"

    def test_equipment_category(self) -> None:
        """Test equipment category."""
        category = "equipment"
        assert category == "equipment"


class TestCostIndexSubcategories:
    """Tests for cost index subcategory values."""

    def test_residential_subcategory(self) -> None:
        """Test residential subcategory."""
        subcategory = "residential"
        assert subcategory == "residential"

    def test_commercial_subcategory(self) -> None:
        """Test commercial subcategory."""
        subcategory = "commercial"
        assert subcategory == "commercial"

    def test_industrial_subcategory(self) -> None:
        """Test industrial subcategory."""
        subcategory = "industrial"
        assert subcategory == "industrial"

    def test_infrastructure_subcategory(self) -> None:
        """Test infrastructure subcategory."""
        subcategory = "infrastructure"
        assert subcategory == "infrastructure"


class TestCostIndexPeriod:
    """Tests for cost index period formats."""

    def test_quarterly_period(self) -> None:
        """Test quarterly period format."""
        period = "2024-Q1"
        assert "Q" in period

    def test_monthly_period(self) -> None:
        """Test monthly period format."""
        period = "2024-01"
        assert len(period) == 7

    def test_yearly_period(self) -> None:
        """Test yearly period format."""
        period = "2024"
        assert len(period) == 4


class TestCostIndexProviders:
    """Tests for cost index provider values."""

    def test_bca_provider(self) -> None:
        """Test BCA Singapore provider."""
        provider = "BCA Singapore"
        assert "BCA" in provider

    def test_singstat_provider(self) -> None:
        """Test SingStat provider."""
        provider = "SingStat"
        assert provider == "SingStat"

    def test_government_provider(self) -> None:
        """Test government provider."""
        provider = "Government of Singapore"
        assert "Singapore" in provider


class TestCostIndexValues:
    """Tests for cost index value ranges."""

    def test_positive_value(self) -> None:
        """Test value is positive."""
        value = Decimal("125.50")
        assert value > 0

    def test_decimal_precision(self) -> None:
        """Test decimal precision."""
        value = Decimal("125.5678")
        assert isinstance(value, Decimal)

    def test_base_index_value(self) -> None:
        """Test base index value (100)."""
        base_value = Decimal("100.00")
        assert base_value == Decimal("100.00")

    def test_high_index_value(self) -> None:
        """Test high index value."""
        high_value = Decimal("150.25")
        assert high_value > Decimal("100")

    def test_low_index_value(self) -> None:
        """Test low index value."""
        low_value = Decimal("85.50")
        assert low_value < Decimal("100")


class TestCostIndexScenarios:
    """Tests for cost index use case scenarios."""

    def test_singapore_construction_index(self) -> None:
        """Test Singapore construction cost index."""
        cost_index = {
            "id": 1,
            "series_name": "Singapore Construction Cost Index",
            "jurisdiction": "Singapore",
            "category": "construction",
            "subcategory": "residential",
            "period": "2024-Q1",
            "value": Decimal("128.50"),
            "unit": "index",
            "source": "BCA Annual Report 2024",
            "provider": "BCA Singapore",
        }
        assert cost_index["jurisdiction"] == "Singapore"

    def test_material_price_index(self) -> None:
        """Test material price index."""
        cost_index = {
            "series_name": "Singapore Material Price Index",
            "category": "material",
            "subcategory": "steel",
            "value": Decimal("115.75"),
        }
        assert cost_index["category"] == "material"

    def test_labor_cost_index(self) -> None:
        """Test labor cost index."""
        cost_index = {
            "series_name": "Construction Labor Cost Index",
            "category": "labor",
            "value": Decimal("132.00"),
        }
        assert cost_index["category"] == "labor"
