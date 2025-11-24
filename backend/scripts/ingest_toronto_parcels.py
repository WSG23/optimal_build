"""Ingest Toronto parcels into ``ref_parcels``.

Supports reading from a pre-downloaded GeoJSON export (recommended) or fetching
from the Toronto Open Data SODA/CKAN endpoint when a dataset ID is provided.

Defaults assume GeoJSON is already WGS84 (EPSG:4326). Override ``--source-epsg``
to 26917 (NAD83 / UTM zone 17N) if using projected exports.

Example usage (local GeoJSON) ::

    PYTHONPATH=$REPO_ROOT \\
      .venv/bin/python -m backend.scripts.ingest_toronto_parcels \\
      --input-path data/toronto/parcels.geojson \\
      --batch-size 1000 \\
      --source-epsg 4326 \\
      --persist

Example usage (SODA fetch) ::

    PYTHONPATH=$REPO_ROOT \\
      .venv/bin/python -m backend.scripts.ingest_toronto_parcels \\
      --dataset-id <DATASET_ID> \\
      --app-token "$TORONTO_SODA_APP_TOKEN" \\
      --limit 5000 \\
      --source-epsg 4326 \\
      --persist
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

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

try:  # pragma: no cover
    from geoalchemy2.shape import from_shape
except ModuleNotFoundError:  # pragma: no cover
    from_shape = None  # type: ignore


logger = structlog.get_logger(__name__)

SODA_BASE = "https://ckan0.cf.opendata.inter.prod-toronto.ca/datastore/odata3.0"  # Toronto CKAN OData; adjust if using SODA JSON
SODA_DEFAULT_DATASET_ID = None  # e.g., placeholder until confirmed

IDENTIFIER_FIELDS = (
    "ROLL_NUM",
    "ARN",
    "PIN",
    "OBJECTID",
    "PARCEL_ID",
)


@dataclass(slots=True)
class ParcelIngestionOptions:
    input_path: Path | None
    dataset_id: str | None
    app_token: str
    jurisdiction: str
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


def _iter_geojson_features(path: Path) -> Iterator[dict[str, Any]]:
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
        if polygons:
            return MultiPolygon(polygons)
    raise ValueError(f"Unsupported geometry type: {geometry.geom_type}")


def _resolve_parcel_identifier(properties: Mapping[str, Any]) -> str | None:
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
    parcel_id = _resolve_parcel_identifier(properties)
    if parcel_id is None:
        raise ValueError("Feature missing parcel identifier")

    area_m2 = float(properties.get("area") or raw_geometry.area)
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
            "parcel_id": parcel_id,
            "roll_num": properties.get("ROLL_NUM"),
            "arn": properties.get("ARN"),
            "pin": properties.get("PIN"),
            "source_area": properties.get("area"),
        },
    }

    return ParcelRecord(
        parcel_ref=f"TOR:PARCEL:{parcel_id}",
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


async def _fetch_parcels_from_soda(
    *,
    dataset_id: str,
    app_token: str,
    limit: int | None,
    skip: int,
) -> list[dict[str, Any]]:
    if not dataset_id:
        raise ValueError("dataset_id is required for SODA/CKAN fetches")

    params: dict[str, str] = {"$format": "geojson"}
    if limit is not None:
        params["$top"] = str(limit)
    if skip > 0:
        params["$skip"] = str(skip)

    headers = {}
    if app_token and app_token != "public":
        headers["X-App-Token"] = app_token

    url = f"{SODA_BASE}/{dataset_id}"
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

    return data.get("features", [])


async def ingest_parcels(options: ParcelIngestionOptions) -> ParcelIngestionStats:
    stats = ParcelIngestionStats()
    transformer = Transformer.from_crs(
        f"EPSG:{options.source_epsg}", "EPSG:4326", always_xy=True
    )

    async with AsyncSessionLocal() as session:
        if options.reset and options.persist:
            removed = await _delete_existing(session, options.jurisdiction)
            await session.commit()
            logger.info("toronto_parcels:cleared_existing", removed=removed)

    if options.input_path:
        feature_iter = _iter_geojson_features(options.input_path)
    else:
        features = await _fetch_parcels_from_soda(
            dataset_id=options.dataset_id or "",
            app_token=options.app_token,
            limit=options.limit,
            skip=options.skip,
        )
        feature_iter = iter(features)

    async with AsyncSessionLocal() as session:
        batch: list[ParcelRecord] = []
        for feature_index, feature in enumerate(feature_iter):
            stats.seen_features += 1
            if feature_index < options.skip and options.input_path:
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
                    "toronto_parcels:feature_skipped",
                    reason=str(exc),
                    feature_index=feature_index,
                )
                continue

            batch.append(record)
            stats.processed_records += 1

            if len(batch) >= options.batch_size:
                if not options.reset and options.persist:
                    await _delete_specific(
                        session,
                        options.jurisdiction,
                        [row.parcel_ref for row in batch],
                    )
                if options.persist:
                    await _persist_batch(
                        session,
                        batch,
                        jurisdiction=options.jurisdiction,
                    )
                    await session.commit()
                    stats.inserted_records += len(batch)
                    logger.info(
                        "toronto_parcels:batch_committed",
                        inserted=len(batch),
                        total_inserted=stats.inserted_records,
                    )
                batch.clear()

        if batch:
            if not options.reset and options.persist:
                await _delete_specific(
                    session,
                    options.jurisdiction,
                    [row.parcel_ref for row in batch],
                )
            if options.persist:
                await _persist_batch(
                    session,
                    batch,
                    jurisdiction=options.jurisdiction,
                )
                await session.commit()
                stats.inserted_records += len(batch)
                logger.info(
                    "toronto_parcels:batch_committed",
                    inserted=len(batch),
                    total_inserted=stats.inserted_records,
                )

    logger.info("toronto_parcels:completed", **stats.as_dict())
    return stats


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ingest Toronto parcels into ref_parcels."
    )
    parser.add_argument(
        "--input-path",
        type=Path,
        default=None,
        help="Path to GeoJSON export. If omitted, fetches from SODA/CKAN.",
    )
    parser.add_argument(
        "--dataset-id",
        type=str,
        default=SODA_DEFAULT_DATASET_ID,
        help="Dataset ID for parcels (Toronto CKAN/SODA).",
    )
    parser.add_argument(
        "--app-token",
        type=str,
        default=None,
        help="Optional app token (defaults to TORONTO_SODA_APP_TOKEN env var).",
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
        help="Upsert parcels without truncating existing TOR entries first.",
    )
    parser.add_argument(
        "--persist",
        action="store_true",
        help="Write results to the database (otherwise dry-run).",
    )
    parser.add_argument(
        "--source-epsg",
        type=int,
        default=4326,
        help="EPSG code of the source dataset (default: 4326 WGS84; use 26917 for UTM).",
    )
    parser.add_argument(
        "--source-label",
        default="toronto_open_data",
        help="Label stored in RefParcel.source (default: toronto_open_data).",
    )
    parser.set_defaults(reset=True)
    return parser


async def _run_from_cli(args: argparse.Namespace) -> ParcelIngestionStats:
    app_token = args.app_token or os.getenv("TORONTO_SODA_APP_TOKEN", "public")

    options = ParcelIngestionOptions(
        input_path=args.input_path.resolve() if args.input_path else None,
        dataset_id=args.dataset_id,
        app_token=app_token,
        jurisdiction="TOR",
        batch_size=args.batch_size,
        limit=args.limit,
        skip=args.skip,
        reset=args.reset,
        persist=args.persist,
        source_epsg=args.source_epsg,
        source_label=args.source_label,
    )
    logger.info(
        "toronto_parcels:starting",
        source="file" if options.input_path else "soda",
        dataset_id=options.dataset_id,
        input=str(options.input_path) if options.input_path else None,
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
    print("\nToronto parcel ingestion complete:")
    for key, value in stats.as_dict().items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
