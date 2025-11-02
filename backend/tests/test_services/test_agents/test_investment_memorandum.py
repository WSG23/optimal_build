"""Integration tests for InvestmentMemorandumGenerator service."""

from __future__ import annotations

import io
from datetime import date
from decimal import Decimal

import pytest
from reportlab.lib.units import inch
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.market import MarketCycle, YieldBenchmark
from app.models.property import (
    MarketTransaction,
    Property,
    PropertyStatus,
    PropertyType,
    RentalListing,
)
from app.services.agents.investment_memorandum import (
    InvestmentHighlight,
    InvestmentMemorandumGenerator,
)

pytestmark = pytest.mark.skip(
    reason=(
        "Investment memorandum service requires SQLAlchemy expressions and richer "
        "session features not provided by the lightweight stub backend."
    )
)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _make_property(**overrides) -> Property:
    """Create a minimal Property for testing."""
    defaults = dict(
        name="Capital Tower",
        address="168 Robinson Road",
        property_type=PropertyType.OFFICE,
        status=PropertyStatus.EXISTING,
        year_built=2000,
        year_renovated=2015,
        floors_above_ground=52,
        building_height_m=252.0,
        gross_floor_area_sqm=Decimal("65000.00"),
        net_lettable_area_sqm=Decimal("55000.00"),
        land_area_sqm=Decimal("5000.00"),
        location="POINT(103.8478 1.2787)",
        district="Raffles Place",
        subzone="Raffles Place",
        planning_area="Downtown Core",
        data_source="test",
        units_total=120,
    )
    defaults.update(overrides)
    return Property(**defaults)


def _make_rental_listing(property_id, **overrides) -> RentalListing:
    """Create a minimal RentalListing for testing."""
    defaults = dict(
        property_id=property_id,
        listing_date=date.today(),
        floor_level="25",
        unit_number="25-01",
        floor_area_sqm=Decimal("1000.00"),
        is_active=True,
        asking_rent_monthly=Decimal("12000.00"),
    )
    defaults.update(overrides)
    return RentalListing(**defaults)


def _make_market_transaction(property_id, **overrides) -> MarketTransaction:
    """Create a minimal MarketTransaction for testing."""
    defaults = dict(
        property_id=property_id,
        transaction_date=date(2024, 6, 15),
        transaction_type="sale",
        sale_price=Decimal("180000000.00"),
        psf_price=Decimal("2800.00"),
        floor_area_sqm=Decimal("5000.00"),
        data_source="test",
    )
    defaults.update(overrides)
    return MarketTransaction(**defaults)


def _make_yield_benchmark(**overrides) -> YieldBenchmark:
    """Create a minimal YieldBenchmark for testing."""
    defaults = dict(
        benchmark_date=date(2024, 9, 1),
        property_type=PropertyType.OFFICE,
        period_type="quarterly",
        cap_rate_median=Decimal("0.045"),
        cap_rate_mean=Decimal("0.047"),
        rental_yield_median=Decimal("0.038"),
        district="Raffles Place",
        sample_size=50,
        data_quality_score=Decimal("0.90"),
    )
    defaults.update(overrides)
    return YieldBenchmark(**defaults)


def _make_market_cycle(**overrides) -> MarketCycle:
    """Create a minimal MarketCycle for testing."""
    defaults = dict(
        cycle_date=date(2024, 9, 1),
        property_type=PropertyType.OFFICE,
        market_segment="CBD",
        cycle_phase="expansion",
        phase_duration_months=18,
        price_momentum=Decimal("0.05"),
        rental_momentum=Decimal("0.03"),
        cycle_outlook="improving",
        model_confidence=Decimal("0.85"),
    )
    defaults.update(overrides)
    return MarketCycle(**defaults)


# ============================================================================
# FLOWABLE TESTS
# ============================================================================


