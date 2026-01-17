"""Unit tests for market intelligence analytics helper methods."""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import pytest

from app.models.property import PropertyType
from app.services.agents.market_intelligence_analytics import (
    MarketIntelligenceAnalytics,
)


@pytest.fixture
def analytics():
    """Create analytics instance without full initialization."""
    instance = MarketIntelligenceAnalytics.__new__(MarketIntelligenceAnalytics)
    instance.metrics = None
    return instance


def _make_transaction(**overrides):
    """Create a mock transaction."""
    defaults = {
        "transaction_date": date(2024, 3, 15),
        "sale_price": 5_000_000,
        "psf_price": 2500.0,
        "property": SimpleNamespace(name="Alpha Tower"),
        "buyer_type": "REIT",
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


# -----------------------------------------------------------
# _group_by_quarter tests
# -----------------------------------------------------------


def test_group_by_quarter_groups_correctly(analytics):
    """Test transactions are correctly grouped into quarters."""
    transactions = [
        _make_transaction(transaction_date=date(2024, 1, 15), sale_price=1_000_000, psf_price=1000.0),
        _make_transaction(transaction_date=date(2024, 2, 10), sale_price=2_000_000, psf_price=2000.0),
        _make_transaction(transaction_date=date(2024, 4, 20), sale_price=3_000_000, psf_price=3000.0),
        _make_transaction(transaction_date=date(2024, 7, 5), sale_price=4_000_000, psf_price=4000.0),
    ]

    result = analytics._group_by_quarter(transactions)

    assert "2024-Q1" in result
    assert "2024-Q2" in result
    assert "2024-Q3" in result
    assert result["2024-Q1"]["count"] == 2
    assert result["2024-Q2"]["count"] == 1
    assert result["2024-Q3"]["count"] == 1


def test_group_by_quarter_calculates_averages(analytics):
    """Test average PSF is correctly calculated per quarter."""
    transactions = [
        _make_transaction(transaction_date=date(2024, 1, 1), sale_price=1_000_000, psf_price=1000.0),
        _make_transaction(transaction_date=date(2024, 1, 15), sale_price=2_000_000, psf_price=2000.0),
    ]

    result = analytics._group_by_quarter(transactions)

    assert result["2024-Q1"]["avg_psf"] == 1500.0
    assert result["2024-Q1"]["total_volume"] == 3_000_000


def test_group_by_quarter_handles_missing_psf(analytics):
    """Test handling of transactions without PSF price."""
    transactions = [
        _make_transaction(transaction_date=date(2024, 1, 1), psf_price=None),
    ]

    result = analytics._group_by_quarter(transactions)

    assert result["2024-Q1"]["avg_psf"] == 0


def test_group_by_quarter_empty_list(analytics):
    """Test with empty transaction list."""
    result = analytics._group_by_quarter([])
    assert result == {}


# -----------------------------------------------------------
# _calculate_price_trend tests
# -----------------------------------------------------------


def test_calculate_price_trend_upward(analytics):
    """Test upward trend detection."""
    quarterly_data = {
        "2023-Q1": {"avg_psf": 1000},
        "2023-Q2": {"avg_psf": 1050},
        "2023-Q3": {"avg_psf": 1100},
        "2023-Q4": {"avg_psf": 1200},
    }

    result = analytics._calculate_price_trend(quarterly_data)
    assert result == "upward"


def test_calculate_price_trend_downward(analytics):
    """Test downward trend detection."""
    quarterly_data = {
        "2023-Q1": {"avg_psf": 1200},
        "2023-Q2": {"avg_psf": 1150},
        "2023-Q3": {"avg_psf": 1050},
        "2023-Q4": {"avg_psf": 1000},
    }

    result = analytics._calculate_price_trend(quarterly_data)
    assert result == "downward"


def test_calculate_price_trend_stable(analytics):
    """Test stable trend detection."""
    quarterly_data = {
        "2023-Q1": {"avg_psf": 1000},
        "2023-Q2": {"avg_psf": 1010},
        "2023-Q3": {"avg_psf": 1020},
        "2023-Q4": {"avg_psf": 1030},
    }

    result = analytics._calculate_price_trend(quarterly_data)
    assert result == "stable"


def test_calculate_price_trend_insufficient_data(analytics):
    """Test insufficient data handling."""
    quarterly_data = {"2023-Q1": {"avg_psf": 1000}}

    result = analytics._calculate_price_trend(quarterly_data)
    assert result == "insufficient_data"


def test_calculate_price_trend_two_quarters(analytics):
    """Test with exactly two quarters."""
    quarterly_data = {
        "2023-Q1": {"avg_psf": 1000},
        "2023-Q2": {"avg_psf": 1200},
    }

    result = analytics._calculate_price_trend(quarterly_data)
    assert result == "upward"


def test_calculate_price_trend_zero_older_avg(analytics):
    """Test handling of zero older average."""
    quarterly_data = {
        "2023-Q1": {"avg_psf": 0},
        "2023-Q2": {"avg_psf": 1000},
        "2023-Q3": {"avg_psf": 1100},
        "2023-Q4": {"avg_psf": 1200},
    }

    result = analytics._calculate_price_trend(quarterly_data)
    # With zero older avg (0 + 1000)/2 = 500, change_pct is calculated
    # recent avg = (1100+1200)/2 = 1150, older avg = 500
    # change = (1150 - 500) / 500 * 100 = 130% -> upward
    assert result == "upward"


# -----------------------------------------------------------
# _get_top_transactions tests
# -----------------------------------------------------------


def test_get_top_transactions_sorts_by_value(analytics):
    """Test transactions are sorted by value descending."""
    transactions = [
        _make_transaction(sale_price=1_000_000),
        _make_transaction(sale_price=5_000_000),
        _make_transaction(sale_price=3_000_000),
    ]

    result = analytics._get_top_transactions(transactions, limit=3)

    assert len(result) == 3
    assert result[0]["price"] == 5_000_000
    assert result[1]["price"] == 3_000_000
    assert result[2]["price"] == 1_000_000


def test_get_top_transactions_respects_limit(analytics):
    """Test limit is respected."""
    transactions = [_make_transaction(sale_price=i * 1_000_000) for i in range(10)]

    result = analytics._get_top_transactions(transactions, limit=3)

    assert len(result) == 3


def test_get_top_transactions_handles_missing_property(analytics):
    """Test handling of transaction without property."""
    transactions = [_make_transaction(property=None)]

    result = analytics._get_top_transactions(transactions, limit=1)

    assert result[0]["property_name"] == "Unknown"


def test_get_top_transactions_handles_missing_psf(analytics):
    """Test handling of transaction without PSF price."""
    transactions = [_make_transaction(psf_price=None)]

    result = analytics._get_top_transactions(transactions, limit=1)

    assert result[0]["psf"] is None


def test_get_top_transactions_empty_list(analytics):
    """Test with empty transaction list."""
    result = analytics._get_top_transactions([], limit=5)
    assert result == []


# -----------------------------------------------------------
# _analyze_buyer_profile tests
# -----------------------------------------------------------


def test_analyze_buyer_profile_counts_correctly(analytics):
    """Test buyer type counting."""
    transactions = [
        _make_transaction(buyer_type="REIT"),
        _make_transaction(buyer_type="REIT"),
        _make_transaction(buyer_type="Private"),
        _make_transaction(buyer_type="Institution"),
    ]

    result = analytics._analyze_buyer_profile(transactions)

    assert result["REIT"] == 2
    assert result["Private"] == 1
    assert result["Institution"] == 1


def test_analyze_buyer_profile_handles_missing_type(analytics):
    """Test handling of missing buyer type."""
    transactions = [
        _make_transaction(buyer_type=None),
        _make_transaction(buyer_type="REIT"),
    ]

    result = analytics._analyze_buyer_profile(transactions)

    assert result["Unknown"] == 1
    assert result["REIT"] == 1


def test_analyze_buyer_profile_empty_list(analytics):
    """Test with empty transaction list."""
    result = analytics._analyze_buyer_profile([])
    assert result == {}


# -----------------------------------------------------------
# _calculate_supply_pressure tests
# -----------------------------------------------------------


def test_calculate_supply_pressure_high(analytics):
    """Test high supply pressure detection."""
    result = analytics._calculate_supply_pressure(
        upcoming_gfa=800_000,
        property_type=PropertyType.OFFICE,
        location="D01"
    )
    assert result == "high"


def test_calculate_supply_pressure_moderate(analytics):
    """Test moderate supply pressure detection."""
    result = analytics._calculate_supply_pressure(
        upcoming_gfa=550_000,
        property_type=PropertyType.OFFICE,
        location="D01"
    )
    assert result == "moderate"


def test_calculate_supply_pressure_low(analytics):
    """Test low supply pressure detection."""
    result = analytics._calculate_supply_pressure(
        upcoming_gfa=200_000,
        property_type=PropertyType.OFFICE,
        location="D01"
    )
    assert result == "low"


def test_calculate_supply_pressure_different_property_types(analytics):
    """Test thresholds for different property types."""
    # Retail has lower threshold (200000)
    result_retail = analytics._calculate_supply_pressure(
        upcoming_gfa=250_000,
        property_type=PropertyType.RETAIL,
        location="D01"
    )
    assert result_retail == "moderate"

    # Residential has higher threshold (1000000)
    result_residential = analytics._calculate_supply_pressure(
        upcoming_gfa=500_000,
        property_type=PropertyType.RESIDENTIAL,
        location="D01"
    )
    assert result_residential == "low"


def test_calculate_supply_pressure_fallback_threshold(analytics):
    """Test fallback threshold for unknown property types."""
    result = analytics._calculate_supply_pressure(
        upcoming_gfa=800_000,
        property_type=PropertyType.LAND,
        location="D01"
    )
    # Uses default 500000 threshold, 800000 > 750000 (1.5x)
    assert result == "high"


# -----------------------------------------------------------
# _get_major_developments tests
# -----------------------------------------------------------


def _make_project(**overrides):
    """Create a mock development project."""
    defaults = {
        "project_name": "Harbor View",
        "developer": "DevCo",
        "total_gfa_sqm": 100_000,
        "total_units": 500,
        "expected_completion": date(2026, 6, 1),
        "development_status": SimpleNamespace(value="planned"),
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_get_major_developments_sorts_by_gfa(analytics):
    """Test projects are sorted by GFA descending."""
    projects = [
        _make_project(project_name="Small", total_gfa_sqm=50_000),
        _make_project(project_name="Large", total_gfa_sqm=200_000),
        _make_project(project_name="Medium", total_gfa_sqm=100_000),
    ]

    result = analytics._get_major_developments(projects, limit=3)

    assert result[0]["name"] == "Large"
    assert result[1]["name"] == "Medium"
    assert result[2]["name"] == "Small"


def test_get_major_developments_respects_limit(analytics):
    """Test limit is respected."""
    projects = [_make_project(total_gfa_sqm=i * 10_000) for i in range(10)]

    result = analytics._get_major_developments(projects, limit=3)

    assert len(result) == 3


def test_get_major_developments_handles_none_gfa(analytics):
    """Test handling of None GFA."""
    projects = [_make_project(total_gfa_sqm=None)]

    result = analytics._get_major_developments(projects, limit=1)

    assert result[0]["gfa"] == 0


def test_get_major_developments_handles_none_completion(analytics):
    """Test handling of None completion date."""
    projects = [_make_project(expected_completion=None)]

    result = analytics._get_major_developments(projects, limit=1)

    assert result[0]["completion"] is None


# -----------------------------------------------------------
# _assess_supply_impact tests
# -----------------------------------------------------------


def test_assess_supply_impact_high(analytics):
    """Test high impact assessment."""
    result = analytics._assess_supply_impact(
        upcoming_gfa=800_000,
        property_type=PropertyType.OFFICE
    )
    assert "downward pressure" in result


def test_assess_supply_impact_moderate(analytics):
    """Test moderate impact assessment."""
    result = analytics._assess_supply_impact(
        upcoming_gfa=550_000,
        property_type=PropertyType.OFFICE
    )
    assert "absorb" in result


def test_assess_supply_impact_low(analytics):
    """Test low impact assessment."""
    result = analytics._assess_supply_impact(
        upcoming_gfa=200_000,
        property_type=PropertyType.OFFICE
    )
    assert "growth" in result


# -----------------------------------------------------------
# _analyze_velocity_trend tests
# -----------------------------------------------------------


def _make_absorption(**overrides):
    """Create mock absorption tracking data."""
    defaults = {
        "quarter": "2024-Q1",
        "net_absorption_sqm": 50_000,
        "gross_takeup_sqm": 80_000,
        "vacancy_rate": 0.08,
        "months_of_supply": 12,
        "avg_units_per_month": 100,  # Required by _analyze_velocity_trend
        "tracking_date": date(2024, 1, 15),  # Required by _detect_seasonal_patterns
        "sales_absorption_rate": 5.0,  # Required by _detect_seasonal_patterns
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_analyze_velocity_trend_accelerating(analytics):
    """Test accelerating velocity detection."""
    # Need at least 6 items: 3 older + 3 recent
    absorption_data = [
        _make_absorption(avg_units_per_month=30),
        _make_absorption(avg_units_per_month=32),
        _make_absorption(avg_units_per_month=35),
        _make_absorption(avg_units_per_month=50),
        _make_absorption(avg_units_per_month=55),
        _make_absorption(avg_units_per_month=60),
    ]

    result = analytics._analyze_velocity_trend(absorption_data)
    assert result == "accelerating"


def test_analyze_velocity_trend_decelerating(analytics):
    """Test decelerating velocity detection."""
    absorption_data = [
        _make_absorption(avg_units_per_month=60),
        _make_absorption(avg_units_per_month=55),
        _make_absorption(avg_units_per_month=50),
        _make_absorption(avg_units_per_month=35),
        _make_absorption(avg_units_per_month=32),
        _make_absorption(avg_units_per_month=30),
    ]

    result = analytics._analyze_velocity_trend(absorption_data)
    assert result == "decelerating"


def test_analyze_velocity_trend_stable(analytics):
    """Test stable velocity detection."""
    absorption_data = [
        _make_absorption(avg_units_per_month=50),
        _make_absorption(avg_units_per_month=52),
        _make_absorption(avg_units_per_month=48),
        _make_absorption(avg_units_per_month=50),
        _make_absorption(avg_units_per_month=51),
        _make_absorption(avg_units_per_month=49),
    ]

    result = analytics._analyze_velocity_trend(absorption_data)
    assert result == "stable"


def test_analyze_velocity_trend_insufficient_data(analytics):
    """Test with insufficient data."""
    absorption_data = [_make_absorption()]

    result = analytics._analyze_velocity_trend(absorption_data)
    assert result == "insufficient_data"


# -----------------------------------------------------------
# _detect_seasonal_patterns tests
# -----------------------------------------------------------


def test_detect_seasonal_patterns_identifies_peak_month(analytics):
    """Test peak month identification with at least 12 months of data."""
    # Create 12+ months of data with varying absorption
    absorption_data = [
        _make_absorption(tracking_date=date(2023, m, 15), sales_absorption_rate=5.0 + m)
        for m in range(1, 13)
    ]
    # Add more data points
    absorption_data.extend([
        _make_absorption(tracking_date=date(2024, m, 15), sales_absorption_rate=5.0 + m)
        for m in range(1, 4)
    ])

    result = analytics._detect_seasonal_patterns(absorption_data)

    # December (month 12) should have highest absorption
    assert result["peak_month"] == 12
    assert "seasonality_strength" in result


def test_detect_seasonal_patterns_insufficient_data(analytics):
    """Test with insufficient data returns message."""
    absorption_data = [
        _make_absorption(tracking_date=date(2023, m, 15), sales_absorption_rate=5.0)
        for m in range(1, 10)  # Only 9 months, need 12
    ]

    result = analytics._detect_seasonal_patterns(absorption_data)

    assert "message" in result
    assert "Insufficient" in result["message"]


# -----------------------------------------------------------
# MarketReport tests
# -----------------------------------------------------------


def test_market_report_init_and_to_dict():
    """Test MarketReport initialization and serialization."""
    from app.services.agents.market_intelligence_analytics import MarketReport

    report = MarketReport(
        property_type=PropertyType.OFFICE,
        location="D01",
        period=(date(2024, 1, 1), date(2024, 6, 30)),
        comparables_analysis={"transaction_count": 10, "total_volume": 50_000_000},
        supply_dynamics={"pipeline_projects": 5, "total_upcoming_gfa": 200_000},
        yield_benchmarks={"current_metrics": {"cap_rate": {"median": 4.5}}},
        absorption_trends={"velocity_trend": "accelerating"},
        market_cycle_position={"current_phase": "expansion"},
        recommendations=["Consider premium positioning"],
    )

    assert report.property_type == PropertyType.OFFICE
    assert report.location == "D01"
    assert report.period == (date(2024, 1, 1), date(2024, 6, 30))
    assert report.comparables["transaction_count"] == 10
    assert report.supply["pipeline_projects"] == 5
    assert report.yields["current_metrics"]["cap_rate"]["median"] == 4.5
    assert report.absorption["velocity_trend"] == "accelerating"
    assert report.cycle["current_phase"] == "expansion"
    assert len(report.recommendations) == 1
    assert report.generated_at is not None

    # Test to_dict
    result = report.to_dict()
    assert result["property_type"] == "office"
    assert result["location"] == "D01"
    assert result["period"]["start"] == "2024-01-01"
    assert result["period"]["end"] == "2024-06-30"
    assert result["comparables_analysis"]["transaction_count"] == 10
    assert result["supply_dynamics"]["pipeline_projects"] == 5
    assert result["recommendations"] == ["Consider premium positioning"]
    assert "generated_at" in result


# -----------------------------------------------------------
# _calculate_yield_trend tests
# -----------------------------------------------------------


def _make_benchmark(**overrides):
    """Create a mock yield benchmark."""
    defaults = {
        "benchmark_date": date(2024, 1, 15),
        "cap_rate_mean": 4.5,
        "cap_rate_median": 4.4,
        "cap_rate_p25": 4.0,
        "cap_rate_p75": 5.0,
        "rental_psf_mean": 8.50,
        "rental_psf_median": 8.25,
        "occupancy_rate_mean": 0.92,
        "transaction_count": 15,
        "total_transaction_value": 250_000_000,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_calculate_yield_trend_increasing(analytics):
    """Test increasing yield trend detection."""
    benchmarks = [
        _make_benchmark(cap_rate_median=4.0),
        _make_benchmark(cap_rate_median=4.2),
        _make_benchmark(cap_rate_median=4.4),
        _make_benchmark(cap_rate_median=4.6),
        _make_benchmark(cap_rate_median=4.8),
        _make_benchmark(cap_rate_median=5.0),
    ]

    result = analytics._calculate_yield_trend(benchmarks, "cap_rate_median")
    assert result == "increasing"


def test_calculate_yield_trend_decreasing(analytics):
    """Test decreasing yield trend detection."""
    benchmarks = [
        _make_benchmark(cap_rate_median=5.0),
        _make_benchmark(cap_rate_median=4.8),
        _make_benchmark(cap_rate_median=4.6),
        _make_benchmark(cap_rate_median=4.4),
        _make_benchmark(cap_rate_median=4.2),
        _make_benchmark(cap_rate_median=4.0),
    ]

    result = analytics._calculate_yield_trend(benchmarks, "cap_rate_median")
    assert result == "decreasing"


def test_calculate_yield_trend_stable(analytics):
    """Test stable yield trend detection."""
    benchmarks = [
        _make_benchmark(cap_rate_median=4.5),
        _make_benchmark(cap_rate_median=4.52),
        _make_benchmark(cap_rate_median=4.48),
        _make_benchmark(cap_rate_median=4.51),
        _make_benchmark(cap_rate_median=4.49),
        _make_benchmark(cap_rate_median=4.50),
    ]

    result = analytics._calculate_yield_trend(benchmarks, "cap_rate_median")
    assert result == "stable"


def test_calculate_yield_trend_insufficient_data(analytics):
    """Test insufficient data handling."""
    benchmarks = [_make_benchmark()]

    result = analytics._calculate_yield_trend(benchmarks, "cap_rate_median")
    assert result == "insufficient_data"


def test_calculate_yield_trend_missing_metric_values(analytics):
    """Test handling of benchmarks with missing metric values."""
    benchmarks = [
        _make_benchmark(cap_rate_median=None),
        _make_benchmark(cap_rate_median=None),
    ]

    result = analytics._calculate_yield_trend(benchmarks, "cap_rate_median")
    assert result == "insufficient_data"


# -----------------------------------------------------------
# _calculate_yoy_change tests
# -----------------------------------------------------------


def test_calculate_yoy_change_with_valid_data(analytics):
    """Test YoY change calculation with valid data."""
    from datetime import timedelta

    base_date = date(2024, 6, 15)
    benchmarks = [
        _make_benchmark(
            benchmark_date=base_date - timedelta(days=365),
            cap_rate_median=4.0,
            rental_psf_median=8.00,
            total_transaction_value=200_000_000,
        )
    ]
    # Add 11 months of data to reach 12 benchmarks
    for i in range(1, 12):
        benchmarks.append(
            _make_benchmark(
                benchmark_date=base_date - timedelta(days=365 - (30 * i)),
                cap_rate_median=4.0 + (i * 0.05),
                rental_psf_median=8.00 + (i * 0.10),
                total_transaction_value=200_000_000 + (i * 10_000_000),
            )
        )
    # Add current benchmark
    benchmarks.append(
        _make_benchmark(
            benchmark_date=base_date,
            cap_rate_median=4.5,
            rental_psf_median=9.00,
            total_transaction_value=300_000_000,
        )
    )

    result = analytics._calculate_yoy_change(benchmarks)

    assert "cap_rate_change_bps" in result
    assert "rental_change_pct" in result
    assert "transaction_volume_change_pct" in result


def test_calculate_yoy_change_insufficient_data(analytics):
    """Test YoY change with insufficient data."""
    benchmarks = [
        _make_benchmark(benchmark_date=date(2024, 1, 15)),
        _make_benchmark(benchmark_date=date(2024, 2, 15)),
    ]

    result = analytics._calculate_yoy_change(benchmarks)
    assert result == {}


def test_calculate_yoy_change_no_matching_year_ago(analytics):
    """Test YoY change when no matching year-ago benchmark exists."""
    from datetime import timedelta

    base_date = date(2024, 6, 15)
    # Create 12 benchmarks but all within last 6 months
    benchmarks = [
        _make_benchmark(benchmark_date=base_date - timedelta(days=i * 15))
        for i in range(12)
    ]

    result = analytics._calculate_yoy_change(benchmarks)
    assert result == {}


# -----------------------------------------------------------
# _assess_yield_position tests
# -----------------------------------------------------------


def test_assess_yield_position_compressed_office(analytics):
    """Test yield position assessment for compressed office yields."""
    benchmark = _make_benchmark(cap_rate_median=3.5)  # Below 4.0 for office

    result = analytics._assess_yield_position(benchmark, PropertyType.OFFICE)
    assert result == "yields_compressed"


def test_assess_yield_position_elevated_office(analytics):
    """Test yield position assessment for elevated office yields."""
    benchmark = _make_benchmark(cap_rate_median=6.0)  # Above 5.5 for office

    result = analytics._assess_yield_position(benchmark, PropertyType.OFFICE)
    assert result == "yields_elevated"


def test_assess_yield_position_normal_office(analytics):
    """Test yield position assessment for normal office yields."""
    benchmark = _make_benchmark(cap_rate_median=4.8)  # Between 4.0-5.5 for office

    result = analytics._assess_yield_position(benchmark, PropertyType.OFFICE)
    assert result == "yields_normal"


def test_assess_yield_position_retail(analytics):
    """Test yield position assessment for retail property."""
    # Retail range is 5.0-7.0
    benchmark = _make_benchmark(cap_rate_median=4.5)  # Below 5.0
    result = analytics._assess_yield_position(benchmark, PropertyType.RETAIL)
    assert result == "yields_compressed"

    benchmark = _make_benchmark(cap_rate_median=7.5)  # Above 7.0
    result = analytics._assess_yield_position(benchmark, PropertyType.RETAIL)
    assert result == "yields_elevated"


def test_assess_yield_position_industrial(analytics):
    """Test yield position assessment for industrial property."""
    # Industrial range is 6.0-8.0
    benchmark = _make_benchmark(cap_rate_median=7.0)  # Within range
    result = analytics._assess_yield_position(benchmark, PropertyType.INDUSTRIAL)
    assert result == "yields_normal"


def test_assess_yield_position_residential(analytics):
    """Test yield position assessment for residential property."""
    # Residential range is 3.0-4.5
    benchmark = _make_benchmark(cap_rate_median=4.0)  # Within range
    result = analytics._assess_yield_position(benchmark, PropertyType.RESIDENTIAL)
    assert result == "yields_normal"


def test_assess_yield_position_fallback_range(analytics):
    """Test yield position assessment with fallback range."""
    benchmark = _make_benchmark(cap_rate_median=5.0)  # Within default 4.0-6.0
    result = analytics._assess_yield_position(benchmark, PropertyType.LAND)
    assert result == "yields_normal"


# -----------------------------------------------------------
# _forecast_absorption tests
# -----------------------------------------------------------


def test_forecast_absorption_basic(analytics):
    """Test basic absorption forecast."""
    absorption_data = [
        _make_absorption(sales_absorption_rate=20.0),
        _make_absorption(sales_absorption_rate=25.0),
        _make_absorption(sales_absorption_rate=30.0),
        _make_absorption(sales_absorption_rate=35.0),
        _make_absorption(sales_absorption_rate=40.0),
        _make_absorption(sales_absorption_rate=45.0),
    ]

    result = analytics._forecast_absorption(absorption_data, months_ahead=6)

    assert "current_absorption" in result
    assert "projected_absorption_6m" in result
    assert "avg_monthly_absorption" in result
    assert "estimated_sellout_months" in result
    assert result["current_absorption"] == 45.0


def test_forecast_absorption_insufficient_data(analytics):
    """Test forecast with insufficient data."""
    absorption_data = [_make_absorption(), _make_absorption()]

    result = analytics._forecast_absorption(absorption_data)

    assert "message" in result
    assert "Insufficient" in result["message"]


def test_forecast_absorption_near_complete(analytics):
    """Test forecast when absorption is near 100%."""
    absorption_data = [
        _make_absorption(sales_absorption_rate=90.0),
        _make_absorption(sales_absorption_rate=92.0),
        _make_absorption(sales_absorption_rate=95.0),
        _make_absorption(sales_absorption_rate=97.0),
        _make_absorption(sales_absorption_rate=98.0),
        _make_absorption(sales_absorption_rate=99.0),
    ]

    result = analytics._forecast_absorption(absorption_data, months_ahead=6)

    # Projected should be capped at 100
    assert result["projected_absorption_6m"] <= 100


def test_forecast_absorption_zero_rate(analytics):
    """Test forecast with zero absorption rate."""
    absorption_data = [
        _make_absorption(sales_absorption_rate=0.0),
        _make_absorption(sales_absorption_rate=0.0),
        _make_absorption(sales_absorption_rate=0.0),
    ]

    result = analytics._forecast_absorption(absorption_data)

    assert result["avg_monthly_absorption"] == 0
    assert result["estimated_sellout_months"] is None


def test_forecast_absorption_very_slow_rate(analytics):
    """Test forecast with very slow absorption rate."""
    absorption_data = [
        _make_absorption(sales_absorption_rate=0.01),
        _make_absorption(sales_absorption_rate=0.02),
        _make_absorption(sales_absorption_rate=0.01),
    ]

    result = analytics._forecast_absorption(absorption_data)

    # Very slow rate should result in None for sellout estimate
    assert result["estimated_sellout_months"] is None


# -----------------------------------------------------------
# _analyze_index_trends tests
# -----------------------------------------------------------


def _make_index(**overrides):
    """Create a mock market index."""
    defaults = {
        "index_date": date(2024, 6, 15),
        "index_value": 150.0,
        "mom_change": 0.5,
        "qoq_change": 1.5,
        "yoy_change": 5.0,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_analyze_index_trends_basic(analytics):
    """Test basic index trends analysis."""
    indices = [
        _make_index(index_value=150.0, mom_change=0.5, qoq_change=1.5, yoy_change=5.0),
        _make_index(index_value=149.5, mom_change=0.3),
        _make_index(index_value=149.0, mom_change=0.2),
    ]

    result = analytics._analyze_index_trends(indices)

    assert result["current_index"] == 150.0
    assert result["mom_change"] == 0.5
    assert result["qoq_change"] == 1.5
    assert result["yoy_change"] == 5.0
    assert "trend" in result


def test_analyze_index_trends_empty_list(analytics):
    """Test with empty indices list."""
    result = analytics._analyze_index_trends([])
    assert result == {}


# -----------------------------------------------------------
# _determine_index_trend tests
# -----------------------------------------------------------


def test_determine_index_trend_uptrend(analytics):
    """Test uptrend detection."""
    indices = [
        _make_index(mom_change=0.5),
        _make_index(mom_change=0.3),
        _make_index(mom_change=0.2),
    ]

    result = analytics._determine_index_trend(indices)
    assert result == "uptrend"


def test_determine_index_trend_downtrend(analytics):
    """Test downtrend detection."""
    indices = [
        _make_index(mom_change=-0.5),
        _make_index(mom_change=-0.3),
        _make_index(mom_change=-0.2),
    ]

    result = analytics._determine_index_trend(indices)
    assert result == "downtrend"


def test_determine_index_trend_sideways(analytics):
    """Test sideways trend detection."""
    indices = [
        _make_index(mom_change=0.5),
        _make_index(mom_change=-0.3),
        _make_index(mom_change=0.2),
    ]

    result = analytics._determine_index_trend(indices)
    assert result == "sideways"


def test_determine_index_trend_insufficient_data(analytics):
    """Test with insufficient data."""
    indices = [_make_index(), _make_index()]

    result = analytics._determine_index_trend(indices)
    assert result == "insufficient_data"


def test_determine_index_trend_with_none_values(analytics):
    """Test handling of None mom_change values."""
    indices = [
        _make_index(mom_change=None),
        _make_index(mom_change=0.5),
        _make_index(mom_change=None),
    ]

    result = analytics._determine_index_trend(indices)
    # Only one valid change, so can't determine trend
    assert result in ["sideways", "uptrend"]


# -----------------------------------------------------------
# _generate_recommendations tests
# -----------------------------------------------------------


def test_generate_recommendations_upward_trend(analytics):
    """Test recommendations for upward price trend."""
    recommendations = analytics._generate_recommendations(
        comparables={"price_trend": "upward"},
        supply={},
        yields={},
        absorption={},
        cycle={},
    )

    assert any("momentum" in r.lower() for r in recommendations)


def test_generate_recommendations_downward_trend(analytics):
    """Test recommendations for downward price trend."""
    recommendations = analytics._generate_recommendations(
        comparables={"price_trend": "downward"},
        supply={},
        yields={},
        absorption={},
        cycle={},
    )

    assert any("value-add" in r.lower() for r in recommendations)


def test_generate_recommendations_high_supply(analytics):
    """Test recommendations for high supply pressure."""
    recommendations = analytics._generate_recommendations(
        comparables={},
        supply={"supply_pressure": "high"},
        yields={},
        absorption={},
        cycle={},
    )

    assert any("supply" in r.lower() or "absorption" in r.lower() for r in recommendations)


def test_generate_recommendations_low_supply(analytics):
    """Test recommendations for low supply pressure."""
    recommendations = analytics._generate_recommendations(
        comparables={},
        supply={"supply_pressure": "low"},
        yields={},
        absorption={},
        cycle={},
    )

    assert any("premium" in r.lower() or "pricing" in r.lower() for r in recommendations)


def test_generate_recommendations_compressed_yields(analytics):
    """Test recommendations for compressed yields."""
    recommendations = analytics._generate_recommendations(
        comparables={},
        supply={},
        yields={"market_position": "yields_compressed"},
        absorption={},
        cycle={},
    )

    assert any("income stability" in r.lower() for r in recommendations)


def test_generate_recommendations_elevated_yields(analytics):
    """Test recommendations for elevated yields."""
    recommendations = analytics._generate_recommendations(
        comparables={},
        supply={},
        yields={"market_position": "yields_elevated"},
        absorption={},
        cycle={},
    )

    assert any("buying opportunity" in r.lower() for r in recommendations)


def test_generate_recommendations_accelerating_absorption(analytics):
    """Test recommendations for accelerating absorption."""
    recommendations = analytics._generate_recommendations(
        comparables={},
        supply={},
        yields={},
        absorption={"velocity_trend": "accelerating"},
        cycle={},
    )

    assert any("momentum" in r.lower() for r in recommendations)


def test_generate_recommendations_decelerating_absorption(analytics):
    """Test recommendations for decelerating absorption."""
    recommendations = analytics._generate_recommendations(
        comparables={},
        supply={},
        yields={},
        absorption={"velocity_trend": "decelerating"},
        cycle={},
    )

    assert any("incentives" in r.lower() or "adjustments" in r.lower() for r in recommendations)


def test_generate_recommendations_expansion_phase(analytics):
    """Test recommendations for expansion market phase."""
    recommendations = analytics._generate_recommendations(
        comparables={},
        supply={},
        yields={},
        absorption={},
        cycle={"current_phase": "expansion"},
    )

    assert any("growth" in r.lower() for r in recommendations)


def test_generate_recommendations_hyper_supply_phase(analytics):
    """Test recommendations for hyper supply market phase."""
    recommendations = analytics._generate_recommendations(
        comparables={},
        supply={},
        yields={},
        absorption={},
        cycle={"current_phase": "hyper_supply"},
    )

    assert any("occupancy" in r.lower() for r in recommendations)


def test_generate_recommendations_recession_phase(analytics):
    """Test recommendations for recession market phase."""
    recommendations = analytics._generate_recommendations(
        comparables={},
        supply={},
        yields={},
        absorption={},
        cycle={"current_phase": "recession"},
    )

    assert any("retention" in r.lower() or "cost" in r.lower() for r in recommendations)


def test_generate_recommendations_recovery_phase(analytics):
    """Test recommendations for recovery market phase."""
    recommendations = analytics._generate_recommendations(
        comparables={},
        supply={},
        yields={},
        absorption={},
        cycle={"current_phase": "recovery"},
    )

    assert any("growth" in r.lower() or "recovering" in r.lower() for r in recommendations)


def test_generate_recommendations_always_includes_monitoring(analytics):
    """Test that monitoring recommendation is always included."""
    recommendations = analytics._generate_recommendations(
        comparables={},
        supply={},
        yields={},
        absorption={},
        cycle={},
    )

    assert any("monitoring" in r.lower() for r in recommendations)


# -----------------------------------------------------------
# _record_metrics tests
# -----------------------------------------------------------


def test_record_metrics_with_no_metrics_collector(analytics):
    """Test record_metrics when metrics collector is None."""
    analytics.metrics = None

    # Should not raise any errors
    analytics._record_metrics(
        property_type=PropertyType.OFFICE,
        location="D01",
        yields={"current_metrics": {"cap_rate": {"median": 4.5}}},
    )


def test_record_metrics_with_valid_yields(analytics):
    """Test record_metrics with valid yield data."""

    class MockMetrics:
        def __init__(self):
            self.recorded = []

        def record_gauge(self, name, value, tags):
            self.recorded.append({"name": name, "value": value, "tags": tags})

    analytics.metrics = MockMetrics()

    analytics._record_metrics(
        property_type=PropertyType.OFFICE,
        location="D01",
        yields={
            "current_metrics": {
                "cap_rate": {"median": 4.5},
                "rental_rates": {"median_psf": 8.50},
            }
        },
    )

    assert len(analytics.metrics.recorded) == 2
    assert analytics.metrics.recorded[0]["name"] == "market_intelligence.cap_rate"
    assert analytics.metrics.recorded[0]["value"] == 4.5
    assert analytics.metrics.recorded[1]["name"] == "market_intelligence.rental_psf"
    assert analytics.metrics.recorded[1]["value"] == 8.50


def test_record_metrics_with_missing_yield_data(analytics):
    """Test record_metrics with missing yield data."""

    class MockMetrics:
        def __init__(self):
            self.recorded = []

        def record_gauge(self, name, value, tags):
            self.recorded.append({"name": name, "value": value, "tags": tags})

    analytics.metrics = MockMetrics()

    analytics._record_metrics(
        property_type=PropertyType.OFFICE,
        location="D01",
        yields={},  # Empty yields
    )

    # Should not record anything with empty yields
    assert len(analytics.metrics.recorded) == 0


def test_record_metrics_with_partial_yield_data(analytics):
    """Test record_metrics with partial yield data."""

    class MockMetrics:
        def __init__(self):
            self.recorded = []

        def record_gauge(self, name, value, tags):
            self.recorded.append({"name": name, "value": value, "tags": tags})

    analytics.metrics = MockMetrics()

    analytics._record_metrics(
        property_type=PropertyType.OFFICE,
        location="D01",
        yields={
            "current_metrics": {
                "cap_rate": {"median": 4.5},
                # Missing rental_rates
            }
        },
    )

    # Should only record cap_rate
    assert len(analytics.metrics.recorded) == 1
    assert analytics.metrics.recorded[0]["name"] == "market_intelligence.cap_rate"


# -----------------------------------------------------------
# _analyze_velocity_trend edge cases
# -----------------------------------------------------------


def test_analyze_velocity_trend_zero_older_velocity(analytics):
    """Test velocity trend when older velocity is zero."""
    absorption_data = [
        _make_absorption(avg_units_per_month=0),
        _make_absorption(avg_units_per_month=0),
        _make_absorption(avg_units_per_month=0),
        _make_absorption(avg_units_per_month=50),
        _make_absorption(avg_units_per_month=55),
        _make_absorption(avg_units_per_month=60),
    ]

    result = analytics._analyze_velocity_trend(absorption_data)
    # When older velocity is 0, should return stable
    assert result == "stable"


# -----------------------------------------------------------
# Edge cases for seasonal patterns
# -----------------------------------------------------------


def test_detect_seasonal_patterns_empty_monthly_avg(analytics):
    """Test seasonal patterns with data that results in empty monthly averages."""
    # All data points have same month - should still work
    absorption_data = [
        _make_absorption(tracking_date=date(2023, 1, d), sales_absorption_rate=5.0 + d)
        for d in range(1, 13)
    ]

    result = analytics._detect_seasonal_patterns(absorption_data)

    # Should have peak/low both at January since all data is January
    assert result.get("peak_month") == 1
    assert result.get("low_month") == 1
