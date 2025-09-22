"""Add reference material, cost, and monitoring tables."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20240115_000001"
down_revision = "20231201_000000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply the migration with guards for pre-existing schema objects."""

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    def refresh_inspector() -> None:
        nonlocal inspector
        inspector = sa.inspect(bind)

    def table_exists(name: str) -> bool:
        return inspector.has_table(name)

    def ensure_column(table: str, column_name: str, column: sa.Column) -> None:
        if not table_exists(table):
            return
        columns = {col["name"] for col in inspector.get_columns(table)}
        if column_name not in columns:
            op.add_column(table, column)
            refresh_inspector()

    def ensure_numeric(table: str, column_name: str, precision: int, scale: int) -> None:
        if not table_exists(table):
            return
        for col in inspector.get_columns(table):
            if col["name"] == column_name:
                current_type = col["type"]
                current_precision = getattr(current_type, "precision", None)
                current_scale = getattr(current_type, "scale", None)
                if current_precision != precision or current_scale != scale:
                    op.alter_column(
                        table,
                        column_name,
                        type_=sa.Numeric(precision, scale),
                        existing_type=current_type,
                        existing_nullable=col.get("nullable", True),
                    )
                    refresh_inspector()
                break

    def ensure_table(table: str, *columns: sa.schema.SchemaItem) -> None:
        if table_exists(table):
            return
        op.create_table(table, *columns)
        refresh_inspector()

    def ensure_index(table: str, index_name: str, columns: list[str], unique: bool = False) -> None:
        if not table_exists(table):
            return
        existing = {idx["name"] for idx in inspector.get_indexes(table)}
        if index_name not in existing:
            op.create_index(index_name, table, columns, unique=unique)
            refresh_inspector()

    def ensure_unique_constraint(table: str, constraint_name: str, columns: list[str]) -> None:
        if not table_exists(table):
            return
        existing = {constraint["name"] for constraint in inspector.get_unique_constraints(table)}
        if constraint_name not in existing:
            op.create_unique_constraint(constraint_name, table, columns)
            refresh_inspector()

    def drop_server_default(table: str, column_name: str) -> None:
        if not table_exists(table):
            return
        for col in inspector.get_columns(table):
            if col["name"] == column_name and col.get("default") is not None:
                op.alter_column(table, column_name, server_default=None)
                refresh_inspector()
                break

    ensure_column(
        "ref_material_standards",
        "standard_body",
        sa.Column("standard_body", sa.String(length=100), nullable=False, server_default="UNKNOWN"),
    )
    ensure_column(
        "ref_material_standards",
        "section",
        sa.Column("section", sa.String(length=100), nullable=True),
    )
    ensure_column(
        "ref_material_standards",
        "applicability",
        sa.Column("applicability", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    ensure_column(
        "ref_material_standards",
        "edition",
        sa.Column("edition", sa.String(length=50), nullable=True),
    )
    ensure_column(
        "ref_material_standards",
        "effective_date",
        sa.Column("effective_date", sa.Date(), nullable=True),
    )
    ensure_column(
        "ref_material_standards",
        "license_ref",
        sa.Column("license_ref", sa.String(length=100), nullable=True),
    )
    ensure_column(
        "ref_material_standards",
        "provenance",
        sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    ensure_column(
        "ref_cost_indices",
        "provider",
        sa.Column("provider", sa.String(length=100), nullable=False, server_default="internal"),
    )
    ensure_column(
        "ref_cost_indices",
        "methodology",
        sa.Column("methodology", sa.Text(), nullable=True),
    )
    ensure_numeric("ref_cost_indices", "value", 12, 4)

    ensure_table(
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
    ensure_index("ref_cost_catalogs", "idx_cost_catalogs_name_code", ["catalog_name", "item_code"])
    ensure_index("ref_cost_catalogs", "idx_cost_catalogs_category", ["category"])

    ensure_table(
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
    ensure_index("ref_ingestion_runs", "idx_ingestion_runs_flow_status", ["flow_name", "status"])
    ensure_unique_constraint("ref_ingestion_runs", "uq_ingestion_runs_run_key", ["run_key"])

    ensure_table(
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
    ensure_index("ref_alerts", "idx_alerts_type_level", ["alert_type", "level"])

    drop_server_default("ref_material_standards", "standard_body")
    drop_server_default("ref_cost_indices", "provider")
    drop_server_default("ref_cost_catalogs", "jurisdiction")
    drop_server_default("ref_cost_catalogs", "currency")
    drop_server_default("ref_ingestion_runs", "status")
    drop_server_default("ref_alerts", "level")


def downgrade() -> None:
    """Revert the migration."""

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    def table_exists(name: str) -> bool:
        return inspector.has_table(name)

    def column_exists(table: str, column_name: str) -> bool:
        if not table_exists(table):
            return False
        return column_name in {col["name"] for col in inspector.get_columns(table)}

    def index_exists(table: str, index_name: str) -> bool:
        if not table_exists(table):
            return False
        return index_name in {idx["name"] for idx in inspector.get_indexes(table)}

    if table_exists("ref_alerts"):
        if column_exists("ref_alerts", "level"):
            op.alter_column("ref_alerts", "level", server_default="info")
        if index_exists("ref_alerts", "idx_alerts_type_level"):
            op.drop_index("idx_alerts_type_level", table_name="ref_alerts")
        op.drop_table("ref_alerts")

    if table_exists("ref_ingestion_runs"):
        if column_exists("ref_ingestion_runs", "status"):
            op.alter_column("ref_ingestion_runs", "status", server_default="running")
        if index_exists("ref_ingestion_runs", "idx_ingestion_runs_flow_status"):
            op.drop_index("idx_ingestion_runs_flow_status", table_name="ref_ingestion_runs")
        constraints = {
            constraint["name"]
            for constraint in inspector.get_unique_constraints("ref_ingestion_runs")
        }
        if "uq_ingestion_runs_run_key" in constraints:
            op.drop_constraint("uq_ingestion_runs_run_key", "ref_ingestion_runs", type_="unique")
        op.drop_table("ref_ingestion_runs")

    if table_exists("ref_cost_catalogs"):
        if column_exists("ref_cost_catalogs", "currency"):
            op.alter_column("ref_cost_catalogs", "currency", server_default="SGD")
        if column_exists("ref_cost_catalogs", "jurisdiction"):
            op.alter_column("ref_cost_catalogs", "jurisdiction", server_default="SG")
        if index_exists("ref_cost_catalogs", "idx_cost_catalogs_category"):
            op.drop_index("idx_cost_catalogs_category", table_name="ref_cost_catalogs")
        if index_exists("ref_cost_catalogs", "idx_cost_catalogs_name_code"):
            op.drop_index("idx_cost_catalogs_name_code", table_name="ref_cost_catalogs")
        op.drop_table("ref_cost_catalogs")

    if table_exists("ref_cost_indices"):
        if column_exists("ref_cost_indices", "provider"):
            op.alter_column("ref_cost_indices", "provider", server_default="internal")
        if column_exists("ref_cost_indices", "methodology"):
            op.drop_column("ref_cost_indices", "methodology")
        if column_exists("ref_cost_indices", "provider"):
            op.drop_column("ref_cost_indices", "provider")
        for col in inspector.get_columns("ref_cost_indices"):
            if col["name"] == "value":
                op.alter_column(
                    "ref_cost_indices",
                    "value",
                    type_=sa.Numeric(12, 2),
                    existing_type=col["type"],
                    existing_nullable=col.get("nullable", True),
                )
                break

    if table_exists("ref_material_standards"):
        if column_exists("ref_material_standards", "standard_body"):
            op.alter_column("ref_material_standards", "standard_body", server_default="UNKNOWN")
            op.drop_column("ref_material_standards", "standard_body")
        if column_exists("ref_material_standards", "section"):
            op.drop_column("ref_material_standards", "section")
        if column_exists("ref_material_standards", "applicability"):
            op.drop_column("ref_material_standards", "applicability")
        if column_exists("ref_material_standards", "edition"):
            op.drop_column("ref_material_standards", "edition")
        if column_exists("ref_material_standards", "effective_date"):
            op.drop_column("ref_material_standards", "effective_date")
        if column_exists("ref_material_standards", "license_ref"):
            op.drop_column("ref_material_standards", "license_ref")
        if column_exists("ref_material_standards", "provenance"):
            op.drop_column("ref_material_standards", "provenance")
