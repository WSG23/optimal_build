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
    # Add asset_type ENUM type if it doesn't exist using raw SQL
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'deal_asset_type') THEN
                    CREATE TYPE deal_asset_type AS ENUM (
                        'office', 'retail', 'industrial', 'residential', 'mixed_use',
                        'hotel', 'warehouse', 'land', 'special_purpose', 'portfolio'
                    );
                END IF;
            END $$;
            """
        )
    )

    # Add asset_type column to agent_deals table using raw SQL
    op.execute(
        sa.text(
            """
            ALTER TABLE agent_deals
            ADD COLUMN IF NOT EXISTS asset_type deal_asset_type NOT NULL DEFAULT 'mixed_use'
            """
        )
    )

    # Create index on asset_type
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_agent_deals_asset_type ON agent_deals (asset_type)"
        )
    )


def downgrade() -> None:
    # Drop index (guarded)
    op.execute(sa.text("DROP INDEX IF EXISTS ix_agent_deals_asset_type"))

    # Drop column (guarded)
    op.execute(sa.text("ALTER TABLE agent_deals DROP COLUMN IF EXISTS asset_type"))

    # Drop ENUM type (guarded)
    op.execute(sa.text("DROP TYPE IF EXISTS deal_asset_type"))
