from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.models.property import Property, PropertyStatus, PropertyType, VoiceNote
from app.services.agents.voice_note_service import VoiceNoteService


@pytest.mark.asyncio
async def test_delete_voice_note_soft_deletes_and_hides_from_queries(
    db_session,
) -> None:
    property_id = uuid4()
    note_id = uuid4()
    db_session.add(
        Property(
            id=property_id,
            name="Voice Note Property",
            address="1 Audio Way",
            property_type=PropertyType.OFFICE,
            status=PropertyStatus.EXISTING,
            location="POINT(103.8547 1.2789)",
            data_source="test",
        )
    )
    note = VoiceNote(
        id=note_id,
        property_id=property_id,
        storage_key=f"voice/{property_id}/{note_id}.webm",
        filename="note.webm",
        mime_type="audio/webm",
        capture_date=datetime.now(timezone.utc),
    )
    db_session.add(note)
    await db_session.commit()

    storage = AsyncMock()
    service = VoiceNoteService(storage_service=storage)

    result = await service.delete_voice_note(str(note_id), db_session)
    await db_session.refresh(note)
    visible_notes = await service.get_property_voice_notes(str(property_id), db_session)

    assert result is True
    assert note.deleted_at is not None
    assert visible_notes == []
    storage.remove_object.assert_awaited_once()
