"""MinIO/S3 storage service wrapper."""

import io
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

    async def upload_file(
        self,
        bucket_name: str,
        object_name: str,
        data: Union[bytes, BinaryIO],
        content_type: str = "application/octet-stream",
        metadata: Optional[dict] = None,
    ) -> bool:
        """Upload file to MinIO/S3."""
        if self.client is None:
            logger.warning("MinIO client unavailable; skipping upload")
            return False

        try:
            # Convert bytes to BytesIO if needed
            if isinstance(data, bytes):
                data = io.BytesIO(data)

            # Get size
            data.seek(0, 2)  # Seek to end
            size = data.tell()
            data.seek(0)  # Reset to beginning

            # Upload
            self.client.put_object(
                bucket_name,
                object_name,
                data,
                size,
                content_type=content_type,
                metadata=metadata,
            )

            logger.info(f"Uploaded {object_name} to {bucket_name}")
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
