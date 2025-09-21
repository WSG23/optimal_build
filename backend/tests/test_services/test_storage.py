from __future__ import annotations

import pytest
from app.services.storage import StorageConfig, StorageService


@pytest.mark.asyncio
async def test_storage_store_and_read(tmp_path) -> None:
    config = StorageConfig(
        bucket="test-bucket",
        endpoint_url=str(tmp_path),
        access_key="test",
        secret_key="test",
        region_name="us-east-1",
        use_ssl=False,
    )
    service = StorageService(config)
    artifact = service.store_bytes(b"hello world", "documents/test.txt", content_type="text/plain")
    assert artifact.size == len(b"hello world")
    data = service.read_bytes("documents/test.txt")
    assert data == b"hello world"
