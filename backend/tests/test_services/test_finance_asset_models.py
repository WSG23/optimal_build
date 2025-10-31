"""Tests for asset-specific finance modeling."""

from __future__ import annotations

from decimal import Decimal


from app.services.finance.asset_models import (
    AREA_QUANT,
    CURRENCY_QUANT,
    MONTHS_QUANT,
    PAYBACK_QUANT,
    PERCENT_QUANT,
    RISK_PRIORITY,
    AssetFinanceBreakdown,
    AssetFinanceInput,
    _quantize_area,
    _quantize_currency,
    _quantize_duration,
    _quantize_percent,
    _to_decimal,
    build_asset_financials,
    serialise_breakdown,
    summarise_asset_financials,
)


class TestToDecimal:
    """Test _to_decimal conversion function."""

    def test_none_returns_none(self) -> None:
        """Test None input returns None."""
        assert _to_decimal(None) is None

    def test_decimal_passthrough(self) -> None:
        """Test Decimal input returns unchanged."""
        value = Decimal("123.45")
        assert _to_decimal(value) == value

    def test_int_conversion(self) -> None:
        """Test integer conversion."""
        assert _to_decimal(100) == Decimal("100")
        assert _to_decimal(0) == Decimal("0")
        assert _to_decimal(-50) == Decimal("-50")

    def test_float_conversion(self) -> None:
        """Test float conversion."""
        assert _to_decimal(123.45) == Decimal("123.45")
        assert _to_decimal(0.0) == Decimal("0")

    def test_string_conversion(self) -> None:
        """Test string conversion."""
        assert _to_decimal("123.45") == Decimal("123.45")
        assert _to_decimal("0") == Decimal("0")
        assert _to_decimal("-50.5") == Decimal("-50.5")

    def test_invalid_string_returns_none(self) -> None:
        """Test invalid string returns None."""
        assert _to_decimal("invalid") is None
        assert _to_decimal("") is None
        assert _to_decimal("abc123") is None


class TestQuantizeFunctions:
    """Test quantization helper functions."""

    def test_quantize_currency(self) -> None:
        """Test currency quantization to 2 decimal places."""
        assert _quantize_currency(None) is None
        assert _quantize_currency(Decimal("123.456")) == Decimal("123.46")
        assert _quantize_currency(Decimal("123.454")) == Decimal("123.45")
        assert _quantize_currency(Decimal("100")) == Decimal("100.00")

    def test_quantize_percent(self) -> None:
        """Test percent quantization to 4 decimal places."""
        assert _quantize_percent(None) is None
        assert _quantize_percent(Decimal("0.12345")) == Decimal("0.1235")
        assert _quantize_percent(Decimal("0.12344")) == Decimal("0.1234")
        assert _quantize_percent(Decimal("0.1")) == Decimal("0.1000")

    def test_quantize_area(self) -> None:
        """Test area quantization to 2 decimal places."""
        assert _quantize_area(None) is None
        assert _quantize_area(Decimal("123.456")) == Decimal("123.46")
        assert _quantize_area(Decimal("100")) == Decimal("100.00")

    def test_quantize_duration(self) -> None:
        """Test duration quantization to 1 decimal place."""
        assert _quantize_duration(None) is None
        assert _quantize_duration(Decimal("12.345")) == Decimal("12.3")
        assert _quantize_duration(Decimal("12.35")) == Decimal("12.4")
        assert _quantize_duration(Decimal("12")) == Decimal("12.0")


class TestAssetFinanceInput:
    """Test AssetFinanceInput dataclass."""

    def test_minimal_input(self) -> None:
        """Test creating minimal AssetFinanceInput."""
        input_data = AssetFinanceInput(asset_type="residential")
        assert input_data.asset_type == "residential"
        assert input_data.allocation_pct is None
        assert input_data.nia_sqm is None
        assert input_data.notes == ()

    def test_full_input(self) -> None:
        """Test creating full AssetFinanceInput."""
        input_data = AssetFinanceInput(
            asset_type="commercial",
            allocation_pct=Decimal("0.50"),
            nia_sqm=Decimal("1000.00"),
            rent_psm_month=Decimal("50.00"),
            stabilised_vacancy_pct=Decimal("0.05"),
            opex_pct_of_rent=Decimal("0.30"),
            estimated_revenue_sgd=Decimal("600000"),
            estimated_capex_sgd=Decimal("2000000"),
            absorption_months=Decimal("18.0"),
            risk_level="moderate",
            heritage_premium_pct=Decimal("0.10"),
            notes=("Note 1", "Note 2"),
        )
        assert input_data.asset_type == "commercial"
        assert input_data.allocation_pct == Decimal("0.50")
        assert input_data.nia_sqm == Decimal("1000.00")
        assert input_data.rent_psm_month == Decimal("50.00")
        assert input_data.stabilised_vacancy_pct == Decimal("0.05")
        assert input_data.opex_pct_of_rent == Decimal("0.30")
        assert input_data.estimated_revenue_sgd == Decimal("600000")
        assert input_data.estimated_capex_sgd == Decimal("2000000")
        assert input_data.absorption_months == Decimal("18.0")
        assert input_data.risk_level == "moderate"
        assert input_data.heritage_premium_pct == Decimal("0.10")
        assert input_data.notes == ("Note 1", "Note 2")


