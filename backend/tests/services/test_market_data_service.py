from __future__ import annotations

from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
import random

import pytest

from app.models.property import PropertyType
from app.services.agents.market_data_service import (
    MarketDataService,
    MockMarketDataProvider,
)


class RecordingSession:
    def __init__(self):
        self.statements: list[object] = []
        self.commits = 0

    async def execute(self, stmt, params=None):
        self.statements.append((stmt, params))
        # Return object with scalars().all() for compatibility
        return SimpleNamespace(
            scalars=lambda: SimpleNamespace(
                all=lambda: [], unique=lambda: SimpleNamespace(all=lambda: [])
            ),
            scalar_one_or_none=lambda: None,
        )

    async def commit(self):
        self.commits += 1


class _Result:
    def __init__(self, record):
        self._record = record

    def scalar_one_or_none(self):
        return self._record


class PropertySession:
    def __init__(self, results: list[_Result]):
        self.results = results
        self.executed: list[object] = []

    async def execute(self, stmt):
        self.executed.append(stmt)
        if self.results:
            return self.results.pop(0)
        return SimpleNamespace(
            scalars=lambda: SimpleNamespace(all=lambda: []),
            scalar_one_or_none=lambda: None,
        )


@pytest.mark.asyncio
async def test_mock_provider_generates_transactions_and_rentals():
    provider = MockMarketDataProvider()
    txns = await provider.fetch_transactions({"count": 2, "property_type": "office"})
    rentals = await provider.fetch_rental_data({"count": 2, "property_type": "office"})
    indices = await provider.fetch_market_indices({})

    assert len(txns) == 2
    assert all("transaction_id" in t and "sale_price" in t for t in txns)
    assert len(rentals) == 2
    assert all("listing_id" in r and "asking_rent_monthly" in r for r in rentals)
    assert len(indices) == 12
    assert indices[0]["index_name"].startswith("Mock_")


@pytest.mark.asyncio
async def test_store_transactions_converts_payload(monkeypatch):
    service = MarketDataService()
    session = RecordingSession()
    monkeypatch.setattr(
        service, "_get_or_create_property", AsyncMock(return_value="prop-1")
    )

    payload = [
        {
            "transaction_date": "2024-01-15",
            "sale_price": "1000000",
            "psf_price": "2500",
            "floor_area_sqm": "500",
        }
    ]
    stored = await service._store_transactions(payload, "mock", session)
    assert stored == 1
    assert len(session.statements) == 1  # upsert called


@pytest.mark.asyncio
async def test_store_rentals_upserts_records(monkeypatch):
    service = MarketDataService()
    session = RecordingSession()
    monkeypatch.setattr(
        service, "_get_or_create_property", AsyncMock(return_value="prop-2")
    )

    payload = [
        {
            "listing_date": "2024-02-01",
            "floor_area_sqm": "800",
            "asking_rent_monthly": "12000",
            "asking_psf_monthly": "7.5",
            "floor_level": "15",
            "available_date": "2024-03-01",
        }
    ]
    stored = await service._store_rentals(payload, "mock", session)
    assert stored == 1
    assert len(session.statements) == 1


@pytest.mark.asyncio
async def test_store_indices_handles_updates():
    service = MarketDataService()
    session = RecordingSession()
    payload = [
        {
            "index_date": "2024-01-01",
            "index_name": "PPI",
            "index_value": "101.5",
            "mom_change": "0.5",
            "yoy_change": "2.0",
        }
    ]
    stored = await service._store_indices(payload, "mock", session)
    assert stored == 1
    assert len(session.statements) == 1


def test_register_provider_and_sync_dates():
    service = MarketDataService()
    stub_provider = MockMarketDataProvider()
    service.register_provider("custom", stub_provider)
    assert "custom" in service.providers

    # Confirm last sync accessor respects history
    today = date.today()
    service.sync_history["custom"] = datetime(today.year, today.month, today.day)
    assert service._get_last_sync_date("custom") == today


@pytest.mark.asyncio
async def test_get_or_create_property_returns_existing():
    service = MarketDataService()
    session = PropertySession(results=[_Result(SimpleNamespace(id="prop-existing"))])

    prop_id = await service._get_or_create_property(
        {"property_name": "Existing Tower"}, session
    )
    assert prop_id == "prop-existing"
    assert len(session.executed) == 1


@pytest.mark.asyncio
async def test_get_or_create_property_creates_new(monkeypatch):
    service = MarketDataService()
    session = PropertySession(results=[_Result(None)])

    monkeypatch.setattr(random, "uniform", lambda *args, **kwargs: 0)
    payload = {
        "property_name": "New Plaza",
        "floor_area_sqm": "1200",
        "property_type": "office",
        "district": "D01",
    }

    prop_id = await service._get_or_create_property(payload, session)
    assert prop_id
    assert len(session.executed) >= 2  # select + insert


class _AsyncSessionStub:
    def __init__(self):
        self.commits = 0

    async def commit(self):
        self.commits += 1


@pytest.mark.asyncio
async def test_sync_provider_accumulates_results(monkeypatch):
    service = MarketDataService()
    provider = SimpleNamespace(
        fetch_transactions=AsyncMock(return_value=[{"id": 1}]),
        fetch_rental_data=AsyncMock(return_value=[{"id": 2}]),
        fetch_market_indices=AsyncMock(return_value=[{"id": 3}]),
    )
    session = _AsyncSessionStub()

    monkeypatch.setattr(service, "_store_transactions", AsyncMock(return_value=2))
    monkeypatch.setattr(service, "_store_rentals", AsyncMock(return_value=1))
    monkeypatch.setattr(service, "_store_indices", AsyncMock(return_value=4))
    monkeypatch.setattr(
        service, "_calculate_yield_benchmarks", AsyncMock(return_value=None)
    )
    monkeypatch.setattr(
        service, "_update_absorption_metrics", AsyncMock(return_value=None)
    )

    result = await service.sync_provider(
        "mocked", provider, session, property_types=[PropertyType.OFFICE]
    )

    assert result["results"]["transactions"] == 2
    assert result["results"]["rentals"] == 1
    assert result["results"]["indices"] == 4
    assert "mocked" in service.sync_history
    assert session.commits == 1


@pytest.mark.asyncio
async def test_sync_provider_collects_errors(monkeypatch):
    service = MarketDataService()
    provider = SimpleNamespace(
        fetch_transactions=AsyncMock(side_effect=RuntimeError("boom")),
        fetch_rental_data=AsyncMock(return_value=[]),
        fetch_market_indices=AsyncMock(return_value=[]),
    )
    session = _AsyncSessionStub()

    monkeypatch.setattr(service, "_store_transactions", AsyncMock(return_value=0))
    monkeypatch.setattr(service, "_store_rentals", AsyncMock(return_value=0))
    monkeypatch.setattr(service, "_store_indices", AsyncMock(return_value=0))
    monkeypatch.setattr(
        service, "_calculate_yield_benchmarks", AsyncMock(return_value=None)
    )
    monkeypatch.setattr(
        service, "_update_absorption_metrics", AsyncMock(return_value=None)
    )

    result = await service.sync_provider(
        "mocked", provider, session, property_types=[PropertyType.OFFICE]
    )
    assert result["results"]["errors"]
