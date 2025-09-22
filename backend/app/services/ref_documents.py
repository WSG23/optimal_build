"""Helpers for persisting and retrieving reference documents."""

from __future__ import annotations

import asyncio
import hashlib
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.models.rkp import RefSource


def _slugify(value: str) -> str:
    """Return a filesystem friendly representation of *value*."""

    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return re.sub(r"-+", "-", value).strip("-")


def compute_document_checksum(payload: bytes) -> str:
    """Compute the SHA-256 checksum for the provided payload."""

    return hashlib.sha256(payload).hexdigest()


@dataclass(slots=True)
class StoredDocument:
    """Metadata captured after persisting a reference document."""

    storage_path: str
    uri: str
    bytes_written: int


class DocumentStorageService:
    """Persist reference documents to a filesystem-backed store."""

    def __init__(
        self,
        *,
        bucket: str,
        prefix: str,
        local_base_path: Path,
        endpoint_url: Optional[str] = None,
    ) -> None:
        self.bucket = bucket
        self.prefix = prefix.strip("/")
        self.local_base_path = local_base_path
        self.endpoint_url = endpoint_url
        self.local_base_path.mkdir(parents=True, exist_ok=True)

    def _build_relative_key(self, source: RefSource, filename: str) -> str:
        parts: list[str] = []
        if self.prefix:
            parts.append(self.prefix)
        parts.extend(
            [
                _slugify(source.jurisdiction or "global"),
                _slugify(source.authority or "authority"),
                f"source-{source.id}",
                filename,
            ]
        )
        return "/".join(filter(None, parts))

    def _make_filename(self, source: RefSource, extension: str, payload: bytes) -> str:
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        digest = hashlib.md5(payload).hexdigest()[:10]
        ext = extension.lstrip(".") or "bin"
        return f"{timestamp}-{digest}.{ext}"

    def _resolve_path(self, relative_key: str) -> Path:
        return self.local_base_path / Path(relative_key)

    def _to_uri(self, relative_key: str) -> str:
        key = relative_key.replace(os.sep, "/")
        if self.endpoint_url:
            base = self.endpoint_url.rstrip("/")
            if self.bucket:
                return f"{base}/{self.bucket}/{key}"
            return f"{base}/{key}"
        if self.bucket:
            return f"s3://{self.bucket}/{key}"
        return key

    async def write_document(self, *, source: RefSource, payload: bytes, extension: str) -> StoredDocument:
        """Persist *payload* for *source* and return storage metadata."""

        filename = self._make_filename(source, extension, payload)
        relative_key = self._build_relative_key(source, filename)
        file_path = self._resolve_path(relative_key)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(file_path.write_bytes, payload)
        return StoredDocument(
            storage_path=relative_key,
            uri=self._to_uri(relative_key),
            bytes_written=len(payload),
        )

    async def read_document(self, storage_path: str) -> bytes:
        """Retrieve the persisted payload referenced by *storage_path*."""

        file_path = self._resolve_path(storage_path)
        return await asyncio.to_thread(file_path.read_bytes)


_document_storage_service: DocumentStorageService | None = None


def get_document_storage_service() -> DocumentStorageService:
    """Return a singleton document storage service instance."""

    global _document_storage_service
    if _document_storage_service is None:
        bucket = os.getenv("REF_STORAGE_BUCKET", "")
        prefix = os.getenv("REF_STORAGE_PREFIX", "ref-documents")
        base_path = Path(os.getenv("REF_STORAGE_LOCAL_PATH", ".ref-docs"))
        endpoint_url = os.getenv("REF_STORAGE_ENDPOINT_URL")
        _document_storage_service = DocumentStorageService(
            bucket=bucket,
            prefix=prefix,
            local_base_path=base_path,
            endpoint_url=endpoint_url,
        )
    return _document_storage_service


def reset_document_storage_service() -> None:
    """Reset the cached storage service. Intended for tests."""

    global _document_storage_service
    _document_storage_service = None


__all__ = [
    "DocumentStorageService",
    "StoredDocument",
    "compute_document_checksum",
    "get_document_storage_service",
    "reset_document_storage_service",
]
