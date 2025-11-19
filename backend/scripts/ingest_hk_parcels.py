"""Stream Hong Kong cadastral parcels into ``ref_parcels``.

This loader consumes the CSDI lot GeoJSON export (HK80 Grid / EPSG:2326),
projects every polygon into WGS84, and upserts the derived geometry into the
reference parcels table so the buildable + preview engines can work with
Hong Kong sites the same way they do for Singapore.

Example usage::

    # Default dataset path (data/hk/lots/...LOT_converted.json)
    PYTHONPATH=. \\
      .venv/bin/python -m backend.scripts.ingest_hk_parcels \\
      --batch-size 2000 --limit 5000

    # Run against a custom GeoJSON export without truncating existing data
    PYTHONPATH=. \\
      .venv/bin/python -m backend.scripts.ingest_hk_parcels \\
      --input-path /tmp/lot_subset.geojson --no-reset

The loader only requires read access to the GeoJSON file; no internet access or
API keys are necessary once the dataset has been downloaded from CSDI.
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

DEFAULT_DATASET_PATH = Path(
    "data/hk/lots/LandParcel_Lot_PUBLIC_20251014.gdb_LOT_converted.json"
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
    lot_identifier = (
        properties.get("LOTCSUID")
        or properties.get("LOTID")
        or properties.get("OBJECTID")
    )
    if lot_identifier is None:
        raise ValueError("Feature missing LOT identifier")

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
            "lot_id": properties.get("LOTID"),
            "lotcsuid": properties.get("LOTCSUID"),
            "object_id": properties.get("OBJECTID"),
            "source_area": properties.get("SHAPE_Area"),
            "source_perimeter": properties.get("SHAPE_Length"),
        },
    }

    zone_code = properties.get("ZONE_CODE")
    if zone_code is not None:
        feature_geojson["zone_code"] = zone_code

    return ParcelRecord(
        parcel_ref=f"HK:LOT:{lot_identifier}",
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
            logger.info("hk_parcels:cleared_existing", removed=removed)

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
                    "hk_parcels:feature_skipped",
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
                    "hk_parcels:batch_committed",
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
                "hk_parcels:batch_committed",
                inserted=len(batch),
                total_inserted=stats.inserted_records,
            )

    logger.info("hk_parcels:completed", **stats.as_dict())
    return stats


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ingest Hong Kong cadastral parcels into ref_parcels."
    )
    parser.add_argument(
        "--input-path",
        type=Path,
        default=DEFAULT_DATASET_PATH,
        help=(
            "Path to the lot GeoJSON export (defaults to data/hk/lots/...LOT_converted.json)."
        ),
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Number of parcels to insert per transaction (default: 500).",
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
        help="Upsert parcels without truncating existing HK entries first.",
    )
    parser.add_argument(
        "--source-epsg",
        type=int,
        default=2326,
        help="EPSG code of the source dataset coordinates (default: 2326 HK80 Grid).",
    )
    parser.add_argument(
        "--source-label",
        default="csdi_lot",
        help="Label stored in the RefParcel.source column (default: csdi_lot).",
    )
    return parser


async def _run_from_cli(args: argparse.Namespace) -> ParcelIngestionStats:
    options = ParcelIngestionOptions(
        input_path=args.input_path.resolve(),
        jurisdiction="HK",
        batch_size=args.batch_size,
        limit=args.limit,
        skip=args.skip,
        reset=args.reset,
        source_epsg=args.source_epsg,
        source_label=args.source_label,
    )
    logger.info(
        "hk_parcels:starting",
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
    print("\nHong Kong parcel ingestion complete:")
    for key, value in stats.as_dict().items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
