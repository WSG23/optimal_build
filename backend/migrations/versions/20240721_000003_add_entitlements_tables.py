"""Add entitlement tracking tables."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20240721_000003"
down_revision = "20240626_000002"
branch_labels = None
depends_on = None


JSONB_TYPE = postgresql.JSONB(astext_type=sa.Text())

ENTITLEMENT_STATUS = sa.Enum(
    "planned",
    "in_progress",
    "submitted",
    "approved",
    "rejected",
    "on_hold",
    "archived",
    name="entitlement_status",
)

ENTITLEMENT_STUDY_TYPE = sa.Enum(
    "traffic",
    "environmental",
    "infrastructure",
    "heritage",
    "other",
    name="entitlement_study_type",
)

ENTITLEMENT_STAKEHOLDER_KIND = sa.Enum(
    "agency",
    "community",
    "political",
    "utility",
    "consultant",
    "other",
    name="entitlement_stakeholder_kind",
)

ENTITLEMENT_LEGAL_TYPE = sa.Enum(
    "agreement",
    "covenant",
    "ordinance",
    "policy",
    "license",
    "other",
    name="entitlement_legal_instrument_type",
)


def upgrade() -> None:
    """Apply the migration."""

    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"
    json_type = sa.JSON() if is_sqlite else JSONB_TYPE

    if not is_sqlite:
        ENTITLEMENT_STATUS.create(bind, checkfirst=True)
        ENTITLEMENT_STUDY_TYPE.create(bind, checkfirst=True)
        ENTITLEMENT_STAKEHOLDER_KIND.create(bind, checkfirst=True)
        ENTITLEMENT_LEGAL_TYPE.create(bind, checkfirst=True)

    op.create_table(
        "ent_authorities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False, unique=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("jurisdiction", sa.String(length=50), nullable=False, server_default="SG"),
        sa.Column("contact_email", sa.String(length=200), nullable=True),
        sa.Column(
            "metadata",
            json_type,
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_ent_authorities_jurisdiction", "ent_authorities", ["jurisdiction"])

    op.create_table(
        "ent_approval_types",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("authority_id", sa.Integer(), sa.ForeignKey("ent_authorities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("default_lead_time_days", sa.Integer(), nullable=True),
        sa.Column(
            "metadata",
            json_type,
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("authority_id", "code", name="uq_ent_approval_code"),
    )
    op.create_index("ix_ent_approval_types_authority", "ent_approval_types", ["authority_id"])

    op.create_table(
        "ent_roadmap_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("approval_type_id", sa.Integer(), sa.ForeignKey("ent_approval_types.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("status", ENTITLEMENT_STATUS, nullable=False, server_default="planned"),
        sa.Column("target_submission_date", sa.Date(), nullable=True),
        sa.Column("actual_submission_date", sa.Date(), nullable=True),
        sa.Column("decision_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "attachments",
            json_type,
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
        sa.Column(
            "metadata",
            json_type,
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("project_id", "sequence", name="uq_ent_roadmap_sequence"),
    )
    op.create_index("ix_ent_roadmap_project", "ent_roadmap_items", ["project_id"])
    op.create_index("ix_ent_roadmap_status", "ent_roadmap_items", ["status"])

    op.create_table(
        "ent_studies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("study_type", ENTITLEMENT_STUDY_TYPE, nullable=False),
        sa.Column("status", ENTITLEMENT_STATUS, nullable=False, server_default="planned"),
        sa.Column("consultant", sa.String(length=200), nullable=True),
        sa.Column("submission_date", sa.Date(), nullable=True),
        sa.Column("approval_date", sa.Date(), nullable=True),
        sa.Column("report_uri", sa.String(length=500), nullable=True),
        sa.Column(
            "findings",
            json_type,
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column(
            "metadata",
            json_type,
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_ent_studies_project", "ent_studies", ["project_id"])
    op.create_index("ix_ent_studies_status", "ent_studies", ["status"])
    op.create_index("ix_ent_studies_type", "ent_studies", ["study_type"])

    op.create_table(
        "ent_engagements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("stakeholder_name", sa.String(length=200), nullable=False),
        sa.Column("stakeholder_type", ENTITLEMENT_STAKEHOLDER_KIND, nullable=False),
        sa.Column("status", ENTITLEMENT_STATUS, nullable=False, server_default="planned"),
        sa.Column("contact_email", sa.String(length=200), nullable=True),
        sa.Column("meeting_date", sa.Date(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column(
            "next_steps",
            json_type,
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
        sa.Column(
            "metadata",
            json_type,
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_ent_engagements_project", "ent_engagements", ["project_id"])
    op.create_index("ix_ent_engagements_status", "ent_engagements", ["status"])

    op.create_table(
        "ent_legal_instruments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("instrument_type", ENTITLEMENT_LEGAL_TYPE, nullable=False),
        sa.Column("status", ENTITLEMENT_STATUS, nullable=False, server_default="planned"),
        sa.Column("reference_code", sa.String(length=100), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("storage_uri", sa.String(length=500), nullable=True),
        sa.Column(
            "attachments",
            json_type,
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
        sa.Column(
            "metadata",
            json_type,
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_ent_legal_project", "ent_legal_instruments", ["project_id"])
    op.create_index("ix_ent_legal_status", "ent_legal_instruments", ["status"])


def downgrade() -> None:
    """Revert the migration."""

    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"

    op.drop_index("ix_ent_legal_status", table_name="ent_legal_instruments")
    op.drop_index("ix_ent_legal_project", table_name="ent_legal_instruments")
    op.drop_table("ent_legal_instruments")

    op.drop_index("ix_ent_engagements_status", table_name="ent_engagements")
    op.drop_index("ix_ent_engagements_project", table_name="ent_engagements")
    op.drop_table("ent_engagements")

    op.drop_index("ix_ent_studies_type", table_name="ent_studies")
    op.drop_index("ix_ent_studies_status", table_name="ent_studies")
    op.drop_index("ix_ent_studies_project", table_name="ent_studies")
    op.drop_table("ent_studies")

    op.drop_index("ix_ent_roadmap_status", table_name="ent_roadmap_items")
    op.drop_index("ix_ent_roadmap_project", table_name="ent_roadmap_items")
    op.drop_table("ent_roadmap_items")

    op.drop_index("ix_ent_approval_types_authority", table_name="ent_approval_types")
    op.drop_table("ent_approval_types")

    op.drop_index("ix_ent_authorities_jurisdiction", table_name="ent_authorities")
    op.drop_table("ent_authorities")

    if not is_sqlite:
        ENTITLEMENT_LEGAL_TYPE.drop(bind, checkfirst=True)
        ENTITLEMENT_STAKEHOLDER_KIND.drop(bind, checkfirst=True)
        ENTITLEMENT_STUDY_TYPE.drop(bind, checkfirst=True)
        ENTITLEMENT_STATUS.drop(bind, checkfirst=True)
