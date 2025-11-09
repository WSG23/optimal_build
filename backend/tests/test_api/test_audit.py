from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

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
