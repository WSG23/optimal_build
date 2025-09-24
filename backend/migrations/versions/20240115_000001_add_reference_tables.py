"""Add reference material, cost, and monitoring tables (patched)"""

from alembic import op
from sqlalchemy.dialects import postgresql

import sqlalchemy as sa

revision = "20240115_000001"
down_revision = "20240711_000000"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'ref_material_standards'
                  AND column_name = 'standard_body'
            ) THEN
                ALTER TABLE ref_material_standards
                ADD COLUMN standard_body VARCHAR(100) DEFAULT 'UNKNOWN' NOT NULL;
            END IF;
        END$$;
        """
    )


def downgrade():
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'ref_material_standards'
                  AND column_name = 'standard_body'
            ) THEN
                ALTER TABLE ref_material_standards
                DROP COLUMN standard_body;
            END IF;
        END$$;
        """
    )
