from __future__ import annotations

import io
from types import SimpleNamespace
from uuid import uuid4

import pytest

from fastapi import HTTPException

from app.api.v1 import agents as agents_api
from app.main import app


class _StubSession:
    def __init__(self, property_obj):
        self._property = property_obj

    async def execute(self, _stmt):
        return SimpleNamespace(scalar_one_or_none=lambda: self._property)


def _override_session(property_obj):
    async def _get_session():
        yield _StubSession(property_obj)

    return _get_session


class _StubPackGenerator:
    def __init__(self):
        self.saved = False

    async def generate(self, property_id, session):
        return io.BytesIO(b"PDF")

    async def save_to_storage(self, pdf_buffer, filename, property_id):
        self.saved = True


class _StubFlyerGenerator:
    async def generate_email_flyer(self, property_id, session, material_type):
        return io.BytesIO(b"FLYER")

    async def save_to_storage(self, pdf_buffer, filename, property_id):
        return None


@pytest.mark.asyncio
async def test_generate_professional_pack_universal_success(client, monkeypatch):
    property_id = uuid4()
    generator = _StubPackGenerator()

    app.dependency_overrides[agents_api.get_session] = _override_session(
        SimpleNamespace(id=property_id)
    )
    monkeypatch.setattr(agents_api, "UniversalSitePackGenerator", lambda: generator)

    try:
        response = await client.post(
            f"/api/v1/agents/commercial-property/properties/{property_id}/generate-pack/universal"
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["pack_type"] == "universal"
        assert generator.saved is True
    finally:
        app.dependency_overrides.pop(agents_api.get_session, None)


@pytest.mark.asyncio
async def test_generate_professional_pack_503_when_generator_missing(
    client, monkeypatch
):
    property_id = uuid4()
    app.dependency_overrides[agents_api.get_session] = _override_session(
        SimpleNamespace(id=property_id)
    )
    monkeypatch.setattr(agents_api, "InvestmentMemorandumGenerator", None)

    try:
        response = await client.post(
            f"/api/v1/agents/commercial-property/properties/{property_id}/generate-pack/investment"
        )
        assert response.status_code == 400
    finally:
        app.dependency_overrides.pop(agents_api.get_session, None)


@pytest.mark.asyncio
async def test_generate_professional_pack_invalid_type_direct(monkeypatch):
    property_id = uuid4()
    session = _StubSession(SimpleNamespace(id=property_id))
    with pytest.raises(HTTPException) as exc:
        await agents_api.generate_professional_pack(
            property_id=str(property_id),
            pack_type="unknown",
            db=session,
            role="viewer",
        )
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_download_generated_file_success(client, monkeypatch, tmp_path):
    property_id = uuid4()
    filename = "report.pdf"
    storage_base = tmp_path / "storage"
    storage_prefix = "uploads"
    file_dir = storage_base / storage_prefix / "reports" / str(property_id)
    file_dir.mkdir(parents=True)
    (file_dir / filename).write_bytes(b"PDF")

    monkeypatch.setenv("STORAGE_LOCAL_PATH", str(storage_base))
    monkeypatch.setenv("STORAGE_PREFIX", storage_prefix)

    response = await client.get(
        f"/api/v1/agents/commercial-property/files/{property_id}/{filename}"
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


@pytest.mark.asyncio
async def test_generate_email_flyer_success(client, monkeypatch):
    property_id = uuid4()
    generator = _StubFlyerGenerator()

    app.dependency_overrides[agents_api.get_session] = _override_session(
        SimpleNamespace(id=property_id)
    )
    monkeypatch.setattr(agents_api, "MarketingMaterialsGenerator", lambda: generator)

    try:
        response = await client.post(
            f"/api/v1/agents/commercial-property/properties/{property_id}/generate-flyer",
            params={"material_type": "sale"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["flyer_type"] == "sale"
    finally:
        app.dependency_overrides.pop(agents_api.get_session, None)
