"""Stream Singapore cadastral parcels into ``ref_parcels``.

This loader consumes the SLA/OneMap Land Lot Boundary GeoJSON export (SVY21 /
EPSG:3414), reprojects each polygon into WGS84, and upserts the geometry into
the reference parcels table so Singapore remains the canonical baseline for GPS
logging, preview, and finance flows.

Example usage::

    # Default dataset path (data/sg/parcels/land_lot_boundary.geojson)
    PYTHONPATH=$REPO_ROOT \\
      .venv/bin/python -m backend.scripts.ingest_sg_parcels \\
      --batch-size 1000

    # Run against a custom GeoJSON export without truncating existing data
    PYTHONPATH=$REPO_ROOT \\
      .venv/bin/python -m backend.scripts.ingest_sg_parcels \\
      --input-path /tmp/land_lots.geojson --no-reset

The loader requires read access to the downloaded GeoJSON. Download the latest
SLA "Land Lot Boundary" dataset from data.gov.sg or the OneMap Theme API and
place it under ``data/sg/parcels`` before running the script.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Sequence

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

DEFAULT_DATASET_PATH = Path("data/sg/parcels/land_lot_boundary.geojson")

IDENTIFIER_FIELDS = (
    "LOT_KEY",  # data.gov.sg export (e.g., "MK26-07308N")
    "LOT_NO",
    "LOT_PARCEL_NO",
    "LOT_NUMBER",
    "LOT_ID",
    "LANDLOT",
    "OBJECTID",
)


@dataclass(slots=True)
class ParcelIngestionOptions:
    input_path: Path
    jurisdiction: str
    batch_size: int
    limit: int | None
    skip: int
    reset: bool
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


def _iter_geojson_features(path: Path) -> Iterator[dict[str, Any]]:
    """Yield GeoJSON feature objects without loading the full file into memory."""

    decoder = json.JSONDecoder()
    buffer = ""
    inside_features = False
    with path.open("r", encoding="utf-8") as handle:
        while True:
            chunk = handle.read(131072)
            if not chunk:
                break
            buffer += chunk
            if not inside_features:
                marker_index = buffer.find('"features"')
                if marker_index == -1:
                    buffer = buffer[-32_768:]
                    continue
                buffer = buffer[marker_index:]
                bracket_index = buffer.find("[")
                if bracket_index == -1:
                    continue
                buffer = buffer[bracket_index + 1 :]
                inside_features = True

            while inside_features:
                buffer = buffer.lstrip()
                if not buffer:
                    break
                leading = buffer[0]
                if leading == ",":
                    buffer = buffer[1:]
                    continue
                if leading == "]":
                    inside_features = False
                    buffer = buffer[1:]
                    break
                try:
                    feature, offset = decoder.raw_decode(buffer)
                except json.JSONDecodeError:
                    break
                if isinstance(feature, dict):
                    yield feature
                buffer = buffer[offset:]

    if inside_features:
        raise RuntimeError(f"Unexpected EOF before completing features array in {path}")


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


def _resolve_lot_identifier(properties: dict[str, Any]) -> str | None:
    """Return the first non-empty parcel identifier from known SLA fields."""

    for key in IDENTIFIER_FIELDS:
        value = properties.get(key)
        if value is None:
            continue
        if isinstance(value, str) and value.strip():
            return value.strip()
        return str(value)
    return None


def _normalise_feature(
    feature: dict[str, Any],
    transformer: Transformer,
    *,
    source_label: str,
) -> ParcelRecord:
    geometry_payload = feature.get("geometry")
    if not isinstance(geometry_payload, dict):
        raise ValueError("Feature missing geometry")

    raw_geometry = make_valid(shape(geometry_payload))
    if raw_geometry.is_empty:
        raise ValueError("Geometry is empty after validation")

    properties = feature.get("properties") or {}
    lot_identifier = _resolve_lot_identifier(properties)
    if lot_identifier is None:
        raise ValueError("Feature missing lot identifier")

    # Use source area metadata if available (for WGS84 exports), otherwise calculate
    area_m2 = properties.get("SHAPE_1.AREA") or properties.get("SHAPE_Area")
    if area_m2 is not None:
        area_m2 = float(area_m2)
    else:
        area_m2 = float(raw_geometry.area)
    if math.isclose(area_m2, 0.0):
        raise ValueError("Parcel area is zero")

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
            "lot_no": properties.get("LOT_NO"),
            "lot_number": properties.get("LOT_NUMBER"),
            "lot_parcel_no": properties.get("LOT_PARCEL_NO"),
            "land_lot": properties.get("LANDLOT"),
            "mk_ts_no": properties.get("MK_TS_NO"),
            "tenure": properties.get("TENURE"),
            "source_area": properties.get("SHAPE_Area"),
            "source_perimeter": properties.get("SHAPE_Length"),
        },
    }

    return ParcelRecord(
        parcel_ref=f"SG:LOT:{lot_identifier}",
        geometry_feature=feature_geojson,
        shapely_geometry=multipolygon,
        centroid_lat=float(centroid.y),
        centroid_lon=float(centroid.x),
        area_m2=area_m2,
        source_label=source_label,
    )


async def _persist_batch(
    session,
    rows: Sequence[ParcelRecord],
    *,
    jurisdiction: str,
) -> None:
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


async def _delete_existing(session, jurisdiction: str) -> int:
    stmt = delete(RefParcel).where(RefParcel.jurisdiction == jurisdiction)
    result = await session.execute(stmt)
    return result.rowcount or 0


async def _delete_specific(
    session, jurisdiction: str, parcel_refs: Sequence[str]
) -> None:
    if not parcel_refs:
        return
    stmt = delete(RefParcel).where(
        RefParcel.jurisdiction == jurisdiction, RefParcel.parcel_ref.in_(parcel_refs)
    )
    await session.execute(stmt)


async def ingest_parcels(options: ParcelIngestionOptions) -> ParcelIngestionStats:
    stats = ParcelIngestionStats()
    transformer = Transformer.from_crs(
        f"EPSG:{options.source_epsg}", "EPSG:4326", always_xy=True
    )

    async with AsyncSessionLocal() as session:
        if options.reset:
            removed = await _delete_existing(session, options.jurisdiction)
            await session.commit()
            logger.info("sg_parcels:cleared_existing", removed=removed)

    async with AsyncSessionLocal() as session:
        batch: list[ParcelRecord] = []
        for feature_index, feature in enumerate(
            _iter_geojson_features(options.input_path)
        ):
            stats.seen_features += 1
            if feature_index < options.skip:
                stats.skipped_features += 1
                continue
            if options.limit is not None and stats.processed_records >= options.limit:
                break
            try:
                record = _normalise_feature(
                    feature,
                    transformer,
                    source_label=options.source_label,
                )
            except ValueError as exc:
                stats.invalid_features += 1
                logger.warning(
                    "sg_parcels:feature_skipped",
                    reason=str(exc),
                    feature_index=feature_index,
                )
                continue

            batch.append(record)
            stats.processed_records += 1

            if len(batch) >= options.batch_size:
                if not options.reset:
                    await _delete_specific(
                        session,
                        options.jurisdiction,
                        [row.parcel_ref for row in batch],
                    )
                await _persist_batch(
                    session,
                    batch,
                    jurisdiction=options.jurisdiction,
                )
                await session.commit()
                stats.inserted_records += len(batch)
                logger.info(
                    "sg_parcels:batch_committed",
                    inserted=len(batch),
                    total_inserted=stats.inserted_records,
                )
                batch.clear()

        if batch:
            if not options.reset:
                await _delete_specific(
                    session,
                    options.jurisdiction,
                    [row.parcel_ref for row in batch],
                )
            await _persist_batch(
                session,
                batch,
                jurisdiction=options.jurisdiction,
            )
            await session.commit()
            stats.inserted_records += len(batch)
            logger.info(
                "sg_parcels:batch_committed",
                inserted=len(batch),
                total_inserted=stats.inserted_records,
            )

    logger.info("sg_parcels:completed", **stats.as_dict())
    return stats


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ingest Singapore cadastral parcels into ref_parcels."
    )
    parser.add_argument(
        "--input-path",
        type=Path,
        default=DEFAULT_DATASET_PATH,
        help=(
            "Path to the Land Lot Boundary GeoJSON export "
            "(defaults to data/sg/parcels/land_lot_boundary.geojson)."
        ),
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
        help="Optional maximum number of parcels to ingest (debug/testing).",
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
        help="Upsert parcels without truncating existing Singapore entries first.",
    )
    parser.add_argument(
        "--source-epsg",
        type=int,
        default=3414,
        help="EPSG code of the source dataset coordinates (default: 3414 SVY21).",
    )
    parser.add_argument(
        "--source-label",
        default="sla_onemap",
        help="Label stored in the RefParcel.source column (default: sla_onemap).",
    )
    return parser


async def _run_from_cli(args: argparse.Namespace) -> ParcelIngestionStats:
    options = ParcelIngestionOptions(
        input_path=args.input_path.resolve(),
        jurisdiction="SG",
        batch_size=args.batch_size,
        limit=args.limit,
        skip=args.skip,
        reset=args.reset,
        source_epsg=args.source_epsg,
        source_label=args.source_label,
    )
    logger.info(
        "sg_parcels:starting",
        input=str(options.input_path),
        batch_size=options.batch_size,
        limit=options.limit,
        skip=options.skip,
        reset=options.reset,
        source_epsg=options.source_epsg,
    )
    return await ingest_parcels(options)


def main() -> None:
    parser = _build_arg_parser()
    args = parser.parse_args()
    stats = asyncio.run(_run_from_cli(args))
    print("\nSingapore parcel ingestion complete:")
    for key, value in stats.as_dict().items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
