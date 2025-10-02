from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa

if not hasattr(sa, "Decimal"):
    # SQLAlchemy 2.x exposes DECIMAL via "sqlalchemy.DECIMAL" but not "Decimal".
    from sqlalchemy import DECIMAL as _SQL_DECIMAL  # type: ignore

    sa.Decimal = _SQL_DECIMAL  # type: ignore[attr-defined]

import importlib
import sys
import types

models_base = importlib.import_module("app.models.base")
sys.modules.setdefault("backend.app.models.base", models_base)

if not hasattr(models_base, "TimestampMixin"):
    class TimestampMixin:  # pragma: no cover - compatibility shim for tests
        created_at = None
        updated_at = None

    models_base.TimestampMixin = TimestampMixin  # type: ignore[attr-defined]

property_models = sys.modules.get("app.models.property")
if property_models is None:
    property_models = importlib.import_module("app.models.property")
sys.modules.setdefault("backend.app.models.property", property_models)

market_models = sys.modules.get("app.models.market")
if market_models is None:
    market_models = importlib.import_module("app.models.market")
sys.modules.setdefault("backend.app.models.market", market_models)

if not hasattr(market_models, "MarketTransaction"):
    market_models.MarketTransaction = getattr(property_models, "MarketTransaction")
if not hasattr(market_models, "RentalListing"):
    market_models.RentalListing = getattr(property_models, "RentalListing")
if not hasattr(market_models, "CompetitiveSet"):
    class CompetitiveSet:  # pragma: no cover - analytics tests don't touch DB
        pass

    market_models.CompetitiveSet = CompetitiveSet
if not hasattr(market_models, "MarketIndex"):
    class MarketIndex:  # pragma: no cover - placeholder for imports
        pass

    market_models.MarketIndex = MarketIndex

market_data_module_name = "app.services.agents.market_data_service"
stub_market_data = types.ModuleType(market_data_module_name)


class MarketDataService:  # pragma: no cover - placeholder to satisfy import
    pass


stub_market_data.MarketDataService = MarketDataService
sys.modules[market_data_module_name] = stub_market_data
sys.modules["backend.app.services.agents.market_data_service"] = stub_market_data

metrics_module_name = "app.core.metrics"
stub_metrics = types.ModuleType(metrics_module_name)


class MetricsCollector:  # pragma: no cover - placeholder to satisfy import
    def record_gauge(self, *_, **__):
        pass


stub_metrics.MetricsCollector = MetricsCollector
sys.modules[metrics_module_name] = stub_metrics
sys.modules["backend.app.core.metrics"] = stub_metrics

from app.models.property import PropertyType
from app.services.agents.market_intelligence_analytics import (
    MarketIntelligenceAnalytics,
    MarketReport,
)


@pytest.fixture
def analytics_service():
    return MarketIntelligenceAnalytics(market_data_service=MagicMock())


def test_market_report_to_dict_serializes_fields():
    report = MarketReport(
        property_type=PropertyType.OFFICE,
        location="CBD",
        period=(date(2023, 1, 1), date(2023, 6, 30)),
        comparables_analysis={"transaction_count": 5},
        supply_dynamics={"pipeline_projects": 2},
        yield_benchmarks={"current_metrics": {}},
        absorption_trends={"velocity_trend": "stable"},
        market_cycle_position={"current_phase": "expansion"},
        recommendations=["Hold pricing"]
    )

    serialized = report.to_dict()

    assert serialized["property_type"] == PropertyType.OFFICE.value
    assert serialized["period"]["start"] == "2023-01-01"
    assert serialized["period"]["end"] == "2023-06-30"
    # generated_at stored as ISO string with date prefix
    assert serialized["generated_at"].startswith(str(date.today().year))


