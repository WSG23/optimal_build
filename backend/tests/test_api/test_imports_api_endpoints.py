from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.api.v1 import imports as imports_api
from app.services.storage import StorageResult


async def _upload_sample_import(
    client,
    monkeypatch,
    project_id: int = 1,
):
    payload = b'{"layers":[{"type":"floor","name":"L1","units":[{"id":"U1"}]}]}'

    class _StorageStub:
        async def store_import_file(self, **kwargs):
            return StorageResult(
                bucket="local",
                key="uploads/import.bin",
                uri="s3://local/uploads/import.bin",
                bytes_written=len(kwargs["payload"]),
                layer_metadata_uri=None,
                vector_data_uri=None,
            )

    storage_stub = _StorageStub()
    vector_mock = AsyncMock(return_value=(None, None, []))
    event_mock = AsyncMock()

    monkeypatch.setattr(imports_api, "get_storage_service", lambda: storage_stub)
    monkeypatch.setattr(imports_api, "_vectorize_payload_if_requested", vector_mock)
    monkeypatch.setattr(imports_api, "append_event", event_mock)

    response = await client.post(
        "/api/v1/import",
        files={"file": ("plan.json", payload, "application/json")},
        data={"project_id": str(project_id), "zone_code": "central"},
    )
    assert response.status_code == 201
    return response.json(), event_mock


@pytest.mark.asyncio
async def test_upload_import_and_get_latest(client, monkeypatch):
    created, _ = await _upload_sample_import(client, monkeypatch, project_id=7)
    latest = await client.get("/api/v1/import/latest", params={"project_id": 7})
    assert latest.status_code == 200
    assert latest.json()["import_id"] == created["import_id"]


@pytest.mark.asyncio
async def test_update_import_overrides_emits_event(client, monkeypatch):
    created, event_mock = await _upload_sample_import(client, monkeypatch)
    import_id = created["import_id"]

    response = await client.post(
        f"/api/v1/import/{import_id}/overrides",
        json={"site_area_sqm": 1500.0},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["metric_overrides"]["site_area_sqm"] == 1500.0
    event_mock.assert_awaited()


@pytest.mark.asyncio
async def test_enqueue_parse_and_poll_status(client, monkeypatch):
    created, _ = await _upload_sample_import(client, monkeypatch)
    import_id = created["import_id"]

    dispatch = SimpleNamespace(
        result={"summary": "ok"},
        task_id="task-123",
        status="completed",
    )
    monkeypatch.setattr(
        imports_api.job_queue,
        "enqueue",
        AsyncMock(return_value=dispatch),
    )

    response = await client.post(f"/api/v1/parse/{import_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["job_id"] == "task-123"

    status_response = await client.get(f"/api/v1/parse/{import_id}")
    assert status_response.status_code == 200
    assert status_response.json()["import_id"] == import_id


@pytest.mark.asyncio
async def test_upload_import_rejects_unsupported_media(client):
    response = await client.post(
        "/api/v1/import",
        files={"file": ("notes.txt", b"text", "text/plain")},
        data={"project_id": "1"},
    )
    assert response.status_code == 415
