from __future__ import annotations

from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.models.property import PropertyType
from app.services.agents.market_intelligence_analytics import (
    MarketIntelligenceAnalytics,
    MarketReport,
)


@pytest.fixture
def analytics():
    instance = MarketIntelligenceAnalytics.__new__(MarketIntelligenceAnalytics)
    instance.metrics = None
    return instance


def test_generate_recommendations_positive_trends(analytics):
    recommendations = analytics._generate_recommendations(
        comparables={"price_trend": "upward"},
        supply={"supply_pressure": "low"},
        yields={"market_position": "yields_compressed"},
        absorption={"velocity_trend": "accelerating"},
        cycle={"current_phase": "expansion"},
    )

    joined = " ".join(recommendations)
    assert "price momentum" in joined
    assert "premium positioning" in joined
    assert "Compressed yields" in joined
    assert "Absorption accelerating" in joined
    assert "expansion phase" in joined
    assert recommendations[-1].startswith("Continue monitoring")


def test_generate_recommendations_negative_trends(analytics):
    recommendations = analytics._generate_recommendations(
        comparables={"price_trend": "downward"},
        supply={"supply_pressure": "high"},
        yields={"market_position": "yields_elevated"},
        absorption={"velocity_trend": "decelerating"},
        cycle={"current_phase": "hyper_supply"},
    )

    text = " ".join(recommendations)
    assert "value-add initiatives" in text
    assert "High supply pressure" in text
    assert "Elevated yields" in text
    assert "Absorption slowing" in text
    assert "oversupply phase" in text


def test_record_metrics_emits_gauges(monkeypatch):
    analytics = MarketIntelligenceAnalytics.__new__(MarketIntelligenceAnalytics)
    calls = []

    class StubMetrics:
        def record_gauge(self, name, value, tags):
            calls.append((name, value, tags))

    analytics.metrics = StubMetrics()
    yields_payload = {
        "current_metrics": {
            "cap_rate": {"median": 0.042},
            "rental_rates": {"median_psf": 11.5},
        }
    }

    analytics._record_metrics(PropertyType.OFFICE, "D01", yields_payload)

    assert calls == [
        (
            "market_intelligence.cap_rate",
            0.042,
            {"property_type": "office", "location": "D01"},
        ),
        (
            "market_intelligence.rental_psf",
            11.5,
            {"property_type": "office", "location": "D01"},
        ),
    ]


def test_record_metrics_no_metrics_collector():
    analytics = MarketIntelligenceAnalytics.__new__(MarketIntelligenceAnalytics)
    analytics.metrics = None

    # Should be a no-op without raising
    analytics._record_metrics(PropertyType.RETAIL, "D09", {})


def test_determine_index_trend_variants():
    analytics = MarketIntelligenceAnalytics.__new__(MarketIntelligenceAnalytics)
    uptrend = analytics._determine_index_trend(
        [
            SimpleNamespace(mom_change=1.0),
            SimpleNamespace(mom_change=0.8),
            SimpleNamespace(mom_change=0.5),
        ]
    )
    assert uptrend == "uptrend"

    downtrend = analytics._determine_index_trend(
        [
            SimpleNamespace(mom_change=-0.2),
            SimpleNamespace(mom_change=-0.5),
            SimpleNamespace(mom_change=-0.9),
        ]
    )
    assert downtrend == "downtrend"

    sideways = analytics._determine_index_trend(
        [
            SimpleNamespace(mom_change=0.1),
            SimpleNamespace(mom_change=-0.2),
            SimpleNamespace(mom_change=0.0),
        ]
    )
    assert sideways == "sideways"


def test_analyze_index_trends_returns_metrics():
    analytics = MarketIntelligenceAnalytics.__new__(MarketIntelligenceAnalytics)
    indices = [
        SimpleNamespace(
            index_value=101.5,
            mom_change=0.8,
            qoq_change=1.5,
            yoy_change=3.2,
        ),
        SimpleNamespace(
            index_value=100.0, mom_change=-0.2, qoq_change=0.1, yoy_change=2.8
        ),
        SimpleNamespace(
            index_value=99.0, mom_change=0.1, qoq_change=0.0, yoy_change=2.5
        ),
    ]
    analytics._determine_index_trend = lambda *_: "uptrend"
    payload = analytics._analyze_index_trends(indices)
    assert payload["trend"] == "uptrend"
    assert payload["current_index"] == 101.5