def test_calculate_price_trend_variations(analytics_service):
    quarterly = {
        "2023-Q1": {"avg_psf": 100},
        "2023-Q2": {"avg_psf": 105},
        "2023-Q3": {"avg_psf": 110},
        "2023-Q4": {"avg_psf": 120},
    }
    trend_up = analytics_service._calculate_price_trend(quarterly)

    quarterly_down = {
        "2023-Q1": {"avg_psf": 120},
        "2023-Q2": {"avg_psf": 110},
        "2023-Q3": {"avg_psf": 100},
        "2023-Q4": {"avg_psf": 95},
    }
    trend_down = analytics_service._calculate_price_trend(quarterly_down)

    quarterly_stable = {
        "2023-Q1": {"avg_psf": 100},
        "2023-Q2": {"avg_psf": 101},
        "2023-Q3": {"avg_psf": 102},
        "2023-Q4": {"avg_psf": 101},
    }
    trend_stable = analytics_service._calculate_price_trend(quarterly_stable)

    assert trend_up == "upward"
    assert trend_down == "downward"
    assert trend_stable == "stable"


def test_assess_yield_position_ranges(analytics_service):
    benchmark_low = SimpleNamespace(cap_rate_median=3.5)
    benchmark_mid = SimpleNamespace(cap_rate_median=5.0)
    benchmark_high = SimpleNamespace(cap_rate_median=6.2)

    assert (
        analytics_service._assess_yield_position(benchmark_low, PropertyType.OFFICE)
        == "yields_compressed"
    )
    assert (
        analytics_service._assess_yield_position(benchmark_mid, PropertyType.OFFICE)
        == "yields_normal"
    )
    assert (
        analytics_service._assess_yield_position(benchmark_high, PropertyType.OFFICE)
        == "yields_elevated"
    )


def test_forecast_absorption_projects_future(analytics_service):
    absorption_samples = [
        SimpleNamespace(
            sales_absorption_rate=rate,
            tracking_date=date(2023, month, 1)
        )
        for month, rate in enumerate(range(10, 70, 10), start=1)
    ]

    forecast = analytics_service._forecast_absorption(absorption_samples)

    assert forecast["current_absorption"] == pytest.approx(60)
    assert forecast["projected_absorption_6m"] == pytest.approx(62.1, rel=1e-3)
    assert forecast["avg_monthly_absorption"] == pytest.approx(35)
    assert forecast["estimated_sellout_months"] == pytest.approx(114.2857, rel=1e-3)


def test_detect_seasonal_patterns_returns_diagnostics(analytics_service):
    monthly_values = {
        1: 10,
        2: 12,
        3: 14,
        4: 16,
        5: 18,
        6: 30,
        7: 20,
        8: 18,
        9: 16,
        10: 14,
        11: 12,
        12: 8,
    }
    absorption_history = [
        SimpleNamespace(
            tracking_date=date(2023, month, 1),
            sales_absorption_rate=value
        )
        for month, value in monthly_values.items()
    ]

    seasonality = analytics_service._detect_seasonal_patterns(absorption_history)

    assert seasonality["peak_month"] == 6
    assert seasonality["peak_absorption"] == pytest.approx(30)
    assert seasonality["low_month"] == 12
    assert seasonality["low_absorption"] == pytest.approx(8)
    assert seasonality["seasonality_strength"] == pytest.approx(2.75, rel=1e-3)


def test_detect_seasonal_patterns_insufficient_data(analytics_service):
    short_history = [
        SimpleNamespace(
            tracking_date=date(2023, month, 1),
            sales_absorption_rate=10
        )
        for month in range(1, 6)
    ]

    seasonality = analytics_service._detect_seasonal_patterns(short_history)

    assert seasonality == {"message": "Insufficient data for seasonal analysis"}


def test_generate_recommendations_compiles_messages(analytics_service):
    recommendations = analytics_service._generate_recommendations(
        comparables={"price_trend": "upward"},
        supply={"supply_pressure": "high"},
        yields={"market_position": "yields_elevated"},
        absorption={"velocity_trend": "accelerating"},
        cycle={"current_phase": "expansion"},
    )

    assert any("accelerating" in rec for rec in recommendations)
    assert any("High supply" in rec for rec in recommendations)
    assert any("Elevated yields" in rec for rec in recommendations)
    assert any("Market in expansion" in rec for rec in recommendations)
    assert recommendations[-1] == "Continue monitoring market indicators weekly for early trend detection"
