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


def upgrade() -> None:
    # Create ENUM using raw SQL to avoid SQLAlchemy auto-creation issues with asyncpg
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'preview_job_status') THEN
                    CREATE TYPE preview_job_status AS ENUM (
                        'queued',
                        'processing',
                        'ready',
                        'failed',
                        'expired'
                    );
                END IF;
            END $$;
            """
        )
    )

    # Create preview_jobs table using raw SQL
    op.execute(
        sa.text(
            """
            CREATE TABLE preview_jobs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
                scenario VARCHAR(80) NOT NULL DEFAULT 'base',
                status preview_job_status NOT NULL DEFAULT 'queued',
                requested_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                started_at TIMESTAMP WITH TIME ZONE,
                finished_at TIMESTAMP WITH TIME ZONE,
                asset_version VARCHAR(64),
                preview_url VARCHAR(500),
                thumbnail_url VARCHAR(500),
                payload_checksum VARCHAR(128),
                message VARCHAR(500),
                metadata JSONB NOT NULL DEFAULT '{}'::jsonb
            )
            """
        )
    )

    # Create indexes
    op.execute(
        sa.text("CREATE INDEX ix_preview_jobs_property ON preview_jobs (property_id)")
    )
    op.execute(
        sa.text(
            "CREATE INDEX ix_preview_jobs_property_scenario ON preview_jobs (property_id, scenario)"
        )
    )


def downgrade() -> None:
    """Drop preview_jobs table and enum."""
    op.execute(sa.text("DROP TABLE IF EXISTS preview_jobs CASCADE"))
    op.execute(sa.text("DROP TYPE IF EXISTS preview_job_status CASCADE"))
