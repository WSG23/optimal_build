from __future__ import annotations

import io
from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.api.v1 import agents as agents_api


class _StubPhotoManager:
    def __init__(self, response=None, photos=None):
        self._response = response or SimpleNamespace(
            to_dict=lambda: {
                "photo_id": str(uuid4()),
                "storage_key": "photos/key.jpg",
                "capture_timestamp": datetime.utcnow().isoformat(),
                "auto_tagged_conditions": ["well_lit"],
                "public_url": "https://cdn.example/photo.jpg",
                "location": {"lat": 1.3, "lng": 103.8},
            }
        )
        self._photos = photos or [{"photo_id": str(uuid4()), "notes": "Existing photo"}]

    async def process_photo(self, **kwargs):
        return self._response

    async def get_property_photos(self, **kwargs):
        return self._photos


@pytest.mark.asyncio
async def test_upload_property_photo_success(client, monkeypatch):
    monkeypatch.setattr(
        agents_api,
        "PhotoDocumentationManager",
        lambda: _StubPhotoManager(),
    )

    response = await client.post(
        "/api/v1/agents/commercial-property/properties/prop-1/photos",
        files={"file": ("test.jpg", io.BytesIO(b"img"), "image/jpeg")},
        data={"notes": "Front elevation"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["storage_key"].startswith("photos/")
    assert payload["auto_tags"] == ["well_lit"]


@pytest.mark.asyncio
async def test_upload_property_photo_invalid_type(client):
    response = await client.post(
        "/api/v1/agents/commercial-property/properties/prop-1/photos",
        files={"file": ("test.txt", io.BytesIO(b"text"), "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "File must be an image"


@pytest.mark.asyncio
async def test_get_property_photos_success(client, monkeypatch):
    photos = [{"photo_id": str(uuid4()), "notes": "Existing"}]
    monkeypatch.setattr(
        agents_api,
        "PhotoDocumentationManager",
        lambda: _StubPhotoManager(photos=photos),
    )

    response = await client.get(
        "/api/v1/agents/commercial-property/properties/prop-1/photos"
    )

    assert response.status_code == 200
    assert response.json()[0]["photo_id"] == photos[0]["photo_id"]
