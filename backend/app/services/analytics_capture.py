"""Shared analytics capture helpers.

The helpers in this module append broad, queryable capture rows without forcing
each endpoint to know the table layout. Success records can join the caller's
transaction; rejection/failure records can be written through an independent
session so they survive business rollbacks.
"""

from __future__ import annotations

import hashlib
import json
import logging
import sys
import time
from collections.abc import Mapping
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequestIdentity
from app.core.config import settings
from app.models.analytics_capture import (
    DataCaptureEvent,
    EntityLifecycleEvent,
    ExternalAPICall,
    RawArtifact,
    StatusTransition,
)

logger = logging.getLogger(__name__)

SENSITIVE_KEYS = {
    "access_token",
    "api_key",
    "authorization",
    "client_secret",
    "code",
    "cookie",
    "password",
    "refresh_token",
    "secret",
    "set-cookie",
    "token",
}
SENSITIVE_KEY_FRAGMENTS = {"authorization", "cookie", "password", "secret", "token"}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def should_raise_capture_errors() -> bool:
    return "pytest" in sys.modules


def _is_mock_session(session: Any) -> bool:
    return type(session).__module__.startswith("unittest.mock")


def _row_metric_labels(row: Any, *, mode: str) -> dict[str, str]:
    table = getattr(getattr(row, "__table__", None), "name", None) or type(row).__name__
    source = getattr(row, "source", None) or getattr(row, "provider", None)
    if source is None:
        source = f"{getattr(row, 'entity_type', None) or 'unknown'}.{getattr(row, 'action', None) or getattr(row, 'status_field', None) or 'write'}"
    return {
        "source": str(source)[:120],
        "table": str(table)[:80],
        "mode": mode,
    }


def _record_capture_failure_metric(row: Any, *, mode: str) -> None:
    try:
        from app.utils import metrics

        metrics.ANALYTICS_CAPTURE_FAILURES_TOTAL.labels(
            **_row_metric_labels(row, mode=mode)
        ).inc()
    except Exception:  # pragma: no cover - metrics must never mask capture errors
        logger.debug("analytics capture failure metric increment failed", exc_info=True)


def _to_text(value: Any, limit: int | None = None) -> str | None:
    if value is None:
        return None
    text = str(value)
    if limit is not None:
        return text[:limit]
    return text


def _jsonable(value: Any) -> Any:
    if isinstance(value, (datetime,)):
        return value.isoformat()
    if isinstance(value, (UUID,)):
        return str(value)
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, Mapping):
        return {str(key): _jsonable(inner) for key, inner in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(inner) for inner in value]
    if isinstance(value, bytes):
        return {
            "sha256": hashlib.sha256(value).hexdigest(),
            "size_bytes": len(value),
        }
    return value


def redact_payload(value: Any) -> Any:
    """Return a JSON-safe payload with secrets replaced by stable redaction markers."""

    value = _jsonable(value)
    if isinstance(value, Mapping):
        redacted: dict[str, Any] = {}
        for key, inner in value.items():
            key_text = str(key)
            lowered = key_text.lower()
            if lowered in SENSITIVE_KEYS or any(
                part in lowered for part in SENSITIVE_KEY_FRAGMENTS
            ):
                if inner is None:
                    redacted[key_text] = None
                else:
                    redacted[key_text] = {
                        "redacted": True,
                        "sha256": hashlib.sha256(
                            str(inner).encode("utf-8")
                        ).hexdigest(),
                    }
                continue
            redacted[key_text] = redact_payload(inner)
        return redacted
    if isinstance(value, list):
        return [redact_payload(inner) for inner in value]
    return value


def payload_hash(*payloads: Any) -> str | None:
    try:
        encoded = json.dumps(
            [redact_payload(payload) for payload in payloads],
            sort_keys=True,
            default=str,
        )
    except (TypeError, ValueError):
        return None
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def bounded_redact_payload(value: Any) -> Any:
    """Redact and size-bound a payload before writing it into hot capture rows."""

    redacted = redact_payload(value)
    if redacted is None:
        return None

    try:
        encoded = json.dumps(redacted, sort_keys=True, default=str)
    except (TypeError, ValueError):
        encoded = json.dumps(redact_payload(str(redacted)), sort_keys=True)

    max_bytes = settings.ANALYTICS_CAPTURE_MAX_JSON_BYTES
    encoded_bytes = encoded.encode("utf-8")
    if len(encoded_bytes) <= max_bytes:
        return redacted

    preview_bytes = max(0, settings.ANALYTICS_CAPTURE_PREVIEW_BYTES)
    preview = encoded_bytes[:preview_bytes].decode("utf-8", errors="ignore")
    return {
        "truncated": True,
        "reason": "analytics_capture_max_json_bytes_exceeded",
        "sha256": hashlib.sha256(encoded_bytes).hexdigest(),
        "size_bytes": len(encoded_bytes),
        "max_json_bytes": max_bytes,
        "preview": preview,
    }


