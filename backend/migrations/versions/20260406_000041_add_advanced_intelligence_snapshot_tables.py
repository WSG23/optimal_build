"""add_advanced_intelligence_snapshot_tables

Revision ID: 20260406_000041
Revises: 20260117_000040
Create Date: 2026-04-06 11:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260406_000041"
down_revision: Union[str, None] = "20260117_000040"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _create_snapshot_table(table_name: str, unique_name: str, index_name: str) -> None:
    op.create_table(
        table_name,
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=255), nullable=False),
        sa.Column(
            "sample_size",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'empty'"),
        ),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column(
            "version",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_id", name=unique_name),
    )
    op.create_index(index_name, table_name, ["workspace_id"], unique=False)


def upgrade() -> None:
    _create_snapshot_table(
        "workspace_graph_snapshots",
        "uq_workspace_graph_snapshots_workspace_id",
        "ix_workspace_graph_snapshots_workspace_id",
    )
    _create_snapshot_table(
        "workspace_predictive_snapshots",
        "uq_workspace_predictive_snapshots_workspace_id",
        "ix_workspace_predictive_snapshots_workspace_id",
    )
    _create_snapshot_table(
        "workspace_correlation_snapshots",
        "uq_workspace_correlation_snapshots_workspace_id",
        "ix_workspace_correlation_snapshots_workspace_id",
    )
    _create_snapshot_table(
        "workspace_signal_snapshots",
        "uq_workspace_signal_snapshots_workspace_id",
        "ix_workspace_signal_snapshots_workspace_id",
    )


def downgrade() -> None:
    for table_name, index_name in (
        (
            "workspace_signal_snapshots",
            "ix_workspace_signal_snapshots_workspace_id",
        ),
        (
            "workspace_correlation_snapshots",
            "ix_workspace_correlation_snapshots_workspace_id",
        ),
        (
            "workspace_predictive_snapshots",
            "ix_workspace_predictive_snapshots_workspace_id",
        ),
        (
            "workspace_graph_snapshots",
            "ix_workspace_graph_snapshots_workspace_id",
        ),
    ):
        op.execute(f'DROP INDEX IF EXISTS "{index_name}"')
        op.execute(f"DROP TABLE IF EXISTS {table_name}")
