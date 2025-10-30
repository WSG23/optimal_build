"""High-quality tests for reference document storage service.

This test suite provides comprehensive coverage of the ReferenceStorage class,
focusing on initialization, path resolution, and URI generation logic.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from app.services.reference_storage import ReferenceStorage, ReferenceStorageResult

# =============================================================================
# ReferenceStorageResult Tests
# =============================================================================


def test_reference_storage_result_creation():
    """Test creating ReferenceStorageResult with all fields."""
    result = ReferenceStorageResult(
        storage_path="path/to/file.pdf",
        uri="s3://bucket/path/to/file.pdf",
        bytes_written=1024,
    )

    assert result.storage_path == "path/to/file.pdf"
    assert result.uri == "s3://bucket/path/to/file.pdf"
    assert result.bytes_written == 1024


# =============================================================================
# ReferenceStorage Initialization Tests
# =============================================================================


def test_storage_initialization_with_custom_base_path():
    """Test ReferenceStorage initialization with custom base path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        custom_path = Path(tmpdir) / "custom"
        storage = ReferenceStorage(base_path=custom_path)

        assert storage.base_path == custom_path
        assert custom_path.exists()  # Should be created


def test_storage_initialization_creates_base_path():
    """Test that initialization creates the base path if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        new_path = Path(tmpdir) / "new" / "nested" / "path"
        assert not new_path.exists()

        storage = ReferenceStorage(base_path=new_path)

        assert new_path.exists()
        assert storage.base_path == new_path


def test_storage_initialization_with_bucket():
    """Test initialization with explicit bucket name."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = ReferenceStorage(base_path=Path(tmpdir), bucket="my-bucket")

        assert storage.bucket == "my-bucket"


def test_storage_initialization_with_custom_prefix():
    """Test initialization with custom prefix."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = ReferenceStorage(base_path=Path(tmpdir), prefix="documents")

        assert storage.prefix == "documents"


def test_storage_initialization_strips_prefix_slashes():
    """Test that prefix slashes are stripped."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = ReferenceStorage(base_path=Path(tmpdir), prefix="/documents/")

        assert storage.prefix == "documents"


