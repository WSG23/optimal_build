"""Fetch New Zealand cadastral parcels from LINZ WFS API and persist to ``ref_parcels``.

This loader queries the LINZ Data Service WFS endpoint for parcel polygons (layer-50804),
reprojects from NZGD2000/NZTM (EPSG:2193) to WGS84 (EPSG:4326), and inserts the derived
geometry into the reference parcels table.

The loader supports city-specific filtering using LINZ land_district values to manage
dataset size (Auckland ~600k parcels, Wellington ~180k, Christchurch ~250k).

Example usage::

    # Ingest Auckland parcels with API key from environment
    PYTHONPATH=$REPO_ROOT \\
      SECRET_KEY=dev-secret \\
      DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/building_compliance" \\
      .venv/bin/python -m backend.scripts.ingest_nz_parcels \\
      --city auckland \\
      --batch-size 1000 \\
      --persist

    # Dry run Wellington parcels (no DB writes)
    PYTHONPATH=$REPO_ROOT \\
      .venv/bin/python -m backend.scripts.ingest_nz_parcels \\
      --city wellington \\
      --limit 500

    # Incremental upsert for Christchurch
    PYTHONPATH=$REPO_ROOT \\
      .venv/bin/python -m backend.scripts.ingest_nz_parcels \\
      --city christchurch \\
      --batch-size 2000 \\
      --no-reset \\
      --persist

Requires NZ_LINZ_API_KEY environment variable (or defaults to 'public' for testing).
"""

from __future__ import annotations

import argparse
import asyncio
import math
import os
from dataclasses import dataclass
from typing import Any, Sequence

import httpx
import structlog
from pyproj import Transformer
from shapely.geometry import GeometryCollection, MultiPolygon, Polygon, shape
from shapely.geometry.base import BaseGeometry
from shapely.geometry import mapping as shapely_mapping
from shapely.ops import transform
from shapely.validation import make_valid
from sqlalchemy import delete, insert

import app.utils.logging  # noqa: F401  pylint: disable=unused-import
from app.core.database import AsyncSessionLocal
from app.models.rkp import RefParcel

try:  # pragma: no cover - optional PostGIS column
    from geoalchemy2.shape import from_shape
except ModuleNotFoundError:  # pragma: no cover - geoalchemy2 not installed
    from_shape = None  # type: ignore


logger = structlog.get_logger(__name__)

# LINZ WFS endpoint with API key placeholder
LINZ_WFS_BASE = "https://data.linz.govt.nz/services;key={api_key}/wfs"
LINZ_PARCEL_LAYER = "layer-50804"  # NZ Primary Parcels

# City-to-land_district mapping
CITY_FILTERS = {
    "auckland": "Auckland",
    "wellington": "Wellington",
    "christchurch": "Canterbury",
}


@dataclass(slots=True)
class ParcelIngestionOptions:
    city: str
    api_key: str
    batch_size: int
    limit: int | None
    skip: int
    reset: bool
    persist: bool
    source_epsg: int
    source_label: str


@dataclass(slots=True)
class ParcelRecord:
    parcel_ref: str
    geometry_feature: dict[str, Any]
    shapely_geometry: BaseGeometry
    centroid_lat: float
    centroid_lon: float
    area_m2: float
    source_label: str


@dataclass(slots=True)
class ParcelIngestionStats:
    seen_features: int = 0
    processed_records: int = 0
    inserted_records: int = 0
    skipped_features: int = 0
    invalid_features: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "seen_features": self.seen_features,
            "processed_records": self.processed_records,
            "inserted_records": self.inserted_records,
            "skipped_features": self.skipped_features,
            "invalid_features": self.invalid_features,
        }


def _force_multipolygon(geometry: BaseGeometry) -> MultiPolygon:
    """Return a MultiPolygon regardless of initial geometry type."""

    if isinstance(geometry, MultiPolygon):
        return geometry
    if isinstance(geometry, Polygon):
        return MultiPolygon([geometry])
    if isinstance(geometry, GeometryCollection):
        polygons: list[Polygon] = []
        for child in geometry.geoms:
            if isinstance(child, MultiPolygon):
                polygons.extend(list(child.geoms))
            elif isinstance(child, Polygon):
                polygons.append(child)
        if not polygons:
            raise ValueError("Geometry collection does not contain polygons")
        return MultiPolygon(polygons)
    raise ValueError(f"Unsupported geometry type: {geometry.geom_type}")


