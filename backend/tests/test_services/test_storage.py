"""Comprehensive tests for storage service.

Tests cover:
- StorageResult dataclass
- StorageService class
- store_bytes method
- purge_expired method
- Singleton functions
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from app.services.storage import (
    StorageResult,
    StorageService,
    get_storage_service,
    reset_storage_service,
)

# Mark all tests in this module as not requiring database
pytestmark = pytest.mark.no_db


class TestStorageResult:
    """Tests for StorageResult dataclass."""

    def test_required_fields(self) -> None:
        """Test required fields."""
        result = StorageResult(
            bucket="test-bucket",
            key="uploads/file.dwg",
            uri="s3://test-bucket/uploads/file.dwg",
            bytes_written=1024,
            layer_metadata_uri=None,
            vector_data_uri=None,
        )
        assert result.bucket == "test-bucket"
        assert result.key == "uploads/file.dwg"
        assert result.uri == "s3://test-bucket/uploads/file.dwg"
        assert result.bytes_written == 1024

    def test_optional_uris(self) -> None:
        """Test optional URI fields."""
        result = StorageResult(
            bucket="test-bucket",
            key="uploads/file.dwg",
            uri="s3://test-bucket/uploads/file.dwg",
            bytes_written=1024,
            layer_metadata_uri="s3://test-bucket/uploads/file.dwg.layers.json",
            vector_data_uri="s3://test-bucket/uploads/file.dwg.vectors.json",
        )
        assert result.layer_metadata_uri is not None
        assert result.vector_data_uri is not None

    def test_content_type(self) -> None:
        """Test content_type field."""
        result = StorageResult(
            bucket="test-bucket",
            key="uploads/file.pdf",
            uri="s3://test-bucket/uploads/file.pdf",
            bytes_written=2048,
            layer_metadata_uri=None,
            vector_data_uri=None,
            content_type="application/pdf",
        )
        assert result.content_type == "application/pdf"


class TestStorageResultAsDict:
    """Tests for StorageResult.as_dict method."""

    def test_basic_as_dict(self) -> None:
        """Test as_dict returns correct dictionary."""
        result = StorageResult(
            bucket="test-bucket",
            key="uploads/file.dwg",
            uri="s3://test-bucket/uploads/file.dwg",
            bytes_written=1024,
            layer_metadata_uri=None,
            vector_data_uri=None,
        )
        d = result.as_dict()
        assert d["bucket"] == "test-bucket"
        assert d["key"] == "uploads/file.dwg"
        assert d["uri"] == "s3://test-bucket/uploads/file.dwg"
        assert d["bytes_written"] == 1024

    def test_as_dict_excludes_none_optional(self) -> None:
        """Test as_dict excludes None optional fields."""
        result = StorageResult(
            bucket="test-bucket",
            key="uploads/file.dwg",
            uri="s3://test-bucket/uploads/file.dwg",
            bytes_written=1024,
            layer_metadata_uri=None,
            vector_data_uri=None,
        )
        d = result.as_dict()
        assert "layer_metadata_uri" not in d
        assert "vector_data_uri" not in d
        assert "content_type" not in d

    def test_as_dict_includes_optional_when_set(self) -> None:
        """Test as_dict includes optional fields when set."""
        result = StorageResult(
            bucket="test-bucket",
            key="uploads/file.dwg",
            uri="s3://test-bucket/uploads/file.dwg",
            bytes_written=1024,
            layer_metadata_uri="s3://test-bucket/layers.json",
            vector_data_uri="s3://test-bucket/vectors.json",
            content_type="application/octet-stream",
        )
        d = result.as_dict()
        assert d["layer_metadata_uri"] == "s3://test-bucket/layers.json"
        assert d["vector_data_uri"] == "s3://test-bucket/vectors.json"
        assert d["content_type"] == "application/octet-stream"


class TestStorageService:
    """Tests for StorageService class."""

    def test_init_creates_base_path(self) -> None:
        """Test initialization creates base path directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir) / "storage"
            StorageService(
                bucket="test-bucket",
                prefix="uploads",
                local_base_path=base_path,
            )
            assert base_path.exists()

    def test_init_with_endpoint_url(self) -> None:
        """Test initialization with endpoint URL."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = StorageService(
                bucket="test-bucket",
                prefix="uploads",
                local_base_path=Path(tmpdir),
                endpoint_url="http://localhost:9000",
            )
            assert service.endpoint_url == "http://localhost:9000"


class TestStorageServiceStoreBytes:
    """Tests for StorageService.store_bytes method."""

    def test_store_bytes_creates_file(self) -> None:
        """Test store_bytes creates file on disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = StorageService(
                bucket="test-bucket",
                prefix="uploads",
                local_base_path=Path(tmpdir),
            )
            service.store_bytes(
                key="test/file.txt",
                payload=b"Hello, World!",
            )
            expected_path = Path(tmpdir) / "uploads" / "test" / "file.txt"
            assert expected_path.exists()
            assert expected_path.read_bytes() == b"Hello, World!"

    def test_store_bytes_returns_result(self) -> None:
        """Test store_bytes returns StorageResult."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = StorageService(
                bucket="test-bucket",
                prefix="uploads",
                local_base_path=Path(tmpdir),
            )
            result = service.store_bytes(
                key="test/file.txt",
                payload=b"Hello, World!",
            )
            assert isinstance(result, StorageResult)
            assert result.bucket == "test-bucket"
            assert result.bytes_written == 13

    def test_store_bytes_with_content_type(self) -> None:
        """Test store_bytes with content type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = StorageService(
                bucket="test-bucket",
                prefix="uploads",
                local_base_path=Path(tmpdir),
            )
            result = service.store_bytes(
                key="test/file.pdf",
                payload=b"%PDF-1.4",
                content_type="application/pdf",
            )
            assert result.content_type == "application/pdf"


