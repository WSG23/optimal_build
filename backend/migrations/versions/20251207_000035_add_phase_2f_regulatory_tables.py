"""Add Phase 2F regulatory tables

Revision ID: 20251207_000035
Revises: 20251207_000027
Create Date: 2025-12-07 02:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20251207_000035"
down_revision = "20251207_000027"
branch_labels = None
depends_on = None


def upgrade():
    # Create Enums manually first to be safe
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'agencycode') THEN
                CREATE TYPE agencycode AS ENUM ('URA', 'BCA', 'SCDF', 'NEA', 'LTA', 'NPARKS', 'PUB', 'SLA');
            END IF;
        END$$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'submissiontype') THEN
                CREATE TYPE submissiontype AS ENUM ('DC', 'BP', 'TOP', 'CSC', 'WAIVER', 'CONSULTATION');
            END IF;
        END$$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'submissionstatus') THEN
                CREATE TYPE submissionstatus AS ENUM ('DRAFT', 'SUBMITTED', 'IN_REVIEW', 'APPROVED', 'REJECTED', 'RFI');
            END IF;
        END$$;
        """
    )

    # Create regulatory_agencies table
    op.create_table(
        "regulatory_agencies",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "code",
            sa.String(),
            nullable=False,
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("api_endpoint", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    # Create authority_submissions table
    op.create_table(
        "authority_submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agency_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "submission_type",
            sa.String(),
            nullable=False,
        ),
        sa.Column("submission_no", sa.String(), nullable=True),
        sa.Column(
            "status",
            sa.String(),
            nullable=False,
        ),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["agency_id"],
            ["regulatory_agencies.id"],
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
        ),
    )

    op.create_index(
        op.f("ix_authority_submissions_project_id"),
        "authority_submissions",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_authority_submissions_agency_id"),
        "authority_submissions",
        ["agency_id"],
        unique=False,
    )


def downgrade():
    op.execute('DROP INDEX IF EXISTS "ix_authority_submissions_agency_id"')
    op.execute('DROP INDEX IF EXISTS "ix_authority_submissions_project_id"')
    op.execute("DROP TABLE IF EXISTS authority_submissions")
    op.execute("DROP TABLE IF EXISTS regulatory_agencies")

    op.execute("DROP TYPE submissionstatus")
    op.execute("DROP TYPE submissiontype")
    op.execute("DROP TYPE agencycode")
