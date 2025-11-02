"""Integration tests for PhotoDocumentationManager service."""

from __future__ import annotations

import io
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.property import Property, PropertyPhoto, PropertyStatus, PropertyType
from app.services.agents.photo_documentation import (
    PhotoDocumentationManager,
    PhotoMetadata,
)

pytestmark = pytest.mark.skip(
    reason=(
        "Photo documentation manager requires SQLAlchemy insert/delete support and "
        "image processing dependencies not present in the stub environment."
    )
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _make_property(**overrides) -> Property:
    """Create a minimal Property for testing."""
    defaults = dict(
        name="Test Property",
        address="1 Test Street",
        property_type=PropertyType.OFFICE,
        status=PropertyStatus.EXISTING,
        location="POINT(103.8547 1.2789)",
        data_source="test",
    )
    defaults.update(overrides)
    return Property(**defaults)


def _make_property_photo(property_id, **overrides) -> PropertyPhoto:
    """Create a minimal PropertyPhoto for testing."""
    defaults = dict(
        property_id=property_id,
        storage_key=f"photos/{property_id}/test.jpg",
        filename="test.jpg",
        capture_date=datetime.now(),
        mime_type="image/jpeg",
        file_size_bytes=1024,
    )
    defaults.update(overrides)
    return PropertyPhoto(**defaults)


def _create_test_image(width=800, height=600, mode="RGB"):
    """Create a test PIL Image."""
    try:
        from PIL import Image

        return Image.new(mode, (width, height), color=(128, 128, 128))
    except ImportError:
        pytest.skip("PIL/Pillow not installed")


def _image_to_bytes(image):
    """Convert PIL Image to bytes."""
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)
    return buffer.getvalue()


# ============================================================================
# PHOTOMETADATA CLASS TESTS
# ============================================================================


def test_photo_metadata_init_minimal():
    """Test PhotoMetadata initialization with minimal parameters."""
    photo_id = uuid4()
    property_id = uuid4()
    storage_key = "test/photo.jpg"

    metadata = PhotoMetadata(
        photo_id=photo_id,
        property_id=property_id,
        storage_key=storage_key,
    )

    assert metadata.photo_id == photo_id
    assert metadata.property_id == property_id
    assert metadata.storage_key == storage_key
    assert metadata.location is None
    assert metadata.capture_timestamp is not None  # Should use utcnow()
    assert metadata.auto_tagged_conditions == []
    assert metadata.camera_info == {}
    assert metadata.file_size == 0


def test_photo_metadata_init_full():
    """Test PhotoMetadata initialization with all parameters."""
    photo_id = uuid4()
    property_id = uuid4()
    storage_key = "test/photo.jpg"
    location = {"latitude": 1.2789, "longitude": 103.8547}
    capture_timestamp = datetime(2023, 10, 15, 14, 30, 45)
    auto_tagged_conditions = ["exterior_view", "bright_conditions"]
    camera_info = {"make": "Canon", "model": "EOS R5"}
    file_size = 2048576

    metadata = PhotoMetadata(
        photo_id=photo_id,
        property_id=property_id,
        storage_key=storage_key,
        location=location,
        capture_timestamp=capture_timestamp,
        auto_tagged_conditions=auto_tagged_conditions,
        camera_info=camera_info,
        file_size=file_size,
    )

    assert metadata.photo_id == photo_id
    assert metadata.property_id == property_id
    assert metadata.storage_key == storage_key
    assert metadata.location == location
    assert metadata.capture_timestamp == capture_timestamp
    assert metadata.auto_tagged_conditions == auto_tagged_conditions
    assert metadata.camera_info == camera_info
    assert metadata.file_size == file_size


def test_photo_metadata_to_dict():
    """Test PhotoMetadata.to_dict() conversion."""
    photo_id = uuid4()
    property_id = uuid4()
    storage_key = "test/photo.jpg"
    location = {"latitude": 1.2789, "longitude": 103.8547}
    capture_timestamp = datetime(2023, 10, 15, 14, 30, 45)
    auto_tagged_conditions = ["exterior_view"]
    camera_info = {"make": "Canon"}
    file_size = 1024

    metadata = PhotoMetadata(
        photo_id=photo_id,
        property_id=property_id,
        storage_key=storage_key,
        location=location,
        capture_timestamp=capture_timestamp,
        auto_tagged_conditions=auto_tagged_conditions,
        camera_info=camera_info,
        file_size=file_size,
    )

    result = metadata.to_dict()

    assert result["photo_id"] == str(photo_id)
    assert result["property_id"] == str(property_id)
    assert result["storage_key"] == storage_key
    assert result["location"] == location
    assert result["capture_timestamp"] == "2023-10-15T14:30:45"
    assert result["auto_tagged_conditions"] == auto_tagged_conditions
    assert result["camera_info"] == camera_info
    assert result["file_size"] == file_size
    assert "public_url" in result