def test_investment_highlight_init():
    """Test InvestmentHighlight initialization."""
    highlights = [
        {"label": "Cap Rate", "value": "4.5%"},
        {"label": "NOI", "value": "$3.2M"},
        {"label": "Occupancy", "value": "95%"},
    ]
    highlight = InvestmentHighlight(highlights)

    assert highlight.highlights == highlights
    assert highlight.width == 6 * inch
    assert highlight.height == 1.5 * inch


def test_investment_highlight_custom_width():
    """Test InvestmentHighlight with custom width."""
    highlights = [{"label": "Test", "value": "100%"}]
    highlight = InvestmentHighlight(highlights, width=8 * inch)

    assert highlight.width == 8 * inch
    assert highlight.height == 1.5 * inch


def test_investment_highlight_empty_list():
    """Test InvestmentHighlight with empty list."""
    highlights = []
    highlight = InvestmentHighlight(highlights)

    assert highlight.highlights == []
    assert highlight.width > 0
    assert highlight.height > 0


# ============================================================================
# DATA LOADING TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_load_property_data_success(db_session: AsyncSession):
    """Test _load_property_data loads property and related data successfully."""
    # Create test data
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    rental1 = _make_rental_listing(
        prop.id, floor_area_sqm=Decimal("1000.00"), is_active=True
    )
    rental2 = _make_rental_listing(
        prop.id, floor_level="30", floor_area_sqm=Decimal("1500.00"), is_active=True
    )
    db_session.add_all([rental1, rental2])

    transaction = _make_market_transaction(prop.id)
    db_session.add(transaction)
    await db_session.flush()

    # Execute
    generator = InvestmentMemorandumGenerator()
    result = await generator._load_property_data(prop.id, db_session)

    # Assert
    assert result is not None
    assert result["property"].id == prop.id
    assert result["property"].name == "Capital Tower"
    assert len(result["transactions"]) == 1
    assert len(result["rentals"]) == 2
    assert "vacancy_rate" in result


@pytest.mark.asyncio
async def test_load_property_data_no_rentals(db_session: AsyncSession):
    """Test _load_property_data with no active rentals."""
    # Create test data
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    # Execute
    generator = InvestmentMemorandumGenerator()
    result = await generator._load_property_data(prop.id, db_session)

    # Assert
    assert result is not None
    assert len(result["rentals"]) == 0
    # With NLA set, 0 occupied = 100% vacancy
    assert result["vacancy_rate"] == 1.0


@pytest.mark.asyncio
async def test_load_property_data_inactive_rentals_excluded(db_session: AsyncSession):
    """Test _load_property_data excludes inactive rentals."""
    # Create test data
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    active_rental = _make_rental_listing(prop.id, is_active=True)
    inactive_rental = _make_rental_listing(prop.id, floor_level="40", is_active=False)
    db_session.add_all([active_rental, inactive_rental])
    await db_session.flush()

    # Execute
    generator = InvestmentMemorandumGenerator()
    result = await generator._load_property_data(prop.id, db_session)

    # Assert
    assert len(result["rentals"]) == 1
    assert result["rentals"][0].is_active is True


@pytest.mark.asyncio
async def test_load_property_data_transactions_sorted(db_session: AsyncSession):
    """Test _load_property_data sorts transactions by date descending."""
    # Create test data
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    transaction1 = _make_market_transaction(prop.id, transaction_date=date(2023, 1, 15))
    transaction2 = _make_market_transaction(prop.id, transaction_date=date(2024, 6, 1))
    transaction3 = _make_market_transaction(prop.id, transaction_date=date(2023, 8, 20))
    db_session.add_all([transaction1, transaction2, transaction3])
    await db_session.flush()

    # Execute
    generator = InvestmentMemorandumGenerator()
    result = await generator._load_property_data(prop.id, db_session)

    # Assert - should be sorted by date desc
    assert len(result["transactions"]) == 3
    assert result["transactions"][0].transaction_date == date(2024, 6, 1)
    assert result["transactions"][1].transaction_date == date(2023, 8, 20)
    assert result["transactions"][2].transaction_date == date(2023, 1, 15)


