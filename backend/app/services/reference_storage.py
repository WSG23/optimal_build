"""Storage helpers for reference source documents."""

from __future__ import annotations

import asyncio
import hashlib
import os
from datetime import datetime
from pathlib import Path

from backend._compat import compat_dataclass
from backend._compat.datetime import UTC


@compat_dataclass(slots=True)
class ReferenceStorageResult:
    """Metadata about a persisted reference document."""

    storage_path: str
    uri: str
    bytes_written: int


class ReferenceStorage:
    """Persist reference documents to a filesystem/S3 compatible backend."""

    def __init__(
        self,
        *,
        base_path: Path | None = None,
        bucket: str | None = None,
        prefix: str = "ref-documents",
        endpoint_url: str | None = None,
    ) -> None:
        self.base_path = base_path or self._resolve_base_path()
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.bucket = (
            bucket
            if bucket is not None
            else os.getenv("REF_STORAGE_BUCKET", os.getenv("STORAGE_BUCKET", ""))
        )
        self.prefix = prefix.strip("/")
        self.endpoint_url = endpoint_url or os.getenv(
            "REF_STORAGE_ENDPOINT_URL", os.getenv("STORAGE_ENDPOINT_URL")
        )

    @staticmethod
    def _resolve_base_path() -> Path:
        base = (
            os.getenv("REF_STORAGE_LOCAL_PATH")
            or os.getenv("STORAGE_LOCAL_PATH")
            or ".storage"
        )
        return Path(base)

    async def write_document(
        self, *, source_id: int, payload: bytes, suffix: str
    ) -> ReferenceStorageResult:
        """Persist ``payload`` for ``source_id`` using a content derived key."""

        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        digest = hashlib.sha256(payload).hexdigest()[:12]
        filename = f"{timestamp}-{digest}{suffix}"
        key_parts = [
            part for part in (self.prefix, f"source-{source_id}", filename) if part
        ]
        storage_key = "/".join(key_parts)
        file_path = self.base_path / storage_key
        file_path.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(file_path.write_bytes, payload)
        uri = self._to_uri(storage_key)
        return ReferenceStorageResult(
            storage_path=storage_key, uri=uri, bytes_written=len(payload)
        )

    async def read_document(self, storage_path: str) -> bytes:
        """Retrieve the raw bytes for ``storage_path``."""

        file_path = self.base_path / storage_path
        return await asyncio.to_thread(file_path.read_bytes)

    def resolve_path(self, storage_path: str) -> Path:
        """Return the absolute path for ``storage_path`` without reading it."""

        return self.base_path / storage_path

    def _to_uri(self, storage_key: str) -> str:
        key = storage_key.replace(os.sep, "/")
        if self.endpoint_url:
            base = self.endpoint_url.rstrip("/")
            if self.bucket:
                return f"{base}/{self.bucket}/{key}"
            return f"{base}/{key}"
        if self.bucket:
            return f"s3://{self.bucket}/{key}"
        return key


__all__ = ["ReferenceStorage", "ReferenceStorageResult"]
