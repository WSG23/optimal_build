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


LISTING_PROVIDER_ENUM = sa.Enum(
    "propertyguru",
    "edgeprop",
    "zoho_crm",
    name="listing_provider",
    create_type=False,
)

ACCOUNT_STATUS_ENUM = sa.Enum(
    "connected",
    "disconnected",
    "revoked",
    name="listing_account_status",
    create_type=False,
)

PUBLICATION_STATUS_ENUM = sa.Enum(
    "draft",
    "queued",
    "published",
    "failed",
    "archived",
    name="listing_publication_status",
    create_type=False,
)


def upgrade() -> None:
    # Recreate enums defensively so the migration is idempotent if partially applied.
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1
                    FROM pg_type t
                    JOIN pg_namespace n ON n.oid = t.typnamespace
                    WHERE t.typname = 'listing_provider'
                      AND n.nspname = 'public'
                ) THEN
                    DROP TYPE public.listing_provider CASCADE;
                END IF;
                CREATE TYPE public.listing_provider AS ENUM ('propertyguru', 'edgeprop', 'zoho_crm');
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
                IF EXISTS (
                    SELECT 1
                    FROM pg_type t
                    JOIN pg_namespace n ON n.oid = t.typnamespace
                    WHERE t.typname = 'listing_account_status'
                      AND n.nspname = 'public'
                ) THEN
                    DROP TYPE public.listing_account_status CASCADE;
                END IF;
                CREATE TYPE public.listing_account_status AS ENUM ('connected', 'disconnected', 'revoked');
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
                IF EXISTS (
                    SELECT 1
                    FROM pg_type t
                    JOIN pg_namespace n ON n.oid = t.typnamespace
                    WHERE t.typname = 'listing_publication_status'
                      AND n.nspname = 'public'
                ) THEN
                    DROP TYPE public.listing_publication_status CASCADE;
                END IF;
                CREATE TYPE public.listing_publication_status AS ENUM (
                    'draft', 'queued', 'published', 'failed', 'archived'
                );
            END
            $$;
            """
        )
    )

    op.create_table(
        "listing_integration_accounts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("provider", LISTING_PROVIDER_ENUM, nullable=False),
        sa.Column(
            "status",
            ACCOUNT_STATUS_ENUM,
            nullable=False,
            server_default="connected",
        ),
        sa.Column("access_token", sa.Text(), nullable=True),
        sa.Column("refresh_token", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "metadata",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
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
            onupdate=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "user_id", "provider", name="uq_listing_account_user_provider"
        ),
    )
    op.create_index(
        "ix_listing_accounts_provider_status",
        "listing_integration_accounts",
        ["provider", "status"],
    )

    op.create_table(
        "listing_publications",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "property_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("properties.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("listing_integration_accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider_listing_id", sa.String(length=128), nullable=True),
        sa.Column(
            "status",
            PUBLICATION_STATUS_ENUM,
            nullable=False,
            server_default="draft",
        ),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column(
            "payload",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
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
            onupdate=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "account_id",
            "provider_listing_id",
            name="uq_listing_publication_provider_ref",
        ),
    )
    op.create_index(
        "ix_listing_publications_status",
        "listing_publications",
        ["status"],
    )
    op.create_index(
        "ix_listing_publications_account_id",
        "listing_publications",
        ["account_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_listing_publications_status",
        table_name="listing_publications",
        if_exists=True,
    )
    op.drop_index(
        "ix_listing_publications_account_id",
        table_name="listing_publications",
        if_exists=True,
    )
    op.drop_table("listing_publications", if_exists=True)

    op.drop_index(
        "ix_listing_accounts_provider_status",
        table_name="listing_integration_accounts",
        if_exists=True,
    )
    op.drop_table("listing_integration_accounts", if_exists=True)

    PUBLICATION_STATUS_ENUM.drop(op.get_bind(), checkfirst=True)
    ACCOUNT_STATUS_ENUM.drop(op.get_bind(), checkfirst=True)
    LISTING_PROVIDER_ENUM.drop(op.get_bind(), checkfirst=True)