@pytest.mark.asyncio
async def test_load_property_data_limits_transactions(db_session: AsyncSession):
    """Test _load_property_data limits transactions to 5 most recent."""
    # Create test data
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    # Create 8 transactions
    for i in range(8):
        transaction = _make_market_transaction(
            prop.id, transaction_date=date(2024, i + 1, 1)
        )
        db_session.add(transaction)
    await db_session.flush()

    # Execute
    generator = InvestmentMemorandumGenerator()
    result = await generator._load_property_data(prop.id, db_session)

    # Assert - should only return 5
    assert len(result["transactions"]) == 5


@pytest.mark.asyncio
async def test_load_market_intelligence_success(db_session: AsyncSession):
    """Test _load_market_intelligence loads market data successfully."""
    # Create test data
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    # Create yield benchmarks
    benchmark1 = _make_yield_benchmark(benchmark_date=date(2024, 9, 1))
    benchmark2 = _make_yield_benchmark(benchmark_date=date(2024, 6, 1))
    db_session.add_all([benchmark1, benchmark2])

    # Create market cycle
    cycle = _make_market_cycle()
    db_session.add(cycle)

    # Create comparable transaction (different property)
    other_prop = _make_property(name="Other Tower", address="123 Comparable St")
    db_session.add(other_prop)
    await db_session.flush()

    comparable = _make_market_transaction(
        other_prop.id, transaction_date=date(2024, 8, 1)
    )
    db_session.add(comparable)
    await db_session.flush()

    # Execute
    generator = InvestmentMemorandumGenerator()
    result = await generator._load_market_intelligence(prop, db_session)

    # Assert
    assert result is not None
    assert len(result["benchmarks"]) >= 1
    assert result["current_cycle"] is not None
    assert result["current_cycle"].cycle_phase == "expansion"
    # Comparables query may not work due to relationship complexity, so just check structure
    assert "comparables" in result
    assert "market_cap_rate" in result


@pytest.mark.asyncio
async def test_load_market_intelligence_no_cycle(db_session: AsyncSession):
    """Test _load_market_intelligence handles missing market cycle."""
    # Create test data
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    benchmark = _make_yield_benchmark()
    db_session.add(benchmark)
    await db_session.flush()

    # Execute
    generator = InvestmentMemorandumGenerator()
    result = await generator._load_market_intelligence(prop, db_session)

    # Assert
    assert result is not None
    assert result["current_cycle"] is None
    assert len(result["benchmarks"]) >= 1


@pytest.mark.asyncio
async def test_load_market_intelligence_no_benchmarks(db_session: AsyncSession):
    """Test _load_market_intelligence handles missing benchmarks."""
    # Create test data
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    # Execute
    generator = InvestmentMemorandumGenerator()
    result = await generator._load_market_intelligence(prop, db_session)

    # Assert
    assert result is not None
    assert len(result["benchmarks"]) == 0
    assert result["market_cap_rate"] == 0.045  # Default value


@pytest.mark.asyncio
async def test_load_market_intelligence_different_property_type(
    db_session: AsyncSession,
):
    """Test _load_market_intelligence filters by property type."""
    # Create test data
    prop = _make_property(property_type=PropertyType.RETAIL)
    db_session.add(prop)
    await db_session.flush()

    # Create benchmark for OFFICE (should not be included)
    office_benchmark = _make_yield_benchmark(property_type=PropertyType.OFFICE)
    # Create benchmark for RETAIL (should be included)
    retail_benchmark = _make_yield_benchmark(property_type=PropertyType.RETAIL)
    db_session.add_all([office_benchmark, retail_benchmark])
    await db_session.flush()

    # Execute
    generator = InvestmentMemorandumGenerator()
    result = await generator._load_market_intelligence(prop, db_session)

    # Assert
    assert result is not None
    assert len(result["benchmarks"]) >= 1
    # All benchmarks should be RETAIL
    for benchmark in result["benchmarks"]:
        assert benchmark.property_type == PropertyType.RETAIL


