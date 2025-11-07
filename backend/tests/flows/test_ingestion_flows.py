from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.flows import ingestion as ingestion_flows


class _SessionStub:
    def __init__(self):
        self.commits = 0

    async def commit(self):
        self.commits += 1


class _SessionContext:
    def __init__(self, session):
        self._session = session

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
async def test_material_standard_ingestion_flow_records_and_alerts(monkeypatch):
    session = _SessionStub()
    start_run = SimpleNamespace(id="run-1")

    async def _start(session, flow_name):
        return start_run

    async def _complete(session, run, **kwargs):
        assert kwargs["records_ingested"] == 2

    async def _upsert(session, payload):
        assert payload["name"]

    alerts_called = {}

    async def _create_alert(session, **kwargs):
        alerts_called["payload"] = kwargs

    monkeypatch.setattr(
        ingestion_flows.ingestion_service, "start_ingestion_run", _start
    )
    monkeypatch.setattr(
        ingestion_flows.ingestion_service, "complete_ingestion_run", _complete
    )
    monkeypatch.setattr(ingestion_flows.standards, "upsert_material_standard", _upsert)
    monkeypatch.setattr(ingestion_flows.alerts, "create_alert", _create_alert)

    records = [
        {"name": "Concrete Mix A", "suspected_update": True},
        {"name": "Steel Grade B"},
    ]
    result = await ingestion_flows.material_standard_ingestion_flow(
        records, session_factory=lambda: _SessionContext(session)
    )

    assert result == {"records_ingested": 2, "suspected_updates": 1}
    assert alerts_called["payload"]["alert_type"] == "material_standard_update"
    assert session.commits == 1


@pytest.mark.asyncio
async def test_material_standard_ingestion_flow_handles_zero_updates(monkeypatch):
    session = _SessionStub()

    async def _start(*args, **kwargs):
        return SimpleNamespace(id="run-2")

    monkeypatch.setattr(
        ingestion_flows.ingestion_service,
        "start_ingestion_run",
        _start,
    )

    async def _complete(*args, **kwargs):
        return None

    monkeypatch.setattr(
        ingestion_flows.ingestion_service, "complete_ingestion_run", _complete
    )

    async def _noop(*args, **kwargs):
        return None

    monkeypatch.setattr(ingestion_flows.standards, "upsert_material_standard", _noop)

    alerted = {"called": False}
    monkeypatch.setattr(
        ingestion_flows.alerts,
        "create_alert",
        lambda *_, **__: alerted.__setitem__("called", True),
    )

    result = await ingestion_flows.material_standard_ingestion_flow(
        [{"name": "Concrete Mix C"}],
        session_factory=lambda: _SessionContext(session),
    )
    assert result == {"records_ingested": 1, "suspected_updates": 0}
    assert alerted["called"] is False
