"""db hardening for ML readiness

Adds the load-bearing primitives the schema was missing:

* ``organizations`` — singleton-seeded tenant table.
* ``organization_id`` (nullable) and ``deleted_at`` on core tables
  (``properties``, ``projects``, ``fin_scenarios``, ``users``).
* ``entity_history`` — generic row-level change history.
* ``predictions`` — model outputs with optional human feedback.
* ``embedding`` columns (pgvector when available, TEXT fallback for SQLite)
  on ``imports`` and ``property_photos``; HNSW indexes on Postgres.
* Float → ``NUMERIC`` for scoring/confidence/cost columns on
  ``ai_agents``, ``ai_agent_sessions``, ``overlay_suggestions``.
* Timezone-aware timestamps on ``users``, ``ai_agents``, ``ai_agent_sessions``.
* Composite indexes for typical ML pull patterns.

Revision ID: 20260518_000042
Revises: 069afe97c108
Create Date: 2026-05-18

"""

from __future__ import annotations

import os
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260518_000042"
down_revision: Union[str, Sequence[str], None] = "069afe97c108"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


DEFAULT_ORG_ID = "00000000-0000-0000-0000-000000000001"


def _json_type() -> sa.types.TypeEngine:
    return sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def _uuid_type() -> sa.types.TypeEngine:
    return sa.String(36).with_variant(postgresql.UUID(as_uuid=True), "postgresql")


def _is_postgres() -> bool:
    bind = op.get_bind()
    return bool(bind is not None and bind.dialect.name == "postgresql")


def _pgvector_enabled() -> bool:
    if not _is_postgres():
        return False
    enabled = os.getenv("BUILDABLE_USE_PGVECTOR", "").strip().lower()
    return enabled in {"1", "true", "yes", "on"}


def _vector_column(name: str) -> sa.Column:
    """Choose pgvector when available + opted-in, else TEXT for portability."""
    if _pgvector_enabled():
        try:
            module = __import__("pgvector.sqlalchemy", fromlist=["Vector"])
        except ModuleNotFoundError:  # pragma: no cover - depends on extras
            module = None
        if module is not None:
            return sa.Column(name, module.Vector(1536), nullable=True)
    return sa.Column(name, sa.Text(), nullable=True)


def _add_nullable_uuid(table: str, name: str) -> None:
    op.add_column(table, sa.Column(name, _uuid_type(), nullable=True))