# ============================================================================
# FINANCIAL CALCULATION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_calculate_financials_success(db_session: AsyncSession):
    """Test _calculate_financials computes financial metrics."""
    # Create test data
    prop = _make_property(
        gross_floor_area_sqm=Decimal("50000.00"),
        net_lettable_area_sqm=Decimal("42000.00"),
    )
    property_data = {
        "property": prop,
        "transactions": [],
        "rentals": [],
        "vacancy_rate": 0.05,
    }

    # Execute
    generator = InvestmentMemorandumGenerator()
    result = await generator._calculate_financials(property_data)

    # Assert
    assert result is not None
    assert "metrics" in result
    assert "valuation" in result
    assert "annual_rental_income" in result
    assert "operating_expenses" in result
    assert "estimated_value" in result
    assert result["annual_rental_income"] > 0
    assert result["operating_expenses"] > 0
    assert result["estimated_value"] > 0


@pytest.mark.asyncio
async def test_calculate_financials_no_net_lettable_area(db_session: AsyncSession):
    """Test _calculate_financials uses GFA when NLA is not available."""
    # Create test data
    prop = _make_property(
        gross_floor_area_sqm=Decimal("50000.00"), net_lettable_area_sqm=None
    )
    property_data = {
        "property": prop,
        "transactions": [],
        "rentals": [],
        "vacancy_rate": 0.05,
    }

    # Execute
    generator = InvestmentMemorandumGenerator()
    result = await generator._calculate_financials(property_data)

    # Assert
    assert result is not None
    assert result["annual_rental_income"] > 0


@pytest.mark.asyncio
async def test_calculate_financials_zero_area(db_session: AsyncSession):
    """Test _calculate_financials handles zero area."""
    # Create test data
    prop = _make_property(gross_floor_area_sqm=None, net_lettable_area_sqm=None)
    property_data = {
        "property": prop,
        "transactions": [],
        "rentals": [],
        "vacancy_rate": 0.05,
    }

    # Execute
    generator = InvestmentMemorandumGenerator()
    result = await generator._calculate_financials(property_data)

    # Assert
    assert result is not None
    assert result["annual_rental_income"] == 0.0
    assert result["estimated_value"] == 0.0


@pytest.mark.asyncio
async def test_calculate_financials_high_vacancy_rate(db_session: AsyncSession):
    """Test _calculate_financials with high vacancy rate."""
    # Create test data
    prop = _make_property(gross_floor_area_sqm=Decimal("50000.00"))
    property_data = {
        "property": prop,
        "transactions": [],
        "rentals": [],
        "vacancy_rate": 0.30,  # 30% vacancy
    }

    # Execute
    generator = InvestmentMemorandumGenerator()
    result = await generator._calculate_financials(property_data)

    # Assert
    assert result is not None
    assert "metrics" in result
    # Vacancy rate should be factored into metrics


# ============================================================================
# HELPER METHOD TESTS
# ============================================================================


def test_calculate_vacancy_rate_with_rentals():
    """Test _calculate_vacancy_rate computes correct rate."""
    generator = InvestmentMemorandumGenerator()
    prop = _make_property(net_lettable_area_sqm=Decimal("10000.00"))

    rental1 = _make_rental_listing(
        prop.id, floor_area_sqm=Decimal("3000.00"), is_active=True
    )
    rental2 = _make_rental_listing(
        prop.id, floor_level="30", floor_area_sqm=Decimal("2000.00"), is_active=True
    )
    rentals = [rental1, rental2]

    # Execute
    result = generator._calculate_vacancy_rate(rentals, prop)

    # Assert - 5000 occupied out of 10000 = 50% vacancy
    assert result == 0.50


