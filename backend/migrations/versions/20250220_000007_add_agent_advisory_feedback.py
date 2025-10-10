"""Add agent advisory feedback table."""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20250220_000007"
down_revision = "20241228_000006_add_commercial_property_agent_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_advisory_feedback",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("property_id", sa.String(length=36), nullable=False, index=True),
        sa.Column("submitted_by", sa.String(length=36), nullable=True),
        sa.Column("channel", sa.String(length=32), nullable=True),
        sa.Column("sentiment", sa.String(length=16), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("context", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["property_id"],
            ["properties.id"],
            name="fk_agent_advisory_feedback_property",
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_agent_advisory_feedback_property_id",
        "agent_advisory_feedback",
        ["property_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_agent_advisory_feedback_property_id",
        table_name="agent_advisory_feedback",
        if_exists=True,
    )
    op.drop_table("agent_advisory_feedback", if_exists=True)
