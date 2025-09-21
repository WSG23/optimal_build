"""Storage helpers for interacting with S3 or filesystem fallbacks."""

from __future__ import annotations

import hashlib
import importlib.util
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import httpx

from app.utils.logging import get_logger

logger = get_logger(__name__)

_BOTO3_SPEC = importlib.util.find_spec("boto3")
HAS_BOTO3 = _BOTO3_SPEC is not None

if HAS_BOTO3:  # pragma: no cover - boto3 unavailable on some Python versions
    import boto3
    from botocore.client import Config
    from botocore.exceptions import ClientError
else:  # pragma: no cover - exercised in local filesystem mode
    boto3 = None  # type: ignore[assignment]

    class Config:  # type: ignore[override]
        def __init__(self, *args: object, **kwargs: object) -> None:  # noqa: D401
            pass

    class ClientError(Exception):
        """Placeholder client error when boto3 is not installed."""

        pass


@dataclass
class StorageConfig:
    """Configuration required to talk to object storage."""

    bucket: str
    endpoint_url: Optional[str] = None
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    region_name: Optional[str] = None
    use_ssl: bool = True


@dataclass
class StorageArtifact:
    """Metadata describing a stored object."""

    bucket: str
    key: str
    checksum: str
    size: int
    content_type: Optional[str]
    stored_at: str
    metadata: Dict[str, str]


class StorageService:
    """High-level helper for downloading and uploading artifacts."""

    def __init__(self, config: StorageConfig) -> None:
        self._config = config
        if HAS_BOTO3:
            session = boto3.session.Session()
            self._client = session.client(
                "s3",
                endpoint_url=config.endpoint_url,
                aws_access_key_id=config.access_key,
                aws_secret_access_key=config.secret_key,
                region_name=config.region_name,
                use_ssl=config.use_ssl,
                config=Config(signature_version="s3v4"),
            )
            self._ensure_bucket()
            self._base_path: Optional[Path] = None
        else:
            base_dir = Path("/tmp/object-storage")
            if config.endpoint_url:
                base_dir = Path(config.endpoint_url)
            self._base_path = base_dir / config.bucket
            self._base_path.mkdir(parents=True, exist_ok=True)
            self._client = None

    def _ensure_bucket(self) -> None:
        if not HAS_BOTO3:
            return
        try:
            self._client.head_bucket(Bucket=self._config.bucket)
        except ClientError:
            logger.info("creating_bucket", bucket=self._config.bucket)
            self._client.create_bucket(Bucket=self._config.bucket)

    async def download_to_object_store(
        self,
        url: str,
        key: str,
        *,
        metadata: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> StorageArtifact:
        """Download a remote document and persist it into object storage."""

        metadata = {key: str(value) for key, value in (metadata or {}).items()}
        async with httpx.AsyncClient(follow_redirects=True, headers=headers) as client:
            response = await client.get(url)
            response.raise_for_status()
            content = response.content
            checksum = hashlib.sha256(content).hexdigest()
            logger.info(
                "downloaded_document",
                url=url,
                bytes=len(content),
                checksum=checksum,
            )
            return self.store_bytes(
                content,
                key,
                content_type=response.headers.get("content-type"),
                metadata=metadata,
            )

    def store_bytes(
        self,
        data: bytes,
        key: str,
        *,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> StorageArtifact:
        """Persist bytes to object storage and return artifact metadata."""

        metadata = {key: str(value) for key, value in (metadata or {}).items()}
        checksum = hashlib.sha256(data).hexdigest()
        if HAS_BOTO3:
            self._client.put_object(
                Bucket=self._config.bucket,
                Key=key,
                Body=data,
                Metadata=metadata,
                ContentType=content_type,
            )
        else:
            assert self._base_path is not None
            destination = self._base_path / key
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
        logger.info("stored_object", key=key, checksum=checksum, size=len(data))
        return StorageArtifact(
            bucket=self._config.bucket,
            key=key,
            checksum=checksum,
            size=len(data),
            content_type=content_type,
            stored_at=datetime.utcnow().isoformat(),
            metadata=metadata,
        )

    def read_bytes(self, key: str) -> bytes:
        """Return the object body for a given key."""

        if HAS_BOTO3:
            obj = self._client.get_object(Bucket=self._config.bucket, Key=key)
            return obj["Body"].read()
        assert self._base_path is not None
        destination = self._base_path / key
        return destination.read_bytes()

    def generate_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """Generate a temporary URL for the object."""

        if HAS_BOTO3:
            return self._client.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": self._config.bucket, "Key": key},
                ExpiresIn=expires_in,
            )
        assert self._base_path is not None
        destination = (self._base_path / key).resolve()
        return f"file://{destination}"