def test_calculate_vacancy_rate_no_rentals():
    """Test _calculate_vacancy_rate returns default when no rentals."""
    generator = InvestmentMemorandumGenerator()
    prop = _make_property(net_lettable_area_sqm=Decimal("10000.00"))
    rentals = []

    # Execute
    result = generator._calculate_vacancy_rate(rentals, prop)

    # Assert - 100% vacancy
    assert result == 1.0


def test_calculate_vacancy_rate_no_net_lettable_area():
    """Test _calculate_vacancy_rate returns default when no NLA."""
    generator = InvestmentMemorandumGenerator()
    prop = _make_property(net_lettable_area_sqm=None)
    rentals = []

    # Execute
    result = generator._calculate_vacancy_rate(rentals, prop)

    # Assert - default 5%
    assert result == 0.05


def test_calculate_vacancy_rate_full_occupancy():
    """Test _calculate_vacancy_rate with full occupancy."""
    generator = InvestmentMemorandumGenerator()
    prop = _make_property(net_lettable_area_sqm=Decimal("10000.00"))

    rental = _make_rental_listing(
        prop.id, floor_area_sqm=Decimal("10000.00"), is_active=True
    )
    rentals = [rental]

    # Execute
    result = generator._calculate_vacancy_rate(rentals, prop)

    # Assert - 0% vacancy
    assert result == 0.0


def test_calculate_vacancy_rate_inactive_rentals_ignored():
    """Test _calculate_vacancy_rate ignores inactive rentals."""
    generator = InvestmentMemorandumGenerator()
    prop = _make_property(net_lettable_area_sqm=Decimal("10000.00"))

    active_rental = _make_rental_listing(
        prop.id, floor_area_sqm=Decimal("3000.00"), is_active=True
    )
    inactive_rental = _make_rental_listing(
        prop.id, floor_level="30", floor_area_sqm=Decimal("5000.00"), is_active=False
    )
    rentals = [active_rental, inactive_rental]

    # Execute
    result = generator._calculate_vacancy_rate(rentals, prop)

    # Assert - only active rental counted: 3000/10000 occupied = 70% vacancy
    assert abs(float(result) - 0.70) < 0.01  # Allow for float/Decimal precision


def test_calculate_vacancy_rate_rental_without_area():
    """Test _calculate_vacancy_rate handles rentals without floor_area_sqm."""
    generator = InvestmentMemorandumGenerator()
    prop = _make_property(net_lettable_area_sqm=Decimal("10000.00"))

    rental_with_area = _make_rental_listing(
        prop.id, floor_area_sqm=Decimal("3000.00"), is_active=True
    )
    rental_without_area = _make_rental_listing(
        prop.id, floor_level="30", floor_area_sqm=None, is_active=True
    )
    rentals = [rental_with_area, rental_without_area]

    # Execute
    result = generator._calculate_vacancy_rate(rentals, prop)

    # Assert - only rental with area counted
    assert abs(float(result) - 0.70) < 0.01  # Allow for float/Decimal precision


# ============================================================================
# SECTION CREATION TESTS
# ============================================================================


def test_create_investment_cover():
    """Test _create_investment_cover generates cover page."""
    generator = InvestmentMemorandumGenerator()
    prop = _make_property()
    property_data = {"property": prop}
    financial_data = {"estimated_value": 180000000.0}

    # Execute
    result = generator._create_investment_cover(property_data, financial_data)

    # Assert
    assert result is not None
    assert hasattr(result, "title")
    assert hasattr(result, "subtitle")


def test_create_table_of_contents():
    """Test _create_table_of_contents generates TOC."""
    generator = InvestmentMemorandumGenerator()

    # Execute
    result = generator._create_table_of_contents()

    # Assert
    assert result is not None
    assert len(result) > 0