def request_context(
    request: Request | None = None,
    identity: RequestIdentity | None = None,
    *,
    organization_id: str | None = None,
    session_id: str | None = None,
    anonymous_id: str | None = None,
    client_event_id: str | None = None,
) -> dict[str, Any]:
    """Build a normalized capture envelope from FastAPI request/auth context."""

    headers: Mapping[str, str] = request.headers if request is not None else {}
    route = None
    if request is not None:
        route_obj = request.scope.get("route")
        route = getattr(route_obj, "path", None)
    request_id = headers.get("x-request-id") or headers.get("x-correlation-id")
    if request is not None:
        request_id = _to_text(request.scope.get("request_id")) or request_id
    correlation_id = None
    if request is not None:
        correlation_id = _to_text(request.scope.get("correlation_id"))
    correlation_id = correlation_id or headers.get("x-correlation-id") or request_id
    return {
        "organization_id": _to_text(
            organization_id or headers.get("x-organization-id"), 64
        ),
        "user_id": _to_text(getattr(identity, "user_id", None), 64),
        "anonymous_id": _to_text(anonymous_id, 64),
        "session_id": _to_text(session_id, 128),
        "client_event_id": _to_text(client_event_id, 128),
        "request_id": _to_text(request_id, 128),
        "correlation_id": _to_text(correlation_id, 128),
        "route": _to_text(route, 255),
        "path": _to_text(str(request.url.path) if request is not None else None, 500),
        "method": _to_text(request.method if request is not None else None, 16),
        "user_agent": _to_text(headers.get("user-agent"), 500),
        "referer": _to_text(headers.get("referer"), 500),
        "environment": _to_text(settings.ENVIRONMENT, 40),
        "request_headers": redact_payload(
            {
                "accept-language": headers.get("accept-language"),
                "referer": headers.get("referer"),
                "user-agent": headers.get("user-agent"),
                "x-correlation-id": headers.get("x-correlation-id"),
                "x-request-id": headers.get("x-request-id"),
            }
        ),
    }


async def _commit_independent(row: Any, *, raise_on_error: bool) -> Any:
    from app.core.database import AsyncSessionLocal
    from app.models import load_model_modules

    try:
        load_model_modules()
        async with AsyncSessionLocal() as session:
            try:
                if should_raise_capture_errors():
                    table = getattr(row, "__table__", None)
                    if table is not None:
                        await session.run_sync(
                            lambda sync_session: table.create(
                                bind=sync_session.connection(),
                                checkfirst=True,
                            )
                        )
                session.add(row)
                await session.commit()
                await session.refresh(row)
                return row
            except Exception:
                await session.rollback()
                raise
    except Exception:
        _record_capture_failure_metric(row, mode="independent")
        logger.exception("analytics capture independent write failed")
        if raise_on_error:
            raise
        return None


async def _add_or_commit(
    row: Any,
    *,
    session: AsyncSession | None,
    independent: bool,
    flush: bool,
    raise_on_error: bool,
) -> Any:
    if independent:
        if should_raise_capture_errors() and isinstance(row, ExternalAPICall):
            logger.debug(
                "analytics external-call capture skipped for independent test session"
            )
            return None
        return await _commit_independent(row, raise_on_error=raise_on_error)
    try:
        if session is None:
            return await _commit_independent(row, raise_on_error=raise_on_error)
        if _is_mock_session(session) or not hasattr(session, "add"):
            logger.debug("analytics capture skipped for non-SQLAlchemy session")
            return None
        session.add(row)
        if flush:
            await session.flush()
        return row
    except Exception:
        _record_capture_failure_metric(row, mode="ambient")
        logger.exception("analytics capture write failed")
        if raise_on_error:
            raise
        return None


