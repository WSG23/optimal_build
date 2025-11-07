from __future__ import annotations

from datetime import datetime

import pytest
from unittest.mock import AsyncMock

from app.api.v1 import market_intelligence as mi_api
from app.main import app


class _StubReport:
    def __init__(self):
        self.property_type = mi_api.PropertyType.OFFICE
        self.location = "D01"
        self.period = (datetime.utcnow().date(), datetime.utcnow().date())
        self.comparables = {"transaction_count": 3}
        self.supply = {"summary": "ok"}
        self.yields = {"median": 3.4}
        self.absorption = {"velocity": "stable"}
        self.cycle = {"phase": "expansion"}
        self.recommendations = ["Hold inventory"]
        self.generated_at = datetime.utcnow()

    def to_dict(self):
        return {"summary": "ok"}


@pytest.fixture(autouse=True)
def override_market_intel_session():
    async def _get_session():
        yield object()

    app.dependency_overrides[mi_api.get_session] = _get_session
    yield
    app.dependency_overrides.pop(mi_api.get_session, None)


@pytest.mark.asyncio
async def test_generate_market_report_success(client, monkeypatch):
    report = _StubReport()
    monkeypatch.setattr(
        mi_api._market_analytics,
        "generate_market_report",
        AsyncMock(return_value=report),
    )

    response = await client.get(
        "/api/v1/market-intelligence/report",
        params={"property_type": "office", "location": "D01", "period_months": 6},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["report"]["property_type"] == "office"
    # type: ignore[attr-defined]
    mi_api._market_analytics.generate_market_report.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_market_report_failure(client, monkeypatch):
    monkeypatch.setattr(
        mi_api._market_analytics,
        "generate_market_report",
        AsyncMock(side_effect=RuntimeError("boom")),
    )

    response = await client.get(
        "/api/v1/market-intelligence/report",
        params={"property_type": "office"},
    )

    assert response.status_code == 500