def test_storage_initialization_with_endpoint_url():
    """Test initialization with custom endpoint URL."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = ReferenceStorage(
            base_path=Path(tmpdir), endpoint_url="https://s3.example.com"
        )

        assert storage.endpoint_url == "https://s3.example.com"


def test_storage_initialization_reads_env_bucket(monkeypatch):
    """Test that bucket is read from environment variables."""
    monkeypatch.setenv("REF_STORAGE_BUCKET", "env-bucket")

    with tempfile.TemporaryDirectory() as tmpdir:
        storage = ReferenceStorage(base_path=Path(tmpdir))

        assert storage.bucket == "env-bucket"


def test_storage_initialization_prefers_ref_storage_bucket_env(monkeypatch):
    """Test that REF_STORAGE_BUCKET is preferred over STORAGE_BUCKET."""
    monkeypatch.setenv("REF_STORAGE_BUCKET", "ref-bucket")
    monkeypatch.setenv("STORAGE_BUCKET", "generic-bucket")

    with tempfile.TemporaryDirectory() as tmpdir:
        storage = ReferenceStorage(base_path=Path(tmpdir))

        assert storage.bucket == "ref-bucket"


def test_storage_initialization_falls_back_to_storage_bucket_env(monkeypatch):
    """Test fallback to STORAGE_BUCKET env var."""
    monkeypatch.delenv("REF_STORAGE_BUCKET", raising=False)
    monkeypatch.setenv("STORAGE_BUCKET", "generic-bucket")

    with tempfile.TemporaryDirectory() as tmpdir:
        storage = ReferenceStorage(base_path=Path(tmpdir))

        assert storage.bucket == "generic-bucket"


def test_storage_initialization_empty_bucket_when_no_env(monkeypatch):
    """Test that bucket is empty string when no env vars set."""
    monkeypatch.delenv("REF_STORAGE_BUCKET", raising=False)
    monkeypatch.delenv("STORAGE_BUCKET", raising=False)

    with tempfile.TemporaryDirectory() as tmpdir:
        storage = ReferenceStorage(base_path=Path(tmpdir))

        assert storage.bucket == ""


def test_storage_initialization_reads_endpoint_url_env(monkeypatch):
    """Test that endpoint URL is read from environment."""
    monkeypatch.setenv("REF_STORAGE_ENDPOINT_URL", "https://ref-s3.example.com")

    with tempfile.TemporaryDirectory() as tmpdir:
        storage = ReferenceStorage(base_path=Path(tmpdir))

        assert storage.endpoint_url == "https://ref-s3.example.com"


def test_storage_initialization_prefers_ref_storage_endpoint_env(monkeypatch):
    """Test that REF_STORAGE_ENDPOINT_URL is preferred."""
    monkeypatch.setenv("REF_STORAGE_ENDPOINT_URL", "https://ref-s3.example.com")
    monkeypatch.setenv("STORAGE_ENDPOINT_URL", "https://generic-s3.example.com")

    with tempfile.TemporaryDirectory() as tmpdir:
        storage = ReferenceStorage(base_path=Path(tmpdir))

        assert storage.endpoint_url == "https://ref-s3.example.com"


# =============================================================================
# ReferenceStorage._resolve_base_path() Tests
# =============================================================================


def test_resolve_base_path_from_ref_storage_local_path_env(monkeypatch):
    """Test resolving base path from REF_STORAGE_LOCAL_PATH."""
    monkeypatch.setenv("REF_STORAGE_LOCAL_PATH", "/custom/ref/path")

    path = ReferenceStorage._resolve_base_path()

    assert path == Path("/custom/ref/path")


def test_resolve_base_path_from_storage_local_path_env(monkeypatch):
    """Test resolving base path from STORAGE_LOCAL_PATH fallback."""
    monkeypatch.delenv("REF_STORAGE_LOCAL_PATH", raising=False)
    monkeypatch.setenv("STORAGE_LOCAL_PATH", "/custom/storage/path")

    path = ReferenceStorage._resolve_base_path()

    assert path == Path("/custom/storage/path")


def test_resolve_base_path_defaults_to_storage(monkeypatch):
    """Test that base path defaults to .storage when no env vars set."""
    monkeypatch.delenv("REF_STORAGE_LOCAL_PATH", raising=False)
    monkeypatch.delenv("STORAGE_LOCAL_PATH", raising=False)

    path = ReferenceStorage._resolve_base_path()

    assert path == Path(".storage")


def test_resolve_base_path_prefers_ref_storage_env(monkeypatch):
    """Test that REF_STORAGE_LOCAL_PATH is preferred over STORAGE_LOCAL_PATH."""
    monkeypatch.setenv("REF_STORAGE_LOCAL_PATH", "/ref/path")
    monkeypatch.setenv("STORAGE_LOCAL_PATH", "/generic/path")

    path = ReferenceStorage._resolve_base_path()

    assert path == Path("/ref/path")


# =============================================================================
# ReferenceStorage.resolve_path() Tests
# =============================================================================


def test_resolve_path_combines_base_and_storage_path():
    """Test that resolve_path combines base path with storage path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = ReferenceStorage(base_path=Path(tmpdir))

        result = storage.resolve_path("documents/file.pdf")

        assert result == Path(tmpdir) / "documents/file.pdf"


def test_resolve_path_handles_nested_paths():
    """Test resolving deeply nested paths."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = ReferenceStorage(base_path=Path(tmpdir))

        result = storage.resolve_path("level1/level2/level3/file.txt")

        assert result == Path(tmpdir) / "level1/level2/level3/file.txt"


def test_resolve_path_with_prefix_in_storage_key():
    """Test resolving path that includes the prefix."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = ReferenceStorage(base_path=Path(tmpdir), prefix="ref-docs")

        result = storage.resolve_path("ref-docs/source-1/file.pdf")

        assert result == Path(tmpdir) / "ref-docs/source-1/file.pdf"


# =============================================================================
# ReferenceStorage._to_uri() Tests
# =============================================================================


def test_to_uri_with_endpoint_and_bucket():
    """Test URI generation with endpoint URL and bucket."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = ReferenceStorage(
            base_path=Path(tmpdir),
            bucket="my-bucket",
            endpoint_url="https://s3.example.com",
        )

        uri = storage._to_uri("documents/file.pdf")

        assert uri == "https://s3.example.com/my-bucket/documents/file.pdf"


def test_to_uri_with_endpoint_strips_trailing_slash():
    """Test that trailing slash is stripped from endpoint URL."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = ReferenceStorage(
            base_path=Path(tmpdir),
            bucket="my-bucket",
            endpoint_url="https://s3.example.com/",
        )

        uri = storage._to_uri("file.pdf")

        assert uri == "https://s3.example.com/my-bucket/file.pdf"


