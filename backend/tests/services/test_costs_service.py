from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.services import costs as costs_service


class _ExecuteResult:
    def __init__(self, record=None, records=None):
        self._record = record
        self._records = records or []

    def scalar_one_or_none(self):
        return self._record

    def scalars(self):
        return self

    def all(self):
        return list(self._records)


class _SessionStub:
    def __init__(self, results):
        self._results = list(results)
        self.added = []
        self.flushed = False

    async def execute(self, _stmt):
        return self._results.pop(0)

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        self.flushed = True


@pytest.mark.asyncio
async def test_upsert_cost_index_inserts_and_updates(monkeypatch):
    events = []
    monkeypatch.setattr(
        costs_service, "log_event", lambda *args, **kwargs: events.append(kwargs)
    )

    payload = {
        "jurisdiction": "SG",
        "series_name": "BCA",
        "period": "2024-Q1",
        "value": 100.0,
    }
    session = _SessionStub([_ExecuteResult(record=None)])
    record = await costs_service.upsert_cost_index(session, payload)
    assert session.added and session.flushed
    assert record.series_name == "BCA"
    assert events[-1]["action"] == "created"

    existing = SimpleNamespace(
        jurisdiction="SG",
        series_name="BCA",
        period="2024-Q2",
        value=90.0,
        unit="index",
        source="BCA",
        category=None,
        subcategory=None,
        provider=None,
        methodology=None,
    )
    session = _SessionStub([_ExecuteResult(record=existing)])
    payload = {
        "jurisdiction": "SG",
        "series_name": "BCA",
        "period": "2024-Q2",
        "value": 95.0,
    }
    record = await costs_service.upsert_cost_index(session, payload)
    assert record.value == 95.0
    assert events[-1]["action"] == "updated"


@pytest.mark.asyncio
async def test_get_latest_cost_index_and_catalog_workflows(monkeypatch):
    events = []
    monkeypatch.setattr(
        costs_service, "log_event", lambda *args, **kwargs: events.append(kwargs)
    )

    latest = SimpleNamespace(series_name="BCA", period="2024-Q2")
    session = _SessionStub([_ExecuteResult(record=latest)])
    record = await costs_service.get_latest_cost_index(
        session,
        series_name="BCA",
        jurisdiction="SG",
        provider="URA",
    )
    assert record is latest
    assert events[-1]["found"] is True

    session = _SessionStub([])
    catalog_payload = {
        "catalog_name": "COSTS",
        "item_code": "CLS-1",
        "category": "structure",
        "unit_cost": 1200.0,
    }
    catalog_record = await costs_service.add_cost_catalog_item(session, catalog_payload)
    assert catalog_record.catalog_name == "COSTS"

    catalog_items = [catalog_record]
    session = _SessionStub([_ExecuteResult(records=catalog_items)])
    entries = await costs_service.list_cost_catalog(
        session,
        catalog_name="COSTS",
        category="structure",
    )
    assert len(entries) == 1
    assert events[-1]["count"] == 1
