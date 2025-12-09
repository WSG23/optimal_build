"""MinIO/S3 storage service wrapper."""

import io
import re
from typing import BinaryIO, Optional, Union

try:  # pragma: no cover - optional runtime dependency
    from minio import Minio
    from minio.error import MinioException
except ModuleNotFoundError:  # pragma: no cover - provide lightweight stub
    Minio = None  # type: ignore[assignment]

    class MinioException(Exception):
        """Fallback MinIO exception type."""

        pass


import structlog

from app.core.config import settings

logger = structlog.get_logger()


def sanitize_object_name(object_name: str) -> str:
    """Sanitize object name to prevent path traversal attacks.

    Args:
        object_name: The requested object name/path

    Returns:
        Sanitized object name safe for storage

    Raises:
        ValueError: If the object name is invalid or potentially malicious
    """
    if not object_name:
        raise ValueError("Object name cannot be empty")

    # Remove null bytes and other control characters
    object_name = re.sub(r"[\x00-\x1f\x7f]", "", object_name)

    # Normalize path separators
    object_name = object_name.replace("\\", "/")

    # Split into parts and filter out dangerous components
    parts = object_name.split("/")
    safe_parts = []

    for part in parts:
        # Skip empty parts (from leading/trailing/double slashes)
        if not part:
            continue
        # Block parent directory traversal
        if part == "..":
            raise ValueError("Path traversal detected: '..' not allowed")
        # Block current directory references (usually harmless but unnecessary)
        if part == ".":
            continue
        # Block hidden files starting with dot (optional security measure)
        # Uncomment if you want to block hidden files:
        # if part.startswith("."):
        #     raise ValueError(f"Hidden files not allowed: {part}")
        safe_parts.append(part)

    if not safe_parts:
        raise ValueError("Object name resolves to empty path")

    # Reconstruct the safe path
    safe_name = "/".join(safe_parts)

    # Additional validation: ensure the name doesn't start with /
    safe_name = safe_name.lstrip("/")

    # Limit total path length (S3 max is 1024 bytes)
    if len(safe_name.encode("utf-8")) > 1024:
        raise ValueError("Object name exceeds maximum length (1024 bytes)")

    return safe_name


class MinIOService:
    """Service for interacting with MinIO/S3 storage."""

    def __init__(
        self,
        endpoint: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        secure: bool = False,
    ):
        self.endpoint = endpoint or settings.S3_ENDPOINT.replace("http://", "").replace(
            "https://", ""
        )
        self.access_key = access_key or settings.S3_ACCESS_KEY
        self.secret_key = secret_key or settings.S3_SECRET_KEY
        self.secure = secure
        self.client = None

        if Minio is not None:
            self.client = Minio(
                self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure,
            )
            for bucket in {
                settings.S3_BUCKET,
                settings.IMPORTS_BUCKET_NAME,
                settings.EXPORTS_BUCKET_NAME,
                settings.DOCUMENTS_BUCKET_NAME,
            }:
                if bucket:
                    self._ensure_bucket(bucket)
        else:  # pragma: no cover - warn in reduced environments
            logger.warning(
                "MinIO client unavailable; storage operations will be no-ops"
            )

    def _ensure_bucket(self, bucket_name: str) -> None:
        """Ensure bucket exists, create if not."""
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                logger.info(f"Created bucket: {bucket_name}")
        except MinioException as e:
            logger.error(f"Error ensuring bucket {bucket_name}: {str(e)}")
        except Exception as e:
            # Handle connection errors (e.g., MinIO not running)
            logger.warning(
                f"Could not connect to MinIO for bucket {bucket_name}: {str(e)}"
            )

    async def upload_file(
        self,
        bucket_name: str,
        object_name: str,
        data: Union[bytes, BinaryIO],
        content_type: str = "application/octet-stream",
        metadata: Optional[dict] = None,
        max_size_bytes: int = 50 * 1024 * 1024,  # 50MB default limit
    ) -> bool:
        """Upload file to MinIO/S3.

        Args:
            bucket_name: Target bucket name
            object_name: Object path/name (will be sanitized)
            data: File content as bytes or file-like object
            content_type: MIME type of the file
            metadata: Optional metadata dict
            max_size_bytes: Maximum allowed file size (default 50MB)

        Returns:
            True if upload succeeded, False otherwise

        Raises:
            ValueError: If object_name contains path traversal or file exceeds size limit
        """
        if self.client is None:
            logger.warning("MinIO client unavailable; skipping upload")
            return False

        # Sanitize object name to prevent path traversal
        safe_object_name = sanitize_object_name(object_name)

        try:
            # Convert bytes to BytesIO if needed
            if isinstance(data, bytes):
                data = io.BytesIO(data)

            # Get size
            data.seek(0, 2)  # Seek to end
            size = data.tell()
            data.seek(0)  # Reset to beginning

            # Enforce file size limit
            if size > max_size_bytes:
                logger.warning(
                    f"File size {size} exceeds limit {max_size_bytes}",
                    object_name=safe_object_name,
                )
                raise ValueError(
                    f"File size ({size} bytes) exceeds maximum allowed "
                    f"({max_size_bytes} bytes)"
                )

            # Upload with sanitized name
            self.client.put_object(
                bucket_name,
                safe_object_name,
                data,
                size,
                content_type=content_type,
                metadata=metadata,
            )

            logger.info(f"Uploaded {safe_object_name} to {bucket_name}")
            return True

        except MinioException as e:
            logger.error(f"Error uploading {object_name}: {str(e)}")
            return False

    async def download_file(
        self, bucket_name: str, object_name: str
    ) -> Optional[bytes]:
        """Download file from MinIO/S3."""
        if self.client is None:
            logger.warning("MinIO client unavailable; skipping download")
            return None

        try:
            response = self.client.get_object(bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()

            return data

        except MinioException as e:
            logger.error(f"Error downloading {object_name}: {str(e)}")
            return None

    async def remove_object(self, bucket_name: str, object_name: str) -> bool:
        """Remove object from MinIO/S3."""
        if self.client is None:
            logger.warning("MinIO client unavailable; skipping remove_object")
            return False

        try:
            self.client.remove_object(bucket_name, object_name)
            logger.info(f"Removed {object_name} from {bucket_name}")
            return True

        except MinioException as e:
            logger.error(f"Error removing {object_name}: {str(e)}")
            return False

    async def list_objects(
        self, bucket_name: str, prefix: Optional[str] = None
    ) -> list:
        """List objects in bucket."""
        if self.client is None:
            logger.warning("MinIO client unavailable; skipping list_objects")
            return []

        try:
            objects = self.client.list_objects(
                bucket_name, prefix=prefix, recursive=True
            )

            return [
                {
                    "name": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified,
                    "etag": obj.etag,
                }
                for obj in objects
            ]

        except MinioException as e:
            logger.error(f"Error listing objects: {str(e)}")
            return []

    def get_presigned_url(
        self, bucket_name: str, object_name: str, expires_seconds: int = 3600
    ) -> Optional[str]:
        """Generate presigned URL for object access."""
        if self.client is None:
            logger.warning(
                "MinIO client unavailable; skipping presigned url generation"
            )
            return None

        try:
            url = self.client.presigned_get_object(
                bucket_name, object_name, expires=expires_seconds
            )
            return url

        except MinioException as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            return None
