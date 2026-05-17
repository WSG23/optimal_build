"""user_events + search_queries (PR1: behavioral capture)

Append-only logs for behavioral telemetry and search intent. Both tables are
high-volume and read mostly in time-ordered windows — indexes lean on
``occurred_at``.

Revision ID: 20260518_000043
Revises: 20260518_000042
Create Date: 2026-05-18

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260518_000043"
down_revision: Union[str, Sequence[str], None] = "20260518_000042"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _json_type() -> sa.types.TypeEngine:
    return sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def _uuid_type() -> sa.types.TypeEngine:
    return sa.String(36).with_variant(postgresql.UUID(as_uuid=True), "postgresql")


def upgrade() -> None:
    op.create_table(
        "user_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", _uuid_type(), nullable=True),
        sa.Column("user_id", _uuid_type(), nullable=True),
        sa.Column("anonymous_id", sa.String(64), nullable=True),
        sa.Column("session_id", sa.String(64), nullable=True),
        sa.Column("event_type", sa.String(40), nullable=False),
        sa.Column("event_name", sa.String(120), nullable=False),
        sa.Column("target_type", sa.String(80), nullable=True),
        sa.Column("target_id", sa.String(64), nullable=True),
        sa.Column("payload", _json_type(), nullable=True),
        sa.Column("path", sa.String(255), nullable=True),
        sa.Column("referrer", sa.String(255), nullable=True),
        sa.Column("user_agent", sa.String(255), nullable=True),
        sa.Column("ip_hash", sa.String(64), nullable=True),
        sa.Column("client_event_id", sa.String(64), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "server_received_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_user_events_organization_id", "user_events", ["organization_id"]
    )
    op.create_index("idx_user_events_occurred", "user_events", ["occurred_at"])
    op.create_index(
        "idx_user_events_user_occurred",
        "user_events",
        ["user_id", "occurred_at"],
    )
    op.create_index(
        "idx_user_events_type_name_occurred",
        "user_events",
        ["event_type", "event_name", "occurred_at"],
    )
    op.create_index(
        "idx_user_events_target",
        "user_events",
        ["target_type", "target_id", "occurred_at"],
    )
    op.create_index("idx_user_events_client_id", "user_events", ["client_event_id"])

    op.create_table(
        "search_queries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", _uuid_type(), nullable=True),
        sa.Column("user_id", _uuid_type(), nullable=True),
        sa.Column("anonymous_id", sa.String(64), nullable=True),
        sa.Column("session_id", sa.String(64), nullable=True),
        sa.Column("query_text", sa.String(500), nullable=False),
        sa.Column("query_type", sa.String(40), nullable=True),
        sa.Column("filters", _json_type(), nullable=True),
        sa.Column("result_count", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("top_results", _json_type(), nullable=True),
        sa.Column("clicked_rank", sa.Integer(), nullable=True),
        sa.Column("clicked_entity_type", sa.String(80), nullable=True),
        sa.Column("clicked_entity_id", sa.String(64), nullable=True),
        sa.Column("clicked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_search_queries_organization_id", "search_queries", ["organization_id"]
    )
    op.create_index("idx_search_queries_occurred", "search_queries", ["occurred_at"])
    op.create_index(
        "idx_search_queries_user_occurred",
        "search_queries",
        ["user_id", "occurred_at"],
    )
    op.create_index(
        "idx_search_queries_type_occurred",
        "search_queries",
        ["query_type", "occurred_at"],
    )


def _drop_idx(name: str) -> None:
    op.execute(f'DROP INDEX IF EXISTS "{name}"')


def _drop_table(name: str) -> None:
    op.execute(f'DROP TABLE IF EXISTS "{name}"')


def downgrade() -> None:
    for name in (
        "idx_search_queries_type_occurred",
        "idx_search_queries_user_occurred",
        "idx_search_queries_occurred",
        "ix_search_queries_organization_id",
    ):
        _drop_idx(name)
    _drop_table("search_queries")

    for name in (
        "idx_user_events_client_id",
        "idx_user_events_target",
        "idx_user_events_type_name_occurred",
        "idx_user_events_user_occurred",
        "idx_user_events_occurred",
        "ix_user_events_organization_id",
    ):
        _drop_idx(name)
    _drop_table("user_events")


__all__: list[str] = []
