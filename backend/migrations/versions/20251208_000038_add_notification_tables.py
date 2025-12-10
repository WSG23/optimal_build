"""Add notification and email_logs tables.

Revision ID: 20251208_000038
Revises: 20251207_000037
Create Date: 2025-12-08
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import inspect

revision = "20251208_000038"
down_revision = "20251207_000037"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create notification_type enum (using DO $$ for safety)
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'notificationtype') THEN
                CREATE TYPE notificationtype AS ENUM (
                    'team_invite',
                    'team_invite_accepted',
                    'team_member_joined',
                    'team_member_left',
                    'workflow_created',
                    'workflow_approval_pending',
                    'workflow_approved',
                    'workflow_rejected',
                    'workflow_step_completed',
                    'submission_status_changed',
                    'submission_approved',
                    'submission_rejected',
                    'submission_rfi',
                    'system',
                    'reminder'
                );
            END IF;
        END$$;
    """
    )

    # Create notification_priority enum
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'notificationpriority') THEN
                CREATE TYPE notificationpriority AS ENUM (
                    'low',
                    'normal',
                    'high',
                    'urgent'
                );
            END IF;
        END$$;
    """
    )

    # Create notifications table
    op.create_table(
        "notifications",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column(
            "notification_type",
            sa.String(),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "priority",
            sa.String(),
            nullable=False,
            server_default="normal",
        ),
        sa.Column("related_entity_type", sa.String(50), nullable=True),
        sa.Column("related_entity_id", UUID(as_uuid=True), nullable=True),
        sa.Column("action_url", sa.String(500), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_dismissed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.Column("dismissed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for notifications
    op.create_index(
        "ix_notifications_user_id",
        "notifications",
        ["user_id"],
    )
    op.create_index(
        "ix_notifications_created_at",
        "notifications",
        ["created_at"],
    )
    op.create_index(
        "ix_notifications_user_id_is_read",
        "notifications",
        ["user_id", "is_read"],
    )

    # Create email_logs table
    op.create_table(
        "email_logs",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("recipient_email", sa.String(255), nullable=False),
        sa.Column("subject", sa.String(500), nullable=False),
        sa.Column("template_name", sa.String(100), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("notification_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["notification_id"], ["notifications.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for email_logs
    op.create_index(
        "ix_email_logs_recipient_email",
        "email_logs",
        ["recipient_email"],
    )
    op.create_index(
        "ix_email_logs_notification_id",
        "email_logs",
        ["notification_id"],
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    table_names = set(inspector.get_table_names())

    if "email_logs" in table_names:
        op.execute('DROP INDEX IF EXISTS "ix_email_logs_notification_id"')
        op.execute('DROP INDEX IF EXISTS "ix_email_logs_recipient_email"')
        op.execute("DROP TABLE IF EXISTS email_logs")

    if "notifications" in table_names:
        op.execute('DROP INDEX IF EXISTS "ix_notifications_user_id_is_read"')
        op.execute('DROP INDEX IF EXISTS "ix_notifications_created_at"')
        op.execute('DROP INDEX IF EXISTS "ix_notifications_user_id"')
        op.execute("DROP TABLE IF EXISTS notifications")

    # Drop enums (optional - enums are usually kept)
    op.execute("DROP TYPE IF EXISTS notificationpriority")
    op.execute("DROP TYPE IF EXISTS notificationtype")
