"""decision_alternatives + documents + document_extractions (PR2)

Decision provenance (preference pairs) and document corpus + extraction
pipeline metadata. Together with PR1's events/search_queries, these complete
the behavioral-and-content data layer.

Revision ID: 20260518_000044
Revises: 20260518_000043
Create Date: 2026-05-18

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260518_000044"
down_revision: Union[str, Sequence[str], None] = "20260518_000043"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _json_type() -> sa.types.TypeEngine:
    return sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def _uuid_type() -> sa.types.TypeEngine:
    return sa.String(36).with_variant(postgresql.UUID(as_uuid=True), "postgresql")


def upgrade() -> None:
    # --- decision_alternatives ------------------------------------------
    op.create_table(
        "decision_alternatives",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", _uuid_type(), nullable=True),
        sa.Column("user_id", _uuid_type(), nullable=True),
        sa.Column("anonymous_id", sa.String(64), nullable=True),
        sa.Column("session_id", sa.String(64), nullable=True),
        sa.Column("decision_type", sa.String(60), nullable=False),
        sa.Column("choice_set_id", sa.String(64), nullable=False),
        sa.Column("context_entity_type", sa.String(80), nullable=True),
        sa.Column("context_entity_id", sa.String(64), nullable=True),
        sa.Column("alternative_rank", sa.Integer(), nullable=False),
        sa.Column("alternative_label", sa.String(255), nullable=True),
        sa.Column("alternative_payload", _json_type(), nullable=True),
        sa.Column("score", sa.Numeric(8, 4), nullable=True),
        sa.Column("presented_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "chosen",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("chosen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("time_to_decide_ms", sa.Integer(), nullable=True),
        sa.Column("dismissed_reason", sa.String(120), nullable=True),
        sa.Column("rationale", sa.String(500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_decision_alternatives_organization_id",
        "decision_alternatives",
        ["organization_id"],
    )
    op.create_index(
        "idx_decision_alts_choice_set",
        "decision_alternatives",
        ["choice_set_id", "alternative_rank"],
    )
    op.create_index(
        "idx_decision_alts_type_chosen_presented",
        "decision_alternatives",
        ["decision_type", "chosen", "presented_at"],
    )
    op.create_index(
        "idx_decision_alts_user_presented",
        "decision_alternatives",
        ["user_id", "presented_at"],
    )
    op.create_index(
        "idx_decision_alts_context",
        "decision_alternatives",
        ["context_entity_type", "context_entity_id", "presented_at"],
    )

    # --- documents -------------------------------------------------------
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", _uuid_type(), nullable=True),
        sa.Column("uploaded_by", _uuid_type(), nullable=True),
        sa.Column("related_entity_type", sa.String(80), nullable=True),
        sa.Column("related_entity_id", sa.String(64), nullable=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=True),
        sa.Column(
            "source",
            sa.String(40),
            nullable=False,
            server_default=sa.text("'upload'"),
        ),
        sa.Column("classification", sa.String(60), nullable=True),
        sa.Column("language", sa.String(10), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_documents_organization_id", "documents", ["organization_id"])
    op.create_index("ix_documents_deleted_at", "documents", ["deleted_at"])
    op.create_index(
        "idx_documents_related_entity",
        "documents",
        ["related_entity_type", "related_entity_id"],
    )
    op.create_index(
        "idx_documents_org_uploaded",
        "documents",
        ["organization_id", "uploaded_at"],
    )
    op.create_index(
        "idx_documents_classification",
        "documents",
        ["classification", "uploaded_at"],
    )
    op.create_index("uq_documents_sha256", "documents", ["sha256"])

    # --- document_extractions -------------------------------------------
    op.create_table(
        "document_extractions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "document_id",
            sa.Integer(),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("extractor_name", sa.String(120), nullable=False),
        sa.Column("extractor_version", sa.String(60), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("structured", _json_type(), nullable=True),
        sa.Column("entities", _json_type(), nullable=True),
        sa.Column("embedding_storage_key", sa.String(255), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_document_extractions_document_id",
        "document_extractions",
        ["document_id"],
    )
    op.create_index(
        "idx_doc_extractions_status_created",
        "document_extractions",
        ["status", "created_at"],
    )
    op.create_index(
        "idx_doc_extractions_doc_extractor",
        "document_extractions",
        ["document_id", "extractor_name", "extractor_version"],
    )


def _drop_idx(name: str) -> None:
    op.execute(f'DROP INDEX IF EXISTS "{name}"')


def _drop_table(name: str) -> None:
    op.execute(f'DROP TABLE IF EXISTS "{name}"')


def downgrade() -> None:
    for name in (
        "idx_doc_extractions_doc_extractor",
        "idx_doc_extractions_status_created",
        "ix_document_extractions_document_id",
    ):
        _drop_idx(name)
    _drop_table("document_extractions")

    for name in (
        "uq_documents_sha256",
        "idx_documents_classification",
        "idx_documents_org_uploaded",
        "idx_documents_related_entity",
        "ix_documents_deleted_at",
        "ix_documents_organization_id",
    ):
        _drop_idx(name)
    _drop_table("documents")

    for name in (
        "idx_decision_alts_context",
        "idx_decision_alts_user_presented",
        "idx_decision_alts_type_chosen_presented",
        "idx_decision_alts_choice_set",
        "ix_decision_alternatives_organization_id",
    ):
        _drop_idx(name)
    _drop_table("decision_alternatives")


__all__: list[str] = []
