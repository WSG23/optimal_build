"""Create entitlement tracking tables."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20240816_000004"
down_revision = "20240801_000003"
branch_labels = None
depends_on = None


JSONB_TYPE = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    """Apply the migration."""

    # Create ENUM types with raw SQL per CODING_RULES.md Rule 1.2
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ent_approval_category') THEN
                CREATE TYPE ent_approval_category AS ENUM ('planning','building','environmental','transport','utilities');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ent_roadmap_status') THEN
                CREATE TYPE ent_roadmap_status AS ENUM ('planned','in_progress','submitted','approved','rejected','blocked','complete');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ent_study_type') THEN
                CREATE TYPE ent_study_type AS ENUM ('traffic','environmental','heritage','utilities','community');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ent_study_status') THEN
                CREATE TYPE ent_study_status AS ENUM ('draft','scope_defined','in_progress','submitted','accepted','rejected');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ent_engagement_type') THEN
                CREATE TYPE ent_engagement_type AS ENUM ('agency','community','political','private_partner','regulator');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ent_engagement_status') THEN
                CREATE TYPE ent_engagement_status AS ENUM ('planned','active','completed','blocked');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ent_legal_instrument_type') THEN
                CREATE TYPE ent_legal_instrument_type AS ENUM ('agreement','licence','memorandum','waiver','variation');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ent_legal_instrument_status') THEN
                CREATE TYPE ent_legal_instrument_status AS ENUM ('draft','in_review','executed','expired');
            END IF;
        END$$;
        """
    )

    op.create_table(
        "ent_authorities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("jurisdiction", sa.String(length=10), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("website", sa.String(length=255), nullable=True),
        sa.Column("contact_email", sa.String(length=120), nullable=True),
        sa.Column(
            "metadata",
            JSONB_TYPE,
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
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
        sa.UniqueConstraint("slug", name="uq_ent_authority_slug"),
    )
    op.create_index(
        "ix_ent_authorities_jurisdiction",
        "ent_authorities",
        ["jurisdiction"],
    )
    op.create_index(
        "ix_ent_authorities_created_at",
        "ent_authorities",
        ["created_at"],
    )

    op.create_table(
        "ent_approval_types",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "authority_id",
            sa.Integer(),
            sa.ForeignKey("ent_authorities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.String(length=60), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "requirements",
            JSONB_TYPE,
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column("processing_time_days", sa.Integer(), nullable=True),
        sa.Column(
            "is_mandatory",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "metadata",
            JSONB_TYPE,
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
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
        sa.UniqueConstraint(
            "authority_id",
            "code",
            name="uq_ent_approval_type_code",
        ),
    )
    op.create_index(
        "ix_ent_approval_types_authority",
        "ent_approval_types",
        ["authority_id"],
    )
    op.create_index(
        "ix_ent_approval_types_created_at",
        "ent_approval_types",
        ["created_at"],
    )

    op.create_table(
        "ent_roadmap_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column(
            "approval_type_id",
            sa.Integer(),
            sa.ForeignKey("ent_approval_types.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("sequence_order", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("status_changed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("target_submission_date", sa.Date(), nullable=True),
        sa.Column("target_decision_date", sa.Date(), nullable=True),
        sa.Column("actual_submission_date", sa.Date(), nullable=True),
        sa.Column("actual_decision_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "metadata",
            JSONB_TYPE,
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
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
        sa.CheckConstraint(
            "sequence_order >= 1",
            name="chk_ent_roadmap_sequence_positive",
        ),
    )
    op.create_index(
        "ix_ent_roadmap_items_project",
        "ent_roadmap_items",
        ["project_id"],
    )
    op.create_index(
        "ix_ent_roadmap_items_approval",
        "ent_roadmap_items",
        ["approval_type_id"],
    )
    op.create_index(
        "idx_ent_roadmap_project_sequence",
        "ent_roadmap_items",
        ["project_id", "sequence_order"],
        unique=True,
    )

    op.create_table(
        "ent_studies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("study_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("consultant", sa.String(length=120), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "attachments",
            JSONB_TYPE,
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
        sa.Column(
            "metadata",
            JSONB_TYPE,
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
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
    )
    op.create_index("ix_ent_studies_project", "ent_studies", ["project_id"])
    op.create_index("ix_ent_studies_created_at", "ent_studies", ["created_at"])

    op.create_table(
        "ent_engagements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("organisation", sa.String(length=150), nullable=True),
        sa.Column("engagement_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("contact_email", sa.String(length=120), nullable=True),
        sa.Column("contact_phone", sa.String(length=40), nullable=True),
        sa.Column(
            "meetings",
            JSONB_TYPE,
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "metadata",
            JSONB_TYPE,
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
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
    )
    op.create_index("ix_ent_engagements_project", "ent_engagements", ["project_id"])
    op.create_index("ix_ent_engagements_created_at", "ent_engagements", ["created_at"])

    op.create_table(
        "ent_legal_instruments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("instrument_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("reference_code", sa.String(length=80), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column(
            "attachments",
            JSONB_TYPE,
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
        sa.Column(
            "metadata",
            JSONB_TYPE,
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
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
    )
    op.create_index(
        "ix_ent_legal_instruments_project",
        "ent_legal_instruments",
        ["project_id"],
    )
    op.create_index(
        "ix_ent_legal_instruments_created_at",
        "ent_legal_instruments",
        ["created_at"],
    )

    # Cast String columns to ENUM types per CODING_RULES.md Rule 1.2
    op.execute(
        "ALTER TABLE ent_approval_types ALTER COLUMN category TYPE ent_approval_category USING category::ent_approval_category"
    )
    op.execute(
        "ALTER TABLE ent_roadmap_items ALTER COLUMN status TYPE ent_roadmap_status USING status::ent_roadmap_status"
    )
    op.execute(
        "ALTER TABLE ent_studies ALTER COLUMN study_type TYPE ent_study_type USING study_type::ent_study_type"
    )
    op.execute(
        "ALTER TABLE ent_studies ALTER COLUMN status TYPE ent_study_status USING status::ent_study_status"
    )
    op.execute(
        "ALTER TABLE ent_engagements ALTER COLUMN engagement_type TYPE ent_engagement_type USING engagement_type::ent_engagement_type"
    )
    op.execute(
        "ALTER TABLE ent_engagements ALTER COLUMN status TYPE ent_engagement_status USING status::ent_engagement_status"
    )
    op.execute(
        "ALTER TABLE ent_legal_instruments ALTER COLUMN instrument_type TYPE ent_legal_instrument_type USING instrument_type::ent_legal_instrument_type"
    )
    op.execute(
        "ALTER TABLE ent_legal_instruments ALTER COLUMN status TYPE ent_legal_instrument_status USING status::ent_legal_instrument_status"
    )


def downgrade() -> None:
    """Rollback the migration."""

    op.execute("DROP INDEX IF EXISTS ix_ent_legal_instruments_created_at")
    op.execute("DROP INDEX IF EXISTS ix_ent_legal_instruments_project")
    op.execute("DROP TABLE IF EXISTS ent_legal_instruments CASCADE")

    op.execute("DROP INDEX IF EXISTS ix_ent_engagements_created_at")
    op.execute("DROP INDEX IF EXISTS ix_ent_engagements_project")
    op.execute("DROP TABLE IF EXISTS ent_engagements CASCADE")

    op.execute("DROP INDEX IF EXISTS ix_ent_studies_created_at")
    op.execute("DROP INDEX IF EXISTS ix_ent_studies_project")
    op.execute("DROP TABLE IF EXISTS ent_studies CASCADE")

    op.execute("DROP INDEX IF EXISTS idx_ent_roadmap_project_sequence")
    op.execute("DROP INDEX IF EXISTS ix_ent_roadmap_items_approval")
    op.execute("DROP INDEX IF EXISTS ix_ent_roadmap_items_project")
    op.execute("DROP TABLE IF EXISTS ent_roadmap_items CASCADE")

    op.execute("DROP INDEX IF EXISTS ix_ent_approval_types_created_at")
    op.execute("DROP INDEX IF EXISTS ix_ent_approval_types_authority")
    op.execute("DROP TABLE IF EXISTS ent_approval_types CASCADE")

    op.execute("DROP INDEX IF EXISTS ix_ent_authorities_created_at")
    op.execute("DROP INDEX IF EXISTS ix_ent_authorities_jurisdiction")
    op.execute("DROP TABLE IF EXISTS ent_authorities CASCADE")

    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS ent_legal_instrument_status")
    op.execute("DROP TYPE IF EXISTS ent_legal_instrument_type")
    op.execute("DROP TYPE IF EXISTS ent_engagement_status")
    op.execute("DROP TYPE IF EXISTS ent_engagement_type")
    op.execute("DROP TYPE IF EXISTS ent_study_status")
    op.execute("DROP TYPE IF EXISTS ent_study_type")
    op.execute("DROP TYPE IF EXISTS ent_roadmap_status")
    op.execute("DROP TYPE IF EXISTS ent_approval_category")
