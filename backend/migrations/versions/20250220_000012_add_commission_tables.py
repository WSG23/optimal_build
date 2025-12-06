"""Add commission ledger tables for agent performance."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20250220_000012"
down_revision = "20250220_000011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ENUM types using raw SQL to avoid SQLAlchemy auto-creation issues
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'commission_type') THEN
                    CREATE TYPE commission_type AS ENUM (
                        'introducer', 'exclusive', 'co_broke', 'referral', 'bonus'
                    );
                END IF;
            END $$;
            """
        )
    )
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'commission_status') THEN
                    CREATE TYPE commission_status AS ENUM (
                        'pending', 'confirmed', 'invoiced', 'paid', 'disputed', 'written_off'
                    );
                END IF;
            END $$;
            """
        )
    )
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'commission_adjustment_type') THEN
                    CREATE TYPE commission_adjustment_type AS ENUM (
                        'clawback', 'bonus', 'correction'
                    );
                END IF;
            END $$;
            """
        )
    )

    # Create agent_commission_records table
    op.execute(
        sa.text(
            """
            CREATE TABLE agent_commission_records (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                deal_id UUID NOT NULL REFERENCES agent_deals(id) ON DELETE CASCADE,
                agent_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                commission_type commission_type NOT NULL,
                status commission_status NOT NULL DEFAULT 'pending',
                basis_amount NUMERIC(16, 2),
                basis_currency VARCHAR(3) NOT NULL DEFAULT 'SGD',
                commission_rate NUMERIC(5, 4),
                commission_amount NUMERIC(16, 2),
                introduced_at TIMESTAMP WITH TIME ZONE,
                confirmed_at TIMESTAMP WITH TIME ZONE,
                invoiced_at TIMESTAMP WITH TIME ZONE,
                paid_at TIMESTAMP WITH TIME ZONE,
                disputed_at TIMESTAMP WITH TIME ZONE,
                resolved_at TIMESTAMP WITH TIME ZONE,
                metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                audit_log_id INTEGER REFERENCES audit_logs(id) ON DELETE SET NULL,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                CONSTRAINT uq_agent_commission_unique_type UNIQUE (deal_id, agent_id, commission_type)
            )
            """
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX ix_agent_commission_records_deal_status ON agent_commission_records (deal_id, status)"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX ix_agent_commission_records_agent_status ON agent_commission_records (agent_id, status)"
        )
    )

    # Create agent_commission_adjustments table
    op.execute(
        sa.text(
            """
            CREATE TABLE agent_commission_adjustments (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                commission_id UUID NOT NULL REFERENCES agent_commission_records(id) ON DELETE CASCADE,
                adjustment_type commission_adjustment_type NOT NULL,
                amount NUMERIC(16, 2),
                currency VARCHAR(3) NOT NULL DEFAULT 'SGD',
                note TEXT,
                recorded_by UUID REFERENCES users(id) ON DELETE SET NULL,
                recorded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                audit_log_id INTEGER REFERENCES audit_logs(id) ON DELETE SET NULL,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
            )
            """
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX ix_agent_commission_adjustments_type ON agent_commission_adjustments (adjustment_type)"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX ix_agent_commission_adjustments_recorded_at ON agent_commission_adjustments (recorded_at)"
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS agent_commission_adjustments CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS agent_commission_records CASCADE"))
    op.execute(sa.text("DROP TYPE IF EXISTS commission_adjustment_type CASCADE"))
    op.execute(sa.text("DROP TYPE IF EXISTS commission_status CASCADE"))
    op.execute(sa.text("DROP TYPE IF EXISTS commission_type CASCADE"))
