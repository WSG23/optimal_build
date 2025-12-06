"""Add listing integration tables for external providers."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20250220_000010"
down_revision = "20250220_000009"
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
                    SELECT 1 FROM pg_type WHERE typname = 'listing_provider'
                ) THEN
                    CREATE TYPE public.listing_provider AS ENUM ('propertyguru', 'edgeprop', 'zoho_crm');
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
                    SELECT 1 FROM pg_type WHERE typname = 'listing_account_status'
                ) THEN
                    CREATE TYPE public.listing_account_status AS ENUM ('connected', 'disconnected', 'revoked');
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
                    SELECT 1 FROM pg_type WHERE typname = 'listing_publication_status'
                ) THEN
                    CREATE TYPE public.listing_publication_status AS ENUM (
                        'draft', 'queued', 'published', 'failed', 'archived'
                    );
                END IF;
            END
            $$;
            """
        )
    )

    # Create tables using raw SQL (separate statements for asyncpg)
    op.execute(
        sa.text(
            """
            CREATE TABLE listing_integration_accounts (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                provider listing_provider NOT NULL,
                status listing_account_status NOT NULL DEFAULT 'connected',
                access_token TEXT,
                refresh_token TEXT,
                expires_at TIMESTAMP WITH TIME ZONE,
                metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                CONSTRAINT uq_listing_account_user_provider UNIQUE (user_id, provider)
            )
            """
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX ix_listing_accounts_user_id ON listing_integration_accounts(user_id)"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX ix_listing_accounts_provider_status ON listing_integration_accounts(provider, status)"
        )
    )

    op.execute(
        sa.text(
            """
            CREATE TABLE listing_publications (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
                account_id UUID NOT NULL REFERENCES listing_integration_accounts(id) ON DELETE CASCADE,
                provider_listing_id VARCHAR(128),
                status listing_publication_status NOT NULL DEFAULT 'draft',
                last_error TEXT,
                payload JSONB NOT NULL DEFAULT '{}'::jsonb,
                published_at TIMESTAMP WITH TIME ZONE,
                last_synced_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                CONSTRAINT uq_listing_publication_provider_ref UNIQUE (account_id, provider_listing_id)
            )
            """
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX ix_listing_publications_property_id ON listing_publications(property_id)"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX ix_listing_publications_account_id ON listing_publications(account_id)"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX ix_listing_publications_status ON listing_publications(status)"
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS listing_publications CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS listing_integration_accounts CASCADE"))
    op.execute(sa.text("DROP TYPE IF EXISTS listing_publication_status CASCADE"))
    op.execute(sa.text("DROP TYPE IF EXISTS listing_account_status CASCADE"))
    op.execute(sa.text("DROP TYPE IF EXISTS listing_provider CASCADE"))