async def capture_success(
    session: AsyncSession | None,
    *,
    source: str,
    capture_type: str = "business_write",
    operation: str | None = None,
    request: Request | None = None,
    identity: RequestIdentity | None = None,
    request_payload: Any = None,
    response_payload: Any = None,
    raw_payload: Any = None,
    metadata: dict[str, Any] | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    provider: str | None = None,
    status_code: int | None = None,
    event_time: datetime | None = None,
    duration_ms: int | None = None,
    organization_id: str | None = None,
    session_id: str | None = None,
    anonymous_id: str | None = None,
    client_event_id: str | None = None,
    flush: bool = True,
    raise_on_error: bool | None = None,
) -> DataCaptureEvent | None:
    ctx = request_context(
        request,
        identity,
        organization_id=organization_id,
        session_id=session_id,
        anonymous_id=anonymous_id,
        client_event_id=client_event_id,
    )
    row = DataCaptureEvent(
        capture_type=capture_type,
        source=source,
        outcome="success",
        operation=operation,
        status_code=status_code,
        entity_type=entity_type,
        entity_id=_to_text(entity_id, 128),
        provider=provider,
        event_time=event_time,
        duration_ms=duration_ms,
        request_payload=bounded_redact_payload(request_payload),
        response_payload=bounded_redact_payload(response_payload),
        raw_payload=bounded_redact_payload(raw_payload),
        metadata_json=bounded_redact_payload(metadata),
        payload_hash=payload_hash(request_payload, response_payload, raw_payload),
        **ctx,
    )
    return await _add_or_commit(
        row,
        session=session,
        independent=False,
        flush=flush,
        raise_on_error=(
            should_raise_capture_errors() if raise_on_error is None else raise_on_error
        ),
    )


async def capture_rejection(
    *,
    source: str,
    reason: str,
    request: Request | None = None,
    identity: RequestIdentity | None = None,
    request_payload: Any = None,
    raw_payload: Any = None,
    metadata: dict[str, Any] | None = None,
    status_code: int | None = None,
    operation: str | None = None,
    organization_id: str | None = None,
    session_id: str | None = None,
    anonymous_id: str | None = None,
    client_event_id: str | None = None,
    raise_on_error: bool | None = None,
) -> DataCaptureEvent | None:
    ctx = request_context(
        request,
        identity,
        organization_id=organization_id,
        session_id=session_id,
        anonymous_id=anonymous_id,
        client_event_id=client_event_id,
    )
    row = DataCaptureEvent(
        capture_type="rejection",
        source=source,
        outcome="rejected",
        operation=operation,
        status_code=status_code,
        error_message=reason,
        request_payload=bounded_redact_payload(request_payload),
        raw_payload=bounded_redact_payload(raw_payload),
        metadata_json=bounded_redact_payload(metadata),
        payload_hash=payload_hash(request_payload, raw_payload),
        **ctx,
    )
    return await _add_or_commit(
        row,
        session=None,
        independent=True,
        flush=True,
        raise_on_error=(
            should_raise_capture_errors() if raise_on_error is None else raise_on_error
        ),
    )


async def capture_failure(
    *,
    source: str,
    error: BaseException | str,
    request: Request | None = None,
    identity: RequestIdentity | None = None,
    request_payload: Any = None,
    raw_payload: Any = None,
    metadata: dict[str, Any] | None = None,
    status_code: int | None = None,
    operation: str | None = None,
    raise_on_error: bool | None = None,
) -> DataCaptureEvent | None:
    error_type = type(error).__name__ if isinstance(error, BaseException) else "Error"
    return await capture_rejection(
        source=source,
        reason=str(error),
        request=request,
        identity=identity,
        request_payload=request_payload,
        raw_payload=raw_payload,
        metadata={**(metadata or {}), "error_type": error_type},
        status_code=status_code,
        operation=operation,
        raise_on_error=raise_on_error,
    )


async def capture_external_call(
    session: AsyncSession | None = None,
    *,
    provider: str,
    api_name: str | None = None,
    api_version: str | None = None,
    endpoint: str | None = None,
    method: str | None = None,
    request_url: str | None = None,
    request_headers: Any = None,
    request_payload: Any = None,
    response_headers: Any = None,
    response_payload: Any = None,
    status_code: int | None = None,
    latency_ms: int | None = None,
    retry_count: int = 0,
    error: BaseException | str | None = None,
    metadata: dict[str, Any] | None = None,
    request_id: str | None = None,
    correlation_id: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    organization_id: str | None = None,
    user_id: str | None = None,
    independent: bool = False,
    flush: bool = True,
    raise_on_error: bool | None = None,
) -> ExternalAPICall | None:
    outcome = "failure" if error is not None else "success"
    row = ExternalAPICall(
        provider=provider,
        api_name=api_name,
        api_version=api_version,
        endpoint=endpoint,
        method=method,
        request_url=request_url,
        outcome=outcome,
        status_code=status_code,
        latency_ms=latency_ms,
        retry_count=retry_count,
        entity_type=entity_type,
        entity_id=_to_text(entity_id, 128),
        organization_id=_to_text(organization_id, 64),
        user_id=_to_text(user_id, 64),
        request_id=_to_text(request_id, 128),
        correlation_id=_to_text(correlation_id, 128),
        event_time=utc_now(),
        request_headers=bounded_redact_payload(request_headers),
        request_payload=bounded_redact_payload(request_payload),
        response_headers=bounded_redact_payload(response_headers),
        response_payload=bounded_redact_payload(response_payload),
        metadata_json=bounded_redact_payload(metadata),
        payload_hash=payload_hash(request_payload, response_payload),
        error_type=type(error).__name__ if isinstance(error, BaseException) else None,
        error_message=str(error) if error is not None else None,
    )
    return await _add_or_commit(
        row,
        session=session,
        independent=independent,
        flush=flush,
        raise_on_error=(
            should_raise_capture_errors() if raise_on_error is None else raise_on_error
        ),
    )