def test_photo_metadata_to_dict_with_none_values():
    """Test PhotoMetadata.to_dict() with None location."""
    photo_id = uuid4()
    property_id = uuid4()
    storage_key = "test/photo.jpg"

    metadata = PhotoMetadata(
        photo_id=photo_id,
        property_id=property_id,
        storage_key=storage_key,
    )

    result = metadata.to_dict()

    assert result["location"] is None
    assert result["auto_tagged_conditions"] == []
    assert result["camera_info"] == {}


# ============================================================================
# PHOTODOCUMENTATIONMANAGER INITIALIZATION TESTS
# ============================================================================


def test_manager_init_with_storage_service():
    """Test PhotoDocumentationManager initialization with provided storage service."""
    mock_storage = Mock()
    manager = PhotoDocumentationManager(storage_service=mock_storage)

    assert manager.storage == mock_storage
    assert manager.supported_formats == {".jpg", ".jpeg", ".png", ".heic", ".heif"}


def test_manager_init_without_storage_service():
    """Test PhotoDocumentationManager initialization creates default storage service."""
    with patch(
        "app.services.agents.photo_documentation.MinIOService"
    ) as mock_minio_class:
        mock_storage_instance = Mock()
        mock_minio_class.return_value = mock_storage_instance

        manager = PhotoDocumentationManager()

        assert manager.storage == mock_storage_instance
        mock_minio_class.assert_called_once()


# ============================================================================
# VALIDATION TESTS
# ============================================================================


def test_validate_photo_format_jpg():
    """Test _validate_photo_format accepts .jpg files."""
    manager = PhotoDocumentationManager(storage_service=Mock())

    assert manager._validate_photo_format("photo.jpg") is True
    assert manager._validate_photo_format("photo.JPG") is True


def test_validate_photo_format_jpeg():
    """Test _validate_photo_format accepts .jpeg files."""
    manager = PhotoDocumentationManager(storage_service=Mock())

    assert manager._validate_photo_format("photo.jpeg") is True
    assert manager._validate_photo_format("photo.JPEG") is True


def test_validate_photo_format_png():
    """Test _validate_photo_format accepts .png files."""
    manager = PhotoDocumentationManager(storage_service=Mock())

    assert manager._validate_photo_format("photo.png") is True


def test_validate_photo_format_heic():
    """Test _validate_photo_format accepts .heic files."""
    manager = PhotoDocumentationManager(storage_service=Mock())

    assert manager._validate_photo_format("photo.heic") is True
    assert manager._validate_photo_format("photo.heif") is True


def test_validate_photo_format_invalid():
    """Test _validate_photo_format rejects unsupported formats."""
    manager = PhotoDocumentationManager(storage_service=Mock())

    assert manager._validate_photo_format("photo.bmp") is False
    assert manager._validate_photo_format("photo.gif") is False
    assert manager._validate_photo_format("photo.webp") is False
    assert manager._validate_photo_format("document.pdf") is False


def test_validate_photo_format_no_extension():
    """Test _validate_photo_format rejects files without extension."""
    manager = PhotoDocumentationManager(storage_service=Mock())

    assert manager._validate_photo_format("photo") is False


# ============================================================================
# EXIF EXTRACTION TESTS
# ============================================================================


def test_extract_exif_data_no_exifread():
    """Test _extract_exif_data returns empty dict when exifread not available."""
    manager = PhotoDocumentationManager(storage_service=Mock())

    with patch("app.services.agents.photo_documentation.exifread", None):
        result = manager._extract_exif_data(b"fake_photo_data")

    assert result == {}