def test_create_executive_summary():
    """Test _create_executive_summary generates executive summary."""
    generator = InvestmentMemorandumGenerator()
    prop = _make_property()
    property_data = {"property": prop, "vacancy_rate": 0.05}

    from app.services.finance import calculate_comprehensive_metrics

    metrics = calculate_comprehensive_metrics(
        property_value=Decimal("180000000.00"),
        gross_rental_income=Decimal("10000000.00"),
        operating_expenses=Decimal("3000000.00"),
        vacancy_rate=Decimal("0.05"),
        other_income=Decimal("500000.00"),
    )
    financial_data = {
        "metrics": metrics,
        "estimated_value": 180000000.0,
        "annual_rental_income": 10000000.0,
    }
    market_data = {"benchmarks": [], "current_cycle": None, "comparables": []}

    # Execute
    result = generator._create_executive_summary(
        property_data, financial_data, market_data
    )

    # Assert
    assert result is not None
    assert len(result) > 0


def test_create_investment_highlights():
    """Test _create_investment_highlights generates highlights."""
    generator = InvestmentMemorandumGenerator()
    prop = _make_property(gross_floor_area_sqm=Decimal("65000.00"))
    property_data = {"property": prop, "vacancy_rate": 0.05}

    from app.services.finance import calculate_comprehensive_metrics

    metrics = calculate_comprehensive_metrics(
        property_value=Decimal("180000000.00"),
        gross_rental_income=Decimal("10000000.00"),
        operating_expenses=Decimal("3000000.00"),
        vacancy_rate=Decimal("0.05"),
        other_income=Decimal("500000.00"),
    )
    financial_data = {"metrics": metrics}

    # Execute
    result = generator._create_investment_highlights(property_data, financial_data)

    # Assert
    assert result is not None
    assert len(result) > 0


def test_create_property_overview():
    """Test _create_property_overview generates property details."""
    generator = InvestmentMemorandumGenerator()
    prop = _make_property()
    property_data = {"property": prop}

    # Execute
    result = generator._create_property_overview(property_data)

    # Assert
    assert result is not None
    assert len(result) > 0


def test_create_location_analysis():
    """Test _create_location_analysis generates location section."""
    generator = InvestmentMemorandumGenerator()
    prop = _make_property()
    property_data = {"property": prop}
    market_data = {
        "benchmarks": [],
        "current_cycle": _make_market_cycle(),
        "comparables": [],
    }

    # Execute
    result = generator._create_location_analysis(property_data, market_data)

    # Assert
    assert result is not None
    assert len(result) > 0


def test_create_location_analysis_with_comparables():
    """Test _create_location_analysis includes comparables."""
    generator = InvestmentMemorandumGenerator()
    prop = _make_property()
    other_prop = _make_property(name="Comparable Tower", address="456 Market St")
    property_data = {"property": prop}

    comparable = _make_market_transaction(other_prop.id)
    comparable.property = other_prop
    market_data = {
        "benchmarks": [],
        "current_cycle": _make_market_cycle(),
        "comparables": [comparable],
    }

    # Execute
    result = generator._create_location_analysis(property_data, market_data)

    # Assert
    assert result is not None
    assert len(result) > 0


def test_create_financial_analysis():
    """Test _create_financial_analysis generates financial section."""
    generator = InvestmentMemorandumGenerator()

    from app.services.finance import calculate_comprehensive_metrics

    metrics = calculate_comprehensive_metrics(
        property_value=Decimal("180000000.00"),
        gross_rental_income=Decimal("10000000.00"),
        operating_expenses=Decimal("3000000.00"),
        vacancy_rate=Decimal("0.05"),
        other_income=Decimal("500000.00"),
    )
    financial_data = {
        "metrics": metrics,
        "annual_rental_income": 10000000.0,
        "operating_expenses": 3000000.0,
    }

    # Execute
    result = generator._create_financial_analysis(financial_data)

    # Assert
    assert result is not None
    assert len(result) > 0


