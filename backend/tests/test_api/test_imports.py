"""Tests for the import and parse API endpoints."""

from __future__ import annotations

import json
from datetime import datetime
from io import BytesIO
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")

from backend.jobs import JobDispatch, job_queue

from app.models.imports import ImportRecord
from app.services.storage import get_storage_service
from httpx import AsyncClient

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "samples"
GLOBAL_SAMPLES_DIR = Path(__file__).resolve().parents[3] / "samples"


@pytest.mark.asyncio
async def test_upload_import_persists_metadata(
    app_client: AsyncClient,
    async_session_factory,
) -> None:
    sample_path = SAMPLES_DIR / "sample_floorplan.json"
    with sample_path.open("rb") as handle:
        response = await app_client.post(
            "/api/v1/import",
            files={"file": (sample_path.name, handle, "application/json")},
        )

    assert response.status_code == 201, response.json()
    payload = response.json()
    assert payload["filename"] == sample_path.name
    assert payload["detected_units"] == ["01-01", "01-02", "02-01", "P1", "P2"]
    assert [floor["name"] for floor in payload["detected_floors"]] == [
        "Level 01 - Floor Plan",
        "Level 02 - Floor Plan",
        "Podium",
    ]
    assert payload["parse_status"] == "pending"
    assert payload["vector_storage_path"] is None
    assert payload["vector_summary"] is None
    assert "zone_code" in payload
    assert payload["zone_code"] is None

    async with async_session_factory() as session:
        record = await session.get(ImportRecord, payload["import_id"])
        assert record is not None
        assert record.storage_path.startswith("s3://")
        assert len(record.layer_metadata) == 3
        assert record.vector_storage_path is None
        assert record.vector_summary is None

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

    vector_path = (
        storage_service.local_base_path
        / "uploads"
        / payload["import_id"]
        / f"{payload['filename']}.vectors.json"
    )
    assert not vector_path.exists()