def test_extract_exif_data_success():
    """Test _extract_exif_data extracts EXIF data successfully."""
    manager = PhotoDocumentationManager(storage_service=Mock())

    mock_tags = {
        "Image Make": Mock(__str__=lambda self: "Canon"),
        "Image Model": Mock(__str__=lambda self: "EOS R5"),
        "EXIF DateTimeOriginal": Mock(__str__=lambda self: "2023:10:15 14:30:45"),
        "Thumbnail JPEGInterchangeFormat": Mock(__str__=lambda self: "1234"),
    }

    with patch("app.services.agents.photo_documentation.exifread") as mock_exifread:
        mock_exifread.process_file = Mock(return_value=mock_tags)
        result = manager._extract_exif_data(b"fake_photo_data")

    assert "Image Make" in result
    assert result["Image Make"] == "Canon"
    assert "Image Model" in result
    assert result["Image Model"] == "EOS R5"
    assert "Thumbnail JPEGInterchangeFormat" not in result  # Thumbnails skipped


def test_extract_exif_data_error():
    """Test _extract_exif_data handles errors gracefully."""
    manager = PhotoDocumentationManager(storage_service=Mock())

    with patch("app.services.agents.photo_documentation.exifread") as mock_exifread:
        mock_exifread.process_file = Mock(side_effect=Exception("EXIF error"))
        result = manager._extract_exif_data(b"fake_photo_data")

    assert result == {}


# ============================================================================
# GPS EXTRACTION TESTS
# ============================================================================


def test_extract_gps_from_exif_success():
    """Test _extract_gps_from_exif extracts GPS coordinates successfully."""
    manager = PhotoDocumentationManager(storage_service=Mock())

    exif_data = {
        "GPS GPSLatitude": "[1, 16, 44.04]",
        "GPS GPSLongitude": "[103, 51, 16.92]",
        "GPS GPSLatitudeRef": "N",
        "GPS GPSLongitudeRef": "E",
    }

    result = manager._extract_gps_from_exif(exif_data)

    assert result is not None
    assert "latitude" in result
    assert "longitude" in result
    # Check approximate values (1 + 16/60 + 44.04/3600 ≈ 1.2789)
    assert 1.27 < result["latitude"] < 1.29
    assert 103.85 < result["longitude"] < 103.86


def test_extract_gps_from_exif_missing_data():
    """Test _extract_gps_from_exif returns None when GPS data missing."""
    manager = PhotoDocumentationManager(storage_service=Mock())

    exif_data = {
        "Image Make": "Canon",
    }

    result = manager._extract_gps_from_exif(exif_data)

    assert result is None


def test_extract_gps_from_exif_partial_data():
    """Test _extract_gps_from_exif returns None with only latitude."""
    manager = PhotoDocumentationManager(storage_service=Mock())

    exif_data = {
        "GPS GPSLatitude": "[1, 16, 44.04]",
        "GPS GPSLatitudeRef": "N",
    }

    result = manager._extract_gps_from_exif(exif_data)

    assert result is None


def test_extract_gps_from_exif_error():
    """Test _extract_gps_from_exif handles errors gracefully."""
    manager = PhotoDocumentationManager(storage_service=Mock())

    exif_data = {
        "GPS GPSLatitude": "invalid",
        "GPS GPSLongitude": "invalid",
    }

    result = manager._extract_gps_from_exif(exif_data)

    assert result is None


# ============================================================================
# GPS CONVERSION TESTS
# ============================================================================


def test_convert_gps_to_decimal_north():
    """Test _convert_gps_to_decimal converts northern latitude correctly."""
    manager = PhotoDocumentationManager(storage_service=Mock())

    result = manager._convert_gps_to_decimal("[1, 16, 44.04]", "N")

    assert result is not None
    assert 1.27 < result < 1.29


def test_convert_gps_to_decimal_south():
    """Test _convert_gps_to_decimal converts southern latitude correctly."""
    manager = PhotoDocumentationManager(storage_service=Mock())

    result = manager._convert_gps_to_decimal("[33, 55, 30.0]", "S")

    assert result is not None
    assert result < 0  # Southern hemisphere is negative


def test_convert_gps_to_decimal_east():
    """Test _convert_gps_to_decimal converts eastern longitude correctly."""
    manager = PhotoDocumentationManager(storage_service=Mock())

    result = manager._convert_gps_to_decimal("[103, 51, 16.92]", "E")

    assert result is not None
    assert 103.85 < result < 103.86


