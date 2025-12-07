"""Add notifications table for Phase 2E.

Revision ID: 20251207_000037
Revises: 20251207_000036
Create Date: 2025-12-07
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers
revision = "20251207_000037"
down_revision = "20251207_000036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ENUM types for notification_type and notification_priority
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE notification_type AS ENUM (
                'team_invitation',
                'team_member_joined',
                'team_member_removed',
                'workflow_created',
                'workflow_step_assigned',
                'workflow_step_completed',
                'workflow_completed',
                'workflow_approval_needed',
                'workflow_rejected',
                'project_update',
                'project_milestone',
                'regulatory_status_change',
                'regulatory_rfi',
                'system_announcement'
            );
        EXCEPTION WHEN duplicate_object THEN
            NULL;
        END $$;
    """
    )

    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE notification_priority AS ENUM (
                'low',
                'normal',
                'high',
                'urgent'
            );
        EXCEPTION WHEN duplicate_object THEN
            NULL;
        END $$;
    """
    )

    # Create notifications table
    op.create_table(
        "notifications",
        sa.Column("id", UUID(), primary_key=True),
        sa.Column("user_id", UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "notification_type",
            sa.String(50),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "priority",
            sa.String(20),
            nullable=False,
            server_default="normal",
        ),
        sa.Column("project_id", UUID(), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("related_entity_type", sa.String(50), nullable=True),
        sa.Column("related_entity_id", UUID(), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
    )

    # Create indexes for efficient querying
    op.create_index(
        "ix_notifications_user_id",
        "notifications",
        ["user_id"],
    )
    op.create_index(
        "ix_notifications_notification_type",
        "notifications",
        ["notification_type"],
    )
    op.create_index(
        "ix_notifications_project_id",
        "notifications",
        ["project_id"],
    )
    op.create_index(
        "ix_notifications_is_read",
        "notifications",
        ["is_read"],
    )
    op.create_index(
        "ix_notifications_created_at",
        "notifications",
        ["created_at"],
    )
    # Composite index for common query pattern
    op.create_index(
        "ix_notifications_user_unread",
        "notifications",
        ["user_id", "is_read", "created_at"],
    )


def downgrade() -> None:
    # Guard drop statements to avoid errors if objects don't exist
    op.execute(
        """
        DROP INDEX IF EXISTS ix_notifications_user_unread;
        DROP INDEX IF EXISTS ix_notifications_created_at;
        DROP INDEX IF EXISTS ix_notifications_is_read;
        DROP INDEX IF EXISTS ix_notifications_project_id;
        DROP INDEX IF EXISTS ix_notifications_notification_type;
        DROP INDEX IF EXISTS ix_notifications_user_id;
        DROP TABLE IF EXISTS notifications;
        DROP TYPE IF EXISTS notification_priority;
        DROP TYPE IF EXISTS notification_type;
    """
    )