def upgrade() -> None:
    # --- organizations ---------------------------------------------------
    op.create_table(
        "organizations",
        sa.Column("id", _uuid_type(), primary_key=True),
        sa.Column("slug", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("slug", name="uq_organizations_slug"),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"])

    # Seed the default singleton tenant.
    op.execute(
        sa.text(
            "INSERT INTO organizations (id, slug, name, is_active) "
            "VALUES (:id, :slug, :name, TRUE)"
        ).bindparams(id=DEFAULT_ORG_ID, slug="default", name="Default Organization")
    )

    # --- entity_history --------------------------------------------------
    op.create_table(
        "entity_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entity_type", sa.String(80), nullable=False),
        sa.Column("entity_id", sa.String(64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("operation", sa.String(16), nullable=False),
        sa.Column("before", _json_type(), nullable=True),
        sa.Column("after", _json_type(), nullable=True),
        sa.Column("changed_fields", _json_type(), nullable=True),
        sa.Column("changed_by", _uuid_type(), nullable=True),
        sa.Column("changed_by_label", sa.String(255), nullable=True),
        sa.Column("reason", sa.String(255), nullable=True),
        sa.Column("request_id", sa.String(64), nullable=True),
        sa.Column("organization_id", _uuid_type(), nullable=True),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "entity_type", "entity_id", "version", name="uq_entity_history_version"
        ),
    )
    op.create_index(
        "idx_entity_history_entity",
        "entity_history",
        ["entity_type", "entity_id", "version"],
    )
    op.create_index(
        "idx_entity_history_changed_at",
        "entity_history",
        ["entity_type", "changed_at"],
    )
    op.create_index(
        "idx_entity_history_org_changed_at",
        "entity_history",
        ["organization_id", "changed_at"],
    )

    # --- predictions -----------------------------------------------------
    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("model_name", sa.String(120), nullable=False),
        sa.Column("model_version", sa.String(60), nullable=False),
        sa.Column("model_provider", sa.String(60), nullable=True),
        sa.Column("input_entity_type", sa.String(80), nullable=False),
        sa.Column("input_entity_id", sa.String(64), nullable=False),
        sa.Column("input_payload", _json_type(), nullable=True),
        sa.Column("input_hash", sa.String(64), nullable=True),
        sa.Column(
            "output", _json_type(), nullable=False, server_default=sa.text("'{}'")
        ),
        sa.Column("label", sa.String(120), nullable=True),
        sa.Column("confidence", sa.Numeric(6, 4), nullable=True),
        sa.Column("tokens_used", sa.Integer(), nullable=True),
        sa.Column("cost_estimate", sa.Numeric(12, 6), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("organization_id", _uuid_type(), nullable=True),
        sa.Column("created_by", _uuid_type(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("human_feedback", _json_type(), nullable=True),
        sa.Column("human_feedback_label", sa.String(60), nullable=True),
        sa.Column("feedback_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("feedback_by", _uuid_type(), nullable=True),
    )
    op.create_index(
        "idx_predictions_model_version",
        "predictions",
        ["model_name", "model_version", "created_at"],
    )
    op.create_index(
        "idx_predictions_entity",
        "predictions",
        ["input_entity_type", "input_entity_id", "created_at"],
    )
    op.create_index(
        "idx_predictions_feedback",
        "predictions",
        ["model_name", "human_feedback_label", "feedback_at"],
    )
    op.create_index(
        "ix_predictions_organization_id",
        "predictions",
        ["organization_id"],
    )

    # --- soft-delete + organization_id on core tables --------------------
    for table in ("properties", "projects", "fin_scenarios", "users"):
        op.add_column(
            table,
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index(
            f"ix_{table}_deleted_at",
            table,
            ["deleted_at"],
        )
        _add_nullable_uuid(table, "organization_id")
        op.create_index(
            f"ix_{table}_organization_id",
            table,
            ["organization_id"],
        )

    # Back-fill organization_id on existing rows to the default tenant.
    for table in ("properties", "projects", "fin_scenarios", "users"):
        op.execute(
            sa.text(
                f"UPDATE {table} SET organization_id = :org "
                "WHERE organization_id IS NULL"
            ).bindparams(org=DEFAULT_ORG_ID)
        )

    # --- composite indexes for ML pulls ----------------------------------
    op.create_index(
        "idx_property_jurisdiction_type_year",
        "properties",
        ["jurisdiction_code", "property_type", "year_built"],
    )
    op.create_index(
        "idx_property_org_jurisdiction",
        "properties",
        ["organization_id", "jurisdiction_code"],
    )
    op.create_index(
        "idx_transaction_segment_type_date",
        "market_transactions",
        ["market_segment", "transaction_type", "transaction_date"],
    )

    # fin_results.created_at + composite (project, scenario, created)
    op.add_column(
        "fin_results",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_fin_results_created_at", "fin_results", ["created_at"])
    op.create_index(
        "idx_fin_results_project_scenario_created",
        "fin_results",
        ["project_id", "scenario_id", "created_at"],
    )

    # --- Float → NUMERIC ------------------------------------------------
    if _is_postgres():
        op.alter_column(
            "ai_agents",
            "temperature",
            type_=sa.Numeric(4, 3),
            existing_type=sa.Float(),
            existing_nullable=True,
            postgresql_using="temperature::numeric",
        )
        op.alter_column(
            "ai_agent_sessions",
            "cost_estimate",
            type_=sa.Numeric(12, 6),
            existing_type=sa.Float(),
            existing_nullable=True,
            postgresql_using="cost_estimate::numeric",
        )
        op.alter_column(
            "ai_agent_sessions",
            "processing_time",
            type_=sa.Numeric(10, 3),
            existing_type=sa.Float(),
            existing_nullable=True,
            postgresql_using="processing_time::numeric",
        )
        op.alter_column(
            "ai_agent_sessions",
            "singapore_compliance_score",
            type_=sa.Numeric(6, 3),
            existing_type=sa.Float(),
            existing_nullable=True,
            postgresql_using="singapore_compliance_score::numeric",
        )
        op.alter_column(
            "overlay_suggestions",
            "score",
            type_=sa.Numeric(8, 4),
            existing_type=sa.Float(),
            existing_nullable=True,
            postgresql_using="score::numeric",
        )

    # --- Timezone-aware timestamps on touched models ---------------------
    if _is_postgres():
        tz_targets: list[tuple[str, str, bool]] = [
            ("users", "created_at", False),
            ("users", "updated_at", False),
            ("users", "last_login", True),
            ("ai_agents", "created_at", False),
            ("ai_agents", "updated_at", False),
            ("ai_agent_sessions", "started_at", False),
            ("ai_agent_sessions", "completed_at", True),
            ("ai_agent_sessions", "last_activity", True),
        ]
        for table, column, nullable in tz_targets:
            op.alter_column(
                table,
                column,
                type_=sa.DateTime(timezone=True),
                existing_type=sa.DateTime(),
                existing_nullable=nullable,
                postgresql_using=f"{column} AT TIME ZONE 'UTC'",
            )

    # --- pgvector columns + HNSW indexes (opt-in, Postgres only) ---------
    if _pgvector_enabled():
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.add_column("imports", _vector_column("embedding"))
    op.add_column(
        "imports", sa.Column("embedding_model", sa.String(120), nullable=True)
    )
    op.add_column("property_photos", _vector_column("embedding"))
    op.add_column(
        "property_photos",
        sa.Column("embedding_model", sa.String(120), nullable=True),
    )

    if _pgvector_enabled():
        op.execute(
            "CREATE INDEX IF NOT EXISTS idx_imports_embedding_hnsw "
            "ON imports USING hnsw (embedding vector_cosine_ops)"
        )
        op.execute(
            "CREATE INDEX IF NOT EXISTS idx_property_photos_embedding_hnsw "
            "ON property_photos USING hnsw (embedding vector_cosine_ops)"
        )


def _drop_idx(name: str) -> None:
    op.execute(f'DROP INDEX IF EXISTS "{name}"')


def _drop_table(name: str) -> None:
    op.execute(f'DROP TABLE IF EXISTS "{name}"')


def _drop_columns(table: str, columns: tuple[str, ...]) -> None:
    with op.batch_alter_table(table) as batch_op:
        for column in columns:
            batch_op.drop_column(column)


def downgrade() -> None:
    if _pgvector_enabled():
        _drop_idx("idx_property_photos_embedding_hnsw")
        _drop_idx("idx_imports_embedding_hnsw")

    _drop_columns("imports", ("embedding_model", "embedding"))
    _drop_columns("property_photos", ("embedding_model", "embedding"))

    if _is_postgres():
        tz_targets: list[tuple[str, str, bool]] = [
            ("users", "created_at", False),
            ("users", "updated_at", False),
            ("users", "last_login", True),
            ("ai_agents", "created_at", False),
            ("ai_agents", "updated_at", False),
            ("ai_agent_sessions", "started_at", False),
            ("ai_agent_sessions", "completed_at", True),
            ("ai_agent_sessions", "last_activity", True),
        ]
        for table, column, nullable in tz_targets:
            op.alter_column(
                table,
                column,
                type_=sa.DateTime(),
                existing_type=sa.DateTime(timezone=True),
                existing_nullable=nullable,
            )

        op.alter_column(
            "overlay_suggestions",
            "score",
            type_=sa.Float(),
            existing_type=sa.Numeric(8, 4),
        )
        op.alter_column(
            "ai_agent_sessions",
            "singapore_compliance_score",
            type_=sa.Float(),
            existing_type=sa.Numeric(6, 3),
        )
        op.alter_column(
            "ai_agent_sessions",
            "processing_time",
            type_=sa.Float(),
            existing_type=sa.Numeric(10, 3),
        )
        op.alter_column(
            "ai_agent_sessions",
            "cost_estimate",
            type_=sa.Float(),
            existing_type=sa.Numeric(12, 6),
        )
        op.alter_column(
            "ai_agents",
            "temperature",
            type_=sa.Float(),
            existing_type=sa.Numeric(4, 3),
        )

    _drop_idx("idx_fin_results_project_scenario_created")
    _drop_idx("ix_fin_results_created_at")
    _drop_columns("fin_results", ("created_at",))

    _drop_idx("idx_transaction_segment_type_date")
    _drop_idx("idx_property_org_jurisdiction")
    _drop_idx("idx_property_jurisdiction_type_year")

    for table in ("properties", "projects", "fin_scenarios", "users"):
        _drop_idx(f"ix_{table}_organization_id")
        _drop_idx(f"ix_{table}_deleted_at")
        _drop_columns(table, ("organization_id", "deleted_at"))

    _drop_idx("ix_predictions_organization_id")
    _drop_idx("idx_predictions_feedback")
    _drop_idx("idx_predictions_entity")
    _drop_idx("idx_predictions_model_version")
    _drop_table("predictions")

    _drop_idx("idx_entity_history_org_changed_at")
    _drop_idx("idx_entity_history_changed_at")
    _drop_idx("idx_entity_history_entity")
    _drop_table("entity_history")

    _drop_idx("ix_organizations_slug")
    _drop_table("organizations")


__all__: list[str] = []