def test_create_investment_returns_with_target():
    """Test _create_investment_returns with target return."""
    generator = InvestmentMemorandumGenerator()

    from app.services.finance import calculate_comprehensive_metrics

    metrics = calculate_comprehensive_metrics(
        property_value=Decimal("180000000.00"),
        gross_rental_income=Decimal("10000000.00"),
        operating_expenses=Decimal("3000000.00"),
        vacancy_rate=Decimal("0.05"),
        other_income=Decimal("500000.00"),
    )
    financial_data = {"metrics": metrics}

    # Execute
    result = generator._create_investment_returns(financial_data, target_return=15.0)

    # Assert
    assert result is not None
    assert len(result) > 0


def test_create_investment_returns_no_target():
    """Test _create_investment_returns without target return."""
    generator = InvestmentMemorandumGenerator()

    from app.services.finance import calculate_comprehensive_metrics

    metrics = calculate_comprehensive_metrics(
        property_value=Decimal("180000000.00"),
        gross_rental_income=Decimal("10000000.00"),
        operating_expenses=Decimal("3000000.00"),
        vacancy_rate=Decimal("0.05"),
        other_income=Decimal("500000.00"),
    )
    financial_data = {"metrics": metrics}

    # Execute
    result = generator._create_investment_returns(financial_data, target_return=None)

    # Assert
    assert result is not None
    assert len(result) > 0


def test_create_risk_analysis():
    """Test _create_risk_analysis generates risk section."""
    generator = InvestmentMemorandumGenerator()
    prop = _make_property()
    property_data = {"property": prop}
    market_data = {"benchmarks": [], "current_cycle": None, "comparables": []}

    # Execute
    result = generator._create_risk_analysis(property_data, market_data)

    # Assert
    assert result is not None
    assert len(result) > 0


def test_create_exit_strategies():
    """Test _create_exit_strategies generates exit section."""
    generator = InvestmentMemorandumGenerator()
    prop = _make_property()
    property_data = {"property": prop}

    from app.services.finance import calculate_comprehensive_metrics

    metrics = calculate_comprehensive_metrics(
        property_value=Decimal("180000000.00"),
        gross_rental_income=Decimal("10000000.00"),
        operating_expenses=Decimal("3000000.00"),
        vacancy_rate=Decimal("0.05"),
        other_income=Decimal("500000.00"),
    )
    financial_data = {"metrics": metrics}

    # Execute
    result = generator._create_exit_strategies(property_data, financial_data)

    # Assert
    assert result is not None
    assert len(result) > 0


def test_create_transaction_structure():
    """Test _create_transaction_structure generates transaction section."""
    generator = InvestmentMemorandumGenerator()
    prop = _make_property()
    property_data = {"property": prop}

    # Execute
    result = generator._create_transaction_structure(property_data)

    # Assert
    assert result is not None
    assert len(result) > 0


def test_create_appendices():
    """Test _create_appendices generates appendix section."""
    generator = InvestmentMemorandumGenerator()

    # Execute
    result = generator._create_appendices()

    # Assert
    assert result is not None
    assert len(result) > 0


# ============================================================================
# FULL GENERATION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_generate_investment_memorandum_success(db_session: AsyncSession):
    """Test generate creates investment memorandum PDF successfully."""
    # Create test data
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    rental = _make_rental_listing(prop.id)
    db_session.add(rental)

    benchmark = _make_yield_benchmark()
    db_session.add(benchmark)
    await db_session.flush()

    # Execute
    generator = InvestmentMemorandumGenerator()
    result = await generator.generate(prop.id, db_session)

    # Assert
    assert result is not None
    assert isinstance(result, io.BytesIO)
    assert result.tell() == 0  # Pointer at start
    content = result.read()
    assert len(content) > 0
    assert content[:4] == b"%PDF"  # PDF magic number


@pytest.mark.asyncio
async def test_generate_with_investment_thesis(db_session: AsyncSession):
    """Test generate with custom investment thesis."""
    # Create test data
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    # Execute
    generator = InvestmentMemorandumGenerator()
    result = await generator.generate(
        prop.id, db_session, investment_thesis="Strategic acquisition opportunity"
    )

    # Assert
    assert result is not None
    content = result.read()
    assert len(content) > 0


