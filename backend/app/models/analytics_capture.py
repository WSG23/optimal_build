"""Append-only analytics capture models.

These tables are deliberately broad and source-agnostic. Operational tables keep
serving product workflows; capture tables preserve raw/provenance data so later
analytics and model-training questions can be answered without re-running the
original request or external API call.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import UUID, BaseModel
from app.models.types import FlexibleJSONB


class DataCaptureEvent(BaseModel):
    """Generic append-only event for request, ingestion, computation, and failure capture."""

    __tablename__ = "data_capture_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(), default=uuid.uuid4, nullable=False, unique=True
    )

    capture_type: Mapped[str] = mapped_column(String(40), nullable=False)
    source: Mapped[str] = mapped_column(String(120), nullable=False)
    outcome: Mapped[str] = mapped_column(String(40), nullable=False)
    operation: Mapped[Optional[str]] = mapped_column(String(80))
    status_code: Mapped[Optional[int]] = mapped_column(Integer)

    entity_type: Mapped[Optional[str]] = mapped_column(String(80))
    entity_id: Mapped[Optional[str]] = mapped_column(String(128))
    provider: Mapped[Optional[str]] = mapped_column(String(80))

    organization_id: Mapped[Optional[str]] = mapped_column(String(64))
    user_id: Mapped[Optional[str]] = mapped_column(String(64))
    anonymous_id: Mapped[Optional[str]] = mapped_column(String(64))
    session_id: Mapped[Optional[str]] = mapped_column(String(128))
    client_event_id: Mapped[Optional[str]] = mapped_column(String(128))
    request_id: Mapped[Optional[str]] = mapped_column(String(128))
    correlation_id: Mapped[Optional[str]] = mapped_column(String(128))

    route: Mapped[Optional[str]] = mapped_column(String(255))
    path: Mapped[Optional[str]] = mapped_column(String(500))
    method: Mapped[Optional[str]] = mapped_column(String(16))
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    referer: Mapped[Optional[str]] = mapped_column(String(500))
    environment: Mapped[Optional[str]] = mapped_column(String(40))

    event_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)

    request_headers: Mapped[Optional[dict]] = mapped_column(FlexibleJSONB)
    request_payload: Mapped[Optional[dict]] = mapped_column(FlexibleJSONB)
    response_payload: Mapped[Optional[dict]] = mapped_column(FlexibleJSONB)
    raw_payload: Mapped[Optional[dict]] = mapped_column(FlexibleJSONB)
    feature_flags: Mapped[Optional[dict]] = mapped_column(FlexibleJSONB)
    metadata_json: Mapped[Optional[dict]] = mapped_column("metadata", FlexibleJSONB)

    payload_hash: Mapped[Optional[str]] = mapped_column(String(64))
    error_type: Mapped[Optional[str]] = mapped_column(String(120))
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    __table_args__ = (
        Index("idx_capture_events_ingested", "ingested_at"),
        Index("idx_capture_events_source_time", "source", "ingested_at"),
        Index("idx_capture_events_outcome_time", "outcome", "ingested_at"),
        Index("idx_capture_events_entity", "entity_type", "entity_id", "ingested_at"),
        Index("idx_capture_events_user_time", "user_id", "ingested_at"),
        Index("idx_capture_events_org_time", "organization_id", "ingested_at"),
        Index("idx_capture_events_session_time", "session_id", "ingested_at"),
        Index("idx_capture_events_request", "request_id"),
        Index("idx_capture_events_correlation", "correlation_id"),
    )


class ExternalAPICall(BaseModel):
    """Raw request/response capture for third-party and AI provider calls."""

    __tablename__ = "external_api_calls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(), default=uuid.uuid4, nullable=False, unique=True
    )

    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    api_name: Mapped[Optional[str]] = mapped_column(String(120))
    api_version: Mapped[Optional[str]] = mapped_column(String(80))
    endpoint: Mapped[Optional[str]] = mapped_column(String(500))
    method: Mapped[Optional[str]] = mapped_column(String(16))
    request_url: Mapped[Optional[str]] = mapped_column(Text)
    outcome: Mapped[str] = mapped_column(String(40), nullable=False)
    status_code: Mapped[Optional[int]] = mapped_column(Integer)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    entity_type: Mapped[Optional[str]] = mapped_column(String(80))
    entity_id: Mapped[Optional[str]] = mapped_column(String(128))
    organization_id: Mapped[Optional[str]] = mapped_column(String(64))
    user_id: Mapped[Optional[str]] = mapped_column(String(64))
    request_id: Mapped[Optional[str]] = mapped_column(String(128))
    correlation_id: Mapped[Optional[str]] = mapped_column(String(128))

    event_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    request_headers: Mapped[Optional[dict]] = mapped_column(FlexibleJSONB)
    request_payload: Mapped[Optional[dict]] = mapped_column(FlexibleJSONB)
    response_headers: Mapped[Optional[dict]] = mapped_column(FlexibleJSONB)
    response_payload: Mapped[Optional[dict]] = mapped_column(FlexibleJSONB)
    metadata_json: Mapped[Optional[dict]] = mapped_column("metadata", FlexibleJSONB)
    payload_hash: Mapped[Optional[str]] = mapped_column(String(64))
    error_type: Mapped[Optional[str]] = mapped_column(String(120))
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    __table_args__ = (
        Index("idx_external_calls_provider_time", "provider", "ingested_at"),
        Index("idx_external_calls_outcome_time", "outcome", "ingested_at"),
        Index("idx_external_calls_entity", "entity_type", "entity_id", "ingested_at"),
        Index("idx_external_calls_request", "request_id"),
        Index("idx_external_calls_correlation", "correlation_id"),
    )


class StatusTransition(BaseModel):
    """Immutable history of status-like field changes."""

    __tablename__ = "status_transitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(128), nullable=False)
    status_field: Mapped[str] = mapped_column(String(80), nullable=False)
    from_status: Mapped[Optional[str]] = mapped_column(String(120))
    to_status: Mapped[str] = mapped_column(String(120), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text)

    organization_id: Mapped[Optional[str]] = mapped_column(String(64))
    actor_user_id: Mapped[Optional[str]] = mapped_column(String(64))
    request_id: Mapped[Optional[str]] = mapped_column(String(128))
    correlation_id: Mapped[Optional[str]] = mapped_column(String(128))
    metadata_json: Mapped[Optional[dict]] = mapped_column("metadata", FlexibleJSONB)

    transitioned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index(
            "idx_status_transitions_entity",
            "entity_type",
            "entity_id",
            "transitioned_at",
        ),
        Index("idx_status_transitions_to_time", "to_status", "transitioned_at"),
        Index("idx_status_transitions_request", "request_id"),
    )


class EntityLifecycleEvent(BaseModel):
    """Append-only lifecycle/tombstone events for create/update/delete/restore actions."""

    __tablename__ = "entity_lifecycle_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(128), nullable=False)
    action: Mapped[str] = mapped_column(String(40), nullable=False)

    organization_id: Mapped[Optional[str]] = mapped_column(String(64))
    actor_user_id: Mapped[Optional[str]] = mapped_column(String(64))
    request_id: Mapped[Optional[str]] = mapped_column(String(128))
    correlation_id: Mapped[Optional[str]] = mapped_column(String(128))
    reason: Mapped[Optional[str]] = mapped_column(Text)

    before_payload: Mapped[Optional[dict]] = mapped_column(FlexibleJSONB)
    after_payload: Mapped[Optional[dict]] = mapped_column(FlexibleJSONB)
    tombstone_payload: Mapped[Optional[dict]] = mapped_column(FlexibleJSONB)
    metadata_json: Mapped[Optional[dict]] = mapped_column("metadata", FlexibleJSONB)

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_lifecycle_entity_time", "entity_type", "entity_id", "occurred_at"),
        Index("idx_lifecycle_action_time", "action", "occurred_at"),
        Index("idx_lifecycle_request", "request_id"),
    )


class RawArtifact(BaseModel):
    """Queryable metadata for raw payloads or large artifacts stored out-of-row."""

    __tablename__ = "raw_artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    artifact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(), default=uuid.uuid4, nullable=False, unique=True
    )
    artifact_type: Mapped[str] = mapped_column(String(60), nullable=False)
    source: Mapped[str] = mapped_column(String(120), nullable=False)
    uri: Mapped[Optional[str]] = mapped_column(Text)
    storage_key: Mapped[Optional[str]] = mapped_column(Text)
    sha256: Mapped[Optional[str]] = mapped_column(String(64))
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer)
    mime_type: Mapped[Optional[str]] = mapped_column(String(120))
    encoding: Mapped[Optional[str]] = mapped_column(String(40))

    entity_type: Mapped[Optional[str]] = mapped_column(String(80))
    entity_id: Mapped[Optional[str]] = mapped_column(String(128))
    data_capture_event_id: Mapped[Optional[int]] = mapped_column(Integer)
    external_api_call_id: Mapped[Optional[int]] = mapped_column(Integer)
    request_id: Mapped[Optional[str]] = mapped_column(String(128))
    metadata_json: Mapped[Optional[dict]] = mapped_column("metadata", FlexibleJSONB)
    preview_payload: Mapped[Optional[dict]] = mapped_column(FlexibleJSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_raw_artifacts_source_time", "source", "created_at"),
        Index("idx_raw_artifacts_entity", "entity_type", "entity_id", "created_at"),
        Index("idx_raw_artifacts_sha256", "sha256"),
        Index("idx_raw_artifacts_request", "request_id"),
    )


__all__ = [
    "DataCaptureEvent",
    "EntityLifecycleEvent",
    "ExternalAPICall",
    "RawArtifact",
    "StatusTransition",
]
