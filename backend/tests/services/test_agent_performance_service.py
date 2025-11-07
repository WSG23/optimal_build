from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.deals.performance import AgentPerformanceService

try:
    from unittest.mock import AsyncMock
except ImportError:  # pragma: no cover
    from asyncmock import AsyncMock  # type: ignore


class FakeAsyncSession:
    def __init__(self):
        self.committed = False
        self.refreshed = False
        self.executed_statements = []
        self.added_objects = []
        self.flushed = False
        self.execute_results: list[DummyResult] = []

    async def commit(self):
        self.committed = True

    async def refresh(self, snapshot):
        self.refreshed = True

    async def execute(self, stmt):
        self.executed_statements.append(stmt)
        if self.execute_results:
            return self.execute_results.pop(0)
        return DummyResult([])

    def add(self, obj):
        self.added_objects.append(obj)

    async def flush(self):
        self.flushed = True


class DummyScalars:
    def __init__(self, rows):
        self._rows = rows

    def unique(self):
        return self

    def all(self):
        return list(self._rows)

    def first(self):
        return self._rows[0] if self._rows else None

    def __iter__(self):
        return iter(self._rows)


class DummyResult:
    def __init__(self, rows, scalars_rows=None):
        self._rows = list(rows)
        self._scalars_rows = (
            list(scalars_rows) if scalars_rows is not None else list(rows)
        )

    def __iter__(self):
        return iter(self._rows)

    def scalars(self):
        return DummyScalars(self._scalars_rows)

    def scalar_one_or_none(self):
        return self._rows[0] if self._rows else None


def _make_deal(
    *,
    status: str,
    value: float,
    confidence: float,
    cycle_days: float | None,
) -> SimpleNamespace:
    created_at = datetime(2025, 1, 1)
    stage_events: list[SimpleNamespace] = []
    actual_close_date = None
    updated_at = created_at
    if cycle_days is not None:
        actual_close_date = created_at + timedelta(days=cycle_days)
        updated_at = actual_close_date
    return SimpleNamespace(
        status=status,
        estimated_value_amount=value,
        confidence=confidence,
        stage_events=stage_events,
        created_at=created_at,
        actual_close_date=actual_close_date,
        updated_at=updated_at,
        metadata={},
    )


@pytest.mark.asyncio
async def test_compute_snapshot_populates_metrics(monkeypatch):
    service = AgentPerformanceService()

    deals = [
        _make_deal(status="closed_won", value=100_000, confidence=0.8, cycle_days=12),
        _make_deal(status="open", value=50_000, confidence=0.5, cycle_days=None),
        _make_deal(status="closed_lost", value=20_000, confidence=0.3, cycle_days=None),
    ]

    snapshot = SimpleNamespace(
        deals_open=None,
        deals_closed_won=None,
        deals_closed_lost=None,
        gross_pipeline_value=None,
        weighted_pipeline_value=None,
        confirmed_commission_amount=None,
        disputed_commission_amount=None,
        avg_cycle_days=None,
        conversion_rate=None,
        roi_metrics=None,
        snapshot_context=None,
    )

    monkeypatch.setattr(service, "_load_deals", AsyncMock(return_value=deals))
    monkeypatch.setattr(
        service, "_commission_totals", AsyncMock(return_value=(12_500.0, 750.0))
    )
    monkeypatch.setattr(
        service, "_get_or_create_snapshot", AsyncMock(return_value=snapshot)
    )
    monkeypatch.setattr(
        service,
        "_aggregate_roi_metrics",
        AsyncMock(return_value={"projects": [], "summary": {}}),
    )

    session = FakeAsyncSession()
    agent_id = uuid4()

    result = await service.compute_snapshot(session=session, agent_id=agent_id)

    assert result is snapshot
    assert snapshot.deals_open == 1
    assert snapshot.deals_closed_won == 1
    assert snapshot.deals_closed_lost == 1
    assert snapshot.gross_pipeline_value == pytest.approx(170_000.0)
    assert snapshot.weighted_pipeline_value == pytest.approx(
        100_000 * 0.8 + 50_000 * 0.5 + 20_000 * 0.3
    )
    assert snapshot.confirmed_commission_amount == 12_500.0
    assert snapshot.disputed_commission_amount == 750.0
    assert snapshot.avg_cycle_days == pytest.approx(12.0)
    assert snapshot.conversion_rate == pytest.approx(1 / 2)
    assert snapshot.roi_metrics == {"projects": [], "summary": {}}
    assert snapshot.snapshot_context["weighted_to_gross_ratio"] == pytest.approx(
        snapshot.weighted_pipeline_value / snapshot.gross_pipeline_value, rel=1e-3
    )
    assert session.committed is True
    assert session.refreshed is True


@pytest.mark.asyncio
async def test_generate_daily_snapshots_uses_target_ids(monkeypatch):
    service = AgentPerformanceService()
    session = FakeAsyncSession()
    agent_ids = [uuid4(), uuid4()]
    snapshots = [SimpleNamespace(id=1), SimpleNamespace(id=2)]

    monkeypatch.setattr(service, "_all_agent_ids", AsyncMock(return_value=agent_ids))
    monkeypatch.setattr(
        service,
        "compute_snapshot",
        AsyncMock(side_effect=snapshots),
    )

    results = await service.generate_daily_snapshots(session=session)

    assert results == snapshots
    assert service.compute_snapshot.await_count == len(agent_ids)
    called_agent_ids = [
        call.kwargs["agent_id"] for call in service.compute_snapshot.await_args_list
    ]
    assert called_agent_ids == agent_ids


@pytest.mark.asyncio
async def test_commission_totals_none(monkeypatch):
    service = AgentPerformanceService()
    session = FakeAsyncSession()
    total = await service._commission_totals(session=session, deals=[])
    assert total == (0.0, 0.0)


@pytest.mark.asyncio
async def test_commission_totals_aggregates(monkeypatch):
    service = AgentPerformanceService()
    session = FakeAsyncSession()
    deals = [SimpleNamespace(id="a"), SimpleNamespace(id="b")]
    session.execute_results.append(DummyResult([("disputed", 300), ("confirmed", 700)]))
    confirmed, disputed = await service._commission_totals(session=session, deals=deals)
    assert confirmed == pytest.approx(700.0)
    assert disputed == pytest.approx(300.0)


@pytest.mark.asyncio
async def test_get_or_create_snapshot_returns_existing():
    service = AgentPerformanceService()
    session = FakeAsyncSession()
    existing = SimpleNamespace()
    session.execute_results.append(DummyResult([existing]))
    snapshot = await service._get_or_create_snapshot(
        session=session, agent_id=uuid4(), as_of=datetime.now().date()
    )
    assert snapshot is existing
    assert not session.added_objects


@pytest.mark.asyncio
async def test_get_or_create_snapshot_creates_new(monkeypatch):
    service = AgentPerformanceService()
    session = FakeAsyncSession()
    session.execute_results.append(DummyResult([]))
    snapshot = await service._get_or_create_snapshot(
        session=session, agent_id=uuid4(), as_of=datetime.now().date()
    )
    assert session.added_objects and session.flushed
    assert snapshot in session.added_objects


@pytest.mark.asyncio
async def test_all_agent_ids_filters_invalid():
    service = AgentPerformanceService()
    session = FakeAsyncSession()
    valid = uuid4()
    session.execute_results.append(DummyResult([], [str(valid), "not-a-uuid", " "]))
    ids = await service._all_agent_ids(session)
    assert ids == [valid]
