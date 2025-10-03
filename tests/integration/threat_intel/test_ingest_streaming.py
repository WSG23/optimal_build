"""Integration-level validation for Prefect schedule helpers."""

from __future__ import annotations

import importlib
import sys
from types import SimpleNamespace

import pytest

from tests.helpers import (
    ensure_sqlite_uuid,
    install_market_analytics_stub,
    install_market_data_stub,
    install_property_stub,
)


@pytest.mark.asyncio
async def test_ensure_deployments_no_prefect(monkeypatch) -> None:
    ensure_sqlite_uuid(monkeypatch)
    install_property_stub(monkeypatch)
    install_market_data_stub(monkeypatch)

    class _Analytics:
        async def generate_market_report(self, **_: object):
            payload = SimpleNamespace()
            payload.property_type = SimpleNamespace(value="office")
            payload.location = "all"
            payload.period = (None, None)
            payload.comparables = {}
            payload.supply = {}
            payload.yields = {}
            payload.absorption = {}
            payload.cycle = {}
            payload.recommendations = []

            def _to_dict():
                return {"property_type": "office", "location": "all", "period": {}}

            payload.to_dict = _to_dict
            return payload

    install_market_analytics_stub(monkeypatch, _Analytics)

    sys.modules.pop("backend.flows.schedules", None)
    schedules = importlib.import_module("backend.flows.schedules")

    monkeypatch.setattr(schedules, "Deployment", None, raising=False)
    monkeypatch.setattr(schedules, "CronSchedule", None, raising=False)

    await schedules.ensure_deployments()
