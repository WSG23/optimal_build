"""Storage helpers for CAD/BIM payloads."""

from __future__ import annotations

import asyncio
import json
import os
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class StorageResult:
    """Outcome of storing an uploaded payload."""

    bucket: str
    key: str
    uri: str
    bytes_written: int
    layer_metadata_uri: str | None
    vector_data_uri: str | None


class StorageService:
    """Persist payloads to an S3 compatible target with a local fallback."""

    def __init__(
        self,
        *,
        bucket: str,
        prefix: str,
        local_base_path: Path,
        endpoint_url: str | None = None,
    ) -> None:
        self.bucket = bucket
        self.prefix = prefix.strip("/")
        self.local_base_path = local_base_path
        self.endpoint_url = endpoint_url
        self._ensure_base_path()

    def _ensure_base_path(self) -> None:
        self.local_base_path.mkdir(parents=True, exist_ok=True)

    async def store_import_file(
        self,
        *,
        import_id: str,
        filename: str,
        payload: bytes,
        layer_metadata: Iterable[dict[str, Any]] | None = None,
        vector_payload: Mapping[str, Any] | None = None,
    ) -> StorageResult:
        """Persist the payload and optional metadata."""

        key_prefix = f"{self.prefix}/{import_id}" if self.prefix else import_id
        relative_key = f"{key_prefix}/{filename}"
        file_path = self.local_base_path / relative_key
        file_path.parent.mkdir(parents=True, exist_ok=True)

        await asyncio.to_thread(file_path.write_bytes, payload)

        layer_metadata_uri: str | None = None
        vector_data_uri: str | None = None
        if layer_metadata is not None:
            metadata_path = file_path.with_suffix(file_path.suffix + ".layers.json")
            json_payload = json.dumps(list(layer_metadata), indent=2, sort_keys=True)
            await asyncio.to_thread(metadata_path.write_text, json_payload)
            layer_metadata_uri = self._to_uri(
                metadata_path.relative_to(self.local_base_path)
            )

        if vector_payload is not None:
            vector_path = file_path.with_suffix(file_path.suffix + ".vectors.json")
            vector_json = json.dumps(vector_payload, indent=2, sort_keys=True)
            await asyncio.to_thread(vector_path.write_text, vector_json)
            vector_data_uri = self._to_uri(
                vector_path.relative_to(self.local_base_path)
            )

        return StorageResult(
            bucket=self.bucket,
            key=relative_key,
            uri=self._to_uri(relative_key),
            bytes_written=len(payload),
            layer_metadata_uri=layer_metadata_uri,
            vector_data_uri=vector_data_uri,
        )

    def _to_uri(self, relative_path: os.PathLike[str] | str) -> str:
        key = str(relative_path).replace(os.sep, "/")
        if self.endpoint_url:
            base = self.endpoint_url.rstrip("/")
            if self.bucket:
                return f"{base}/{self.bucket}/{key}"
            return f"{base}/{key}"
        if self.bucket:
            return f"s3://{self.bucket}/{key}"
        return key


_storage_service: StorageService | None = None


def get_storage_service() -> StorageService:
    """Retrieve a singleton storage service instance configured from the environment."""

    global _storage_service
    if _storage_service is None:
        bucket = os.getenv("STORAGE_BUCKET", "local-imports")
        prefix = os.getenv("STORAGE_PREFIX", "uploads")
        base_path = Path(os.getenv("STORAGE_LOCAL_PATH", ".storage"))
        endpoint_url = os.getenv("STORAGE_ENDPOINT_URL")
        _storage_service = StorageService(
            bucket=bucket,
            prefix=prefix,
            local_base_path=base_path,
            endpoint_url=endpoint_url,
        )
    return _storage_service


def reset_storage_service() -> None:
    """Reset the cached storage service. Intended for tests."""

    global _storage_service
    _storage_service = None


__all__ = [
    "StorageResult",
    "StorageService",
    "get_storage_service",
    "reset_storage_service",
]