@pytest.mark.asyncio
async def test_upload_dxf_emits_detection(app_client: AsyncClient) -> None:
    pytest.importorskip("ezdxf", reason="ezdxf is required for DXF detection")

    sample_path = GLOBAL_SAMPLES_DIR / "dxf" / "flat_two_bed.dxf"
    with sample_path.open("rb") as handle:
        response = await app_client.post(
            "/api/v1/import",
            files={"file": (sample_path.name, handle, "application/dxf")},
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["detected_units"]
    assert len(payload["detected_units"]) == 2
    assert payload["layer_metadata"]
    layer_names = {entry["name"].upper() for entry in payload["layer_metadata"]}
    assert {"LEVEL_01", "LEVEL_02"}.issubset(layer_names)
    floor_names = {floor["name"].upper() for floor in payload["detected_floors"]}
    assert {"LEVEL_01", "LEVEL_02"}.issubset(floor_names)
    assert payload.get("zone_code") is None


@pytest.mark.asyncio
async def test_upload_ifc_surfaces_storeys(app_client: AsyncClient) -> None:
    pytest.importorskip(
        "ifcopenshell", reason="ifcopenshell is required for IFC detection"
    )

    sample_path = GLOBAL_SAMPLES_DIR / "ifc" / "office_small.ifc"
    ifc_bytes = sample_path.read_bytes()
    response = await app_client.post(
        "/api/v1/import",
        files={"file": (sample_path.name, ifc_bytes, "application/octet-stream")},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["detected_units"]
    assert len(payload["detected_units"]) == 3
    floor_names = {floor["name"] for floor in payload["detected_floors"]}
    assert {"Ground Floor", "Level 02"}.issubset(floor_names)


@pytest.mark.asyncio
async def test_parse_endpoints_return_summary(
    app_client: AsyncClient,
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
        upload_response = await app_client.post(
            "/api/v1/import",
            files={"file": (sample_path.name, handle, "application/json")},
        )
    import_payload = upload_response.json()

    parse_response = await app_client.post(
        f"/api/v1/parse/{import_payload['import_id']}"
    )
    assert parse_response.status_code == 200
    parse_payload = parse_response.json()
    assert parse_payload["status"] == "completed"
    assert parse_payload["result"]["floors"] == 3
    assert parse_payload["result"]["units"] == 5
    assert parse_payload["job_id"] is None

    assert calls
    job_callable, *_ = calls[0]
    assert getattr(job_callable, "job_name", "").endswith("parse_import")

    poll_response = await app_client.get(f"/api/v1/parse/{import_payload['import_id']}")
    assert poll_response.status_code == 200
    poll_payload = poll_response.json()
    assert poll_payload == parse_payload


@pytest.mark.asyncio
async def test_parse_uses_existing_result_when_worker_already_completed(
    app_client: AsyncClient,
    async_session_factory,
    monkeypatch,
) -> None:
    """If a worker finishes before the poll, reuse the stored result."""

    sample_path = SAMPLES_DIR / "sample_floorplan.json"
    with sample_path.open("rb") as handle:
        upload_response = await app_client.post(
            "/api/v1/import",
            files={"file": (sample_path.name, handle, "application/json")},
        )

    assert upload_response.status_code == 201
    import_payload = upload_response.json()

    async def fake_enqueue(job_func, *args, **kwargs):
        async with async_session_factory() as session:
            record = await session.get(ImportRecord, import_payload["import_id"])
            assert record is not None
            record.parse_status = "completed"
            record.parse_completed_at = datetime.now()
            record.parse_result = {
                "floors": 3,
                "units": 5,
                "metadata": {"source": "json"},
            }
            await session.commit()
        return JobDispatch(
            backend="celery",
            job_name="backend.jobs.parse_cad.parse_import_job",
            queue="high",
            status="queued",
            task_id="celery-123",
            result=None,
        )

    async def explode_inline(import_id: str) -> None:
        raise AssertionError("parse_import_job should not run when worker finished")

    monkeypatch.setattr(job_queue, "enqueue", fake_enqueue)
    monkeypatch.setattr(job_queue._backend, "name", "celery")
    monkeypatch.setattr("backend.app.api.v1.imports.parse_import_job", explode_inline)

    parse_response = await app_client.post(
        f"/api/v1/parse/{import_payload['import_id']}"
    )
    assert parse_response.status_code == 200
    parse_payload = parse_response.json()
    assert parse_payload["status"] == "completed"
    assert parse_payload["result"]["floors"] == 3
    assert parse_payload["job_id"] is None


@pytest.mark.asyncio
async def test_upload_pdf_vectorizes_when_enabled(
    app_client: AsyncClient,
    async_session_factory,
) -> None:
    pytest.importorskip("fitz")

    pdf_path = (
        Path(__file__).resolve().parents[3] / "samples" / "pdf" / "floor_simple.pdf"
    )
    with pdf_path.open("rb") as handle:
        response = await app_client.post(
            "/api/v1/import",
            files={
                "file": (pdf_path.name, handle, "application/pdf"),
                "infer_walls": (None, "true", None),
            },
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["vector_storage_path"]
    assert payload["vector_summary"] is not None
    assert payload["vector_summary"]["options"]["requested"] is True
    assert payload["vector_summary"]["options"]["infer_walls"] is True
    assert payload["layer_metadata"]
    vector_layers = {entry["name"] for entry in payload["layer_metadata"]}
    assert {"0", "1"}.issubset(vector_layers)

    storage_service = get_storage_service()
    vector_path = (
        storage_service.local_base_path
        / "uploads"
        / payload["import_id"]
        / f"{payload['filename']}.vectors.json"
    )
    assert vector_path.exists()
    vector_payload = json.loads(vector_path.read_text())
    assert vector_payload["paths"]
    assert vector_payload["walls"] == payload["vector_summary"]["walls"]


@pytest.mark.asyncio
async def test_upload_jpeg_vectorizes_bitmap_when_enabled(
    app_client: AsyncClient,
) -> None:
    Image = pytest.importorskip("PIL.Image")

    image = Image.new("L", (32, 32), color=255)
    for x in range(8, 24):
        image.putpixel((x, 16), 0)

    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)

    response = await app_client.post(
        "/api/v1/import",
        files={
            "file": ("floorplan.jpg", buffer, "image/jpeg"),
            "infer_walls": (None, "true", None),
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["filename"].endswith(".jpg")
    assert payload["vector_summary"] is not None
    assert payload["vector_summary"]["source"] == "jpeg"
    assert payload["vector_summary"]["options"]["bitmap_walls"] is True


@pytest.mark.asyncio
async def test_upload_rejects_unsupported_extension(app_client: AsyncClient) -> None:
    response = await app_client.post(
        "/api/v1/import",
        files={"file": ("plan.dwg", b"fake", "application/octet-stream")},
    )

    assert response.status_code == 415
    payload = response.json()
    assert "Unsupported file type" in payload.get("detail", "")


@pytest.mark.asyncio
async def test_import_overrides_and_latest_endpoint(
    app_client: AsyncClient,
) -> None:
    sample_path = SAMPLES_DIR / "sample_floorplan.json"
    project_id = 7777
    with sample_path.open("rb") as handle:
        upload_response = await app_client.post(
            "/api/v1/import",
            files={"file": (sample_path.name, handle, "application/json")},
            data={"project_id": str(project_id)},
        )

    assert upload_response.status_code == 201
    upload_payload = upload_response.json()

    override_response = await app_client.post(
        f"/api/v1/import/{upload_payload['import_id']}/overrides",
        json={"max_height_m": 42.5},
    )
    assert override_response.status_code == 200
    override_payload = override_response.json()
    assert override_payload["metric_overrides"]["max_height_m"] == 42.5

    latest_response = await app_client.get(
        f"/api/v1/import/latest?project_id={project_id}"
    )
    assert latest_response.status_code == 200
    latest_payload = latest_response.json()
    assert latest_payload["import_id"] == upload_payload["import_id"]
    assert latest_payload["metric_overrides"]["max_height_m"] == 42.5


def test_normalise_zone_code_roundtrip():
    from backend.app.api.v1.imports import _normalise_zone_code

    assert _normalise_zone_code("residential") == "SG:residential"
    assert _normalise_zone_code(" SG:Industrial ") == "SG:industrial"
    assert _normalise_zone_code("SG:") == "SG:"
    assert _normalise_zone_code("") is None
