"""analytics capture layer

Revision ID: 20260520_000045
Revises: 20260518_000044
Create Date: 2026-05-20

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260520_000045"
down_revision: Union[str, Sequence[str], None] = "20260518_000044"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _json_type() -> sa.types.TypeEngine:
    return sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def _uuid_type() -> sa.types.TypeEngine:
    return sa.String(36).with_variant(postgresql.UUID(as_uuid=True), "postgresql")


def upgrade() -> None:
    op.create_table(
        "data_capture_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", _uuid_type(), nullable=False, unique=True),
        sa.Column("capture_type", sa.String(40), nullable=False),
        sa.Column("source", sa.String(120), nullable=False),
        sa.Column("outcome", sa.String(40), nullable=False),
        sa.Column("operation", sa.String(80), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("entity_type", sa.String(80), nullable=True),
        sa.Column("entity_id", sa.String(128), nullable=True),
        sa.Column("provider", sa.String(80), nullable=True),
        sa.Column("organization_id", sa.String(64), nullable=True),
        sa.Column("user_id", sa.String(64), nullable=True),
        sa.Column("anonymous_id", sa.String(64), nullable=True),
        sa.Column("session_id", sa.String(128), nullable=True),
        sa.Column("client_event_id", sa.String(128), nullable=True),
        sa.Column("request_id", sa.String(128), nullable=True),
        sa.Column("correlation_id", sa.String(128), nullable=True),
        sa.Column("route", sa.String(255), nullable=True),
        sa.Column("path", sa.String(500), nullable=True),
        sa.Column("method", sa.String(16), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("referer", sa.String(500), nullable=True),
        sa.Column("environment", sa.String(40), nullable=True),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("request_headers", _json_type(), nullable=True),
        sa.Column("request_payload", _json_type(), nullable=True),
        sa.Column("response_payload", _json_type(), nullable=True),
        sa.Column("raw_payload", _json_type(), nullable=True),
        sa.Column("feature_flags", _json_type(), nullable=True),
        sa.Column("metadata", _json_type(), nullable=True),
        sa.Column("payload_hash", sa.String(64), nullable=True),
        sa.Column("error_type", sa.String(120), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.create_index(
        "idx_capture_events_ingested", "data_capture_events", ["ingested_at"]
    )
    op.create_index(
        "idx_capture_events_source_time",
        "data_capture_events",
        ["source", "ingested_at"],
    )
    op.create_index(
        "idx_capture_events_outcome_time",
        "data_capture_events",
        ["outcome", "ingested_at"],
    )
    op.create_index(
        "idx_capture_events_entity",
        "data_capture_events",
        ["entity_type", "entity_id", "ingested_at"],
    )
    op.create_index(
        "idx_capture_events_user_time",
        "data_capture_events",
        ["user_id", "ingested_at"],
    )
    op.create_index(
        "idx_capture_events_org_time",
        "data_capture_events",
        ["organization_id", "ingested_at"],
    )
    op.create_index(
        "idx_capture_events_session_time",
        "data_capture_events",
        ["session_id", "ingested_at"],
    )
    op.create_index("idx_capture_events_request", "data_capture_events", ["request_id"])
    op.create_index(
        "idx_capture_events_correlation", "data_capture_events", ["correlation_id"]
    )

    op.create_table(
        "external_api_calls",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("call_id", _uuid_type(), nullable=False, unique=True),
        sa.Column("provider", sa.String(80), nullable=False),
        sa.Column("api_name", sa.String(120), nullable=True),
        sa.Column("api_version", sa.String(80), nullable=True),
        sa.Column("endpoint", sa.String(500), nullable=True),
        sa.Column("method", sa.String(16), nullable=True),
        sa.Column("request_url", sa.Text(), nullable=True),
        sa.Column("outcome", sa.String(40), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("entity_type", sa.String(80), nullable=True),
        sa.Column("entity_id", sa.String(128), nullable=True),
        sa.Column("organization_id", sa.String(64), nullable=True),
        sa.Column("user_id", sa.String(64), nullable=True),
        sa.Column("request_id", sa.String(128), nullable=True),
        sa.Column("correlation_id", sa.String(128), nullable=True),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("request_headers", _json_type(), nullable=True),
        sa.Column("request_payload", _json_type(), nullable=True),
        sa.Column("response_headers", _json_type(), nullable=True),
        sa.Column("response_payload", _json_type(), nullable=True),
        sa.Column("metadata", _json_type(), nullable=True),
        sa.Column("payload_hash", sa.String(64), nullable=True),
        sa.Column("error_type", sa.String(120), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.create_index(
        "idx_external_calls_provider_time",
        "external_api_calls",
        ["provider", "ingested_at"],
    )
    op.create_index(
        "idx_external_calls_outcome_time",
        "external_api_calls",
        ["outcome", "ingested_at"],
    )
    op.create_index(
        "idx_external_calls_entity",
        "external_api_calls",
        ["entity_type", "entity_id", "ingested_at"],
    )
    op.create_index("idx_external_calls_request", "external_api_calls", ["request_id"])
    op.create_index(
        "idx_external_calls_correlation", "external_api_calls", ["correlation_id"]
    )

    op.create_table(
        "status_transitions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entity_type", sa.String(80), nullable=False),
        sa.Column("entity_id", sa.String(128), nullable=False),
        sa.Column("status_field", sa.String(80), nullable=False),
        sa.Column("from_status", sa.String(120), nullable=True),
        sa.Column("to_status", sa.String(120), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("organization_id", sa.String(64), nullable=True),
        sa.Column("actor_user_id", sa.String(64), nullable=True),
        sa.Column("request_id", sa.String(128), nullable=True),
        sa.Column("correlation_id", sa.String(128), nullable=True),
        sa.Column("metadata", _json_type(), nullable=True),
        sa.Column(
            "transitioned_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_status_transitions_entity",
        "status_transitions",
        ["entity_type", "entity_id", "transitioned_at"],
    )
    op.create_index(
        "idx_status_transitions_to_time",
        "status_transitions",
        ["to_status", "transitioned_at"],
    )
    op.create_index(
        "idx_status_transitions_request", "status_transitions", ["request_id"]
    )

    op.create_table(
        "entity_lifecycle_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entity_type", sa.String(80), nullable=False),
        sa.Column("entity_id", sa.String(128), nullable=False),
        sa.Column("action", sa.String(40), nullable=False),
        sa.Column("organization_id", sa.String(64), nullable=True),
        sa.Column("actor_user_id", sa.String(64), nullable=True),
        sa.Column("request_id", sa.String(128), nullable=True),
        sa.Column("correlation_id", sa.String(128), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("before_payload", _json_type(), nullable=True),
        sa.Column("after_payload", _json_type(), nullable=True),
        sa.Column("tombstone_payload", _json_type(), nullable=True),
        sa.Column("metadata", _json_type(), nullable=True),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_lifecycle_entity_time",
        "entity_lifecycle_events",
        ["entity_type", "entity_id", "occurred_at"],
    )
    op.create_index(
        "idx_lifecycle_action_time",
        "entity_lifecycle_events",
        ["action", "occurred_at"],
    )
    op.create_index("idx_lifecycle_request", "entity_lifecycle_events", ["request_id"])

    op.create_table(
        "raw_artifacts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("artifact_id", _uuid_type(), nullable=False, unique=True),
        sa.Column("artifact_type", sa.String(60), nullable=False),
        sa.Column("source", sa.String(120), nullable=False),
        sa.Column("uri", sa.Text(), nullable=True),
        sa.Column("storage_key", sa.Text(), nullable=True),
        sa.Column("sha256", sa.String(64), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("mime_type", sa.String(120), nullable=True),
        sa.Column("encoding", sa.String(40), nullable=True),
        sa.Column("entity_type", sa.String(80), nullable=True),
        sa.Column("entity_id", sa.String(128), nullable=True),
        sa.Column("data_capture_event_id", sa.Integer(), nullable=True),
        sa.Column("external_api_call_id", sa.Integer(), nullable=True),
        sa.Column("request_id", sa.String(128), nullable=True),
        sa.Column("metadata", _json_type(), nullable=True),
        sa.Column("preview_payload", _json_type(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_raw_artifacts_source_time", "raw_artifacts", ["source", "created_at"]
    )
    op.create_index(
        "idx_raw_artifacts_entity",
        "raw_artifacts",
        ["entity_type", "entity_id", "created_at"],
    )
    op.create_index("idx_raw_artifacts_sha256", "raw_artifacts", ["sha256"])
    op.create_index("idx_raw_artifacts_request", "raw_artifacts", ["request_id"])

    op.add_column(
        "property_photos",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "property_voice_notes",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "singapore_properties",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_property_photos_deleted_at", "property_photos", ["deleted_at"])
    op.create_index(
        "ix_property_voice_notes_deleted_at",
        "property_voice_notes",
        ["deleted_at"],
    )
    op.create_index(
        "ix_singapore_properties_deleted_at",
        "singapore_properties",
        ["deleted_at"],
    )


def _drop_idx(name: str) -> None:
    op.execute(f'DROP INDEX IF EXISTS "{name}"')


def _drop_table(name: str) -> None:
    op.execute(f'DROP TABLE IF EXISTS "{name}"')


def _table_exists(table: str) -> bool:
    return bool(sa.inspect(op.get_bind()).has_table(table))


def _column_exists(table: str, column: str) -> bool:
    if not _table_exists(table):
        return False
    return column in {
        col["name"] for col in sa.inspect(op.get_bind()).get_columns(table)
    }


def _drop_columns(table: str, columns: tuple[str, ...]) -> None:
    if not _table_exists(table):
        return
    with op.batch_alter_table(table) as batch_op:
        for column in columns:
            if _column_exists(table, column):
                batch_op.drop_column(column)


def downgrade() -> None:
    for name in (
        "ix_singapore_properties_deleted_at",
        "ix_property_voice_notes_deleted_at",
        "ix_property_photos_deleted_at",
    ):
        _drop_idx(name)
    _drop_columns("singapore_properties", ("deleted_at",))
    _drop_columns("property_voice_notes", ("deleted_at",))
    _drop_columns("property_photos", ("deleted_at",))

    for name in (
        "idx_raw_artifacts_request",
        "idx_raw_artifacts_sha256",
        "idx_raw_artifacts_entity",
        "idx_raw_artifacts_source_time",
    ):
        _drop_idx(name)
    _drop_table("raw_artifacts")

    for name in (
        "idx_lifecycle_request",
        "idx_lifecycle_action_time",
        "idx_lifecycle_entity_time",
    ):
        _drop_idx(name)
    _drop_table("entity_lifecycle_events")

    for name in (
        "idx_status_transitions_request",
        "idx_status_transitions_to_time",
        "idx_status_transitions_entity",
    ):
        _drop_idx(name)
    _drop_table("status_transitions")

    for name in (
        "idx_external_calls_correlation",
        "idx_external_calls_request",
        "idx_external_calls_entity",
        "idx_external_calls_outcome_time",
        "idx_external_calls_provider_time",
    ):
        _drop_idx(name)
    _drop_table("external_api_calls")

    for name in (
        "idx_capture_events_correlation",
        "idx_capture_events_request",
        "idx_capture_events_session_time",
        "idx_capture_events_org_time",
        "idx_capture_events_user_time",
        "idx_capture_events_entity",
        "idx_capture_events_outcome_time",
        "idx_capture_events_source_time",
        "idx_capture_events_ingested",
    ):
        _drop_idx(name)
    _drop_table("data_capture_events")


__all__: list[str] = []
