from __future__ import annotations

from datetime import date, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from unittest.mock import AsyncMock

from app.api.v1 import performance as perf_api
from app.api.deps import RequestIdentity
from app.main import app


def _make_snapshot():
    return SimpleNamespace(
        id=uuid4(),
        agent_id=uuid4(),
        as_of_date=date(2025, 1, 1),
        deals_open=2,
        deals_closed_won=1,
        deals_closed_lost=0,
        gross_pipeline_value=1000000.0,
        weighted_pipeline_value=750000.0,
        confirmed_commission_amount=12000.0,
        disputed_commission_amount=0.0,
        avg_cycle_days=15.0,
        conversion_rate=0.5,
        roi_metrics={"projects": [], "summary": {"irr": 0.12}},
        snapshot_context={"weighted_to_gross_ratio": 0.75},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


def _make_benchmark():
    return SimpleNamespace(
        id=uuid4(),
        metric_key="dscr",
        asset_type="office",
        deal_type="lease",
        cohort="core",
        value_numeric=1.5,
        value_text=None,
        source="demo",
        effective_date=date(2024, 12, 1),
        metadata={"p90": 2.0},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture(autouse=True)
def override_performance_dependencies():
    async def _get_session():
        yield SimpleNamespace()

    app.dependency_overrides[perf_api.get_session] = _get_session
    app.dependency_overrides[perf_api.require_viewer] = lambda: RequestIdentity(
        role="viewer", user_id=str(uuid4()), email="viewer@example.com"
    )
    yield
    app.dependency_overrides.pop(perf_api.get_session, None)
    app.dependency_overrides.pop(perf_api.require_viewer, None)


@pytest.mark.asyncio
async def test_performance_summary_returns_snapshot(client, monkeypatch):
    snapshot = _make_snapshot()
    monkeypatch.setattr(
        perf_api.service, "compute_snapshot", AsyncMock(return_value=snapshot)
    )

    response = await client.get(
        "/api/v1/performance/summary",
        params={"agent_id": str(snapshot.agent_id)},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["agent_id"] == str(snapshot.agent_id)
    perf_api.service.compute_snapshot.assert_awaited_once()  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_create_snapshot_post_path(client, monkeypatch):
    snapshot = _make_snapshot()
    monkeypatch.setattr(
        perf_api.service, "compute_snapshot", AsyncMock(return_value=snapshot)
    )

    response = await client.post(
        "/api/v1/performance/snapshots",
        json={"agent_id": str(snapshot.agent_id), "as_of": "2025-01-01"},
    )
    assert response.status_code == 200
    assert response.json()["id"] == str(snapshot.id)


@pytest.mark.asyncio
async def test_list_snapshots_returns_collection(client, monkeypatch):
    snapshots = [_make_snapshot(), _make_snapshot()]
    monkeypatch.setattr(
        perf_api.service, "list_snapshots", AsyncMock(return_value=snapshots)
    )

    response = await client.get(
        "/api/v1/performance/snapshots",
        params={"agent_id": str(uuid4()), "limit": 2},
    )
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_generate_daily_snapshots(client, monkeypatch):
    snapshots = [_make_snapshot()]
    monkeypatch.setattr(
        perf_api.service,
        "generate_daily_snapshots",
        AsyncMock(return_value=snapshots),
    )

    response = await client.post(
        "/api/v1/performance/snapshots/generate",
        params={"as_of": "2025-01-01", "agent_ids": str(uuid4())},
    )
    assert response.status_code == 200
    assert response.json()[0]["id"] == str(snapshots[0].id)


@pytest.mark.asyncio
async def test_list_benchmarks_success(client, monkeypatch):
    benchmarks = [_make_benchmark()]
    monkeypatch.setattr(
        perf_api.service,
        "list_benchmarks",
        AsyncMock(return_value=benchmarks),
    )

    response = await client.get(
        "/api/v1/performance/benchmarks",
        params={"metric_key": "dscr"},
    )
    assert response.status_code == 200
    assert response.json()[0]["metric_key"] == "dscr"


@pytest.mark.asyncio
async def test_list_benchmarks_missing_metric_key(client):
    response = await client.get(
        "/api/v1/performance/benchmarks",
        params={"metric_key": ""},
    )
    assert response.status_code == 400
