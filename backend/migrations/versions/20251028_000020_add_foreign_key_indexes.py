"""Add indexes for foreign key columns referenced frequently.

Revision ID: 20251028_000020
Revises: 20251026_000019
Create Date: 2025-10-28
"""

from __future__ import annotations

from typing import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251028_000020"
down_revision = "20251026_000019"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


# These indexes are for columns that actually exist in the schema
INDEXES = (
    (
        "developer_condition_assessments",
        "ix_developer_condition_assessments_recorded_by",
        ["recorded_by"],
    ),
    (
        "developer_property_checklists",
        "ix_developer_property_checklists_completed_by",
        ["completed_by"],
    ),
    (
        "developer_property_checklists",
        "ix_developer_property_checklists_assigned_to",
        ["assigned_to"],
    ),
    (
        "developer_property_checklists",
        "ix_developer_property_checklists_template_id",
        ["template_id"],
    ),
    ("development_analyses", "ix_development_analyses_property_id", ["property_id"]),
    ("market_transactions", "ix_market_transactions_property_id", ["property_id"]),
    ("projects", "ix_projects_owner_id_fk", ["owner_id"]),
    ("ref_alerts", "ix_ref_alerts_ingestion_run_id", ["ingestion_run_id"]),
    ("ref_documents", "ix_ref_documents_source_id", ["source_id"]),
    ("ref_geocode_cache", "ix_ref_geocode_cache_parcel_id", ["parcel_id"]),
    ("rental_listings", "ix_rental_listings_property_id", ["property_id"]),
    ("listing_publications", "ix_listing_publications_account_id", ["account_id"]),
    ("overlay_decisions", "ix_overlay_decisions_suggestion_id", ["suggestion_id"]),
    ("ref_clauses", "ix_ref_clauses_document_id", ["document_id"]),
    ("ref_rules", "ix_ref_rules_document_id", ["document_id"]),
    ("ref_rules", "ix_ref_rules_source_id", ["source_id"]),
    ("singapore_properties", "ix_singapore_properties_project_id", ["project_id"]),
    (
        "agent_commission_records",
        "ix_agent_commission_records_audit_log_id",
        ["audit_log_id"],
    ),
    (
        "agent_commission_records",
        "ix_agent_commission_records_deal_id",
        ["deal_id"],
    ),
    ("agent_deal_documents", "ix_agent_deal_documents_uploaded_by", ["uploaded_by"]),
    (
        "agent_commission_adjustments",
        "ix_agent_commission_adjustments_recorded_by",
        ["recorded_by"],
    ),
    (
        "agent_commission_adjustments",
        "ix_agent_commission_adjustments_audit_log_id",
        ["audit_log_id"],
    ),
)


def upgrade() -> None:
    # Use PL/pgSQL to create indexes safely, skipping if table or column doesn't exist
    for table, index_name, columns in INDEXES:
        cols = ", ".join(columns)
        # Use IF NOT EXISTS and wrap in a DO block to handle missing tables gracefully
        op.execute(
            sa.text(
                f"""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_name = '{table}'
                    ) AND EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = '{table}' AND column_name = '{columns[0]}'
                    ) THEN
                        EXECUTE 'CREATE INDEX IF NOT EXISTS {index_name} ON {table} ({cols})';
                    END IF;
                END $$;
                """
            )
        )


def downgrade() -> None:
    for table, index_name, _ in reversed(INDEXES):
        op.execute(sa.text(f"DROP INDEX IF EXISTS {index_name}"))
