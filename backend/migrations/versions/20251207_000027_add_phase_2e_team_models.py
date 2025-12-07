"""add_phase_2e_team_models

Revision ID: 20251207_000027
Revises: f64ee42f9736
Create Date: 2025-12-07 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20251207_000027"
down_revision: Union[str, None] = "f64ee42f9736"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # team_members
    op.create_table(
        "team_members",
        sa.Column("id", sa.CHAR(36), nullable=False),
        sa.Column("project_id", sa.CHAR(36), nullable=False),
        sa.Column("user_id", sa.CHAR(36), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "admin",
                "developer",
                "investor",
                "contractor",
                "consultant",
                "regulatory_officer",
                "viewer",
                name="userrole",
            ),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("joined_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sqlite_autoincrement=True,
    )
    op.create_index(
        op.f("ix_team_members_project_id"), "team_members", ["project_id"], unique=False
    )
    op.create_index(
        op.f("ix_team_members_user_id"), "team_members", ["user_id"], unique=False
    )

    # team_invitations
    op.create_table(
        "team_invitations",
        sa.Column("id", sa.CHAR(36), nullable=False),
        sa.Column("project_id", sa.CHAR(36), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "admin",
                "developer",
                "investor",
                "contractor",
                "consultant",
                "regulatory_officer",
                "viewer",
                name="userrole",
            ),
            nullable=False,
        ),
        sa.Column("token", sa.String(length=100), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending", "accepted", "expired", "revoked", name="invitationstatus"
            ),
            nullable=False,
        ),
        sa.Column("invited_by_id", sa.CHAR(36), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("accepted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["invited_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_team_invitations_email"), "team_invitations", ["email"], unique=False
    )
    op.create_index(
        op.f("ix_team_invitations_project_id"),
        "team_invitations",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_team_invitations_token"), "team_invitations", ["token"], unique=True
    )

    # approval_workflows
    op.create_table(
        "approval_workflows",
        sa.Column("id", sa.CHAR(36), nullable=False),
        sa.Column("project_id", sa.CHAR(36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("workflow_type", sa.String(length=50), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "draft",
                "in_progress",
                "approved",
                "rejected",
                "cancelled",
                name="workflowstatus",
            ),
            nullable=False,
        ),
        sa.Column("created_by_id", sa.CHAR(36), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_approval_workflows_project_id"),
        "approval_workflows",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_approval_workflows_status"),
        "approval_workflows",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_approval_workflows_workflow_type"),
        "approval_workflows",
        ["workflow_type"],
        unique=False,
    )

    # approval_steps
    op.create_table(
        "approval_steps",
        sa.Column("id", sa.CHAR(36), nullable=False),
        sa.Column("workflow_id", sa.CHAR(36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("sequence_order", sa.Integer(), nullable=False),
        sa.Column(
            "required_role",
            sa.Enum(
                "admin",
                "developer",
                "investor",
                "contractor",
                "consultant",
                "regulatory_officer",
                "viewer",
                name="userrole",
            ),
            nullable=True,
        ),
        sa.Column("required_user_id", sa.CHAR(36), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "in_review",
                "approved",
                "rejected",
                "skipped",
                name="stepstatus",
            ),
            nullable=False,
        ),
        sa.Column("approved_by_id", sa.CHAR(36), nullable=True),
        sa.Column("decision_at", sa.DateTime(), nullable=True),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["approved_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["required_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["workflow_id"], ["approval_workflows.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_approval_steps_workflow_id"),
        "approval_steps",
        ["workflow_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_approval_steps_workflow_id"), table_name="approval_steps")
    op.drop_table("approval_steps")
    op.drop_index(
        op.f("ix_approval_workflows_workflow_type"), table_name="approval_workflows"
    )
    op.drop_index(op.f("ix_approval_workflows_status"), table_name="approval_workflows")
    op.drop_index(
        op.f("ix_approval_workflows_project_id"), table_name="approval_workflows"
    )
    op.drop_table("approval_workflows")
    op.drop_index(op.f("ix_team_invitations_token"), table_name="team_invitations")
    op.drop_index(op.f("ix_team_invitations_project_id"), table_name="team_invitations")
    op.drop_index(op.f("ix_team_invitations_email"), table_name="team_invitations")
    op.drop_table("team_invitations")
    op.drop_index(op.f("ix_team_members_user_id"), table_name="team_members")
    op.drop_index(op.f("ix_team_members_project_id"), table_name="team_members")
    op.drop_table("team_members")

    # Enums are usually not dropped automatically in Postgres, but if we created types we might need to drop them.
    # However, 'userrole' likely existed. 'invitationstatus', 'workflowstatus', 'stepstatus' are new.
    # Since we use sa.Enum(.... name='xyz'), it creates the type in Postgres.
    # To be safe in downgrade, we should try to drop them if we want a clean slate, but strict downgrade often leaves Enums.
    pass