def test_convert_gps_to_decimal_west():
    """Test _convert_gps_to_decimal converts western longitude correctly."""
    manager = PhotoDocumentationManager(storage_service=Mock())

    result = manager._convert_gps_to_decimal("[122, 24, 0.0]", "W")

    assert result is not None
    assert result < 0  # Western hemisphere is negative


def test_convert_gps_to_decimal_invalid_format():
    """Test _convert_gps_to_decimal returns None for invalid format."""
    manager = PhotoDocumentationManager(storage_service=Mock())

    result = manager._convert_gps_to_decimal("[1, 2]", "N")  # Only 2 parts

    assert result is None


def test_convert_gps_to_decimal_invalid_value():
    """Test _convert_gps_to_decimal returns None for invalid values."""
    manager = PhotoDocumentationManager(storage_service=Mock())

    result = manager._convert_gps_to_decimal("[abc, def, ghi]", "N")

    assert result is None


# ============================================================================
# TIMESTAMP EXTRACTION TESTS
# ============================================================================


def test_extract_timestamp_from_exif_success():
    """Test _extract_timestamp_from_exif extracts timestamp successfully."""
    manager = PhotoDocumentationManager(storage_service=Mock())

    exif_data = {
        "EXIF DateTimeOriginal": "2023:10:15 14:30:45",
    }

    result = manager._extract_timestamp_from_exif(exif_data)

    assert result is not None
    assert result == datetime(2023, 10, 15, 14, 30, 45)


def test_extract_timestamp_from_exif_digitized():
    """Test _extract_timestamp_from_exif uses DateTimeDigitized as fallback."""
    manager = PhotoDocumentationManager(storage_service=Mock())

    exif_data = {
        "EXIF DateTimeDigitized": "2023:09:20 10:15:30",
    }

    result = manager._extract_timestamp_from_exif(exif_data)

    assert result is not None
    assert result == datetime(2023, 9, 20, 10, 15, 30)


def test_extract_timestamp_from_exif_image_datetime():
    """Test _extract_timestamp_from_exif uses Image DateTime as fallback."""
    manager = PhotoDocumentationManager(storage_service=Mock())

    exif_data = {
        "Image DateTime": "2023:08:10 08:00:00",
    }

    result = manager._extract_timestamp_from_exif(exif_data)

    assert result is not None
    assert result == datetime(2023, 8, 10, 8, 0, 0)


def test_extract_timestamp_from_exif_priority():
    """Test _extract_timestamp_from_exif prefers DateTimeOriginal."""
    manager = PhotoDocumentationManager(storage_service=Mock())

    exif_data = {
        "EXIF DateTimeOriginal": "2023:10:15 14:30:45",
        "EXIF DateTimeDigitized": "2023:09:20 10:15:30",
        "Image DateTime": "2023:08:10 08:00:00",
    }

    result = manager._extract_timestamp_from_exif(exif_data)

    assert result == datetime(2023, 10, 15, 14, 30, 45)  # Uses first one


def test_extract_timestamp_from_exif_missing():
    """Test _extract_timestamp_from_exif returns None when no timestamp."""
    manager = PhotoDocumentationManager(storage_service=Mock())

    exif_data = {
        "Image Make": "Canon",
    }

    result = manager._extract_timestamp_from_exif(exif_data)

    assert result is None


def test_extract_timestamp_from_exif_invalid_format():
    """Test _extract_timestamp_from_exif returns None for invalid format."""
    manager = PhotoDocumentationManager(storage_service=Mock())

    exif_data = {
        "EXIF DateTimeOriginal": "invalid_date",
    }

    result = manager._extract_timestamp_from_exif(exif_data)

    assert result is None


# ============================================================================
# CAMERA INFO EXTRACTION TESTS
# ============================================================================


def test_extract_camera_info_from_exif_full():
    """Test _extract_camera_info_from_exif extracts all camera info."""
    manager = PhotoDocumentationManager(storage_service=Mock())

    exif_data = {
        "Image Make": "Canon",
        "Image Model": "EOS R5",
        "EXIF LensModel": "RF 24-70mm f/2.8L IS USM",
        "EXIF FocalLength": "50",
        "EXIF FNumber": "2.8",
        "EXIF ISOSpeedRatings": "800",
        "EXIF ExposureTime": "1/125",
    }

    result = manager._extract_camera_info_from_exif(exif_data)

    assert result["make"] == "Canon"
    assert result["model"] == "EOS R5"
    assert result["lens"] == "RF 24-70mm f/2.8L IS USM"
    assert result["focal_length"] == "50"
    assert result["aperture"] == "2.8"
    assert result["iso"] == "800"
    assert result["exposure"] == "1/125"