def test_market_report_to_dict_serializes_period():
    period = (date(2024, 1, 1), date(2024, 1, 31))
    report = MarketReport(
        property_type=PropertyType.OFFICE,
        location="D01",
        period=period,
        comparables_analysis={"price_trend": "upward"},
        supply_dynamics={"supply_pressure": "low"},
        yield_benchmarks={"current_metrics": {}},
        absorption_trends={"velocity_trend": "stable"},
        market_cycle_position={"current_phase": "expansion"},
        recommendations=["Monitor weekly."],
    )
    payload = report.to_dict()
    assert payload["property_type"] == "office"
    assert payload["period"]["start"] == "2024-01-01"
    assert payload["recommendations"][0].startswith("Monitor")


@pytest.mark.asyncio
async def test_generate_market_report_aggregates_sections():
    analytics = MarketIntelligenceAnalytics.__new__(MarketIntelligenceAnalytics)
    analytics.market_data = SimpleNamespace()
    analytics.metrics = None

    analytics._analyze_comparables = AsyncMock(return_value={"price_trend": "upward"})
    analytics._analyze_supply_dynamics = AsyncMock(
        return_value={"supply_pressure": "low"}
    )
    analytics._analyze_yield_benchmarks = AsyncMock(
        return_value={"market_position": "yields_compressed"}
    )
    analytics._analyze_absorption_trends = AsyncMock(
        return_value={"velocity_trend": "accelerating"}
    )
    analytics._analyze_market_cycle = AsyncMock(
        return_value={"current_phase": "expansion"}
    )

    report = await analytics.generate_market_report(
        PropertyType.OFFICE,
        location="D01",
        period_months=3,
        session=SimpleNamespace(),
    )

    payload = report.to_dict()
    assert payload["comparables_analysis"]["price_trend"] == "upward"
    assert payload["location"] == "D01"
    assert payload["recommendations"]


class _ExecuteResult:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return SimpleNamespace(
            all=lambda: list(self._items),
            unique=lambda: SimpleNamespace(all=lambda: list(self._items)),
        )


class _SessionStub:
    def __init__(self, batches):
        self._batches = list(batches)

    async def execute(self, _stmt):
        return _ExecuteResult(self._batches.pop(0))


@pytest.mark.asyncio
async def test_analyze_comparables_summarises_transactions():
    analytics = MarketIntelligenceAnalytics.__new__(MarketIntelligenceAnalytics)
    analytics.metrics = None
    txn = SimpleNamespace(
        transaction_date=date(2024, 1, 10),
        sale_price=5_000_000,
        psf_price=2500.0,
        property=SimpleNamespace(name="Alpha Tower"),
        buyer_type="REIT",
    )
    session = _SessionStub([[txn]])
    result = await analytics._analyze_comparables(
        PropertyType.OFFICE,
        location="D01",
        period=(date(2023, 1, 1), date(2024, 2, 1)),
        session=session,
    )
    assert result["transaction_count"] == 1
    assert result["average_psf"] == 2500.0


@pytest.mark.asyncio
async def test_analyze_supply_dynamics_groups_pipeline_projects():
    analytics = MarketIntelligenceAnalytics.__new__(MarketIntelligenceAnalytics)
    analytics.metrics = None
    project = SimpleNamespace(
        project_name="Harbor Residences",
        developer="DevCo",
        total_gfa_sqm=150000.0,
        total_units=400,
        expected_completion=date(2026, 6, 1),
        development_status=SimpleNamespace(value="planned"),
    )
    session = _SessionStub([[project]])
    result = await analytics._analyze_supply_dynamics(
        PropertyType.RESIDENTIAL,
        location="D02",
        period=(date(2023, 1, 1), date(2025, 1, 1)),
        session=session,
    )
    assert result["pipeline_projects"] == 1
    assert result["supply_by_year"][2026]["projects"] == 1


@pytest.mark.asyncio
async def test_analyze_yield_benchmarks_derives_trends():
    analytics = MarketIntelligenceAnalytics.__new__(MarketIntelligenceAnalytics)
    analytics.metrics = None
    benchmarks = [
        SimpleNamespace(
            benchmark_date=datetime(2023, month, 1),
            cap_rate_mean=0.045,
            cap_rate_median=0.044 + month * 0.0001,
            cap_rate_p25=0.042,
            cap_rate_p75=0.046,
            rental_psf_median=11.0 + month * 0.05,
            rental_psf_mean=11.2 + month * 0.05,
            total_transaction_value=80_000_000 + month * 1_000_000,
            occupancy_rate_mean=0.92,
            transaction_count=15,
        )
        for month in range(1, 13)
    ]
    session = _SessionStub([benchmarks])
    result = await analytics._analyze_yield_benchmarks(
        PropertyType.OFFICE,
        location="all",
        period=(date(2023, 1, 1), date(2023, 12, 31)),
        session=session,
    )
    assert "current_metrics" in result
    assert result["current_metrics"]["cap_rate"]["median"] > 0
