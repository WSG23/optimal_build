"""Router-level tests for the market intelligence API."""

from __future__ import annotations

import importlib
import importlib.util
import sys
import types
from datetime import date, datetime
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")

from app.models.property import PropertyType


class _DummyReport:
    def __init__(self) -> None:
        self.property_type = PropertyType.OFFICE
        self.location = "all"
        self.period = (date(2024, 1, 1), date(2024, 3, 31))
        self.comparables = {"transaction_count": 0}
        self.supply = {"pipeline_projects": 0}
        self.yields = {"message": "No yield data available"}
        self.absorption = {"message": "No absorption data available"}
        self.cycle = {"phase": "unknown"}
        self.recommendations = ["Continue monitoring market indicators"]
        self.generated_at = datetime(2024, 4, 1, 12, 0, 0)


class _StubSession:  # pragma: no cover - simple sentinel
    pass


@pytest.mark.asyncio
async def test_market_intelligence_router_response(monkeypatch) -> None:
    project_root = Path(__file__).resolve().parents[1]
    module_path = (
        project_root / "backend" / "app" / "api" / "v1" / "market_intelligence.py"
    )

    app_base = importlib.import_module("app.models.base")
    app_property = importlib.import_module("app.models.property")
    monkeypatch.setitem(sys.modules, "backend.app.models.base", app_base)
    monkeypatch.setitem(sys.modules, "backend.app.models.property", app_property)

    market_data_module_name = "app.services.agents.market_data_service"
    stub_market_data = types.ModuleType(market_data_module_name)

    class MarketDataService:  # pragma: no cover - placeholder to satisfy import
        pass

    stub_market_data.MarketDataService = MarketDataService
    monkeypatch.setitem(sys.modules, market_data_module_name, stub_market_data)
    monkeypatch.setitem(
        sys.modules, "backend.app.services.agents.market_data_service", stub_market_data
    )

    metrics_module_name = "app.core.metrics"
    stub_metrics = types.ModuleType(metrics_module_name)

    class MetricsCollector:  # pragma: no cover - placeholder to satisfy import
        def record_gauge(self, *_, **__):
            pass

    stub_metrics.MetricsCollector = MetricsCollector
    monkeypatch.setitem(sys.modules, metrics_module_name, stub_metrics)
    monkeypatch.setitem(sys.modules, "backend.app.core.metrics", stub_metrics)

    database_module_name = "app.core.database"
    stub_database = types.ModuleType(database_module_name)

    async def get_session_stub() -> _StubSession:  # pragma: no cover - simple stub
        return _StubSession()

    stub_database.get_session = get_session_stub
    monkeypatch.setitem(sys.modules, database_module_name, stub_database)
    monkeypatch.setitem(sys.modules, "backend.app.core.database", stub_database)

    analytics_module_name = "app.services.agents.market_intelligence_analytics"
    stub_analytics = types.ModuleType(analytics_module_name)

    class MarketIntelligenceAnalytics:
        def __init__(self, *_: object, **__: object) -> None:
            pass

        async def generate_market_report(self, **_: object) -> _DummyReport:
            return _DummyReport()

    stub_analytics.MarketIntelligenceAnalytics = MarketIntelligenceAnalytics
    monkeypatch.setitem(sys.modules, analytics_module_name, stub_analytics)
    monkeypatch.setitem(
        sys.modules,
        "backend.app.services.agents.market_intelligence_analytics",
        stub_analytics,
    )

    module_name = "unit_tests.market_intelligence_router"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec and spec.loader  # pragma: no cover - safety check
    market_intelligence = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, module_name, market_intelligence)
    spec.loader.exec_module(market_intelligence)

    response = await market_intelligence.generate_market_report(  # type: ignore[attr-defined]
        property_type=PropertyType.OFFICE,
        location="all",
        period_months=12,
        session=_StubSession(),
    )

    assert response.report.property_type == PropertyType.OFFICE
    assert response.report.location == "all"
    assert response.report.period.start == date(2024, 1, 1)
    assert response.report.comparables_analysis["transaction_count"] == 0
    assert response.generated_at == datetime(2024, 4, 1, 12, 0, 0)
