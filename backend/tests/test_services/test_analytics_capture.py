from __future__ import annotations

import pytest
from sqlalchemy import func, select

from app.models.analytics_capture import DataCaptureEvent
from app.core.config import settings
from app.services.analytics_capture import (
    bounded_redact_payload,
    capture_rejection,
    capture_success,
    redact_payload,
)


def test_redact_payload_hashes_sensitive_values() -> None:
    redacted = redact_payload(
        {
            "authorization": "Bearer secret-token",
            "nested": {"refresh_token": "refresh", "postal_code": "123456"},
        }
    )

    assert redacted["authorization"]["redacted"] is True
    assert redacted["nested"]["refresh_token"]["redacted"] is True
    assert redacted["nested"]["postal_code"] == "123456"


def test_bounded_redact_payload_keeps_hash_when_truncated(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ANALYTICS_CAPTURE_MAX_JSON_BYTES", 64)
    monkeypatch.setattr(settings, "ANALYTICS_CAPTURE_PREVIEW_BYTES", 12)

    payload = bounded_redact_payload({"blob": "x" * 500, "api_key": "secret"})

    assert payload["truncated"] is True
    assert payload["size_bytes"] > 64
    assert payload["sha256"]
    assert len(payload["preview"].encode("utf-8")) <= 12


@pytest.mark.asyncio
async def test_capture_success_and_rejection_are_queryable(
    async_session_factory,
) -> None:
    async with async_session_factory() as session:
        await capture_success(
            session,
            source="test.capture",
            capture_type="unit_test",
            operation="success",
            request_payload={"safe": "value", "access_token": "secret"},
            entity_type="test_entity",
            entity_id="entity-1",
        )
        await session.commit()

    await capture_rejection(
        source="test.capture",
        reason="rejected for test",
        request_payload={"password": "secret"},
        operation="reject",
    )

    async with async_session_factory() as session:
        count = await session.scalar(
            select(func.count())
            .select_from(DataCaptureEvent)
            .where(DataCaptureEvent.source == "test.capture")
        )
        rejected = (
            (
                await session.execute(
                    select(DataCaptureEvent).where(
                        DataCaptureEvent.outcome == "rejected"
                    )
                )
            )
            .scalars()
            .first()
        )

    assert count == 2
    assert rejected is not None
    assert rejected.request_payload["password"]["redacted"] is True
