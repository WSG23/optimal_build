from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.api.v1 import agents as agents_api


@pytest.mark.asyncio
async def test_generate_market_report_returns_payload(client, monkeypatch):
    class DummyReport:
        def to_dict(self):
            return {"summary": "ok", "sections": []}

    mocked = AsyncMock(return_value=DummyReport())
    monkeypatch.setattr(
        agents_api.market_analytics,
        "generate_market_report",
        mocked,
    )

    response = await client.post(
        "/api/v1/agents/commercial-property/market-intelligence/report",
        json={"property_type": "office", "location": "D01"},
    )

    assert response.status_code == 200
    assert response.json()["summary"] == "ok"
    mocked.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_market_report_handles_error(client, monkeypatch):
    monkeypatch.setattr(
        agents_api.market_analytics,
        "generate_market_report",
        AsyncMock(side_effect=ValueError("unsupported type")),
    )

    response = await client.post(
        "/api/v1/agents/commercial-property/market-intelligence/report",
        json={"property_type": "land"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "unsupported type"


@pytest.mark.asyncio
async def test_sync_market_data_returns_summary(client, monkeypatch):
    monkeypatch.setattr(
        agents_api.market_data_service,
        "sync_all_providers",
        AsyncMock(return_value={"mock": {"transactions": 5}}),
    )

    response = await client.post(
        "/api/v1/agents/commercial-property/market-intelligence/sync",
        json={"property_types": ["office"]},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["results"]["mock"]["transactions"] == 5


@pytest.mark.asyncio
async def test_sync_market_data_handles_error(client, monkeypatch):
    monkeypatch.setattr(
        agents_api.market_data_service,
        "sync_all_providers",
        AsyncMock(side_effect=RuntimeError("provider down")),
    )

    response = await client.post(
        "/api/v1/agents/commercial-property/market-intelligence/sync",
        json={"property_types": ["retail"]},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "provider down"


@pytest.mark.asyncio
async def test_get_market_transactions_returns_serialised_rows(client, monkeypatch):
    txn = SimpleNamespace(
        id=uuid4(),
        property=SimpleNamespace(name="Alpha Tower", district="D02"),
        transaction_date=date(2025, 1, 15),
        sale_price=1_500_000,
        psf_price=2_100,
    )

    monkeypatch.setattr(
        agents_api.market_data_service,
        "get_transactions",
        AsyncMock(return_value=[txn]),
    )

    response = await client.get(
        "/api/v1/agents/commercial-property/market-intelligence/transactions",
        params={"property_type": "office", "location": "D02", "limit": 1},
    )

    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["property_name"] == "Alpha Tower"
    assert rows[0]["property_type"] == "office"
