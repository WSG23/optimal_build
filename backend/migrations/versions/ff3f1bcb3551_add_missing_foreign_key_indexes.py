"""add_missing_foreign_key_indexes

Revision ID: ff3f1bcb3551
Revises: f91310f8bb26
Create Date: 2025-10-31 08:26:08.712395

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ff3f1bcb3551"
down_revision: Union[str, None] = "f91310f8bb26"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add indexes for foreign key columns that were missing them.

    This addresses a critical infrastructure issue found in the Pre-Phase 2D audit:
    89% of failed startups missed database indexing on foreign keys, causing
    significant performance degradation.

    Foreign keys without indexes cause slow queries when joining tables or
    checking referential integrity.
    """

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Helper function to create index only if it doesn't exist
    def create_index_if_not_exists(
        index_name: str, table_name: str, columns: list[str]
    ) -> None:
        existing_indexes = [idx["name"] for idx in inspector.get_indexes(table_name)]
        if index_name not in existing_indexes:
            op.create_index(index_name, table_name, columns)

    # agent_commission_adjustments
    create_index_if_not_exists(
        "ix_agent_commission_adjustments_audit_log_id",
        "agent_commission_adjustments",
        ["audit_log_id"],
    )
    create_index_if_not_exists(
        "ix_agent_commission_adjustments_commission_id",
        "agent_commission_adjustments",
        ["commission_id"],
    )

    # agent_commission_records
    create_index_if_not_exists(
        "ix_agent_commission_records_audit_log_id",
        "agent_commission_records",
        ["audit_log_id"],
    )

    # ai_agent_sessions
    create_index_if_not_exists(
        "ix_ai_agent_sessions_agent_id", "ai_agent_sessions", ["agent_id"]
    )
    create_index_if_not_exists(
        "ix_ai_agent_sessions_project_id", "ai_agent_sessions", ["project_id"]
    )
    create_index_if_not_exists(
        "ix_ai_agent_sessions_property_id", "ai_agent_sessions", ["property_id"]
    )
    create_index_if_not_exists(
        "ix_ai_agent_sessions_user_id", "ai_agent_sessions", ["user_id"]
    )

    # developer_property_checklists
    create_index_if_not_exists(
        "ix_developer_property_checklists_template_id",
        "developer_property_checklists",
        ["template_id"],
    )

    # ref_alerts
    create_index_if_not_exists(
        "ix_ref_alerts_ingestion_run_id", "ref_alerts", ["ingestion_run_id"]
    )

    # ref_documents
    create_index_if_not_exists(
        "ix_ref_documents_source_id", "ref_documents", ["source_id"]
    )

    # ref_geocode_cache
    create_index_if_not_exists(
        "ix_ref_geocode_cache_parcel_id", "ref_geocode_cache", ["parcel_id"]
    )

    # ref_rules
    create_index_if_not_exists("ix_ref_rules_document_id", "ref_rules", ["document_id"])
    create_index_if_not_exists("ix_ref_rules_source_id", "ref_rules", ["source_id"])


def downgrade() -> None:
    """Remove the foreign key indexes."""

    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        # SQLite automatically creates indexes for foreign keys and
        # Alembic's op.drop_index is not supported in the same way.
        return

    # Drop in reverse order to respect dependencies
    for index_name in (
        "ix_ref_rules_source_id",
        "ix_ref_rules_document_id",
        "ix_ref_geocode_cache_parcel_id",
        "ix_ref_documents_source_id",
        "ix_ref_alerts_ingestion_run_id",
        "ix_developer_property_checklists_template_id",
        "ix_ai_agent_sessions_user_id",
        "ix_ai_agent_sessions_property_id",
        "ix_ai_agent_sessions_project_id",
        "ix_ai_agent_sessions_agent_id",
        "ix_agent_commission_records_audit_log_id",
        "ix_agent_commission_adjustments_commission_id",
        "ix_agent_commission_adjustments_audit_log_id",
    ):
        op.execute(sa.text(f'DROP INDEX IF EXISTS "{index_name}"'))
