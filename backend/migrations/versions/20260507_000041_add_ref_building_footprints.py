"""add reference building footprints

Revision ID: 20260507_000041
Revises: 20260117_000040, a1b2c3d4e5f6
Create Date: 2026-05-07

"""

from __future__ import annotations

import os
from typing import Any, Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

try:  # pragma: no cover - optional dependency in CI
    from geoalchemy2 import Geometry as GeoAlchemyGeometry
except ModuleNotFoundError:  # pragma: no cover
    GeoAlchemyGeometry = None

Geometry: Any | None = GeoAlchemyGeometry


revision: str = "20260507_000041"
down_revision: Union[str, Sequence[str], None] = (
    "20260117_000040",
    "a1b2c3d4e5f6",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _json_type() -> sa.types.TypeEngine:
    return sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def _postgis_enabled() -> bool:
    bind = op.get_bind()
    if bind is None or bind.dialect.name != "postgresql":
        return False
    enabled = os.getenv("BUILDABLE_USE_POSTGIS", "").strip().lower()
    return enabled in {"1", "true", "yes", "on"} and Geometry is not None


def upgrade() -> None:
    columns: list[sa.Column] = [
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("jurisdiction", sa.String(10), nullable=False),
        sa.Column("layer_name", sa.String(100), nullable=True),
        sa.Column("footprint_ref", sa.String(100), nullable=True),
        sa.Column("bounds_json", _json_type(), nullable=True),
        sa.Column("centroid_lat", sa.Numeric(10, 7), nullable=True),
        sa.Column("centroid_lon", sa.Numeric(10, 7), nullable=True),
        sa.Column("area_m2", sa.Numeric(12, 2), nullable=True),
        sa.Column("attributes", _json_type(), nullable=True),
        sa.Column("source", sa.String(50), nullable=True),
    ]
    if _postgis_enabled():
        columns.append(
            sa.Column(
                "geometry",
                Geometry(geometry_type="MULTIPOLYGON", srid=4326),
                nullable=True,
            )
        )

    op.create_table("ref_building_footprints", *columns)
    op.create_index(
        "ix_ref_building_footprints_jurisdiction",
        "ref_building_footprints",
        ["jurisdiction"],
    )
    op.create_index(
        "ix_ref_building_footprints_layer_name",
        "ref_building_footprints",
        ["layer_name"],
    )
    op.create_index(
        "ix_ref_building_footprints_footprint_ref",
        "ref_building_footprints",
        ["footprint_ref"],
    )
    op.create_index(
        "idx_ref_building_footprints_centroid",
        "ref_building_footprints",
        ["centroid_lat", "centroid_lon"],
    )
    op.create_index(
        "idx_ref_building_footprints_jurisdiction_layer",
        "ref_building_footprints",
        ["jurisdiction", "layer_name"],
    )
    op.create_index(
        "idx_ref_building_footprints_jurisdiction_ref",
        "ref_building_footprints",
        ["jurisdiction", "footprint_ref"],
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ref_building_footprints")
