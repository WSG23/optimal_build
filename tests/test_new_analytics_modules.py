"""Analytics module smoke tests for schema utilities."""

import importlib
import sys
from datetime import date

from tests.helpers import ensure_sqlite_uuid, install_property_stub


def test_market_report_payload_accepts_basic_dict(monkeypatch):
    ensure_sqlite_uuid(monkeypatch)
    install_property_stub(monkeypatch)
    sys.modules.pop("app.schemas.market", None)
    sys.modules.pop("backend.app.schemas.market", None)
    module = importlib.import_module("app.schemas.market")

    payload = module.MarketReportPayload(
        property_type="retail",
        location="central",
        period=module.MarketPeriod(start=date(2024, 1, 1), end=date(2024, 2, 1)),
        comparables_analysis={"transaction_count": 1},
        supply_dynamics={"pipeline_projects": 0},
        yield_benchmarks={"cap_rate": 5.0},
        absorption_trends={"velocity": "steady"},
        market_cycle_position={"phase": "expansion"},
        recommendations=["Increase marketing"],
    )

    assert payload.location == "central"
    assert payload.recommendations == ["Increase marketing"]
