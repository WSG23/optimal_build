"""Tests for market intelligence orchestration flows."""

from __future__ import annotations

import importlib
import sys
from datetime import date
from types import SimpleNamespace

import pytest

from tests.helpers import (
    ensure_sqlite_uuid,
    install_market_analytics_stub,
    install_market_data_stub,
    install_property_stub,
)


class _StubSession:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):  # pragma: no cover
        return False


class _SessionFactory:
    def __call__(self):
        return _StubSession()


@pytest.mark.asyncio
async def test_refresh_market_intelligence_uses_stub(monkeypatch) -> None:
    ensure_sqlite_uuid(monkeypatch)
    install_property_stub(monkeypatch)
    install_market_data_stub(monkeypatch)

    calls: list[tuple[str, str, int]] = []

    class _Analytics:
        def __init__(self, *_: object, **__: object) -> None:
            pass

        async def generate_market_report(
            self,
            *,
            property_type,
            location,
            period_months,
            session,
            **kwargs,
        ):
            calls.append((property_type.value, location, period_months))

            class _MinimalReport:
                def __init__(self) -> None:
                    self.property_type = property_type
                    self.location = location
                    self.period = (date(2024, 1, 1), date(2024, 2, 1))
                    self.comparables = {}
                    self.supply = {}
                    self.yields = {}
                    self.absorption = {}
                    self.cycle = {}
                    self.recommendations = []

                def to_dict(self) -> dict[str, object]:
                    return {
                        "property_type": property_type.value,
                        "location": location,
                        "period": {
                            "start": self.period[0].isoformat(),
                            "end": self.period[1].isoformat(),
                        },
                    }

            return _MinimalReport()

    install_market_analytics_stub(monkeypatch, _Analytics)

    sys.modules.pop("backend.flows.analytics_flow", None)
    analytics_flow = importlib.import_module("backend.flows.analytics_flow")

    property_type = SimpleNamespace(value="office")
    results = await analytics_flow.refresh_market_intelligence(
        _SessionFactory(),
        property_types=[property_type],
        locations=["all"],
        period_months=6,
    )

    assert calls == [("office", "all", 6)]
    assert results[0]["location"] == "all"