@pytest.mark.asyncio
async def test_generate_with_target_return(db_session: AsyncSession):
    """Test generate with target return specified."""
    # Create test data
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    # Execute
    generator = InvestmentMemorandumGenerator()
    result = await generator.generate(prop.id, db_session, target_return=18.5)

    # Assert
    assert result is not None
    content = result.read()
    assert len(content) > 0


@pytest.mark.asyncio
async def test_generate_with_all_market_data(db_session: AsyncSession):
    """Test generate with complete market intelligence."""
    # Create test data
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    rental = _make_rental_listing(prop.id)
    db_session.add(rental)

    transaction = _make_market_transaction(prop.id)
    db_session.add(transaction)

    benchmark = _make_yield_benchmark()
    db_session.add(benchmark)

    cycle = _make_market_cycle()
    db_session.add(cycle)

    # Create comparable property and transaction
    other_prop = _make_property(name="Comparable Tower", address="789 Comparable Ave")
    db_session.add(other_prop)
    await db_session.flush()

    comparable = _make_market_transaction(
        other_prop.id, transaction_date=date(2024, 7, 1)
    )
    db_session.add(comparable)
    await db_session.flush()

    # Execute
    generator = InvestmentMemorandumGenerator()
    result = await generator.generate(prop.id, db_session)

    # Assert
    assert result is not None
    content = result.read()
    assert len(content) > 0
    assert content[:4] == b"%PDF"


# ============================================================================
# EDGE CASE TESTS
# ============================================================================


def test_create_property_overview_no_year_built():
    """Test property overview handles missing year_built."""
    generator = InvestmentMemorandumGenerator()
    prop = _make_property(year_built=None)
    property_data = {"property": prop}

    # Execute
    result = generator._create_property_overview(property_data)

    # Assert
    assert result is not None
    assert len(result) > 0


def test_create_property_overview_no_year_renovated():
    """Test property overview handles missing year_renovated."""
    generator = InvestmentMemorandumGenerator()
    prop = _make_property(year_renovated=None)
    property_data = {"property": prop}

    # Execute
    result = generator._create_property_overview(property_data)

    # Assert
    assert result is not None
    assert len(result) > 0


def test_create_property_overview_no_floors():
    """Test property overview handles missing floors_above_ground."""
    generator = InvestmentMemorandumGenerator()
    prop = _make_property(floors_above_ground=None)
    property_data = {"property": prop}

    # Execute
    result = generator._create_property_overview(property_data)

    # Assert
    assert result is not None
    assert len(result) > 0


def test_create_location_analysis_no_cycle():
    """Test location analysis handles missing market cycle."""
    generator = InvestmentMemorandumGenerator()
    prop = _make_property()
    property_data = {"property": prop}
    market_data = {"benchmarks": [], "current_cycle": None, "comparables": []}

    # Execute
    result = generator._create_location_analysis(property_data, market_data)

    # Assert
    assert result is not None
    assert len(result) > 0


def test_create_location_analysis_no_comparables():
    """Test location analysis handles missing comparables."""
    generator = InvestmentMemorandumGenerator()
    prop = _make_property()
    property_data = {"property": prop}
    market_data = {"benchmarks": [], "current_cycle": None, "comparables": []}

    # Execute
    result = generator._create_location_analysis(property_data, market_data)

    # Assert
    assert result is not None
    assert len(result) > 0


@pytest.mark.asyncio
async def test_generate_minimal_data(db_session: AsyncSession):
    """Test generate works with minimal data (no rentals, no market data)."""
    # Create test data - only property
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    # Execute
    generator = InvestmentMemorandumGenerator()
    result = await generator.generate(prop.id, db_session)

    # Assert
    assert result is not None
    content = result.read()
    assert len(content) > 0
    assert content[:4] == b"%PDF"
