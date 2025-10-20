"""add_asset_type_to_agent_deals_manual

Revision ID: 4c8849dec050
Revises: 20251020_000016
Create Date: 2025-10-20 14:06:20.562705+00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4c8849dec050"
down_revision: Union[str, None] = "20251020_000016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add asset_type ENUM type if it doesn't exist
    op.execute(
        "DO $$ BEGIN CREATE TYPE deal_asset_type AS ENUM ('office', 'retail', 'industrial', 'residential', 'mixed_use', 'hotel', 'warehouse', 'land', 'special_purpose', 'portfolio'); EXCEPTION WHEN duplicate_object THEN null; END $$;"
    )

    # Add asset_type column to agent_deals table with a default value
    op.add_column(
        "agent_deals",
        sa.Column(
            "asset_type",
            sa.Enum(
                "office",
                "retail",
                "industrial",
                "residential",
                "mixed_use",
                "hotel",
                "warehouse",
                "land",
                "special_purpose",
                "portfolio",
                name="deal_asset_type",
                create_type=False,  # Type already created above
            ),
            nullable=False,
            server_default="mixed_use",
        ),
    )

    # Create index on asset_type
    op.create_index(
        op.f("ix_agent_deals_asset_type"), "agent_deals", ["asset_type"], unique=False
    )


def downgrade() -> None:
    # Drop index (guarded)
    op.execute("DROP INDEX IF EXISTS ix_agent_deals_asset_type")

    # Drop column (guarded)
    op.execute("ALTER TABLE agent_deals DROP COLUMN IF EXISTS asset_type")

    # Drop ENUM type (guarded)
    op.execute("DROP TYPE IF EXISTS deal_asset_type")
