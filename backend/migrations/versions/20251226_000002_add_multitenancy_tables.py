"""Add multi-tenancy tables for organization/workspace isolation.

Creates:
- organizations: Top-level tenant container
- organization_members: User membership in organizations
- organization_invitations: Pending invitations to organizations

Also adds:
- organization_id to projects table (nullable for backwards compatibility)
- primary_organization_id to users table

Revision ID: 20251226_000002
Revises: 20251226_000001
Create Date: 2025-12-26
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = "20251226_000002"
down_revision = "20251226_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create organization_plan enum
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'organizationplan') THEN
                CREATE TYPE organizationplan AS ENUM (
                    'free',
                    'starter',
                    'professional',
                    'enterprise'
                );
            END IF;
        END $$;
        """
    )

    # Create organization_role enum
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'organizationrole') THEN
                CREATE TYPE organizationrole AS ENUM (
                    'owner',
                    'admin',
                    'member',
                    'viewer'
                );
            END IF;
        END $$;
        """
    )

    # Create organizations table
    op.create_table(
        "organizations",
        sa.Column("id", UUID(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("plan", sa.String(20), nullable=False, server_default="free"),
        sa.Column("settings", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("uen_number", sa.String(50), nullable=True),  # Singapore UEN
    )

    # Create indexes for organizations
    op.create_index("ix_organizations_slug", "organizations", ["slug"])
    op.create_index("ix_organizations_is_active", "organizations", ["is_active"])

    # Create organization_members table
    op.create_table(
        "organization_members",
        sa.Column("id", UUID(), primary_key=True),
        sa.Column("organization_id", UUID(), nullable=False),
        sa.Column("user_id", UUID(), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="member"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "joined_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
    )

    # Add foreign keys for organization_members
    op.create_foreign_key(
        "fk_organization_members_organization_id",
        "organization_members",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_organization_members_user_id",
        "organization_members",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Create indexes for organization_members
    op.create_index(
        "ix_organization_members_org_id", "organization_members", ["organization_id"]
    )
    op.create_index(
        "ix_organization_members_user_id", "organization_members", ["user_id"]
    )
    op.create_index(
        "ix_organization_members_active",
        "organization_members",
        ["organization_id", "is_active"],
    )

    # Create unique constraint for organization_members
    op.create_unique_constraint(
        "uq_org_member",
        "organization_members",
        ["organization_id", "user_id"],
    )

    # Create organization_invitations table
    op.create_table(
        "organization_invitations",
        sa.Column("id", UUID(), primary_key=True),
        sa.Column("organization_id", UUID(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="member"),
        sa.Column("token", sa.String(100), nullable=False, unique=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("invited_by", UUID(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("accepted_at", sa.DateTime(), nullable=True),
    )

    # Add foreign keys for organization_invitations
    op.create_foreign_key(
        "fk_organization_invitations_organization_id",
        "organization_invitations",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_organization_invitations_invited_by",
        "organization_invitations",
        "users",
        ["invited_by"],
        ["id"],
    )

    # Create indexes for organization_invitations
    op.create_index(
        "ix_organization_invitations_org_id",
        "organization_invitations",
        ["organization_id"],
    )
    op.create_index(
        "ix_organization_invitations_email_status",
        "organization_invitations",
        ["email", "status"],
    )
    op.create_index(
        "ix_organization_invitations_token", "organization_invitations", ["token"]
    )

    # Add organization_id to projects table
    op.add_column(
        "projects",
        sa.Column("organization_id", UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_projects_organization_id",
        "projects",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_projects_organization_id", "projects", ["organization_id"])

    # Add primary_organization_id to users table
    op.add_column(
        "users",
        sa.Column("primary_organization_id", UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_users_primary_organization_id",
        "users",
        "organizations",
        ["primary_organization_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_users_primary_organization_id", "users", ["primary_organization_id"]
    )


def downgrade() -> None:
    # Remove columns from users (guarded)
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_users_primary_organization_id') THEN
                DROP INDEX ix_users_primary_organization_id;
            END IF;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name = 'fk_users_primary_organization_id') THEN
                ALTER TABLE users DROP CONSTRAINT fk_users_primary_organization_id;
            END IF;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'primary_organization_id') THEN
                ALTER TABLE users DROP COLUMN primary_organization_id;
            END IF;
        END $$;
        """
    )

    # Remove columns from projects (guarded)
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_projects_organization_id') THEN
                DROP INDEX ix_projects_organization_id;
            END IF;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name = 'fk_projects_organization_id') THEN
                ALTER TABLE projects DROP CONSTRAINT fk_projects_organization_id;
            END IF;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'projects' AND column_name = 'organization_id') THEN
                ALTER TABLE projects DROP COLUMN organization_id;
            END IF;
        END $$;
        """
    )

    # Drop organization_invitations table (guarded)
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_organization_invitations_token') THEN
                DROP INDEX ix_organization_invitations_token;
            END IF;
            IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_organization_invitations_email_status') THEN
                DROP INDEX ix_organization_invitations_email_status;
            END IF;
            IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_organization_invitations_org_id') THEN
                DROP INDEX ix_organization_invitations_org_id;
            END IF;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name = 'fk_organization_invitations_invited_by') THEN
                ALTER TABLE organization_invitations DROP CONSTRAINT fk_organization_invitations_invited_by;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name = 'fk_organization_invitations_organization_id') THEN
                ALTER TABLE organization_invitations DROP CONSTRAINT fk_organization_invitations_organization_id;
            END IF;
        END $$;
        """
    )
    op.execute("DROP TABLE IF EXISTS organization_invitations")

    # Drop organization_members table (guarded)
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name = 'uq_org_member') THEN
                ALTER TABLE organization_members DROP CONSTRAINT uq_org_member;
            END IF;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_organization_members_active') THEN
                DROP INDEX ix_organization_members_active;
            END IF;
            IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_organization_members_user_id') THEN
                DROP INDEX ix_organization_members_user_id;
            END IF;
            IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_organization_members_org_id') THEN
                DROP INDEX ix_organization_members_org_id;
            END IF;
        END $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name = 'fk_organization_members_user_id') THEN
                ALTER TABLE organization_members DROP CONSTRAINT fk_organization_members_user_id;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name = 'fk_organization_members_organization_id') THEN
                ALTER TABLE organization_members DROP CONSTRAINT fk_organization_members_organization_id;
            END IF;
        END $$;
        """
    )
    op.execute("DROP TABLE IF EXISTS organization_members")

    # Drop organizations table (guarded)
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_organizations_is_active') THEN
                DROP INDEX ix_organizations_is_active;
            END IF;
            IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_organizations_slug') THEN
                DROP INDEX ix_organizations_slug;
            END IF;
        END $$;
        """
    )
    op.execute("DROP TABLE IF EXISTS organizations")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS organizationrole")
    op.execute("DROP TYPE IF EXISTS organizationplan")
