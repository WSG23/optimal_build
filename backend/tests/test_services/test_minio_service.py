"""Tests for MinIO storage service."""

from __future__ import annotations

import io
from unittest.mock import Mock, patch

import pytest


@pytest.fixture
def mock_minio_client():
    """Create a mock MinIO client."""
    client = Mock()
    client.bucket_exists = Mock(return_value=True)
    client.make_bucket = Mock()
    client.put_object = Mock()
    client.get_object = Mock()
    client.remove_object = Mock()
    client.list_objects = Mock(return_value=[])
    client.presigned_get_object = Mock(return_value="https://example.com/presigned")
    return client


@pytest.fixture
def minio_exception():
    """Get MinIO exception class."""
    try:
        from minio.error import MinioException

        return MinioException
    except ImportError:
        # Use the fallback exception from the service module
        from app.services.minio_service import MinioException

        return MinioException


def test_minio_service_initialization_with_defaults():
    """Test MinIOService initializes with default settings."""
    with patch("app.services.minio_service.Minio") as MockMinio:
        mock_client = Mock()
        MockMinio.return_value = mock_client
        mock_client.bucket_exists.return_value = True

        from app.services.minio_service import MinIOService

        service = MinIOService()

        assert service.endpoint is not None
        assert service.client is not None
        MockMinio.assert_called_once()


def test_minio_service_initialization_with_custom_params():
    """Test MinIOService initializes with custom parameters."""
    with patch("app.services.minio_service.Minio") as MockMinio:
        mock_client = Mock()
        MockMinio.return_value = mock_client
        mock_client.bucket_exists.return_value = True

        from app.services.minio_service import MinIOService

        service = MinIOService(
            endpoint="custom.endpoint.com",
            access_key="custom_key",
            secret_key="custom_secret",
            secure=True,
        )

        assert service.endpoint == "custom.endpoint.com"
        assert service.access_key == "custom_key"
        assert service.secret_key == "custom_secret"
        assert service.secure is True


def test_minio_service_creates_bucket_if_not_exists(minio_exception):
    """Test MinIOService creates bucket if it doesn't exist."""
    with patch("app.services.minio_service.Minio") as MockMinio:
        mock_client = Mock()
        MockMinio.return_value = mock_client
        mock_client.bucket_exists.return_value = False

        from app.services.minio_service import MinIOService

        MinIOService()

        mock_client.make_bucket.assert_called_once()


def test_minio_service_handles_bucket_creation_error(minio_exception):
    """Test MinIOService handles bucket creation errors gracefully."""
    with patch("app.services.minio_service.Minio") as MockMinio:
        mock_client = Mock()
        MockMinio.return_value = mock_client
        mock_client.bucket_exists.side_effect = minio_exception("Bucket error")

        from app.services.minio_service import MinIOService

        # Should not raise, just log error
        service = MinIOService()
        assert service.client is not None


@pytest.mark.asyncio
async def test_upload_file_with_bytes():
    """Test uploading a file from bytes."""
    with patch("app.services.minio_service.Minio") as MockMinio:
        mock_client = Mock()
        MockMinio.return_value = mock_client
        mock_client.bucket_exists.return_value = True

        from app.services.minio_service import MinIOService

        service = MinIOService()
        test_data = b"test file content"

        result = await service.upload_file(
            bucket_name="test-bucket",
            object_name="test-object.txt",
            data=test_data,
            content_type="text/plain",
            metadata={"key": "value"},
        )

        assert result is True
        mock_client.put_object.assert_called_once()
        call_args = mock_client.put_object.call_args
        assert call_args[0][0] == "test-bucket"
        assert call_args[0][1] == "test-object.txt"
        assert call_args[0][3] == len(test_data)
        assert call_args[1]["content_type"] == "text/plain"
        assert call_args[1]["metadata"] == {"key": "value"}


@pytest.mark.asyncio
async def test_upload_file_with_binary_io():
    """Test uploading a file from BinaryIO."""
    with patch("app.services.minio_service.Minio") as MockMinio:
        mock_client = Mock()
        MockMinio.return_value = mock_client
        mock_client.bucket_exists.return_value = True

        from app.services.minio_service import MinIOService

        service = MinIOService()
        test_data = io.BytesIO(b"test file content from stream")

        result = await service.upload_file(
            bucket_name="test-bucket",
            object_name="test-stream.txt",
            data=test_data,
        )

        assert result is True
        mock_client.put_object.assert_called_once()