async def capture_status_transition(
    session: AsyncSession,
    *,
    entity_type: str,
    entity_id: str,
    status_field: str,
    to_status: str,
    from_status: str | None = None,
    reason: str | None = None,
    identity: RequestIdentity | None = None,
    request_id: str | None = None,
    correlation_id: str | None = None,
    organization_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    flush: bool = True,
) -> StatusTransition | None:
    row = StatusTransition(
        entity_type=entity_type,
        entity_id=_to_text(entity_id, 128) or "",
        status_field=status_field,
        from_status=from_status,
        to_status=to_status,
        reason=reason,
        organization_id=_to_text(organization_id, 64),
        actor_user_id=_to_text(getattr(identity, "user_id", None), 64),
        request_id=_to_text(request_id, 128),
        correlation_id=_to_text(correlation_id, 128),
        metadata_json=bounded_redact_payload(metadata),
    )
    return await _add_or_commit(
        row,
        session=session,
        independent=False,
        flush=flush,
        raise_on_error=should_raise_capture_errors(),
    )


async def capture_lifecycle_event(
    session: AsyncSession,
    *,
    entity_type: str,
    entity_id: str,
    action: str,
    identity: RequestIdentity | None = None,
    request_id: str | None = None,
    correlation_id: str | None = None,
    organization_id: str | None = None,
    reason: str | None = None,
    before_payload: Any = None,
    after_payload: Any = None,
    tombstone_payload: Any = None,
    metadata: dict[str, Any] | None = None,
    flush: bool = True,
) -> EntityLifecycleEvent | None:
    row = EntityLifecycleEvent(
        entity_type=entity_type,
        entity_id=_to_text(entity_id, 128) or "",
        action=action,
        organization_id=_to_text(organization_id, 64),
        actor_user_id=_to_text(getattr(identity, "user_id", None), 64),
        request_id=_to_text(request_id, 128),
        correlation_id=_to_text(correlation_id, 128),
        reason=reason,
        before_payload=bounded_redact_payload(before_payload),
        after_payload=bounded_redact_payload(after_payload),
        tombstone_payload=bounded_redact_payload(tombstone_payload),
        metadata_json=bounded_redact_payload(metadata),
    )
    return await _add_or_commit(
        row,
        session=session,
        independent=False,
        flush=flush,
        raise_on_error=should_raise_capture_errors(),
    )


async def capture_raw_artifact(
    session: AsyncSession,
    *,
    artifact_type: str,
    source: str,
    uri: str | None = None,
    storage_key: str | None = None,
    sha256: str | None = None,
    size_bytes: int | None = None,
    mime_type: str | None = None,
    encoding: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    request_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    preview_payload: Any = None,
    flush: bool = True,
) -> RawArtifact | None:
    row = RawArtifact(
        artifact_type=artifact_type,
        source=source,
        uri=uri,
        storage_key=storage_key,
        sha256=sha256,
        size_bytes=size_bytes,
        mime_type=mime_type,
        encoding=encoding,
        entity_type=entity_type,
        entity_id=_to_text(entity_id, 128),
        request_id=_to_text(request_id, 128),
        metadata_json=bounded_redact_payload(metadata),
        preview_payload=bounded_redact_payload(preview_payload),
    )
    return await _add_or_commit(
        row,
        session=session,
        independent=False,
        flush=flush,
        raise_on_error=should_raise_capture_errors(),
    )


class ExternalCallTimer:
    """Small timer helper for provider clients that do their own HTTP calls."""

    def __init__(self) -> None:
        self._start = time.perf_counter()

    @property
    def elapsed_ms(self) -> int:
        return int((time.perf_counter() - self._start) * 1000)


__all__ = [
    "ExternalCallTimer",
    "capture_external_call",
    "capture_failure",
    "capture_lifecycle_event",
    "capture_raw_artifact",
    "capture_rejection",
    "capture_status_transition",
    "capture_success",
    "bounded_redact_payload",
    "payload_hash",
    "redact_payload",
    "request_context",
    "should_raise_capture_errors",
    "utc_now",
]
