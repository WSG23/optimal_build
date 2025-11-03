"""fix legacy propertytype enum

Revision ID: 20251104_000022
Revises: 20251104_000021
Create Date: 2025-11-04 22:30:00.000000

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20251104_000022"
down_revision: Union[str, None] = "20251104_000021"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PROPERTY_TYPE_VALUES = (
    "office",
    "retail",
    "industrial",
    "residential",
    "mixed_use",
    "hotel",
    "warehouse",
    "land",
    "special_purpose",
)


def upgrade() -> None:
    connection = op.get_bind()

    # Ensure the canonical property_type enum exists
    connection.exec_driver_sql(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_type WHERE typname = 'property_type'
            ) THEN
                CREATE TYPE property_type AS ENUM (
                    'office',
                    'retail',
                    'industrial',
                    'residential',
                    'mixed_use',
                    'hotel',
                    'warehouse',
                    'land',
                    'special_purpose'
                );
            END IF;
        END$$;
        """
    )

    # Migrate any legacy columns that still reference propertytype -> property_type
    connection.exec_driver_sql(
        """
        DO $$
        DECLARE
            rec record;
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'propertytype') THEN
                FOR rec IN
                    SELECT table_schema, table_name, column_name
                    FROM information_schema.columns
                    WHERE udt_name = 'propertytype'
                LOOP
                    EXECUTE format(
                        'ALTER TABLE %I.%I ALTER COLUMN %I TYPE text USING %I::text',
                        rec.table_schema,
                        rec.table_name,
                        rec.column_name,
                        rec.column_name
                    );
                    EXECUTE format(
                        'ALTER TABLE %I.%I ALTER COLUMN %I TYPE property_type USING %I::property_type',
                        rec.table_schema,
                        rec.table_name,
                        rec.column_name,
                        rec.column_name
                    );
                END LOOP;

                DROP TYPE propertytype;
            END IF;
        END$$;
        """
    )


def downgrade() -> None:
    connection = op.get_bind()

    # Recreate legacy enum if needed and revert columns back to propertytype
    connection.exec_driver_sql(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'propertytype') THEN
                CREATE TYPE propertytype AS ENUM (
                    'office',
                    'retail',
                    'industrial',
                    'residential',
                    'mixed_use',
                    'hotel',
                    'warehouse',
                    'land',
                    'special_purpose'
                );
            END IF;
        END$$;
        """
    )

    connection.exec_driver_sql(
        """
        DO $$
        DECLARE
            rec record;
        BEGIN
            FOR rec IN
                SELECT table_schema, table_name, column_name
                FROM information_schema.columns
                WHERE udt_name = 'property_type'
            LOOP
                EXECUTE format(
                    'ALTER TABLE %I.%I ALTER COLUMN %I TYPE text USING %I::text',
                    rec.table_schema,
                    rec.table_name,
                    rec.column_name,
                    rec.column_name
                );
                EXECUTE format(
                    'ALTER TABLE %I.%I ALTER COLUMN %I TYPE propertytype USING %I::propertytype',
                    rec.table_schema,
                    rec.table_name,
                    rec.column_name,
                    rec.column_name
                );
            END LOOP;

            -- Only drop property_type if it exists (it may still be referenced elsewhere)
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'property_type') THEN
                DROP TYPE property_type;
            END IF;
        END$$;
        """
    )
