"""Pydantic schema validation for market reports."""

import importlib
import sys
from datetime import date, datetime

from tests.helpers import ensure_sqlite_uuid, install_property_stub


def test_market_report_schema(monkeypatch):
    ensure_sqlite_uuid(monkeypatch)
    install_property_stub(monkeypatch)
    sys.modules.pop("app.schemas.market", None)
    module = importlib.import_module("app.schemas.market")

    payload = module.MarketReportPayload(
        property_type="office",
        location="all",
        period=module.MarketPeriod(start=date(2024, 1, 1), end=date(2024, 2, 1)),
        comparables_analysis={"transaction_count": 0},
        supply_dynamics={"pipeline_projects": 0},
        yield_benchmarks={"cap_rate": 0.0},
        absorption_trends={"message": "steady"},
        market_cycle_position={"phase": "recovery"},
        recommendations=["Monitor"],
    )

    response = module.MarketReportResponse(
        report=payload, generated_at=datetime(2024, 3, 1, 12, 0)
    )
    assert response.report.location == "all"
