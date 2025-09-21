"""Tests for the import and parse API endpoints."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")

from httpx import AsyncClient

from app.models.imports import ImportRecord
from app.services.storage import get_storage_service
from jobs import job_queue

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "samples"


@pytest.mark.asyncio
async def test_upload_import_persists_metadata(
    client: AsyncClient,
    async_session_factory,
) -> None:
    sample_path = SAMPLES_DIR / "sample_floorplan.json"
    with sample_path.open("rb") as handle:
        response = await client.post(
            "/api/v1/import",
            files={"file": (sample_path.name, handle, "application/json")},
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["filename"] == sample_path.name
    assert payload["detected_units"] == ["01-01", "01-02", "02-01", "P1", "P2"]
    assert [floor["name"] for floor in payload["detected_floors"]] == [
        "Level 01 - Floor Plan",
        "Level 02 - Floor Plan",
        "Podium",
    ]
    assert payload["parse_status"] == "pending"

    async with async_session_factory() as session:
        record = await session.get(ImportRecord, payload["import_id"])
        assert record is not None
        assert record.storage_path.startswith("s3://")
        assert len(record.layer_metadata) == 3

    storage_service = get_storage_service()
    metadata_path = (
        storage_service.local_base_path
        / "uploads"
        / payload["import_id"]
        / f"{payload['filename']}.layers.json"
    )
    assert metadata_path.exists()
    metadata = json.loads(metadata_path.read_text())
    assert metadata[0]["metadata"]["discipline"] == "architecture"


@pytest.mark.asyncio
async def test_parse_endpoints_return_summary(
    client: AsyncClient,
    monkeypatch,
) -> None:
    sample_path = SAMPLES_DIR / "sample_floorplan.json"

    calls = []

    original_enqueue = job_queue.enqueue

    async def tracking_enqueue(*args, **kwargs):
        calls.append(args)
        return await original_enqueue(*args, **kwargs)

    monkeypatch.setattr(job_queue, "enqueue", tracking_enqueue)

    with sample_path.open("rb") as handle:
        upload_response = await client.post(
            "/api/v1/import",
            files={"file": (sample_path.name, handle, "application/json")},
        )
    import_payload = upload_response.json()

    parse_response = await client.post(f"/api/v1/parse/{import_payload['import_id']}")
    assert parse_response.status_code == 200
    parse_payload = parse_response.json()
    assert parse_payload["status"] == "completed"
    assert parse_payload["result"]["floors"] == 3
    assert parse_payload["result"]["units"] == 5
    assert parse_payload["job_id"] is None

    assert calls
    job_callable, *_ = calls[0]
    assert getattr(job_callable, "job_name", "").endswith("parse_import")

    poll_response = await client.get(f"/api/v1/parse/{import_payload['import_id']}")
    assert poll_response.status_code == 200
    poll_payload = poll_response.json()
    assert poll_payload == parse_payload
