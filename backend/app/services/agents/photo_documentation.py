"""Photo Documentation system for property site conditions."""

from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from backend._compat.datetime import utcnow

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

try:  # pragma: no cover - optional runtime dependency
    from PIL import Image
except ModuleNotFoundError:  # pragma: no cover
    Image = None  # type: ignore[assignment]

try:  # pragma: no cover - optional runtime dependency
    import exifread
except ModuleNotFoundError:  # pragma: no cover
    exifread = None  # type: ignore[assignment]

import structlog

from app.core.config import settings
from app.models.property import PropertyPhoto
from app.services.minio_service import MinIOService

logger = structlog.get_logger()


class PhotoMetadata:
    """Photo metadata and analysis results."""

    def __init__(
        self,
        photo_id: UUID,
        property_id: UUID,
        storage_key: str,
        location: Optional[Dict[str, float]] = None,
        capture_timestamp: Optional[datetime] = None,
        auto_tagged_conditions: Optional[List[str]] = None,
        camera_info: Optional[Dict[str, str]] = None,
        file_size: int = 0,
    ):
        self.photo_id = photo_id
        self.property_id = property_id
        self.storage_key = storage_key
        self.location = location
        self.capture_timestamp = capture_timestamp or utcnow()
        self.auto_tagged_conditions = auto_tagged_conditions or []
        self.camera_info = camera_info or {}
        self.file_size = file_size

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "photo_id": str(self.photo_id),
            "property_id": str(self.property_id),
            "storage_key": self.storage_key,
            "location": self.location,
            "capture_timestamp": self.capture_timestamp.isoformat(),
            "auto_tagged_conditions": self.auto_tagged_conditions,
            "camera_info": self.camera_info,
            "file_size": self.file_size,
            "public_url": f"{settings.S3_ENDPOINT}/{settings.S3_BUCKET}/{self.storage_key}",
        }


