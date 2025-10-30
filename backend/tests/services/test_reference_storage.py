"""Tests for the reference storage helper."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from app.services.reference_storage import ReferenceStorage


@dataclass
class _FixedDateTime:
    """Helper to override datetime.now with a deterministic value."""

    year: int = 2025
    month: int = 1
    day: int = 15
    hour: int = 3
    minute: int = 4
    second: int = 5

    def now(self, tz=None):
        from datetime import datetime

        return datetime(
            self.year,
            self.month,
            self.day,
            self.hour,
            self.minute,
            self.second,
            tzinfo=tz,
        )


@pytest.mark.asyncio
async def test_write_document_generates_key_and_uri(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """write_document should include source_id, timestamp, and hash in key/URI."""

    monkeypatch.setenv("REF_STORAGE_BUCKET", "ref-bucket")
    storage = ReferenceStorage(
        base_path=tmp_path,
        prefix="references",
        endpoint_url="https://files.example.com",
    )

    monkeypatch.setattr(
        "app.services.reference_storage.datetime",
        _FixedDateTime(),
    )

    payload = b"reference-content"
    result = await storage.write_document(source_id=42, payload=payload, suffix=".pdf")

    assert result.bytes_written == len(payload)
    assert result.storage_path.startswith("references/source-42/20250115T030405Z-")
    assert result.storage_path.endswith(".pdf")
    assert result.uri.startswith(
        "https://files.example.com/ref-bucket/references/source-42/"
    )

    stored_file = tmp_path / result.storage_path
    assert stored_file.read_bytes() == payload


@pytest.mark.asyncio
async def test_read_and_resolve_document(tmp_path: Path) -> None:
    """read_document and resolve_path should retrieve the stored bytes."""

    storage = ReferenceStorage(base_path=tmp_path, bucket="", prefix="")

    result = await storage.write_document(source_id=1, payload=b"hello", suffix=".txt")

    resolved = storage.resolve_path(result.storage_path)
    assert resolved.exists()

    data = await storage.read_document(result.storage_path)
    assert data == b"hello"
