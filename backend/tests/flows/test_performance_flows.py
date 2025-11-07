from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.flows import performance


def test_parse_agent_ids_returns_valid_uuid_list():
    valid = str(uuid4())
    result = performance._parse_agent_ids([valid, "not-a-uuid", None])
    assert result and len(result) == 1
    assert str(result[0]) == valid
    assert performance._parse_agent_ids(None) is None


def test_parse_date_handles_blank_inputs():
    assert performance._parse_date(" 2024-01-15 ") == date(2024, 1, 15)
    assert performance._parse_date("   ") is None
    assert performance._parse_date(None) is None


class _AsyncSessionStub:
    async def __aenter__(self):
        return SimpleNamespace()

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
async def test_agent_performance_snapshots_flow_invokes_service(monkeypatch):
    captured = {}

    class StubService:
        async def generate_daily_snapshots(self, session, as_of, agent_ids):
            captured["as_of"] = as_of
            captured["agent_ids"] = agent_ids
            return [1, 2, 3]

    monkeypatch.setattr(performance, "AgentPerformanceService", lambda: StubService())
    monkeypatch.setattr(performance, "AsyncSessionLocal", lambda: _AsyncSessionStub())

    future = await performance.agent_performance_snapshots_flow(
        agent_ids=[str(uuid4()), "invalid"], as_of="2024-02-01"
    )
    assert future["snapshots"] == 3
    assert captured["as_of"] == date(2024, 2, 1)
    assert len(captured["agent_ids"]) == 1


@pytest.mark.asyncio
async def test_seed_performance_benchmarks_flow_returns_count(monkeypatch):
    class StubService:
        async def seed_default_benchmarks(self, session):
            return 7

    monkeypatch.setattr(performance, "AgentPerformanceService", lambda: StubService())
    monkeypatch.setattr(performance, "AsyncSessionLocal", lambda: _AsyncSessionStub())

    result = await performance.seed_performance_benchmarks_flow()
    assert result == {"benchmarks": 7}