class PhotoDocumentationManager:
    """Manager for property photo documentation and analysis."""

    def __init__(self, storage_service: Optional[MinIOService] = None):
        self.storage = storage_service or self._create_storage_service()
        self.supported_formats = {".jpg", ".jpeg", ".png", ".heic", ".heif"}

    def _create_storage_service(self) -> MinIOService:
        """Create MinIO storage service instance."""
        return MinIOService(
            endpoint=settings.S3_ENDPOINT.replace("http://", "").replace(
                "https://", ""
            ),
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
            secure=settings.S3_ENDPOINT.startswith("https"),
        )

    async def process_photo(
        self,
        photo_data: bytes,
        property_id: str,
        filename: str,
        session: AsyncSession,
        user_metadata: Optional[Dict[str, str]] = None,
    ) -> PhotoMetadata:
        """
        Process and store a property photo.

        This will:
        1. Validate the photo format
        2. Extract EXIF data for location and timestamp
        3. Analyze image for site conditions
        4. Store photo in MinIO/S3
        5. Create database record
        6. Return photo metadata
        """
        try:
            photo_id = uuid4()

            # Validate photo format
            if not self._validate_photo_format(filename):
                raise ValueError(f"Unsupported photo format: {filename}")

            # Open image for processing
            if Image is None:
                raise RuntimeError("Pillow is required to process images")
            image = Image.open(BytesIO(photo_data))

            # Extract EXIF data
            exif_data = self._extract_exif_data(photo_data)
            gps_info = self._extract_gps_from_exif(exif_data)
            timestamp = self._extract_timestamp_from_exif(exif_data)
            camera_info = self._extract_camera_info_from_exif(exif_data)

            # Analyze image for conditions
            auto_tags = await self._analyze_site_conditions(image)

            # Generate optimized versions
            versions = await self._generate_image_versions(image, photo_id)

            # Store all versions in S3
            storage_key = await self._store_photo_versions(
                versions, property_id, photo_id
            )

            # Create database record
            await self._create_photo_record(
                photo_id=photo_id,
                property_id=UUID(property_id),
                storage_key=storage_key,
                filename=filename,
                file_size=len(photo_data),
                location=gps_info,
                capture_timestamp=timestamp,
                auto_tags=auto_tags,
                camera_info=camera_info,
                exif_data=exif_data,
                user_metadata=user_metadata,
                session=session,
            )

            await session.commit()

            # Return metadata
            return PhotoMetadata(
                photo_id=photo_id,
                property_id=UUID(property_id),
                storage_key=storage_key,
                location=gps_info,
                capture_timestamp=timestamp,
                auto_tagged_conditions=auto_tags,
                camera_info=camera_info,
                file_size=len(photo_data),
            )

        except Exception as e:
            logger.error(f"Error processing photo: {str(e)}")
            await session.rollback()
            raise

    def _validate_photo_format(self, filename: str) -> bool:
        """Validate photo file format."""
        import os

        ext = os.path.splitext(filename)[1].lower()
        return ext in self.supported_formats

    def _extract_exif_data(self, photo_data: bytes) -> Dict[str, Any]:
        """Extract EXIF data from photo."""
        if exifread is None:
            return {}

        try:
            tags = exifread.process_file(BytesIO(photo_data))

            # Convert EXIF tags to serializable format
            exif_dict = {}
            for tag, value in tags.items():
                # Skip thumbnail data
                if tag.startswith("Thumbnail"):
                    continue

                # Convert to string for JSON serialization
                exif_dict[tag] = str(value)

            return exif_dict

        except Exception as e:
            logger.warning(f"Could not extract EXIF data: {str(e)}")
            return {}

    def _extract_gps_from_exif(
        self, exif_data: Dict[str, Any]
    ) -> Optional[Dict[str, float]]:
        """Extract GPS coordinates from EXIF data."""
        try:
            gps_keys = {
                "GPS GPSLatitude": "latitude",
                "GPS GPSLongitude": "longitude",
                "GPS GPSLatitudeRef": "lat_ref",
                "GPS GPSLongitudeRef": "lon_ref",
            }

            gps_data = {}
            for exif_key, data_key in gps_keys.items():
                if exif_key in exif_data:
                    gps_data[data_key] = exif_data[exif_key]

            if "latitude" in gps_data and "longitude" in gps_data:
                # Convert GPS coordinates to decimal degrees
                lat = self._convert_gps_to_decimal(
                    gps_data["latitude"], gps_data.get("lat_ref", "N")
                )
                lon = self._convert_gps_to_decimal(
                    gps_data["longitude"], gps_data.get("lon_ref", "E")
                )

                if lat and lon:
                    return {"latitude": lat, "longitude": lon}

            return None

        except Exception as e:
            logger.warning(f"Could not extract GPS data: {str(e)}")
            return None

    def _convert_gps_to_decimal(self, coord_str: str, ref: str) -> Optional[float]:
        """Convert GPS coordinates from EXIF format to decimal degrees."""
        try:
            # Parse the coordinate string "[degrees, minutes, seconds]"
            parts = coord_str.strip("[]").split(", ")
            if len(parts) != 3:
                return None

            # Extract degrees, minutes, seconds
            degrees = float(eval(parts[0]))
            minutes = float(eval(parts[1]))
            seconds = float(eval(parts[2]))

            # Convert to decimal
            decimal = degrees + (minutes / 60) + (seconds / 3600)

            # Apply hemisphere
            if ref in ["S", "W"]:
                decimal = -decimal

            return decimal

        except Exception:
            return None

    def _extract_timestamp_from_exif(
        self, exif_data: Dict[str, Any]
    ) -> Optional[datetime]:
        """Extract capture timestamp from EXIF data."""
        try:
            # Try different timestamp fields
            timestamp_keys = [
                "EXIF DateTimeOriginal",
                "EXIF DateTimeDigitized",
                "Image DateTime",
            ]

            for key in timestamp_keys:
                if key in exif_data:
                    # Parse EXIF datetime format: "2023:10:15 14:30:45"
                    timestamp_str = str(exif_data[key])
                    return datetime.strptime(timestamp_str, "%Y:%m:%d %H:%M:%S")

            return None

        except Exception as e:
            logger.warning(f"Could not extract timestamp: {str(e)}")
            return None

    def _extract_camera_info_from_exif(
        self, exif_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Extract camera information from EXIF data."""
        camera_info = {}

        camera_keys = {
            "Image Make": "make",
            "Image Model": "model",
            "EXIF LensModel": "lens",
            "EXIF FocalLength": "focal_length",
            "EXIF FNumber": "aperture",
            "EXIF ISOSpeedRatings": "iso",
            "EXIF ExposureTime": "exposure",
        }

        for exif_key, info_key in camera_keys.items():
            if exif_key in exif_data:
                camera_info[info_key] = str(exif_data[exif_key])

        return camera_info

    async def _analyze_site_conditions(self, image: Image) -> List[str]:
        """Analyze image for site conditions using basic heuristics."""
        # This is a simplified version - in production, you would use
        # computer vision models or cloud AI services

        tags = []

        # Analyze image properties
        width, height = image.size

        # Check aspect ratio for different shot types
        aspect_ratio = width / height
        if aspect_ratio > 1.5:
            tags.append("wide_angle_shot")
        elif aspect_ratio < 0.7:
            tags.append("vertical_shot")

        # Analyze color distribution for basic conditions
        # Convert to RGB if necessary
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Get color statistics
        pixels = list(image.getdata())
        avg_brightness = sum(sum(pixel) for pixel in pixels) / (len(pixels) * 3)

        # Basic condition detection based on brightness
        if avg_brightness > 200:
            tags.append("bright_conditions")
            tags.append("possible_overexposed")
        elif avg_brightness < 50:
            tags.append("dark_conditions")
            tags.append("possible_underexposed")

        # Check for common construction/property features
        # In production, use ML models for these detections
        tags.extend(
            [
                "exterior_view",  # Default assumption
                "site_documentation",
                "property_condition",
            ]
        )

        return tags

    async def _generate_image_versions(
        self, image: Image, photo_id: UUID
    ) -> Dict[str, BytesIO]:
        """Generate multiple versions of the image."""
        versions = {}

        # Original
        original_buffer = BytesIO()
        image.save(original_buffer, format="JPEG", quality=95)
        original_buffer.seek(0)
        versions["original"] = original_buffer

        # Thumbnail (300x300)
        thumbnail = image.copy()
        thumbnail.thumbnail((300, 300), Image.Resampling.LANCZOS)
        thumb_buffer = BytesIO()
        thumbnail.save(thumb_buffer, format="JPEG", quality=85)
        thumb_buffer.seek(0)
        versions["thumbnail"] = thumb_buffer

        # Medium (1200x1200)
        medium = image.copy()
        medium.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
        medium_buffer = BytesIO()
        medium.save(medium_buffer, format="JPEG", quality=90)
        medium_buffer.seek(0)
        versions["medium"] = medium_buffer

        # Web optimized (1920x1920)
        web = image.copy()
        web.thumbnail((1920, 1920), Image.Resampling.LANCZOS)
        web_buffer = BytesIO()
        web.save(web_buffer, format="JPEG", quality=85, optimize=True)
        web_buffer.seek(0)
        versions["web"] = web_buffer

        return versions

    async def _store_photo_versions(
        self, versions: Dict[str, BytesIO], property_id: str, photo_id: UUID
    ) -> str:
        """Store photo versions in MinIO/S3."""
        base_key = f"agents/properties/{property_id}/photos/{photo_id}"

        # Store each version
        for version_name, buffer in versions.items():
            key = f"{base_key}/{version_name}.jpg"

            # Upload to S3
            await self.storage.upload_file(
                bucket_name=settings.S3_BUCKET,
                object_name=key,
                data=buffer.getvalue(),
                content_type="image/jpeg",
            )

            logger.info(f"Uploaded {version_name} version to {key}")

        # Return the base key (original is at base_key/original.jpg)
        return f"{base_key}/original.jpg"

    async def _create_photo_record(
        self,
        photo_id: UUID,
        property_id: UUID,
        storage_key: str,
        filename: str,
        file_size: int,
        location: Optional[Dict[str, float]],
        capture_timestamp: Optional[datetime],
        auto_tags: List[str],
        camera_info: Dict[str, str],
        exif_data: Dict[str, Any],
        user_metadata: Optional[Dict[str, str]],
        session: AsyncSession,
    ):
        """Create photo record in database."""

        # Create point geometry if location available
        capture_location = None
        if location:
            capture_location = f"POINT({location['longitude']} {location['latitude']})"

        photo_record = {
            "id": photo_id,
            "property_id": property_id,
            "storage_key": storage_key,
            "filename": filename,
            "mime_type": "image/jpeg",
            "file_size_bytes": file_size,
            "capture_date": capture_timestamp,
            "capture_location": capture_location,
            "auto_tags": auto_tags,
            "manual_tags": user_metadata.get("tags", []) if user_metadata else [],
            "site_conditions": {
                "detected": auto_tags,
                "user_notes": user_metadata.get("notes") if user_metadata else None,
            },
            "exif_data": exif_data,
            "camera_model": camera_info.get("model"),
        }

        stmt = insert(PropertyPhoto).values(**photo_record)
        await session.execute(stmt)

        logger.info(f"Created photo record: {photo_id} for property {property_id}")

    async def get_property_photos(
        self, property_id: str, session: AsyncSession, include_urls: bool = True
    ) -> List[Dict[str, Any]]:
        """Get all photos for a property."""
        from sqlalchemy import select

        stmt = (
            select(PropertyPhoto)
            .where(PropertyPhoto.property_id == UUID(property_id))
            .order_by(PropertyPhoto.capture_date.desc())
        )

        result = await session.execute(stmt)
        photos = result.scalars().all()

        photo_list = []
        for photo in photos:
            photo_dict = {
                "photo_id": str(photo.id),
                "storage_key": photo.storage_key,
                "filename": photo.filename,
                "capture_date": (
                    photo.capture_date.isoformat() if photo.capture_date else None
                ),
                "auto_tags": photo.auto_tags or [],
                "manual_tags": photo.manual_tags or [],
                "site_conditions": photo.site_conditions,
                "camera_model": photo.camera_model,
                "file_size": photo.file_size_bytes,
            }

            if include_urls:
                base_key = photo.storage_key.replace("/original.jpg", "")
                photo_dict["urls"] = {
                    "original": f"{settings.S3_ENDPOINT}/{settings.S3_BUCKET}/{photo.storage_key}",
                    "thumbnail": f"{settings.S3_ENDPOINT}/{settings.S3_BUCKET}/{base_key}/thumbnail.jpg",
                    "medium": f"{settings.S3_ENDPOINT}/{settings.S3_BUCKET}/{base_key}/medium.jpg",
                    "web": f"{settings.S3_ENDPOINT}/{settings.S3_BUCKET}/{base_key}/web.jpg",
                }

            if photo.capture_location:
                # Extract coordinates from geometry
                photo_dict["location"] = {
                    "latitude": photo.capture_location.y,
                    "longitude": photo.capture_location.x,
                }

            photo_list.append(photo_dict)

        return photo_list

    async def delete_photo(self, photo_id: str, session: AsyncSession) -> bool:
        """Delete a photo and its versions from storage."""
        from sqlalchemy import delete, select

        # Get photo record
        stmt = select(PropertyPhoto).where(PropertyPhoto.id == UUID(photo_id))
        result = await session.execute(stmt)
        photo = result.scalar_one_or_none()

        if not photo:
            return False

        # Delete from storage
        base_key = photo.storage_key.replace("/original.jpg", "")
        versions = ["original", "thumbnail", "medium", "web"]

        for version in versions:
            key = f"{base_key}/{version}.jpg"
            try:
                await self.storage.remove_object(settings.S3_BUCKET, key)
            except Exception as e:
                logger.warning(f"Could not delete {key}: {str(e)}")

        # Delete from database
        stmt = delete(PropertyPhoto).where(PropertyPhoto.id == UUID(photo_id))
        await session.execute(stmt)
        await session.commit()

        logger.info(f"Deleted photo {photo_id}")
        return True
