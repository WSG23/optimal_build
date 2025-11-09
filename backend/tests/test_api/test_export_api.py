from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.api.v1 import export as export_api
from app.api.v1.export import ExportRequestPayload
from app.core.database import get_session
from app.core.export import ProjectGeometryMissing
from app.main import app


class _SessionStub:
    pass


@pytest.fixture(autouse=True)
def override_export_dependencies():
    async def _session_override():
        yield _SessionStub()

    app.dependency_overrides[get_session] = _session_override
    yield
    app.dependency_overrides.pop(get_session, None)


def test_build_layer_mapping_handles_defaults():
    mapping = export_api._build_layer_mapping(
        export_api.LayerMapPayload(
            source={"existing": "New"},
            overlays={"pending": "Layer"},
            styles={"existing": {"color": "#fff"}},
            default_source_layer="existing",
        )
    )
    assert mapping.source["existing"] == "New"
    assert mapping.default_source_layer == "existing"


def test_normalise_header_value_strips_non_ascii():
    assert export_api._normalise_header_value("Hello 🚀") == "Hello "
    assert export_api._normalise_header_value("ASCII") == "ASCII"


@pytest.mark.asyncio
async def test_export_project_success(client, monkeypatch, tmp_path):
    artifact_path = tmp_path / "export.zip"
    artifact_path.write_bytes(b"content")
    artifact = SimpleNamespace(
        path=str(artifact_path),
        media_type="application/zip",
        filename="project.zip",
        manifest={"renderer": "fallback", "watermark": "Tést Watermark"},
    )

    async def fake_generate(session, project_id, options, storage):
        assert project_id == 123
        assert isinstance(options, export_api.ExportOptions)
        return artifact

    monkeypatch.setattr(export_api, "generate_project_export", fake_generate)
    monkeypatch.setattr(export_api, "LocalExportStorage", lambda: SimpleNamespace())

    response = await client.post(
        "/api/v1/export/123",
        json={"format": "dxf", "include_pending_overlays": True},
    )
    assert response.status_code == 200
    assert response.headers["X-Export-Renderer"] == "fallback"
    assert response.headers["X-Export-Fallback"] == "1"
    expected_watermark = export_api._normalise_header_value("Tést Watermark")
    assert response.headers["X-Export-Watermark"] == expected_watermark


@pytest.mark.asyncio
async def test_export_project_rejects_unknown_format(client):
    response = await client.post("/api/v1/export/5", json={"format": ""})
    assert response.status_code == 422  # validator catches empty format

    response = await client.post("/api/v1/export/5", json={"format": "unknown"})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_export_project_handles_missing_geometry(client, monkeypatch):
    async def fake_generate(session, project_id, options, storage):
        raise ProjectGeometryMissing("Missing geometry")

    monkeypatch.setattr(export_api, "generate_project_export", fake_generate)
    monkeypatch.setattr(export_api, "LocalExportStorage", lambda: SimpleNamespace())

    response = await client.post(
        "/api/v1/export/9",
        json=ExportRequestPayload(format="dxf").model_dump(),
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Missing geometry"
