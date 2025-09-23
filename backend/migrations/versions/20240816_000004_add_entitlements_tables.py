"""Create entitlement tracking tables."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20240816_000004"
down_revision = "20240801_000003"
branch_labels = None
depends_on = None


JSONB_TYPE = postgresql.JSONB(astext_type=sa.Text())


APPROVAL_CATEGORY_ENUM = postgresql.ENUM('planning', 'building', 'environmental', 'transport', 'utilities', name='ent_approval_category', create_type=False)

ROADMAP_STATUS_ENUM = postgresql.ENUM('planned', 'in_progress', 'submitted', 'approved', 'rejected', 'blocked', 'complete', name='ent_roadmap_status', create_type=False)

STUDY_TYPE_ENUM = postgresql.ENUM('traffic', 'environmental', 'heritage', 'utilities', 'community', name='ent_study_type', create_type=False)

STUDY_STATUS_ENUM = postgresql.ENUM('draft', 'scope_defined', 'in_progress', 'submitted', 'accepted', 'rejected', name='ent_study_status', create_type=False)

ENGAGEMENT_TYPE_ENUM = postgresql.ENUM('agency', 'community', 'political', 'private_partner', 'regulator', name='ent_engagement_type', create_type=False)

ENGAGEMENT_STATUS_ENUM = postgresql.ENUM('planned', 'active', 'completed', 'blocked', name='ent_engagement_status', create_type=False)

LEGAL_INSTRUMENT_TYPE_ENUM = postgresql.ENUM('agreement', 'licence', 'memorandum', 'waiver', 'variation', name='ent_legal_instrument_type', create_type=False)

LEGAL_INSTRUMENT_STATUS_ENUM = postgresql.ENUM('draft', 'in_review', 'executed', 'expired', name='ent_legal_instrument_status', create_type=False)


def _create_enum(enum: sa.Enum) -> None:
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":  # SQLite does not create dedicated enum types
        enum.create(bind, checkfirst=True)


def _drop_enum(enum: sa.Enum) -> None:
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        enum.drop(bind, checkfirst=True)


def upgrade() -> None:
    """Apply the migration."""


    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ent_approval_category') THEN
                CREATE TYPE ent_approval_category AS ENUM ('planning','building','environmental','transport','utilities');
            END IF;
        END$$;
        """
    )

    for enum in (
        APPROVAL_CATEGORY_ENUM,
        ROADMAP_STATUS_ENUM,
        STUDY_TYPE_ENUM,
        STUDY_STATUS_ENUM,
        ENGAGEMENT_TYPE_ENUM,
        ENGAGEMENT_STATUS_ENUM,
        LEGAL_INSTRUMENT_TYPE_ENUM,
        LEGAL_INSTRUMENT_STATUS_ENUM,
    ):
        _create_enum(enum)

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
        sa.Column("category", APPROVAL_CATEGORY_ENUM, nullable=False),
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
        sa.Column("status", ROADMAP_STATUS_ENUM, nullable=False),
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
        sa.Column("study_type", STUDY_TYPE_ENUM, nullable=False),
        sa.Column("status", STUDY_STATUS_ENUM, nullable=False),
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
        sa.Column("engagement_type", ENGAGEMENT_TYPE_ENUM, nullable=False),
        sa.Column("status", ENGAGEMENT_STATUS_ENUM, nullable=False),
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
        sa.Column("instrument_type", LEGAL_INSTRUMENT_TYPE_ENUM, nullable=False),
        sa.Column("status", LEGAL_INSTRUMENT_STATUS_ENUM, nullable=False),
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

    for enum in (
        LEGAL_INSTRUMENT_STATUS_ENUM,
        LEGAL_INSTRUMENT_TYPE_ENUM,
        ENGAGEMENT_STATUS_ENUM,
        ENGAGEMENT_TYPE_ENUM,
        STUDY_STATUS_ENUM,
        STUDY_TYPE_ENUM,
        ROADMAP_STATUS_ENUM,
        APPROVAL_CATEGORY_ENUM,
    ):
        _drop_enum(enum)