def test_extract_camera_info_from_exif_partial():
    """Test _extract_camera_info_from_exif extracts partial camera info."""
    manager = PhotoDocumentationManager(storage_service=Mock())

    exif_data = {
        "Image Make": "Sony",
        "Image Model": "A7R IV",
    }

    result = manager._extract_camera_info_from_exif(exif_data)

    assert result["make"] == "Sony"
    assert result["model"] == "A7R IV"
    assert "lens" not in result
    assert "iso" not in result


def test_extract_camera_info_from_exif_empty():
    """Test _extract_camera_info_from_exif returns empty dict when no camera info."""
    manager = PhotoDocumentationManager(storage_service=Mock())

    exif_data = {}

    result = manager._extract_camera_info_from_exif(exif_data)

    assert result == {}


# ============================================================================
# IMAGE ANALYSIS TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_analyze_site_conditions_wide_angle():
    """Test _analyze_site_conditions detects wide angle shots."""
    manager = PhotoDocumentationManager(storage_service=Mock())
    image = _create_test_image(width=1920, height=1080)  # 16:9 ratio

    result = await manager._analyze_site_conditions(image)

    assert "wide_angle_shot" in result


@pytest.mark.asyncio
async def test_analyze_site_conditions_vertical():
    """Test _analyze_site_conditions detects vertical shots."""
    manager = PhotoDocumentationManager(storage_service=Mock())
    image = _create_test_image(width=1080, height=1920)  # 9:16 ratio

    result = await manager._analyze_site_conditions(image)

    assert "vertical_shot" in result


@pytest.mark.asyncio
async def test_analyze_site_conditions_bright():
    """Test _analyze_site_conditions detects bright conditions."""
    manager = PhotoDocumentationManager(storage_service=Mock())

    try:
        from PIL import Image

        # Create a very bright image
        image = Image.new("RGB", (800, 600), color=(250, 250, 250))

        result = await manager._analyze_site_conditions(image)

        assert "bright_conditions" in result
        assert "possible_overexposed" in result
    except ImportError:
        pytest.skip("PIL/Pillow not installed")


@pytest.mark.asyncio
async def test_analyze_site_conditions_dark():
    """Test _analyze_site_conditions detects dark conditions."""
    manager = PhotoDocumentationManager(storage_service=Mock())

    try:
        from PIL import Image

        # Create a very dark image
        image = Image.new("RGB", (800, 600), color=(10, 10, 10))

        result = await manager._analyze_site_conditions(image)

        assert "dark_conditions" in result
        assert "possible_underexposed" in result
    except ImportError:
        pytest.skip("PIL/Pillow not installed")


@pytest.mark.asyncio
async def test_analyze_site_conditions_default_tags():
    """Test _analyze_site_conditions includes default tags."""
    manager = PhotoDocumentationManager(storage_service=Mock())
    image = _create_test_image()

    result = await manager._analyze_site_conditions(image)

    assert "exterior_view" in result
    assert "site_documentation" in result
    assert "property_condition" in result


@pytest.mark.asyncio
async def test_analyze_site_conditions_converts_non_rgb():
    """Test _analyze_site_conditions converts non-RGB images."""
    manager = PhotoDocumentationManager(storage_service=Mock())
    image = _create_test_image(mode="L")  # Grayscale

    result = await manager._analyze_site_conditions(image)

    # Should complete without error and return tags
    assert isinstance(result, list)


# ============================================================================
# IMAGE VERSION GENERATION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_generate_image_versions_all_sizes():
    """Test _generate_image_versions creates all versions."""
    manager = PhotoDocumentationManager(storage_service=Mock())
    image = _create_test_image(width=3000, height=2000)
    photo_id = uuid4()

    result = await manager._generate_image_versions(image, photo_id)

    assert "original" in result
    assert "thumbnail" in result
    assert "medium" in result
    assert "web" in result


@pytest.mark.asyncio
async def test_generate_image_versions_original():
    """Test _generate_image_versions creates original version."""
    manager = PhotoDocumentationManager(storage_service=Mock())
    image = _create_test_image(width=2000, height=1500)
    photo_id = uuid4()

    result = await manager._generate_image_versions(image, photo_id)

    original = result["original"]
    assert isinstance(original, io.BytesIO)
    assert original.tell() == 0  # Pointer at start