class TestAssetFinanceBreakdown:
    """Test AssetFinanceBreakdown dataclass."""

    def test_minimal_breakdown(self) -> None:
        """Test creating minimal breakdown."""
        breakdown = AssetFinanceBreakdown(
            asset_type="residential",
            allocation_pct=Decimal("0.50"),
            nia_sqm=Decimal("1000"),
            capex_sgd=Decimal("2000000"),
            annual_revenue_sgd=Decimal("600000"),
        )
        assert breakdown.asset_type == "residential"
        assert breakdown.allocation_pct == Decimal("0.50")
        assert breakdown.nia_sqm == Decimal("1000")
        assert breakdown.estimated_capex_sgd == Decimal("2000000")
        assert breakdown.annual_revenue_sgd == Decimal("600000")

    def test_full_breakdown(self) -> None:
        """Test creating full breakdown."""
        breakdown = AssetFinanceBreakdown(
            asset_type="commercial",
            allocation_pct=Decimal("0.50"),
            nia_sqm=Decimal("1000.00"),
            capex_sgd=Decimal("2000000.00"),
            annual_revenue_sgd=Decimal("600000.00"),
            annual_opex_sgd=Decimal("180000.00"),
            annual_noi_sgd=Decimal("420000.00"),
            stabilised_yield_pct=Decimal("0.21"),
            absorption_months=Decimal("18.0"),
            payback_years=Decimal("4.76"),
            risk_level="moderate",
            risk_priority=3,
            notes=("Note 1",),
        )
        assert breakdown.asset_type == "commercial"
        assert breakdown.annual_opex_sgd == Decimal("180000.00")
        assert breakdown.annual_noi_sgd == Decimal("420000.00")
        assert breakdown.stabilised_yield_pct == Decimal("0.21")
        assert breakdown.absorption_months == Decimal("18.0")
        assert breakdown.payback_years == Decimal("4.76")
        assert breakdown.risk_level == "moderate"
        assert breakdown.risk_priority == 3
        assert breakdown.notes == ("Note 1",)


class TestRiskPriority:
    """Test RISK_PRIORITY constant."""

    def test_risk_priority_values(self) -> None:
        """Test risk priority mapping."""
        assert RISK_PRIORITY["low"] == 1
        assert RISK_PRIORITY["balanced"] == 2
        assert RISK_PRIORITY["moderate"] == 3
        assert RISK_PRIORITY["elevated"] == 4


class TestQuantConstants:
    """Test quantization constants."""

    def test_currency_quant(self) -> None:
        """Test currency quantization constant."""
        assert CURRENCY_QUANT == Decimal("0.01")

    def test_percent_quant(self) -> None:
        """Test percent quantization constant."""
        assert PERCENT_QUANT == Decimal("0.0001")

    def test_area_quant(self) -> None:
        """Test area quantization constant."""
        assert AREA_QUANT == Decimal("0.01")

    def test_months_quant(self) -> None:
        """Test months quantization constant."""
        assert MONTHS_QUANT == Decimal("0.1")

    def test_payback_quant(self) -> None:
        """Test payback quantization constant."""
        assert PAYBACK_QUANT == Decimal("0.01")


class TestBuildAssetFinancials:
    """Test build_asset_financials function."""

    def test_build_simple_asset(self) -> None:
        """Test building simple asset financials."""
        input_data = AssetFinanceInput(
            asset_type="residential",
            allocation_pct=Decimal("0.50"),
            nia_sqm=Decimal("1000.00"),
            rent_psm_month=Decimal("50.00"),
            stabilised_vacancy_pct=Decimal("0.05"),
            opex_pct_of_rent=Decimal("0.30"),
            estimated_capex_sgd=Decimal("2000000"),
            absorption_months=Decimal("12.0"),
            risk_level="low",
        )

        breakdown = build_asset_financials(input_data)

        assert breakdown.asset_type == "residential"
        assert breakdown.allocation_pct == Decimal("0.50")
        assert breakdown.nia_sqm == Decimal("1000.00")
        assert breakdown.estimated_capex_sgd == Decimal("2000000.00")
        # Annual revenue = 1000 * 50 * 12 = 600,000
        assert breakdown.annual_revenue_sgd == Decimal("600000.00")
        # Vacancy loss = 600000 * 0.05 = 30,000
        # Effective revenue = 600000 - 30000 = 570,000
        # Opex = 570000 * 0.30 = 171,000
        # NOI = 570000 - 171000 = 399,000
        assert breakdown.annual_noi_sgd == Decimal("399000.00")

    def test_build_asset_with_estimated_revenue(self) -> None:
        """Test building asset with pre-calculated revenue."""
        input_data = AssetFinanceInput(
            asset_type="commercial",
            allocation_pct=Decimal("0.30"),
            nia_sqm=Decimal("500.00"),
            estimated_revenue_sgd=Decimal("400000"),
            estimated_capex_sgd=Decimal("1500000"),
            opex_pct_of_rent=Decimal("0.25"),
            risk_level="moderate",
        )

        breakdown = build_asset_financials(input_data)

        assert breakdown.annual_revenue_sgd == Decimal("400000.00")
        # Opex = 400000 * 0.25 = 100,000
        # NOI = 400000 - 100000 = 300,000
        assert breakdown.annual_noi_sgd == Decimal("300000.00")