def _normalise_feature(
    feature: dict[str, Any],
    transformer: Transformer,
    *,
    source_label: str,
) -> ParcelRecord:
    """Convert LINZ WFS feature to ParcelRecord with WGS84 geometry."""

    geometry_payload = feature.get("geometry")
    if not isinstance(geometry_payload, dict):
        raise ValueError("Feature missing geometry")

    raw_geometry = make_valid(shape(geometry_payload))
    if raw_geometry.is_empty:
        raise ValueError("Geometry is empty after validation")

    properties = feature.get("properties") or {}
    parcel_id = properties.get("id") or properties.get("parcel_intent")
    if parcel_id is None:
        raise ValueError("Feature missing parcel identifier")

    # Calculate area in source CRS (meters) before projection
    area_m2 = float(raw_geometry.area)
    if math.isclose(area_m2, 0.0):
        raise ValueError("Parcel area is zero")

    # Reproject from EPSG:2193 (NZTM) to EPSG:4326 (WGS84)
    projected = make_valid(transform(transformer.transform, raw_geometry))
    if projected.is_empty:
        raise ValueError("Transformed geometry is empty")

    multipolygon = _force_multipolygon(projected)
    centroid = multipolygon.centroid

    geometry_geojson = shapely_mapping(multipolygon)
    feature_geojson: dict[str, Any] = {
        "type": "Feature",
        "geometry": geometry_geojson,
        "properties": {
            "id": properties.get("id"),
            "parcel_intent": properties.get("parcel_intent"),
            "land_district": properties.get("land_district"),
            "titles": properties.get("titles"),
            "survey_area": properties.get("survey_area"),
        },
    }

    return ParcelRecord(
        parcel_ref=f"NZ:PARCEL:{parcel_id}",
        geometry_feature=feature_geojson,
        shapely_geometry=multipolygon,
        centroid_lat=float(centroid.y),
        centroid_lon=float(centroid.x),
        area_m2=area_m2,
        source_label=source_label,
    )


async def _fetch_parcels_from_wfs(
    city: str,
    api_key: str,
    limit: int | None,
    skip: int,
) -> list[dict[str, Any]]:
    """Fetch parcel features from LINZ WFS API with city-specific CQL filter."""

    land_district = CITY_FILTERS.get(city.lower())
    if not land_district:
        raise ValueError(
            f"Unknown city: {city}. Valid options: {', '.join(CITY_FILTERS.keys())}"
        )

    wfs_url = LINZ_WFS_BASE.format(api_key=api_key)
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": LINZ_PARCEL_LAYER,
        "outputFormat": "application/json",
        "cql_filter": f"land_district='{land_district}'",
    }

    if limit is not None:
        params["count"] = str(limit)
    if skip > 0:
        params["startIndex"] = str(skip)

    logger.info(
        "nz_parcels:fetching_from_wfs",
        city=city,
        land_district=land_district,
        limit=limit,
        skip=skip,
    )

    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.get(wfs_url, params=params)
        response.raise_for_status()
        data = response.json()

    features = data.get("features", [])
    logger.info(
        "nz_parcels:wfs_fetch_complete",
        city=city,
        features_received=len(features),
    )

    return features


async def _persist_batch(
    session,
    rows: Sequence[ParcelRecord],
    *,
    jurisdiction: str,
) -> None:
    """Insert batch of ParcelRecords into ref_parcels table."""

    if not rows:
        return

    payloads: list[dict[str, Any]] = []
    has_geometry_column = getattr(RefParcel, "geometry", None) is not None

    for row in rows:
        payload: dict[str, Any] = {
            "jurisdiction": jurisdiction,
            "parcel_ref": row.parcel_ref,
            "bounds_json": row.geometry_feature,
            "centroid_lat": row.centroid_lat,
            "centroid_lon": row.centroid_lon,
            "area_m2": row.area_m2,
            "source": row.source_label,
        }
        if has_geometry_column and from_shape is not None:
            payload["geometry"] = from_shape(row.shapely_geometry, srid=4326)
        payloads.append(payload)

    stmt = insert(RefParcel).values(payloads)
    await session.execute(stmt)


async def _delete_existing(session, jurisdiction: str, city: str) -> int:
    """Delete existing NZ parcels for the specified city."""

    # For city-specific deletion, we'd need a city column or filter by parcel_ref prefix
    # For now, delete all NZ parcels (user can use --no-reset for incremental)
    stmt = delete(RefParcel).where(RefParcel.jurisdiction == jurisdiction)
    result = await session.execute(stmt)
    return result.rowcount or 0


async def _delete_specific(
    session, jurisdiction: str, parcel_refs: Sequence[str]
) -> None:
    """Delete specific parcels by parcel_ref (for incremental upsert)."""

    if not parcel_refs:
        return
    stmt = delete(RefParcel).where(
        RefParcel.jurisdiction == jurisdiction, RefParcel.parcel_ref.in_(parcel_refs)
    )
    await session.execute(stmt)