@pytest.mark.asyncio
async def test_generate_image_versions_thumbnail_size():
    """Test _generate_image_versions creates thumbnail at 300x300."""
    manager = PhotoDocumentationManager(storage_service=Mock())
    image = _create_test_image(width=2000, height=1500)
    photo_id = uuid4()

    result = await manager._generate_image_versions(image, photo_id)

    # Verify thumbnail is created (we can't easily check dimensions without reading back)
    assert "thumbnail" in result
    assert isinstance(result["thumbnail"], io.BytesIO)


@pytest.mark.asyncio
async def test_generate_image_versions_buffers_are_bytes():
    """Test _generate_image_versions creates BytesIO with content."""
    manager = PhotoDocumentationManager(storage_service=Mock())
    image = _create_test_image()
    photo_id = uuid4()

    result = await manager._generate_image_versions(image, photo_id)

    for version_name, buffer in result.items():
        assert isinstance(buffer, io.BytesIO)
        buffer.seek(0, 2)  # Seek to end
        size = buffer.tell()
        assert size > 0, f"{version_name} should have content"


# ============================================================================
# DATABASE OPERATION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_create_photo_record_success(db_session: AsyncSession):
    """Test _create_photo_record creates database record successfully."""
    # Create test property
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    manager = PhotoDocumentationManager(storage_service=Mock())
    photo_id = uuid4()
    location = {"latitude": 1.2789, "longitude": 103.8547}
    capture_timestamp = datetime(2023, 10, 15, 14, 30, 45)
    auto_tags = ["exterior_view", "bright_conditions"]
    camera_info = {"make": "Canon", "model": "EOS R5"}
    exif_data = {"Image Make": "Canon"}

    await manager._create_photo_record(
        photo_id=photo_id,
        property_id=prop.id,
        storage_key="test/photo.jpg",
        filename="photo.jpg",
        file_size=2048576,
        location=location,
        capture_timestamp=capture_timestamp,
        auto_tags=auto_tags,
        camera_info=camera_info,
        exif_data=exif_data,
        user_metadata=None,
        session=db_session,
    )

    # Verify record was created
    from sqlalchemy import select

    stmt = select(PropertyPhoto).where(PropertyPhoto.id == photo_id)
    result = await db_session.execute(stmt)
    photo = result.scalar_one_or_none()

    assert photo is not None
    assert photo.property_id == prop.id
    assert photo.storage_key == "test/photo.jpg"
    assert photo.filename == "photo.jpg"
    assert photo.file_size_bytes == 2048576
    assert photo.capture_date == capture_timestamp
    assert photo.auto_tags == auto_tags
    assert photo.camera_model == "EOS R5"


@pytest.mark.asyncio
async def test_create_photo_record_with_user_metadata(db_session: AsyncSession):
    """Test _create_photo_record includes user metadata."""
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    manager = PhotoDocumentationManager(storage_service=Mock())
    photo_id = uuid4()
    user_metadata = {
        "tags": ["construction", "foundation"],
        "notes": "Site inspection photo",
    }

    await manager._create_photo_record(
        photo_id=photo_id,
        property_id=prop.id,
        storage_key="test/photo.jpg",
        filename="photo.jpg",
        file_size=1024,
        location=None,
        capture_timestamp=None,
        auto_tags=[],
        camera_info={},
        exif_data={},
        user_metadata=user_metadata,
        session=db_session,
    )

    # Verify user metadata was stored
    from sqlalchemy import select

    stmt = select(PropertyPhoto).where(PropertyPhoto.id == photo_id)
    result = await db_session.execute(stmt)
    photo = result.scalar_one_or_none()

    assert photo.manual_tags == ["construction", "foundation"]
    assert photo.site_conditions["user_notes"] == "Site inspection photo"


@pytest.mark.asyncio
async def test_get_property_photos_success(db_session: AsyncSession):
    """Test get_property_photos retrieves photos successfully."""
    # Create test property
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    # Create test photos
    photo1 = _make_property_photo(
        prop.id,
        capture_date=datetime(2023, 10, 1),
        auto_tags=["exterior"],
        manual_tags=["front"],
    )
    photo2 = _make_property_photo(
        prop.id,
        capture_date=datetime(2023, 10, 15),
        auto_tags=["interior"],
        filename="interior.jpg",
    )
    db_session.add_all([photo1, photo2])
    await db_session.flush()

    manager = PhotoDocumentationManager(storage_service=Mock())
    result = await manager.get_property_photos(str(prop.id), db_session)

    assert len(result) == 2
    # Should be sorted by capture_date descending
    assert result[0]["filename"] == "interior.jpg"
    assert result[1]["filename"] == "test.jpg"


