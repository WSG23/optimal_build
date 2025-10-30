"""Unit tests for the storage service local fallback."""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from app.services.storage import StorageResult, StorageService


@pytest.mark.asyncio
async def test_store_import_file_writes_payload_and_metadata(tmp_path: Path) -> None:
    """store_import_file should persist payload, metadata, and vector JSON."""

    service = StorageService(
        bucket="demo-bucket",
        prefix="imports",
        local_base_path=tmp_path,
        endpoint_url=None,
    )

    payload = b"test-payload"
    layer_metadata = [{"layer": "L1", "color": "red"}]
    vector_payload = {"features": [{"name": "poly", "area": 42}]}

    result = await service.store_import_file(
        import_id="abc123",
        filename="drawing.dxf",
        payload=payload,
        layer_metadata=layer_metadata,
        vector_payload=vector_payload,
    )

    stored_path = tmp_path / "imports/abc123/drawing.dxf"
    metadata_path = stored_path.with_suffix(".dxf.layers.json")
    vector_path = stored_path.with_suffix(".dxf.vectors.json")

    assert stored_path.read_bytes() == payload
    assert json.loads(metadata_path.read_text()) == layer_metadata
    assert json.loads(vector_path.read_text()) == vector_payload

    assert result.bucket == "demo-bucket"
    assert result.key == "imports/abc123/drawing.dxf"
    assert result.uri == "s3://demo-bucket/imports/abc123/drawing.dxf"
    assert (
        result.layer_metadata_uri
        == "s3://demo-bucket/imports/abc123/drawing.dxf.layers.json"
    )
    assert (
        result.vector_data_uri
        == "s3://demo-bucket/imports/abc123/drawing.dxf.vectors.json"
    )
    assert result.as_dict()["uri"] == result.uri


def test_store_bytes_honours_endpoint_and_retention(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """store_bytes should construct URIs with endpoint and purge expired files."""

    monkeypatch.setenv("STORAGE_RETENTION_DAYS", "1")
    service = StorageService(
        bucket="demo-bucket",
        prefix="assets",
        local_base_path=tmp_path,
        endpoint_url="http://localhost:9000",
    )

    # Create an old file that should be removed by retention.
    old_file = tmp_path / "assets/old/data.txt"
    old_file.parent.mkdir(parents=True, exist_ok=True)
    old_file.write_text("stale")
    old_time = datetime.now() - timedelta(days=2)
    os.utime(old_file, (old_time.timestamp(), old_time.timestamp()))

    result = service.store_bytes(
        key="current.bin",
        payload=b"live-data",
        content_type="application/octet-stream",
    )

    stored_path = tmp_path / "assets/current.bin"
    assert stored_path.read_bytes() == b"live-data"
    assert result.content_type == "application/octet-stream"
    assert result.uri == "http://localhost:9000/demo-bucket/assets/current.bin"
    assert not old_file.exists(), "retention should purge files older than cutoff"


def test_storage_result_optional_fields_absent_when_none() -> None:
    """as_dict should omit optional fields that are None."""

    result = StorageResult(
        bucket="bucket",
        key="key",
        uri="s3://bucket/key",
        bytes_written=10,
        layer_metadata_uri=None,
        vector_data_uri=None,
    )

    payload = result.as_dict()
    assert "layer_metadata_uri" not in payload
    assert "vector_data_uri" not in payload
    assert payload["bytes_written"] == 10