def test_to_uri_with_endpoint_without_bucket():
    """Test URI generation with endpoint but no bucket."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = ReferenceStorage(
            base_path=Path(tmpdir), endpoint_url="https://s3.example.com"
        )

        uri = storage._to_uri("documents/file.pdf")

        assert uri == "https://s3.example.com/documents/file.pdf"


def test_to_uri_with_bucket_without_endpoint():
    """Test S3 URI generation with bucket but no endpoint."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = ReferenceStorage(base_path=Path(tmpdir), bucket="my-bucket")

        uri = storage._to_uri("documents/file.pdf")

        assert uri == "s3://my-bucket/documents/file.pdf"


def test_to_uri_without_bucket_or_endpoint():
    """Test URI generation without bucket or endpoint returns key as-is."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = ReferenceStorage(base_path=Path(tmpdir))

        uri = storage._to_uri("documents/file.pdf")

        assert uri == "documents/file.pdf"


def test_to_uri_normalizes_path_separators():
    """Test that path separators are normalized to forward slashes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = ReferenceStorage(base_path=Path(tmpdir), bucket="my-bucket")

        # Use OS-specific separator
        storage_key = os.path.join("documents", "subfolder", "file.pdf")
        uri = storage._to_uri(storage_key)

        # Should use forward slashes in URI
        assert uri == "s3://my-bucket/documents/subfolder/file.pdf"


def test_to_uri_with_complex_path():
    """Test URI generation with complex nested paths."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = ReferenceStorage(
            base_path=Path(tmpdir),
            bucket="bucket",
            endpoint_url="https://storage.example.com",
        )

        uri = storage._to_uri("prefix/source-123/2024/01/file.pdf")

        assert (
            uri
            == "https://storage.example.com/bucket/prefix/source-123/2024/01/file.pdf"
        )


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.asyncio
async def test_write_document_creates_storage_result():
    """Test that write_document creates appropriate directory structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = ReferenceStorage(base_path=Path(tmpdir), prefix="ref-documents")

        payload = b"Test document content"
        result = await storage.write_document(
            source_id=123, payload=payload, suffix=".pdf"
        )

        assert result.bytes_written == len(payload)
        assert "ref-documents/source-123/" in result.storage_path
        assert result.storage_path.endswith(".pdf")
        assert isinstance(result.uri, str)


@pytest.mark.asyncio
async def test_write_document_creates_subdirectories():
    """Test that write_document creates necessary subdirectories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = ReferenceStorage(base_path=Path(tmpdir), prefix="documents")

        payload = b"Content"
        result = await storage.write_document(
            source_id=456, payload=payload, suffix=".txt"
        )

        # Verify file was actually written
        file_path = storage.resolve_path(result.storage_path)
        assert file_path.exists()
        assert file_path.read_bytes() == payload


@pytest.mark.asyncio
async def test_read_document_retrieves_content():
    """Test that read_document retrieves written content."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = ReferenceStorage(base_path=Path(tmpdir))

        payload = b"Test content to read back"
        write_result = await storage.write_document(
            source_id=789, payload=payload, suffix=".txt"
        )

        # Read it back
        retrieved = await storage.read_document(write_result.storage_path)

        assert retrieved == payload


@pytest.mark.asyncio
async def test_write_document_filename_includes_digest():
    """Test that filename includes content digest for uniqueness."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = ReferenceStorage(base_path=Path(tmpdir))

        payload1 = b"Content A"
        payload2 = b"Content B"

        result1 = await storage.write_document(
            source_id=1, payload=payload1, suffix=".txt"
        )
        result2 = await storage.write_document(
            source_id=1, payload=payload2, suffix=".txt"
        )

        # Different content should produce different filenames
        assert result1.storage_path != result2.storage_path


@pytest.mark.asyncio
async def test_write_document_with_empty_prefix():
    """Test write_document when prefix is empty."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = ReferenceStorage(base_path=Path(tmpdir), prefix="")

        payload = b"Test"
        result = await storage.write_document(
            source_id=1, payload=payload, suffix=".txt"
        )

        # Should start directly with source-
        assert result.storage_path.startswith("source-1/")
