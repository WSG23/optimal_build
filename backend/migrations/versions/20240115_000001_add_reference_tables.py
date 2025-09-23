"""Add reference material, cost, and monitoring tables."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20240115_000001"
down_revision = "20240711_000000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply the migration."""
#__SKIP_NEXT_ADD_COLUMN__
# already handled with IF NOT EXISTS above
#__SKIP_NEXT_ADD_COLUMN__
#__SKIP_NEXT_ADD_COLUMN__
op.add_column(
        "ref_material_standards",
        sa.Column("section", sa.String(length=100), nullable=True),
    )
#__SKIP_NEXT_ADD_COLUMN__
#__SKIP_NEXT_ADD_COLUMN__
op.add_column(
        "ref_material_standards",
        sa.Column("applicability", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
#__SKIP_NEXT_ADD_COLUMN__
#__SKIP_NEXT_ADD_COLUMN__
op.add_column(
        "ref_material_standards",
        sa.Column("edition", sa.String(length=50), nullable=True),
    )
#__SKIP_NEXT_ADD_COLUMN__
#__SKIP_NEXT_ADD_COLUMN__
op.add_column(
        "ref_material_standards",
        sa.Column("effective_date", sa.Date(), nullable=True),
    )
#__SKIP_NEXT_ADD_COLUMN__
#__SKIP_NEXT_ADD_COLUMN__
op.add_column(
        "ref_material_standards",
        sa.Column("license_ref", sa.String(length=100), nullable=True),
    )
#__SKIP_NEXT_ADD_COLUMN__
#__SKIP_NEXT_ADD_COLUMN__
op.add_column(
        "ref_material_standards",
        sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    op.add_column(
        "ref_cost_indices",
        sa.Column("provider", sa.String(length=100), nullable=False, server_default="internal"),
    )
    op.add_column(
        "ref_cost_indices",
        sa.Column("methodology", sa.Text(), nullable=True),
    )
    op.alter_column(
        "ref_cost_indices",
        "value",
        type_=sa.Numeric(12, 4),
        existing_type=sa.Numeric(12, 2),
        existing_nullable=False,
    )

    op.create_table(
        "ref_cost_catalogs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("jurisdiction", sa.String(length=10), nullable=False, server_default="SG"),
        sa.Column("catalog_name", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=True),
        sa.Column("item_code", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("unit", sa.String(length=20), nullable=True),
        sa.Column("unit_cost", sa.Numeric(12, 2), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True, server_default="SGD"),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("item_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("source", sa.String(length=100), nullable=True),
    )
    op.create_index("idx_cost_catalogs_name_code", "ref_cost_catalogs", ["catalog_name", "item_code"], unique=False)
    op.create_index("idx_cost_catalogs_category", "ref_cost_catalogs", ["category"], unique=False)

    op.create_table(
        "ref_ingestion_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_key", sa.String(length=100), nullable=False),
        sa.Column("flow_name", sa.String(length=100), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="running"),
        sa.Column("records_ingested", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("suspected_updates", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_index("idx_ingestion_runs_flow_status", "ref_ingestion_runs", ["flow_name", "status"], unique=False)
    op.create_unique_constraint("uq_ingestion_runs_run_key", "ref_ingestion_runs", ["run_key"])

    op.create_table(
        "ref_alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("alert_type", sa.String(length=50), nullable=False),
        sa.Column("level", sa.String(length=20), nullable=False, server_default="info"),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("context", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ingestion_run_id", sa.Integer(), nullable=True),
        sa.Column("acknowledged", sa.Boolean(), nullable=True, server_default=sa.text("false")),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_by", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(["ingestion_run_id"], ["ref_ingestion_runs.id"], ondelete="SET NULL"),
    )
    op.create_index("idx_alerts_type_level", "ref_alerts", ["alert_type", "level"], unique=False)

    op.alter_column("ref_material_standards", "standard_body", server_default=None)
    op.alter_column("ref_cost_indices", "provider", server_default=None)
    op.alter_column("ref_cost_catalogs", "jurisdiction", server_default=None)
    op.alter_column("ref_cost_catalogs", "currency", server_default=None)
    op.alter_column("ref_ingestion_runs", "status", server_default=None)
    op.alter_column("ref_alerts", "level", server_default=None)


def downgrade() -> None:
    """Revert the migration."""

    op.alter_column("ref_alerts", "level", server_default="info")
    op.alter_column("ref_ingestion_runs", "status", server_default="running")
    op.alter_column("ref_cost_catalogs", "currency", server_default="SGD")
    op.alter_column("ref_cost_catalogs", "jurisdiction", server_default="SG")
    op.alter_column("ref_cost_indices", "provider", server_default="internal")
    op.alter_column("ref_material_standards", "standard_body", server_default="UNKNOWN")

    op.drop_index("idx_alerts_type_level", table_name="ref_alerts")
    op.drop_table("ref_alerts")

    op.drop_constraint("uq_ingestion_runs_run_key", "ref_ingestion_runs", type_="unique")
    op.drop_index("idx_ingestion_runs_flow_status", table_name="ref_ingestion_runs")
    op.drop_table("ref_ingestion_runs")

    op.drop_index("idx_cost_catalogs_category", table_name="ref_cost_catalogs")
    op.drop_index("idx_cost_catalogs_name_code", table_name="ref_cost_catalogs")
    op.drop_table("ref_cost_catalogs")

    op.drop_column("ref_cost_indices", "methodology")
    op.drop_column("ref_cost_indices", "provider")
    op.alter_column(
        "ref_cost_indices",
        "value",
        type_=sa.Numeric(12, 2),
        existing_type=sa.Numeric(12, 4),
        existing_nullable=False,
    )

    op.drop_column("ref_material_standards", "provenance")
    op.drop_column("ref_material_standards", "license_ref")
    op.drop_column("ref_material_standards", "effective_date")
    op.drop_column("ref_material_standards", "edition")
    op.drop_column("ref_material_standards", "applicability")
    op.drop_column("ref_material_standards", "section")
    op.drop_column("ref_material_standards", "standard_body")