@pytest.mark.asyncio
async def test_upload_file_handles_error(minio_exception):
    """Test upload_file handles MinIO errors."""
    with patch("app.services.minio_service.Minio") as MockMinio:
        mock_client = Mock()
        MockMinio.return_value = mock_client
        mock_client.bucket_exists.return_value = True
        mock_client.put_object.side_effect = minio_exception("Upload failed")

        from app.services.minio_service import MinIOService

        service = MinIOService()
        result = await service.upload_file(
            bucket_name="test-bucket",
            object_name="test-fail.txt",
            data=b"data",
        )

        assert result is False


@pytest.mark.asyncio
async def test_upload_file_without_client():
    """Test upload_file returns False when client is unavailable."""
    with patch("app.services.minio_service.Minio", None):
        from app.services.minio_service import MinIOService

        service = MinIOService()
        service.client = None

        result = await service.upload_file(
            bucket_name="test-bucket",
            object_name="test.txt",
            data=b"data",
        )

        assert result is False


@pytest.mark.asyncio
async def test_download_file_success():
    """Test downloading a file successfully."""
    with patch("app.services.minio_service.Minio") as MockMinio:
        mock_client = Mock()
        MockMinio.return_value = mock_client
        mock_client.bucket_exists.return_value = True

        # Mock response object
        mock_response = Mock()
        mock_response.read.return_value = b"downloaded content"
        mock_response.close = Mock()
        mock_response.release_conn = Mock()
        mock_client.get_object.return_value = mock_response

        from app.services.minio_service import MinIOService

        service = MinIOService()
        result = await service.download_file(
            bucket_name="test-bucket",
            object_name="test-download.txt",
        )

        assert result == b"downloaded content"
        mock_response.close.assert_called_once()
        mock_response.release_conn.assert_called_once()


@pytest.mark.asyncio
async def test_download_file_handles_error(minio_exception):
    """Test download_file handles MinIO errors."""
    with patch("app.services.minio_service.Minio") as MockMinio:
        mock_client = Mock()
        MockMinio.return_value = mock_client
        mock_client.bucket_exists.return_value = True
        mock_client.get_object.side_effect = minio_exception("Download failed")

        from app.services.minio_service import MinIOService

        service = MinIOService()
        result = await service.download_file(
            bucket_name="test-bucket",
            object_name="test-fail.txt",
        )

        assert result is None


@pytest.mark.asyncio
async def test_download_file_without_client():
    """Test download_file returns None when client is unavailable."""
    with patch("app.services.minio_service.Minio", None):
        from app.services.minio_service import MinIOService

        service = MinIOService()
        service.client = None

        result = await service.download_file(
            bucket_name="test-bucket",
            object_name="test.txt",
        )

        assert result is None


@pytest.mark.asyncio
async def test_remove_object_success():
    """Test removing an object successfully."""
    with patch("app.services.minio_service.Minio") as MockMinio:
        mock_client = Mock()
        MockMinio.return_value = mock_client
        mock_client.bucket_exists.return_value = True

        from app.services.minio_service import MinIOService

        service = MinIOService()
        result = await service.remove_object(
            bucket_name="test-bucket",
            object_name="test-remove.txt",
        )

        assert result is True
        mock_client.remove_object.assert_called_once_with(
            "test-bucket", "test-remove.txt"
        )


@pytest.mark.asyncio
async def test_remove_object_handles_error(minio_exception):
    """Test remove_object handles MinIO errors."""
    with patch("app.services.minio_service.Minio") as MockMinio:
        mock_client = Mock()
        MockMinio.return_value = mock_client
        mock_client.bucket_exists.return_value = True
        mock_client.remove_object.side_effect = minio_exception("Remove failed")

        from app.services.minio_service import MinIOService

        service = MinIOService()
        result = await service.remove_object(
            bucket_name="test-bucket",
            object_name="test-fail.txt",
        )

        assert result is False


