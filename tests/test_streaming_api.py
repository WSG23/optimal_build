"""API function tests for the market intelligence router."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
import importlib
import importlib.util
import sys
from types import SimpleNamespace

import pytest

from tests.helpers import (
    ensure_sqlite_uuid,
    install_market_analytics_stub,
    install_market_data_stub,
    install_property_stub,
)

pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")


class _StubReport:
    def __init__(self) -> None:
        self.property_type = "office"
        self.location = "all"
        self.period = (date(2024, 1, 1), date(2024, 2, 1))
        self.comparables = {"transactions": 0}
        self.supply = {"projects": 0}
        self.yields = {"cap_rate": 0}
        self.absorption = {"message": "steady"}
        self.cycle = {"phase": "recovery"}
        self.recommendations = ["Hold"]
        self.generated_at = datetime(2024, 3, 1, 12, 0, 0)


@pytest.mark.asyncio
async def test_generate_market_report_endpoint(monkeypatch) -> None:
    ensure_sqlite_uuid(monkeypatch)
    install_property_stub(monkeypatch)
    install_market_data_stub(monkeypatch)

    class _Analytics:
        def __init__(self, *_: object, **__: object) -> None:
            pass

        async def generate_market_report(self, **_: object) -> _StubReport:
            return _StubReport()

    install_market_analytics_stub(monkeypatch, _Analytics)

    project_root = Path(__file__).resolve().parents[1]
    module_path = (
        project_root / "backend" / "app" / "api" / "v1" / "market_intelligence.py"
    )
    sys.modules.pop("backend.app.api.v1.market_intelligence", None)

    spec = importlib.util.spec_from_file_location(
        "unit_tests.market_intelligence", module_path
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)

    response = await module.generate_market_report(  # type: ignore[attr-defined]
        property_type=module.PropertyType("office"),
        location="all",
        period_months=12,
        competitive_set_id=None,
        session=SimpleNamespace(),
    )

    assert response.report.location == "all"
    assert response.report.period.start == date(2024, 1, 1)