@pytest.mark.asyncio
async def test_get_property_photos_empty(db_session: AsyncSession):
    """Test get_property_photos with no photos."""
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    manager = PhotoDocumentationManager(storage_service=Mock())
    result = await manager.get_property_photos(str(prop.id), db_session)

    assert len(result) == 0


@pytest.mark.asyncio
async def test_get_property_photos_includes_urls(db_session: AsyncSession):
    """Test get_property_photos includes URLs when requested."""
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    photo = _make_property_photo(prop.id, storage_key=f"photos/{prop.id}/original.jpg")
    db_session.add(photo)
    await db_session.flush()

    manager = PhotoDocumentationManager(storage_service=Mock())
    result = await manager.get_property_photos(
        str(prop.id), db_session, include_urls=True
    )

    assert len(result) == 1
    assert "urls" in result[0]
    assert "original" in result[0]["urls"]
    assert "thumbnail" in result[0]["urls"]
    assert "medium" in result[0]["urls"]
    assert "web" in result[0]["urls"]


@pytest.mark.asyncio
async def test_get_property_photos_excludes_urls(db_session: AsyncSession):
    """Test get_property_photos excludes URLs when requested."""
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    photo = _make_property_photo(prop.id)
    db_session.add(photo)
    await db_session.flush()

    manager = PhotoDocumentationManager(storage_service=Mock())
    result = await manager.get_property_photos(
        str(prop.id), db_session, include_urls=False
    )

    assert len(result) == 1
    assert "urls" not in result[0]


@pytest.mark.asyncio
async def test_delete_photo_success(db_session: AsyncSession):
    """Test delete_photo removes photo and versions from storage."""
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    photo = _make_property_photo(prop.id, storage_key=f"photos/{prop.id}/original.jpg")
    db_session.add(photo)
    await db_session.flush()

    mock_storage = AsyncMock()
    manager = PhotoDocumentationManager(storage_service=mock_storage)

    result = await manager.delete_photo(str(photo.id), db_session)

    assert result is True
    # Verify storage calls
    assert mock_storage.remove_object.call_count == 4  # 4 versions


@pytest.mark.asyncio
async def test_delete_photo_not_found(db_session: AsyncSession):
    """Test delete_photo returns False when photo not found."""
    manager = PhotoDocumentationManager(storage_service=Mock())

    result = await manager.delete_photo(str(uuid4()), db_session)

    assert result is False


@pytest.mark.asyncio
async def test_delete_photo_storage_error(db_session: AsyncSession):
    """Test delete_photo continues when storage deletion fails."""
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    photo = _make_property_photo(prop.id)
    db_session.add(photo)
    await db_session.flush()

    mock_storage = AsyncMock()
    mock_storage.remove_object.side_effect = Exception("Storage error")
    manager = PhotoDocumentationManager(storage_service=mock_storage)

    # Should not raise, just log warnings
    result = await manager.delete_photo(str(photo.id), db_session)

    assert result is True  # Still returns True even with storage errors


# ============================================================================
# PROCESS PHOTO INTEGRATION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_process_photo_success(db_session: AsyncSession):
    """Test process_photo complete workflow."""
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    image = _create_test_image()
    photo_data = _image_to_bytes(image)

    mock_storage = AsyncMock()
    manager = PhotoDocumentationManager(storage_service=mock_storage)

    result = await manager.process_photo(
        photo_data=photo_data,
        property_id=str(prop.id),
        filename="test.jpg",
        session=db_session,
    )

    assert isinstance(result, PhotoMetadata)
    assert result.property_id == prop.id
    assert result.file_size == len(photo_data)
    # Verify storage was called for 4 versions
    assert mock_storage.upload_file.call_count == 4


@pytest.mark.asyncio
async def test_process_photo_invalid_format(db_session: AsyncSession):
    """Test process_photo rejects invalid file format."""
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    manager = PhotoDocumentationManager(storage_service=Mock())

    with pytest.raises(ValueError, match="Unsupported photo format"):
        await manager.process_photo(
            photo_data=b"fake_data",
            property_id=str(prop.id),
            filename="test.pdf",
            session=db_session,
        )