class TestStorageServiceUri:
    """Tests for URI generation."""

    def test_s3_uri_format(self) -> None:
        """Test S3 URI format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = StorageService(
                bucket="my-bucket",
                prefix="data",
                local_base_path=Path(tmpdir),
            )
            result = service.store_bytes(key="file.txt", payload=b"test")
            assert result.uri.startswith("s3://my-bucket/")

    def test_endpoint_uri_format(self) -> None:
        """Test endpoint URI format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = StorageService(
                bucket="my-bucket",
                prefix="data",
                local_base_path=Path(tmpdir),
                endpoint_url="http://localhost:9000",
            )
            result = service.store_bytes(key="file.txt", payload=b"test")
            assert result.uri.startswith("http://localhost:9000/my-bucket/")


class TestStorageServicePurgeExpired:
    """Tests for StorageService.purge_expired method."""

    def test_purge_returns_empty_list_when_no_files(self) -> None:
        """Test purge returns empty list when no files exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = StorageService(
                bucket="test-bucket",
                prefix="uploads",
                local_base_path=Path(tmpdir),
            )
            removed = service.purge_expired(older_than_days=30)
            assert removed == []

    def test_purge_returns_empty_with_zero_days(self) -> None:
        """Test purge returns empty list when days is 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = StorageService(
                bucket="test-bucket",
                prefix="uploads",
                local_base_path=Path(tmpdir),
            )
            # Create a file
            service.store_bytes(key="test.txt", payload=b"test")
            removed = service.purge_expired(older_than_days=0)
            assert removed == []


class TestSingletonFunctions:
    """Tests for singleton functions."""

    def test_get_storage_service_returns_instance(self) -> None:
        """Test get_storage_service returns an instance."""
        reset_storage_service()
        service = get_storage_service()
        assert isinstance(service, StorageService)

    def test_get_storage_service_returns_same_instance(self) -> None:
        """Test get_storage_service returns the same instance."""
        reset_storage_service()
        service1 = get_storage_service()
        service2 = get_storage_service()
        assert service1 is service2

    def test_reset_storage_service_creates_new_instance(self) -> None:
        """Test reset_storage_service creates new instance."""
        service1 = get_storage_service()
        reset_storage_service()
        service2 = get_storage_service()
        assert service1 is not service2


class TestStorageScenarios:
    """Tests for storage use case scenarios."""

    def test_store_cad_file(self) -> None:
        """Test storing a CAD file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = StorageService(
                bucket="cad-imports",
                prefix="uploads",
                local_base_path=Path(tmpdir),
            )
            result = service.store_bytes(
                key="project-123/floor-plan.dwg",
                payload=b"AC1032" + b"\x00" * 100,  # Mock DWG header
                content_type="application/acad",
            )
            assert "floor-plan.dwg" in result.key
            assert result.bytes_written > 0

    def test_store_pdf_report(self) -> None:
        """Test storing a PDF report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = StorageService(
                bucket="reports",
                prefix="generated",
                local_base_path=Path(tmpdir),
            )
            result = service.store_bytes(
                key="feasibility/report-2024-01.pdf",
                payload=b"%PDF-1.4\n...",
                content_type="application/pdf",
            )
            assert result.content_type == "application/pdf"

    def test_store_json_data(self) -> None:
        """Test storing JSON data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = StorageService(
                bucket="data",
                prefix="exports",
                local_base_path=Path(tmpdir),
            )
            service.store_bytes(
                key="metrics/project-456.json",
                payload=b'{"gfa": 10000, "nia": 8200}',
                content_type="application/json",
            )
            expected_path = Path(tmpdir) / "exports" / "metrics" / "project-456.json"
            assert expected_path.exists()
