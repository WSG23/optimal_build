from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.api.v1 import audit as audit_api


@pytest.mark.asyncio
async def test_list_project_audit_returns_serialised_logs(client, monkeypatch):
    logs = [SimpleNamespace(version=1), SimpleNamespace(version=2)]
    monkeypatch.setattr(audit_api, "verify_chain", AsyncMock(return_value=(True, logs)))
    monkeypatch.setattr(
        audit_api, "serialise_log", lambda log: {"version": log.version}
    )

    response = await client.get("/api/v1/audit/42")

    assert response.status_code == 200
    payload = response.json()
    assert payload["project_id"] == 42
    assert payload["valid"] is True
    assert payload["count"] == 2
    assert payload["items"][0]["version"] == 1


@pytest.mark.asyncio
async def test_diff_project_audit_returns_diff(client, monkeypatch):
    log_a = SimpleNamespace(version=1)
    log_b = SimpleNamespace(version=2)
    logs = [log_a, log_b]
    monkeypatch.setattr(
        audit_api, "verify_chain", AsyncMock(return_value=(False, logs))
    )
    monkeypatch.setattr(
        audit_api, "serialise_log", lambda log: {"version": log.version}
    )
    monkeypatch.setattr(
        audit_api,
        "diff_logs",
        lambda a, b: {"changes": [{"field": "status", "from": "draft", "to": "final"}]},
    )

    response = await client.get("/api/v1/audit/99/diff/1/2")

    assert response.status_code == 200
    payload = response.json()
    assert payload["project_id"] == 99
    assert payload["valid"] is False
    assert payload["version_a"]["version"] == 1
    assert payload["version_b"]["version"] == 2
    assert payload["diff"]["changes"][0]["field"] == "status"


@pytest.mark.asyncio
async def test_diff_project_audit_missing_version_returns_404(client, monkeypatch):
    logs = [SimpleNamespace(version=1)]
    monkeypatch.setattr(audit_api, "verify_chain", AsyncMock(return_value=(True, logs)))

    response = await client.get("/api/v1/audit/99/diff/1/3")

    assert response.status_code == 404
    assert response.json()["detail"] == "Audit entry not found"


@pytest.mark.asyncio
async def test_project_audit_evidence_returns_summary(client, monkeypatch):
    logs = [SimpleNamespace(version=1), SimpleNamespace(version=2)]
    monkeypatch.setattr(audit_api, "verify_chain", AsyncMock(return_value=(True, logs)))
    monkeypatch.setattr(
        audit_api,
        "build_evidence_report",
        lambda project_id, valid, rows: {
            "project_id": project_id,
            "valid": valid,
            "chain": {"entry_count": len(rows)},
            "event_types": [{"event_type": "export_generated", "count": 1}],
        },
    )

    response = await client.get("/api/v1/audit/17/evidence")

    assert response.status_code == 200
    payload = response.json()
    assert payload["project_id"] == 17
    assert payload["valid"] is True
    assert payload["chain"]["entry_count"] == 2
    assert payload["event_types"][0]["event_type"] == "export_generated"


@pytest.mark.asyncio
async def test_project_audit_evidence_by_ref_returns_summary(client, monkeypatch):
    project_ref = str(uuid4())
    logs = [SimpleNamespace(version=1)]
    monkeypatch.setattr(audit_api, "verify_chain", AsyncMock(return_value=(True, logs)))
    monkeypatch.setattr(
        audit_api,
        "build_evidence_report",
        lambda project_id, valid, rows: {
            "project_id": project_id,
            "valid": valid,
            "chain": {"entry_count": len(rows)},
            "finance_events": [{"origin": "quick_screen"}],
        },
    )

    response = await client.get(f"/api/v1/audit/by-ref/{project_ref}/evidence")

    assert response.status_code == 200
    payload = response.json()
    assert payload["valid"] is True
    assert payload["chain"]["entry_count"] == 1
    assert payload["finance_events"][0]["origin"] == "quick_screen"


@pytest.mark.asyncio
async def test_project_audit_evidence_by_ref_invalid_returns_404(client):
    response = await client.get("/api/v1/audit/by-ref/not-a-project/evidence")

    assert response.status_code == 404
    assert response.json()["detail"] == "Audit project not found"