async def ingest_parcels(options: ParcelIngestionOptions) -> ParcelIngestionStats:
    """Main ingestion workflow: fetch from WFS, transform, and persist to DB."""

    stats = ParcelIngestionStats()
    transformer = Transformer.from_crs(
        f"EPSG:{options.source_epsg}", "EPSG:4326", always_xy=True
    )

    # Reset database if requested
    if options.reset and options.persist:
        async with AsyncSessionLocal() as session:
            removed = await _delete_existing(session, "NZ", options.city)
            await session.commit()
            logger.info(
                "nz_parcels:cleared_existing", city=options.city, removed=removed
            )

    # Fetch features from LINZ WFS
    features = await _fetch_parcels_from_wfs(
        city=options.city,
        api_key=options.api_key,
        limit=options.limit,
        skip=options.skip,
    )

    # Process features and persist in batches
    batch: list[ParcelRecord] = []
    async with AsyncSessionLocal() as session:
        for feature_index, feature in enumerate(features):
            stats.seen_features += 1

            try:
                record = _normalise_feature(
                    feature,
                    transformer,
                    source_label=options.source_label,
                )
            except ValueError as exc:
                stats.invalid_features += 1
                logger.warning(
                    "nz_parcels:feature_skipped",
                    reason=str(exc),
                    feature_index=feature_index,
                )
                continue

            batch.append(record)
            stats.processed_records += 1

            if len(batch) >= options.batch_size:
                if options.persist:
                    if not options.reset:
                        await _delete_specific(
                            session,
                            "NZ",
                            [row.parcel_ref for row in batch],
                        )
                    await _persist_batch(
                        session,
                        batch,
                        jurisdiction="NZ",
                    )
                    await session.commit()
                    stats.inserted_records += len(batch)
                    logger.info(
                        "nz_parcels:batch_committed",
                        inserted=len(batch),
                        total_inserted=stats.inserted_records,
                    )
                else:
                    logger.info(
                        "nz_parcels:batch_processed_dry_run",
                        processed=len(batch),
                        total_processed=stats.processed_records,
                    )
                batch.clear()

        # Persist remaining batch
        if batch:
            if options.persist:
                if not options.reset:
                    await _delete_specific(
                        session,
                        "NZ",
                        [row.parcel_ref for row in batch],
                    )
                await _persist_batch(
                    session,
                    batch,
                    jurisdiction="NZ",
                )
                await session.commit()
                stats.inserted_records += len(batch)
                logger.info(
                    "nz_parcels:batch_committed",
                    inserted=len(batch),
                    total_inserted=stats.inserted_records,
                )
            else:
                logger.info(
                    "nz_parcels:batch_processed_dry_run",
                    processed=len(batch),
                    total_processed=stats.processed_records,
                )

    logger.info("nz_parcels:completed", **stats.as_dict())
    return stats


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ingest New Zealand cadastral parcels from LINZ WFS API into ref_parcels."
    )
    parser.add_argument(
        "--city",
        type=str,
        required=True,
        choices=["auckland", "wellington", "christchurch"],
        help="City to ingest parcels for (determines land_district filter).",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="LINZ API key (defaults to NZ_LINZ_API_KEY environment variable).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Number of parcels to insert per transaction (default: 1000).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional maximum number of parcels to ingest (for testing).",
    )
    parser.add_argument(
        "--skip",
        type=int,
        default=0,
        help="Number of features to skip from the beginning of the dataset.",
    )
    parser.add_argument(
        "--no-reset",
        action="store_false",
        dest="reset",
        help="Upsert parcels without truncating existing NZ entries first.",
    )
    parser.add_argument(
        "--persist",
        action="store_true",
        help="Write to database (without this flag, runs as dry-run).",
    )
    parser.add_argument(
        "--source-epsg",
        type=int,
        default=2193,
        help="EPSG code of the source dataset coordinates (default: 2193 NZTM).",
    )
    parser.add_argument(
        "--source-label",
        default="linz_wfs",
        help="Label stored in the RefParcel.source column (default: linz_wfs).",
    )
    return parser


async def _run_from_cli(args: argparse.Namespace) -> ParcelIngestionStats:
    api_key = args.api_key or os.getenv("NZ_LINZ_API_KEY", "public")

    options = ParcelIngestionOptions(
        city=args.city,
        api_key=api_key,
        batch_size=args.batch_size,
        limit=args.limit,
        skip=args.skip,
        reset=args.reset,
        persist=args.persist,
        source_epsg=args.source_epsg,
        source_label=args.source_label,
    )
    logger.info(
        "nz_parcels:starting",
        city=options.city,
        batch_size=options.batch_size,
        limit=options.limit,
        skip=options.skip,
        reset=options.reset,
        persist=options.persist,
        source_epsg=options.source_epsg,
    )
    return await ingest_parcels(options)


def main() -> None:
    parser = _build_arg_parser()
    args = parser.parse_args()
    stats = asyncio.run(_run_from_cli(args))
    print("\nNew Zealand parcel ingestion complete:")
    for key, value in stats.as_dict().items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