class TestSummariseAssetFinancials:
    """Test summarise_asset_financials function."""

    def test_summarise_single_asset(self) -> None:
        """Test summarizing single asset."""
        breakdown = AssetFinanceBreakdown(
            asset_type="residential",
            allocation_pct=Decimal("1.00"),
            nia_sqm=Decimal("1000.00"),
            capex_sgd=Decimal("2000000.00"),
            annual_revenue_sgd=Decimal("600000.00"),
            annual_opex_sgd=Decimal("180000.00"),
            annual_noi_sgd=Decimal("420000.00"),
        )

        summary = summarise_asset_financials([breakdown], project_name="Test Project")

        assert summary.project_name == "Test Project"
        assert summary.total_nia_sqm == Decimal("1000.00")
        assert summary.total_capex_sgd == Decimal("2000000.00")
        assert summary.total_annual_revenue_sgd == Decimal("600000.00")
        assert summary.total_annual_noi_sgd == Decimal("420000.00")
        assert summary.blended_yield_pct == Decimal("0.2100")  # 420000 / 2000000

    def test_summarise_multiple_assets(self) -> None:
        """Test summarizing multiple assets."""
        breakdown1 = AssetFinanceBreakdown(
            asset_type="residential",
            allocation_pct=Decimal("0.50"),
            nia_sqm=Decimal("1000.00"),
            capex_sgd=Decimal("2000000.00"),
            annual_revenue_sgd=Decimal("600000.00"),
            annual_noi_sgd=Decimal("420000.00"),
        )
        breakdown2 = AssetFinanceBreakdown(
            asset_type="commercial",
            allocation_pct=Decimal("0.50"),
            nia_sqm=Decimal("500.00"),
            capex_sgd=Decimal("1500000.00"),
            annual_revenue_sgd=Decimal("400000.00"),
            annual_noi_sgd=Decimal("300000.00"),
        )

        summary = summarise_asset_financials(
            [breakdown1, breakdown2], project_name="Mixed Use"
        )

        assert summary.total_nia_sqm == Decimal("1500.00")
        assert summary.total_capex_sgd == Decimal("3500000.00")
        assert summary.total_annual_revenue_sgd == Decimal("1000000.00")
        assert summary.total_annual_noi_sgd == Decimal("720000.00")


class TestSerialiseBreakdown:
    """Test serialise_breakdown function."""

    def test_serialise_basic_breakdown(self) -> None:
        """Test serializing basic breakdown."""
        breakdown = AssetFinanceBreakdown(
            asset_type="residential",
            allocation_pct=Decimal("0.50"),
            nia_sqm=Decimal("1000.00"),
            capex_sgd=Decimal("2000000.00"),
            annual_revenue_sgd=Decimal("600000.00"),
        )

        schema = serialise_breakdown(breakdown)

        assert schema.asset_type == "residential"
        assert schema.allocation_pct == "0.50"
        assert schema.nia_sqm == "1000.00"
        assert schema.estimated_capex_sgd == "2000000.00"
        assert schema.annual_revenue_sgd == "600000.00"

    def test_serialise_full_breakdown(self) -> None:
        """Test serializing full breakdown with all fields."""
        breakdown = AssetFinanceBreakdown(
            asset_type="commercial",
            allocation_pct=Decimal("0.30"),
            nia_sqm=Decimal("500.00"),
            capex_sgd=Decimal("1500000.00"),
            annual_revenue_sgd=Decimal("400000.00"),
            annual_opex_sgd=Decimal("100000.00"),
            annual_noi_sgd=Decimal("300000.00"),
            stabilised_yield_pct=Decimal("0.20"),
            absorption_months=Decimal("18.0"),
            payback_years=Decimal("5.0"),
            risk_level="moderate",
            risk_priority=3,
            notes=("Note 1", "Note 2"),
        )

        schema = serialise_breakdown(breakdown)

        assert schema.asset_type == "commercial"
        assert schema.annual_opex_sgd == "100000.00"
        assert schema.annual_noi_sgd == "300000.00"
        assert schema.stabilised_yield_pct == "0.2000"
        assert schema.risk_level == "moderate"
        assert len(schema.notes) == 2
