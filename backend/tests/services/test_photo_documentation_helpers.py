from __future__ import annotations

from datetime import datetime
from io import BytesIO
from types import SimpleNamespace
from uuid import uuid4

import pytest
from PIL import Image

from app.services.agents import photo_documentation as photo_doc


class _DummyStorage:
    def __init__(self):
        self.uploads: list[dict[str, str]] = []

    async def upload_file(self, **kwargs):
        self.uploads.append(kwargs)


class _SessionStub:
    def __init__(self, results=None):
        self._results = list(results or [])
        self.executed: list = []

    async def execute(self, _stmt):
        if self._results:
            return self._results.pop(0)
        self.executed.append(_stmt)
        return SimpleNamespace()

    async def rollback(self):
        return None

    async def commit(self):
        return None


class _ScalarResult:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return self

    def all(self):
        return list(self._items)


@pytest.fixture
def manager():
    return photo_doc.PhotoDocumentationManager(storage_service=_DummyStorage())


def test_photo_metadata_to_dict(manager):
    metadata = photo_doc.PhotoMetadata(
        photo_id=uuid4(),
        property_id=uuid4(),
        storage_key="agents/properties/demo/photos/photo/original.jpg",
        location={"latitude": 1.3, "longitude": 103.8},
        auto_tagged_conditions=["site_documentation"],
        file_size=2048,
    )
    payload = metadata.to_dict()
    assert payload["public_url"].endswith("original.jpg")
    assert payload["auto_tagged_conditions"] == ["site_documentation"]


def test_validate_and_extract_helpers(manager, monkeypatch):
    assert manager._validate_photo_format("image.JPG")
    assert not manager._validate_photo_format("diagram.svg")

    exif_stub = {
        "GPS GPSLatitude": "[1, 20, 0]",
        "GPS GPSLatitudeRef": "N",
        "GPS GPSLongitude": "[103, 50, 0]",
        "GPS GPSLongitudeRef": "E",
        "EXIF DateTimeOriginal": "2024:05:01 12:30:00",
        "Image Make": "Canon",
        "Image Model": "5D",
    }
    gps = manager._extract_gps_from_exif(exif_stub)
    assert gps == {
        "latitude": pytest.approx(1.3333, rel=1e-4),
        "longitude": pytest.approx(103.8333, rel=1e-4),
    }

    timestamp = manager._extract_timestamp_from_exif(exif_stub)
    assert isinstance(timestamp, datetime)

    camera = manager._extract_camera_info_from_exif(exif_stub)
    assert camera["make"] == "Canon"

    monkeypatch.setattr(
        photo_doc,
        "exifread",
        SimpleNamespace(process_file=lambda _: {"Image Make": "Canon"}),
    )
    data = manager._extract_exif_data(b"bytes")
    assert data["Image Make"] == "Canon"


@pytest.mark.asyncio
async def test_analyze_and_generate_versions(manager):
    image = Image.new("RGB", (2000, 800), color=(255, 255, 255))
    tags = await manager._analyze_site_conditions(image)
    assert "wide_angle_shot" in tags

    versions = await manager._generate_image_versions(image, uuid4())
    assert set(versions.keys()) == {"original", "thumbnail", "medium", "web"}
    for buffer in versions.values():
        assert isinstance(buffer, BytesIO)
        assert buffer.getbuffer().nbytes > 0


@pytest.mark.asyncio
async def test_store_versions_and_create_record(manager):
    image = Image.new("RGB", (600, 400), color=(200, 200, 200))
    versions = await manager._generate_image_versions(image, uuid4())
    storage_key = await manager._store_photo_versions(
        versions, property_id="PROP", photo_id=uuid4()
    )
    assert storage_key.endswith("original.jpg")
    assert len(manager.storage.uploads) == 4

    session = _SessionStub()
    await manager._create_photo_record(
        photo_id=uuid4(),
        property_id=uuid4(),
        storage_key=storage_key,
        filename="image.jpg",
        file_size=1234,
        location={"latitude": 1.3, "longitude": 103.8},
        capture_timestamp=datetime.utcnow(),
        auto_tags=["tag"],
        camera_info={"model": "Demo"},
        exif_data={"Image Model": "Demo"},
        user_metadata={"tags": ["user"], "notes": "ok"},
        session=session,
    )
    assert session.executed  # insert called


@pytest.mark.asyncio
async def test_get_property_photos_serialises_urls(manager):
    class _Point:
        def __init__(self, x, y):
            self.x = x
            self.y = y

    photo = SimpleNamespace(
        id=uuid4(),
        storage_key="agents/properties/demo/photos/photo/original.jpg",
        filename="photo.jpg",
        capture_date=datetime(2024, 1, 1),
        auto_tags=["auto"],
        manual_tags=["manual"],
        site_conditions={"detected": ["auto"]},
        camera_model="Canon",
        file_size_bytes=1024,
        capture_location=_Point(103.8, 1.3),
    )
    session = _SessionStub(results=[_ScalarResult([photo])])
    photos = await manager.get_property_photos(str(uuid4()), session=session)
    assert photos[0]["urls"]["original"].endswith("original.jpg")
    assert photos[0]["location"] == {"latitude": 1.3, "longitude": 103.8}
