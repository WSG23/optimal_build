from __future__ import annotations

from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select

from app.models.analytics_capture import DataCaptureEvent
from app.models.events import UserEvent


@pytest.mark.asyncio
async def test_event_batch_writes_business_and_capture_rows(
    app_client: AsyncClient, async_session_factory
) -> None:
    async with async_session_factory() as session:
        before_events = await session.scalar(
            select(func.count()).select_from(UserEvent)
        )
        before_capture = await session.scalar(
            select(func.count()).select_from(DataCaptureEvent)
        )

    payload = {
        "events": [
            {
                "event_type": "click",
                "event_name": "analytics_test",
                "payload": {"button": "save"},
                "path": "/analytics-test",
                "anonymous_id": "anon-test",
                "session_id": "session-test",
                "client_event_id": "client-test",
                "occurred_at": datetime.now(timezone.utc).isoformat(),
            }
        ]
    }
    response = await app_client.post(
        "/api/v1/events/batch",
        json=payload,
        headers={"X-Request-ID": "capture-test-request"},
    )

    assert response.status_code == 202, response.text

    async with async_session_factory() as session:
        after_events = await session.scalar(select(func.count()).select_from(UserEvent))
        after_capture = await session.scalar(
            select(func.count()).select_from(DataCaptureEvent)
        )
        capture = (
            (
                await session.execute(
                    select(DataCaptureEvent).where(
                        DataCaptureEvent.source == "telemetry.events.batch",
                        DataCaptureEvent.request_id == "capture-test-request",
                    )
                )
            )
            .scalars()
            .first()
        )

    assert after_events == before_events + 1
    assert after_capture == before_capture + 1
    assert capture is not None
    assert capture.outcome == "success"
    assert capture.session_id == "session-test"


@pytest.mark.asyncio
async def test_event_batch_rejection_is_persisted_without_business_row(
    app_client: AsyncClient, async_session_factory
) -> None:
    async with async_session_factory() as session:
        before_events = await session.scalar(
            select(func.count()).select_from(UserEvent)
        )
        before_rejections = await session.scalar(
            select(func.count())
            .select_from(DataCaptureEvent)
            .where(DataCaptureEvent.outcome == "rejected")
        )

    oversized_payload = {"blob": "x" * (17 * 1024)}
    response = await app_client.post(
        "/api/v1/events/batch",
        json={
            "events": [
                {
                    "event_type": "click",
                    "event_name": "oversized",
                    "payload": oversized_payload,
                    "occurred_at": datetime.now(timezone.utc).isoformat(),
                }
            ]
        },
        headers={"X-Request-ID": "capture-reject-request"},
    )

    assert response.status_code == 413

    async with async_session_factory() as session:
        after_events = await session.scalar(select(func.count()).select_from(UserEvent))
        after_rejections = await session.scalar(
            select(func.count())
            .select_from(DataCaptureEvent)
            .where(DataCaptureEvent.outcome == "rejected")
        )

    assert after_events == before_events
    assert after_rejections == before_rejections + 1
