"""Behavioral event ingestion endpoints (PR1).

Two routes:

* ``POST /events/batch`` — accept up to 200 events in one round-trip. Client
  generates ``client_event_id`` so duplicate flushes are detectable.
* ``POST /events/search`` — log a search query plus optional click-through.

Both endpoints are intentionally permissive on the role guard: anonymous
viewers still emit events. PII (raw IP, email) is hashed before persistence —
plaintext never reaches the storage tier.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequestIdentity, get_db, get_identity
from app.models.events import SearchQuery, UserEvent

router = APIRouter(prefix="/events", tags=["telemetry"])

MAX_BATCH = 200
PAYLOAD_MAX_BYTES = 16 * 1024


def _hash_ip(ip: str | None) -> str | None:
    if not ip:
        return None
    return hashlib.sha256(ip.encode("utf-8")).hexdigest()


def _truncate(value: str | None, limit: int) -> str | None:
    if value is None:
        return None
    return value[:limit]


class EventIn(BaseModel):
    event_type: str = Field(min_length=1, max_length=40)
    event_name: str = Field(min_length=1, max_length=120)
    target_type: str | None = Field(default=None, max_length=80)
    target_id: str | None = Field(default=None, max_length=64)
    payload: dict[str, Any] | None = None
    path: str | None = Field(default=None, max_length=255)
    referrer: str | None = Field(default=None, max_length=255)
    anonymous_id: str | None = Field(default=None, max_length=64)
    session_id: str | None = Field(default=None, max_length=64)
    client_event_id: str | None = Field(default=None, max_length=64)
    occurred_at: datetime


class EventBatchIn(BaseModel):
    events: list[EventIn]


class EventBatchResult(BaseModel):
    accepted: int


class SearchIn(BaseModel):
    query_text: str = Field(min_length=1, max_length=500)
    query_type: str | None = Field(default=None, max_length=40)
    filters: dict[str, Any] | None = None
    result_count: int | None = None
    latency_ms: int | None = None
    top_results: list[dict[str, Any]] | None = None
    anonymous_id: str | None = Field(default=None, max_length=64)
    session_id: str | None = Field(default=None, max_length=64)
    clicked_rank: int | None = None
    clicked_entity_type: str | None = Field(default=None, max_length=80)
    clicked_entity_id: str | None = Field(default=None, max_length=64)
    clicked_at: datetime | None = None


class SearchResult(BaseModel):
    id: int


def _resolve_user_id(identity: RequestIdentity) -> str | None:
    return identity.user_id


@router.post(
    "/batch",
    response_model=EventBatchResult,
    status_code=status.HTTP_202_ACCEPTED,
)
async def ingest_event_batch(
    body: EventBatchIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
    identity: RequestIdentity = Depends(get_identity),
) -> EventBatchResult:
    """Persist a batch of behavioral events."""

    if not body.events:
        return EventBatchResult(accepted=0)
    if len(body.events) > MAX_BATCH:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Batch exceeds maximum of {MAX_BATCH} events",
        )

    client_host = request.client.host if request.client else None
    user_agent = _truncate(request.headers.get("user-agent"), 255)
    ip_hash = _hash_ip(client_host)
    user_id = _resolve_user_id(identity)

    rows: list[UserEvent] = []
    for event in body.events:
        payload = event.payload
        if payload is not None:
            # Cheap guard against runaway payloads — bigger blobs belong on
            # a dedicated entity, not the high-volume event log.
            import json

            if len(json.dumps(payload, default=str)) > PAYLOAD_MAX_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="Event payload exceeds 16KB",
                )
        rows.append(
            UserEvent(
                user_id=user_id,
                anonymous_id=event.anonymous_id,
                session_id=event.session_id,
                event_type=event.event_type,
                event_name=event.event_name,
                target_type=event.target_type,
                target_id=event.target_id,
                payload=payload,
                path=event.path,
                referrer=event.referrer,
                user_agent=user_agent,
                ip_hash=ip_hash,
                client_event_id=event.client_event_id,
                occurred_at=event.occurred_at,
            )
        )

    db.add_all(rows)
    await db.commit()
    return EventBatchResult(accepted=len(rows))


@router.post(
    "/search",
    response_model=SearchResult,
    status_code=status.HTTP_201_CREATED,
)
async def log_search_query(
    body: SearchIn,
    db: AsyncSession = Depends(get_db),
    identity: RequestIdentity = Depends(get_identity),
) -> SearchResult:
    """Persist a single search query + optional click-through."""

    user_id = _resolve_user_id(identity)
    row = SearchQuery(
        user_id=user_id,
        anonymous_id=body.anonymous_id,
        session_id=body.session_id,
        query_text=body.query_text,
        query_type=body.query_type,
        filters=body.filters,
        result_count=body.result_count,
        latency_ms=body.latency_ms,
        top_results=body.top_results,
        clicked_rank=body.clicked_rank,
        clicked_entity_type=body.clicked_entity_type,
        clicked_entity_id=body.clicked_entity_id,
        clicked_at=body.clicked_at,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return SearchResult(id=row.id)


__all__ = ["router"]