@pytest.mark.asyncio
async def test_remove_object_without_client():
    """Test remove_object returns False when client is unavailable."""
    with patch("app.services.minio_service.Minio", None):
        from app.services.minio_service import MinIOService

        service = MinIOService()
        service.client = None

        result = await service.remove_object(
            bucket_name="test-bucket",
            object_name="test.txt",
        )

        assert result is False


@pytest.mark.asyncio
async def test_list_objects_success():
    """Test listing objects successfully."""
    with patch("app.services.minio_service.Minio") as MockMinio:
        mock_client = Mock()
        MockMinio.return_value = mock_client
        mock_client.bucket_exists.return_value = True

        # Create mock objects
        mock_obj1 = Mock()
        mock_obj1.object_name = "file1.txt"
        mock_obj1.size = 1024
        mock_obj1.last_modified = "2024-01-01"
        mock_obj1.etag = "abc123"

        mock_obj2 = Mock()
        mock_obj2.object_name = "file2.txt"
        mock_obj2.size = 2048
        mock_obj2.last_modified = "2024-01-02"
        mock_obj2.etag = "def456"

        mock_client.list_objects.return_value = [mock_obj1, mock_obj2]

        from app.services.minio_service import MinIOService

        service = MinIOService()
        result = await service.list_objects(
            bucket_name="test-bucket",
            prefix="test/",
        )

        assert len(result) == 2
        assert result[0]["name"] == "file1.txt"
        assert result[0]["size"] == 1024
        assert result[1]["name"] == "file2.txt"
        mock_client.list_objects.assert_called_once_with(
            "test-bucket", prefix="test/", recursive=True
        )


@pytest.mark.asyncio
async def test_list_objects_handles_error(minio_exception):
    """Test list_objects handles MinIO errors."""
    with patch("app.services.minio_service.Minio") as MockMinio:
        mock_client = Mock()
        MockMinio.return_value = mock_client
        mock_client.bucket_exists.return_value = True
        mock_client.list_objects.side_effect = minio_exception("List failed")

        from app.services.minio_service import MinIOService

        service = MinIOService()
        result = await service.list_objects(bucket_name="test-bucket")

        assert result == []


@pytest.mark.asyncio
async def test_list_objects_without_client():
    """Test list_objects returns empty list when client is unavailable."""
    with patch("app.services.minio_service.Minio", None):
        from app.services.minio_service import MinIOService

        service = MinIOService()
        service.client = None

        result = await service.list_objects(bucket_name="test-bucket")

        assert result == []


def test_get_presigned_url_success():
    """Test generating presigned URL successfully."""
    with patch("app.services.minio_service.Minio") as MockMinio:
        mock_client = Mock()
        MockMinio.return_value = mock_client
        mock_client.bucket_exists.return_value = True
        mock_client.presigned_get_object.return_value = (
            "https://example.com/presigned?token=abc"
        )

        from app.services.minio_service import MinIOService

        service = MinIOService()
        result = service.get_presigned_url(
            bucket_name="test-bucket",
            object_name="test-file.txt",
            expires_seconds=7200,
        )

        assert result == "https://example.com/presigned?token=abc"
        mock_client.presigned_get_object.assert_called_once_with(
            "test-bucket", "test-file.txt", expires=7200
        )


def test_get_presigned_url_handles_error(minio_exception):
    """Test get_presigned_url handles MinIO errors."""
    with patch("app.services.minio_service.Minio") as MockMinio:
        mock_client = Mock()
        MockMinio.return_value = mock_client
        mock_client.bucket_exists.return_value = True
        mock_client.presigned_get_object.side_effect = minio_exception(
            "Presigned URL failed"
        )

        from app.services.minio_service import MinIOService

        service = MinIOService()
        result = service.get_presigned_url(
            bucket_name="test-bucket",
            object_name="test-fail.txt",
        )

        assert result is None


def test_get_presigned_url_without_client():
    """Test get_presigned_url returns None when client is unavailable."""
    with patch("app.services.minio_service.Minio", None):
        from app.services.minio_service import MinIOService

        service = MinIOService()
        service.client = None

        result = service.get_presigned_url(
            bucket_name="test-bucket",
            object_name="test.txt",
        )

        assert result is None
