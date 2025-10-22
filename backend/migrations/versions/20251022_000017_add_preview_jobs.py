"""Create preview_jobs table for developer visualisation pipeline.

Revision ID: 20251022_000017
Revises: 20251020_000016
Create Date: 2025-10-22

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20251022_000017"
down_revision = "20251020_000016"
branch_labels = None
depends_on = None

PREVIEW_STATUS_ENUM = sa.Enum(
    "queued",
    "processing",
    "ready",
    "failed",
    "expired",
    name="preview_job_status",
    create_type=False,
)


def upgrade() -> None:
    PREVIEW_STATUS_ENUM.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "preview_jobs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("property_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "scenario", sa.String(length=80), nullable=False, server_default="base"
        ),
        sa.Column(
            "status", PREVIEW_STATUS_ENUM, nullable=False, server_default="queued"
        ),
        sa.Column(
            "requested_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("asset_version", sa.String(length=64), nullable=True),
        sa.Column("preview_url", sa.String(length=500), nullable=True),
        sa.Column("thumbnail_url", sa.String(length=500), nullable=True),
        sa.Column("payload_checksum", sa.String(length=128), nullable=True),
        sa.Column("message", sa.String(length=500), nullable=True),
        sa.Column(
            "metadata",
            sa.JSON().with_variant(postgresql.JSONB(), "postgresql"),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_preview_jobs_property",
        "preview_jobs",
        ["property_id"],
    )
    op.create_index(
        "ix_preview_jobs_property_scenario",
        "preview_jobs",
        ["property_id", "scenario"],
    )


def downgrade() -> None:
    """Downgrade not implemented for Phase 2B preview pipeline.

    If downgrade is needed, manually drop the preview_jobs table and preview_job_status enum.
    """
    pass
