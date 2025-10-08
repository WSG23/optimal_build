"""Add optional PostGIS geometry columns for parcels and zoning layers."""

from __future__ import annotations

import os

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20240919_000005"
down_revision = "20240816_000004"
branch_labels = None
depends_on = None


ENABLE_POSTGIS = os.getenv("BUILDABLE_USE_POSTGIS", "").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

try:  # pragma: no cover - geoalchemy2 is optional in CI environments
    from geoalchemy2 import Geometry  # type: ignore[import-not-found]
except (
    ModuleNotFoundError
):  # pragma: no cover - defensive guard when dependency missing
    Geometry = None  # type: ignore[assignment]


def _should_run() -> bool:
    bind = op.get_bind()
    if bind is None:
        return False
    if not ENABLE_POSTGIS or Geometry is None:
        return False
    return bind.dialect.name == "postgresql"


def upgrade() -> None:  # pragma: no cover - executed via Alembic migrations
    if not _should_run():
        return

    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.add_column(
        "ref_parcels",
        sa.Column(
            "geometry", Geometry(geometry_type="MULTIPOLYGON", srid=4326), nullable=True
        ),
    )
    op.add_column(
        "ref_zoning_layers",
        sa.Column(
            "geometry", Geometry(geometry_type="MULTIPOLYGON", srid=4326), nullable=True
        ),
    )


def downgrade() -> None:  # pragma: no cover - executed via Alembic migrations
    if not _should_run():
        return

    op.execute(
        "ALTER TABLE IF EXISTS ref_zoning_layers DROP COLUMN IF EXISTS geometry CASCADE"
    )
    op.execute(
        "ALTER TABLE IF EXISTS ref_parcels DROP COLUMN IF EXISTS geometry CASCADE"
    )
