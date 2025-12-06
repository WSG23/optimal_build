"""Add agent business performance tables for deal pipeline foundation."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20250220_000011"
down_revision = "20250220_000010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enums using raw SQL to avoid SQLAlchemy auto-creation issues
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_type WHERE typname = 'deal_asset_type'
                ) THEN
                    CREATE TYPE public.deal_asset_type AS ENUM (
                        'office', 'retail', 'industrial', 'residential', 'mixed_use',
                        'hotel', 'warehouse', 'land', 'special_purpose', 'portfolio'
                    );
                END IF;
            END
            $$;
            """
        )
    )
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_type WHERE typname = 'deal_type'
                ) THEN
                    CREATE TYPE public.deal_type AS ENUM (
                        'buy_side', 'sell_side', 'lease', 'management', 'capital_raise', 'other'
                    );
                END IF;
            END
            $$;
            """
        )
    )
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_type WHERE typname = 'pipeline_stage'
                ) THEN
                    CREATE TYPE public.pipeline_stage AS ENUM (
                        'lead_captured', 'qualification', 'needs_analysis', 'proposal',
                        'negotiation', 'agreement', 'due_diligence', 'awaiting_closure',
                        'closed_won', 'closed_lost'
                    );
                END IF;
            END
            $$;
            """
        )
    )
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_type WHERE typname = 'deal_status'
                ) THEN
                    CREATE TYPE public.deal_status AS ENUM (
                        'open', 'closed_won', 'closed_lost', 'cancelled'
                    );
                END IF;
            END
            $$;
            """
        )
    )
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_type WHERE typname = 'deal_contact_type'
                ) THEN
                    CREATE TYPE public.deal_contact_type AS ENUM (
                        'principal', 'co_broke', 'legal', 'finance', 'other'
                    );
                END IF;
            END
            $$;
            """
        )
    )
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_type WHERE typname = 'deal_document_type'
                ) THEN
                    CREATE TYPE public.deal_document_type AS ENUM (
                        'loi', 'valuation', 'agreement', 'financials', 'other'
                    );
                END IF;
            END
            $$;
            """
        )
    )

    # Create agent_deals table
    op.execute(
        sa.text(
            """
            CREATE TABLE agent_deals (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                agent_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
                property_id UUID REFERENCES properties(id) ON DELETE SET NULL,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                asset_type deal_asset_type NOT NULL,
                deal_type deal_type NOT NULL,
                pipeline_stage pipeline_stage NOT NULL DEFAULT 'lead_captured',
                status deal_status NOT NULL DEFAULT 'open',
                lead_source VARCHAR(120),
                estimated_value_amount NUMERIC(16, 2),
                estimated_value_currency VARCHAR(3) NOT NULL DEFAULT 'SGD',
                expected_close_date DATE,
                actual_close_date DATE,
                confidence NUMERIC(5, 4),
                metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
            )
            """
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX ix_agent_deals_agent_stage ON agent_deals(agent_id, pipeline_stage)"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX ix_agent_deals_status_created ON agent_deals(status, created_at)"
        )
    )
    op.execute(
        sa.text("CREATE INDEX ix_agent_deals_project_id ON agent_deals(project_id)")
    )
    op.execute(
        sa.text("CREATE INDEX ix_agent_deals_property_id ON agent_deals(property_id)")
    )

    # Create agent_deal_stage_events table
    op.execute(
        sa.text(
            """
            CREATE TABLE agent_deal_stage_events (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                deal_id UUID NOT NULL REFERENCES agent_deals(id) ON DELETE CASCADE,
                from_stage pipeline_stage,
                to_stage pipeline_stage NOT NULL,
                changed_by UUID REFERENCES users(id) ON DELETE SET NULL,
                note TEXT,
                recorded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                metadata JSONB NOT NULL DEFAULT '{}'::jsonb
            )
            """
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX ix_agent_deal_stage_events_deal_id ON agent_deal_stage_events(deal_id)"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX ix_agent_deal_stage_events_stage_time ON agent_deal_stage_events(to_stage, recorded_at)"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX ix_agent_deal_stage_events_changed_by ON agent_deal_stage_events(changed_by)"
        )
    )

    # Create agent_deal_contacts table
    op.execute(
        sa.text(
            """
            CREATE TABLE agent_deal_contacts (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                deal_id UUID NOT NULL REFERENCES agent_deals(id) ON DELETE CASCADE,
                contact_type deal_contact_type NOT NULL,
                name VARCHAR(200) NOT NULL,
                email VARCHAR(255),
                phone VARCHAR(50),
                company VARCHAR(200),
                notes TEXT,
                metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
            )
            """
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX ix_agent_deal_contacts_deal_id ON agent_deal_contacts(deal_id)"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX ix_agent_deal_contacts_type ON agent_deal_contacts(contact_type)"
        )
    )

    # Create agent_deal_documents table
    op.execute(
        sa.text(
            """
            CREATE TABLE agent_deal_documents (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                deal_id UUID NOT NULL REFERENCES agent_deals(id) ON DELETE CASCADE,
                document_type deal_document_type NOT NULL,
                title VARCHAR(200) NOT NULL,
                uri VARCHAR(500) NOT NULL,
                mime_type VARCHAR(120),
                uploaded_by UUID REFERENCES users(id) ON DELETE SET NULL,
                uploaded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                CONSTRAINT uq_agent_deal_document_title UNIQUE (deal_id, title)
            )
            """
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX ix_agent_deal_documents_deal_id ON agent_deal_documents(deal_id)"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX ix_agent_deal_documents_type ON agent_deal_documents(document_type)"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX ix_agent_deal_documents_uploaded_by ON agent_deal_documents(uploaded_by)"
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS agent_deal_documents CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS agent_deal_contacts CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS agent_deal_stage_events CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS agent_deals CASCADE"))
    op.execute(sa.text("DROP TYPE IF EXISTS deal_document_type CASCADE"))
    op.execute(sa.text("DROP TYPE IF EXISTS deal_contact_type CASCADE"))
    op.execute(sa.text("DROP TYPE IF EXISTS deal_status CASCADE"))
    op.execute(sa.text("DROP TYPE IF EXISTS pipeline_stage CASCADE"))
    op.execute(sa.text("DROP TYPE IF EXISTS deal_type CASCADE"))
    op.execute(sa.text("DROP TYPE IF EXISTS deal_asset_type CASCADE"))
