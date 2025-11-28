"""Voice Note Service for site documentation audio recordings."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import structlog
from sqlalchemy import delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend._compat.datetime import utcnow

from app.core.config import settings
from app.models.property import VoiceNote
from app.services.minio_service import MinIOService

logger = structlog.get_logger()


class VoiceNoteMetadata:
    """Voice note metadata and processing results."""

    def __init__(
        self,
        voice_note_id: UUID,
        property_id: UUID,
        storage_key: str,
        location: Optional[Dict[str, float]] = None,
        capture_timestamp: Optional[datetime] = None,
        duration_seconds: Optional[float] = None,
        file_size: int = 0,
        title: Optional[str] = None,
        photo_id: Optional[UUID] = None,
    ):
        self.voice_note_id = voice_note_id
        self.property_id = property_id
        self.storage_key = storage_key
        self.location = location
        self.capture_timestamp = capture_timestamp or utcnow()
        self.duration_seconds = duration_seconds
        self.file_size = file_size
        self.title = title
        self.photo_id = photo_id

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "voice_note_id": str(self.voice_note_id),
            "property_id": str(self.property_id),
            "storage_key": self.storage_key,
            "location": self.location,
            "capture_timestamp": self.capture_timestamp.isoformat(),
            "duration_seconds": self.duration_seconds,
            "file_size": self.file_size,
            "title": self.title,
            "photo_id": str(self.photo_id) if self.photo_id else None,
            "public_url": f"{settings.S3_ENDPOINT}/{settings.S3_BUCKET}/{self.storage_key}",
        }


class VoiceNoteService:
    """Service for managing property voice note recordings."""

    SUPPORTED_FORMATS = {
        "audio/webm",
        "audio/mp3",
        "audio/mpeg",
        "audio/wav",
        "audio/ogg",
        "audio/m4a",
        "audio/mp4",
    }

    def __init__(self, storage_service: Optional[MinIOService] = None):
        self.storage = storage_service or self._create_storage_service()

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

    def _validate_audio_format(self, mime_type: str) -> bool:
        """Validate audio file format."""
        return mime_type.lower() in self.SUPPORTED_FORMATS

    async def process_voice_note(
        self,
        audio_data: bytes,
        property_id: str,
        filename: str,
        mime_type: str,
        session: AsyncSession,
        duration_seconds: Optional[float] = None,
        location: Optional[Dict[str, float]] = None,
        title: Optional[str] = None,
        tags: Optional[List[str]] = None,
        photo_id: Optional[str] = None,
        audio_metadata: Optional[Dict[str, Any]] = None,
    ) -> VoiceNoteMetadata:
        """
        Process and store a voice note recording.

        Args:
            audio_data: Raw audio bytes
            property_id: UUID of the property
            filename: Original filename
            mime_type: Audio MIME type
            session: Database session
            duration_seconds: Duration of the recording
            location: GPS coordinates {latitude, longitude}
            title: Optional title for the note
            tags: Optional list of tags
            photo_id: Optional associated photo ID
            audio_metadata: Optional metadata from browser/device

        Returns:
            VoiceNoteMetadata with storage details
        """
        try:
            voice_note_id = uuid4()

            # Validate audio format
            if not self._validate_audio_format(mime_type):
                raise ValueError(f"Unsupported audio format: {mime_type}")

            # Generate storage key
            storage_key = await self._store_audio(
                audio_data, property_id, voice_note_id, filename
            )

            # Create database record
            await self._create_voice_note_record(
                voice_note_id=voice_note_id,
                property_id=UUID(property_id),
                photo_id=UUID(photo_id) if photo_id else None,
                storage_key=storage_key,
                filename=filename,
                mime_type=mime_type,
                file_size=len(audio_data),
                duration_seconds=duration_seconds,
                location=location,
                title=title,
                tags=tags,
                audio_metadata=audio_metadata,
                session=session,
            )

            await session.commit()

            return VoiceNoteMetadata(
                voice_note_id=voice_note_id,
                property_id=UUID(property_id),
                storage_key=storage_key,
                location=location,
                capture_timestamp=utcnow(),
                duration_seconds=duration_seconds,
                file_size=len(audio_data),
                title=title,
                photo_id=UUID(photo_id) if photo_id else None,
            )

        except Exception as e:
            logger.error(f"Error processing voice note: {str(e)}")
            await session.rollback()
            raise

    async def _store_audio(
        self,
        audio_data: bytes,
        property_id: str,
        voice_note_id: UUID,
        filename: str,
    ) -> str:
        """Store audio file in MinIO/S3."""
        # Determine file extension from filename
        ext = filename.rsplit(".", 1)[-1] if "." in filename else "webm"
        storage_key = (
            f"agents/properties/{property_id}/voice_notes/{voice_note_id}.{ext}"
        )

        # Upload to S3
        await self.storage.upload_file(
            bucket_name=settings.S3_BUCKET,
            object_name=storage_key,
            data=audio_data,
            content_type=f"audio/{ext}",
        )

        logger.info(f"Uploaded voice note to {storage_key}")
        return storage_key

    async def _create_voice_note_record(
        self,
        voice_note_id: UUID,
        property_id: UUID,
        photo_id: Optional[UUID],
        storage_key: str,
        filename: str,
        mime_type: str,
        file_size: int,
        duration_seconds: Optional[float],
        location: Optional[Dict[str, float]],
        title: Optional[str],
        tags: Optional[List[str]],
        audio_metadata: Optional[Dict[str, Any]],
        session: AsyncSession,
    ) -> None:
        """Create voice note record in database."""
        # Create point geometry if location available
        capture_location = None
        if location:
            capture_location = f"POINT({location['longitude']} {location['latitude']})"

        voice_note_record = {
            "id": voice_note_id,
            "property_id": property_id,
            "photo_id": photo_id,
            "storage_key": storage_key,
            "filename": filename,
            "mime_type": mime_type,
            "file_size_bytes": file_size,
            "duration_seconds": duration_seconds,
            "capture_date": utcnow(),
            "capture_location": capture_location,
            "title": title,
            "tags": tags or [],
            "audio_metadata": audio_metadata,
        }

        stmt = insert(VoiceNote).values(**voice_note_record)
        await session.execute(stmt)

        logger.info(
            f"Created voice note record: {voice_note_id} for property {property_id}"
        )

    async def get_property_voice_notes(
        self,
        property_id: str,
        session: AsyncSession,
        include_urls: bool = True,
    ) -> List[Dict[str, Any]]:
        """Get all voice notes for a property."""
        stmt = (
            select(VoiceNote)
            .where(VoiceNote.property_id == UUID(property_id))
            .order_by(VoiceNote.capture_date.desc())
        )

        result = await session.execute(stmt)
        voice_notes = result.scalars().all()

        note_list = []
        for note in voice_notes:
            note_dict = {
                "voice_note_id": str(note.id),
                "property_id": str(note.property_id),
                "photo_id": str(note.photo_id) if note.photo_id else None,
                "storage_key": note.storage_key,
                "filename": note.filename,
                "mime_type": note.mime_type,
                "file_size": note.file_size_bytes,
                "duration_seconds": (
                    float(note.duration_seconds) if note.duration_seconds else None
                ),
                "capture_date": (
                    note.capture_date.isoformat() if note.capture_date else None
                ),
                "title": note.title,
                "tags": note.tags or [],
                "transcript": note.transcript,
                "audio_metadata": note.audio_metadata,
            }

            if include_urls:
                note_dict["public_url"] = (
                    f"{settings.S3_ENDPOINT}/{settings.S3_BUCKET}/{note.storage_key}"
                )

            if note.capture_location:
                # Extract coordinates from geometry (stored as WKT)
                note_dict["location"] = {
                    "latitude": (
                        note.capture_location.y
                        if hasattr(note.capture_location, "y")
                        else None
                    ),
                    "longitude": (
                        note.capture_location.x
                        if hasattr(note.capture_location, "x")
                        else None
                    ),
                }

            note_list.append(note_dict)

        return note_list

    async def get_voice_note(
        self,
        voice_note_id: str,
        session: AsyncSession,
    ) -> Optional[Dict[str, Any]]:
        """Get a single voice note by ID."""
        stmt = select(VoiceNote).where(VoiceNote.id == UUID(voice_note_id))
        result = await session.execute(stmt)
        note = result.scalar_one_or_none()

        if not note:
            return None

        return {
            "voice_note_id": str(note.id),
            "property_id": str(note.property_id),
            "photo_id": str(note.photo_id) if note.photo_id else None,
            "storage_key": note.storage_key,
            "filename": note.filename,
            "mime_type": note.mime_type,
            "file_size": note.file_size_bytes,
            "duration_seconds": (
                float(note.duration_seconds) if note.duration_seconds else None
            ),
            "capture_date": (
                note.capture_date.isoformat() if note.capture_date else None
            ),
            "title": note.title,
            "tags": note.tags or [],
            "transcript": note.transcript,
            "audio_metadata": note.audio_metadata,
            "public_url": f"{settings.S3_ENDPOINT}/{settings.S3_BUCKET}/{note.storage_key}",
        }

    async def delete_voice_note(
        self,
        voice_note_id: str,
        session: AsyncSession,
    ) -> bool:
        """Delete a voice note and its audio file from storage."""
        # Get voice note record
        stmt = select(VoiceNote).where(VoiceNote.id == UUID(voice_note_id))
        result = await session.execute(stmt)
        note = result.scalar_one_or_none()

        if not note:
            return False

        # Delete from storage
        try:
            await self.storage.remove_object(settings.S3_BUCKET, note.storage_key)
        except Exception as e:
            logger.warning(f"Could not delete {note.storage_key}: {str(e)}")

        # Delete from database
        stmt = delete(VoiceNote).where(VoiceNote.id == UUID(voice_note_id))
        await session.execute(stmt)
        await session.commit()

        logger.info(f"Deleted voice note {voice_note_id}")
        return True

    async def update_voice_note(
        self,
        voice_note_id: str,
        session: AsyncSession,
        title: Optional[str] = None,
        tags: Optional[List[str]] = None,
        transcript: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update voice note metadata."""
        stmt = select(VoiceNote).where(VoiceNote.id == UUID(voice_note_id))
        result = await session.execute(stmt)
        note = result.scalar_one_or_none()

        if not note:
            return None

        # Update fields if provided
        if title is not None:
            note.title = title
        if tags is not None:
            note.tags = tags
        if transcript is not None:
            note.transcript = transcript

        await session.commit()
        await session.refresh(note)

        return await self.get_voice_note(voice_note_id, session)