@pytest.mark.asyncio
async def test_process_photo_no_pillow(db_session: AsyncSession):
    """Test process_photo raises error when PIL not available."""
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    manager = PhotoDocumentationManager(storage_service=Mock())

    with patch("app.services.agents.photo_documentation.Image", None):
        with pytest.raises(RuntimeError, match="Pillow is required"):
            await manager.process_photo(
                photo_data=b"fake_data",
                property_id=str(prop.id),
                filename="test.jpg",
                session=db_session,
            )


@pytest.mark.asyncio
async def test_process_photo_with_user_metadata(db_session: AsyncSession):
    """Test process_photo includes user metadata."""
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    image = _create_test_image()
    photo_data = _image_to_bytes(image)

    mock_storage = AsyncMock()
    manager = PhotoDocumentationManager(storage_service=mock_storage)

    user_metadata = {"tags": ["inspection"], "notes": "Foundation check"}

    result = await manager.process_photo(
        photo_data=photo_data,
        property_id=str(prop.id),
        filename="test.jpg",
        session=db_session,
        user_metadata=user_metadata,
    )

    assert isinstance(result, PhotoMetadata)


@pytest.mark.asyncio
async def test_process_photo_rollback_on_error(db_session: AsyncSession):
    """Test process_photo rolls back transaction on error."""
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    mock_storage = AsyncMock()
    mock_storage.upload_file.side_effect = Exception("Upload failed")
    manager = PhotoDocumentationManager(storage_service=mock_storage)

    image = _create_test_image()
    photo_data = _image_to_bytes(image)

    with pytest.raises(Exception, match="Upload failed"):
        await manager.process_photo(
            photo_data=photo_data,
            property_id=str(prop.id),
            filename="test.jpg",
            session=db_session,
        )

    # Verify rollback was called (session should be clean)
    from sqlalchemy import select

    stmt = select(PropertyPhoto)
    result = await db_session.execute(stmt)
    photos = result.scalars().all()
    assert len(photos) == 0


# ============================================================================
# EDGE CASE TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_process_photo_with_gps_exif(db_session: AsyncSession):
    """Test process_photo extracts GPS coordinates from EXIF."""
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    image = _create_test_image()
    photo_data = _image_to_bytes(image)

    mock_storage = AsyncMock()
    manager = PhotoDocumentationManager(storage_service=mock_storage)

    # Mock EXIF extraction to return GPS data
    mock_exif = {
        "GPS GPSLatitude": "[1, 16, 44.04]",
        "GPS GPSLongitude": "[103, 51, 16.92]",
        "GPS GPSLatitudeRef": "N",
        "GPS GPSLongitudeRef": "E",
    }

    with patch.object(manager, "_extract_exif_data", return_value=mock_exif):
        result = await manager.process_photo(
            photo_data=photo_data,
            property_id=str(prop.id),
            filename="test.jpg",
            session=db_session,
        )

    assert result.location is not None
    assert "latitude" in result.location
    assert "longitude" in result.location


@pytest.mark.asyncio
async def test_get_property_photos_with_location(db_session: AsyncSession):
    """Test get_property_photos includes location from geometry."""
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    # Create photo with location (we can't easily set PostGIS geometry in SQLite)
    photo = _make_property_photo(prop.id)
    db_session.add(photo)
    await db_session.flush()

    manager = PhotoDocumentationManager(storage_service=Mock())
    result = await manager.get_property_photos(str(prop.id), db_session)

    # In SQLite, capture_location will be None since we can't create PostGIS geometry
    assert len(result) == 1


def test_convert_gps_to_decimal_edge_cases():
    """Test _convert_gps_to_decimal with various edge cases."""
    manager = PhotoDocumentationManager(storage_service=Mock())

    # Zero coordinates
    result = manager._convert_gps_to_decimal("[0, 0, 0]", "N")
    assert result == 0.0

    # Maximum values
    result = manager._convert_gps_to_decimal("[90, 0, 0]", "N")
    assert result == 90.0

    # With decimal seconds
    result = manager._convert_gps_to_decimal("[45, 30, 30.5]", "N")
    assert result is not None
    assert 45.50 < result < 45.51
