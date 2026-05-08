"""Ingest Singapore URA Master Plan building footprints.

The source is data.gov.sg's "Master Plan 2019 Building layer". Capture uses
these indicative footprints to classify parcels as vacant, developed, or
uncertain before current GFA evidence is available.
"""

from __future__ import annotations

import argparse
import asyncio
import importlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Sequence

import httpx
import structlog
from shapely.geometry import GeometryCollection, MultiPolygon, Polygon, shape
from shapely.geometry import mapping as shapely_mapping
from shapely.geometry.base import BaseGeometry
from shapely.validation import make_valid
from sqlalchemy import delete, insert

from app.core.database import AsyncSessionLocal, engine
from app.models.rkp import RefBuildingFootprint

try:  # pragma: no cover - optional PostGIS column
    geoalchemy_shape = importlib.import_module("geoalchemy2.shape")
except ModuleNotFoundError:  # pragma: no cover
    from_shape = None
else:
    from_shape = getattr(geoalchemy_shape, "from_shape", None)


logger = structlog.get_logger(__name__)

SG_MASTER_PLAN_2019_BUILDING_DATASET_ID = "d_e8e3249d4433845bdd8034ae44329d9e"
DATA_GOV_POLL_DOWNLOAD_URL = (
    "https://api-open.data.gov.sg/v1/public/api/datasets/"
    f"{SG_MASTER_PLAN_2019_BUILDING_DATASET_ID}/poll-download"
)
DEFAULT_DATASET_PATH = Path("data/sg/buildings/master_plan_2019_building.geojson")


@dataclass(slots=True)
class BuildingFootprintIngestionOptions:
    input_path: Path
    jurisdiction: str
    layer_name: str
    batch_size: int
    limit: int | None
    reset: bool
    source_label: str
    download: bool


@dataclass(slots=True)
class BuildingFootprintRecord:
    footprint_ref: str
    geometry_feature: dict[str, Any]
    shapely_geometry: BaseGeometry
    centroid_lat: float
    centroid_lon: float
    area_m2: float
    attributes: dict[str, Any]
    source_label: str


@dataclass(slots=True)
class BuildingFootprintIngestionStats:
    seen_features: int = 0
    processed_records: int = 0
    inserted_records: int = 0
    invalid_features: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "seen_features": self.seen_features,
            "processed_records": self.processed_records,
            "inserted_records": self.inserted_records,
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


async def _download_building_geojson(output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    async with httpx.AsyncClient(timeout=180.0, follow_redirects=True) as client:
        poll_response = await client.get(DATA_GOV_POLL_DOWNLOAD_URL)
        poll_response.raise_for_status()
        poll_payload = poll_response.json()
        if poll_payload.get("code") != 0:
            raise RuntimeError(poll_payload.get("errMsg") or "data.gov.sg poll failed")
        download_url = poll_payload.get("data", {}).get("url")
        if not isinstance(download_url, str) or not download_url:
            raise RuntimeError(
                "data.gov.sg poll response did not include a download URL"
            )

        async with client.stream("GET", download_url) as response:
            response.raise_for_status()
            with output_path.open("wb") as handle:
                async for chunk in response.aiter_bytes():
                    handle.write(chunk)
    logger.info("sg_buildings:downloaded", output_path=str(output_path))
    return output_path


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


def _feature_identifier(properties: dict[str, Any]) -> str | None:
    for key in ("OBJECTID", "INC_CRC", "BLDG_ID", "BUILDING_ID"):
        value = properties.get(key)
        if value not in (None, ""):
            return str(value).strip()
    return None


def _normalise_feature(
    feature: dict[str, Any],
    *,
    source_label: str,
) -> BuildingFootprintRecord:
    geometry_payload = feature.get("geometry")
    if not isinstance(geometry_payload, dict):
        raise ValueError("Feature missing geometry")

    raw_geometry = make_valid(shape(geometry_payload))
    if raw_geometry.is_empty:
        raise ValueError("Geometry is empty after validation")
    multipolygon = _force_multipolygon(raw_geometry)

    properties = feature.get("properties") or {}
    if not isinstance(properties, dict):
        properties = {}

    identifier = _feature_identifier(properties)
    if identifier is None:
        raise ValueError("Feature missing building identifier")

    area_m2 = (
        properties.get("SHAPE.AREA")
        or properties.get("SHAPE_Area")
        or properties.get("shape_area")
    )
    if area_m2 is not None:
        area = float(area_m2)
    else:
        area = float(multipolygon.area)
    if math.isclose(area, 0.0):
        raise ValueError("Building footprint area is zero")

    centroid = multipolygon.centroid
    attributes = {
        "OBJECTID": properties.get("OBJECTID"),
        "BLDG_TYPE": properties.get("BLDG_TYPE"),
        "INC_CRC": properties.get("INC_CRC"),
        "FMEL_UPD_D": properties.get("FMEL_UPD_D"),
        "source_dataset_id": SG_MASTER_PLAN_2019_BUILDING_DATASET_ID,
        "source_title": "URA Master Plan 2019 Building layer",
    }
    attributes = {
        key: value for key, value in attributes.items() if value not in (None, "")
    }

    geometry_feature = {
        "type": "Feature",
        "geometry": shapely_mapping(multipolygon),
        "properties": {
            "footprint_ref": f"SG:BUILDING:{identifier}",
            "source_dataset_id": SG_MASTER_PLAN_2019_BUILDING_DATASET_ID,
        },
    }
    return BuildingFootprintRecord(
        footprint_ref=f"SG:BUILDING:{identifier}",
        geometry_feature=geometry_feature,
        shapely_geometry=multipolygon,
        centroid_lat=float(centroid.y),
        centroid_lon=float(centroid.x),
        area_m2=area,
        attributes=attributes,
        source_label=source_label,
    )


async def _persist_batch(
    session,
    rows: Sequence[BuildingFootprintRecord],
    *,
    jurisdiction: str,
    layer_name: str,
) -> None:
    if not rows:
        return

    payloads: list[dict[str, Any]] = []
    has_geometry_column = getattr(RefBuildingFootprint, "geometry", None) is not None
    for row in rows:
        payload: dict[str, Any] = {
            "jurisdiction": jurisdiction,
            "layer_name": layer_name,
            "footprint_ref": row.footprint_ref,
            "bounds_json": row.geometry_feature,
            "centroid_lat": row.centroid_lat,
            "centroid_lon": row.centroid_lon,
            "area_m2": row.area_m2,
            "attributes": row.attributes,
            "source": row.source_label,
        }
        if has_geometry_column and from_shape is not None:
            payload["geometry"] = from_shape(row.shapely_geometry, srid=4326)
        payloads.append(payload)

    await session.execute(insert(RefBuildingFootprint).values(payloads))


async def _delete_existing(session, jurisdiction: str, layer_name: str) -> int:
    stmt = delete(RefBuildingFootprint).where(
        RefBuildingFootprint.jurisdiction == jurisdiction,
        RefBuildingFootprint.layer_name == layer_name,
    )
    result = await session.execute(stmt)
    return result.rowcount or 0


async def _ensure_reference_table() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(RefBuildingFootprint.__table__.create, checkfirst=True)


async def ingest_building_footprints(
    options: BuildingFootprintIngestionOptions,
) -> BuildingFootprintIngestionStats:
    stats = BuildingFootprintIngestionStats()
    input_path = options.input_path
    if options.download or not input_path.exists():
        input_path = await _download_building_geojson(input_path)

    await _ensure_reference_table()

    async with AsyncSessionLocal() as session:
        if options.reset:
            removed = await _delete_existing(
                session,
                options.jurisdiction,
                options.layer_name,
            )
            await session.commit()
            logger.info("sg_buildings:cleared_existing", removed=removed)

    async with AsyncSessionLocal() as session:
        batch: list[BuildingFootprintRecord] = []
        for feature in _iter_geojson_features(input_path):
            stats.seen_features += 1
            if options.limit is not None and stats.processed_records >= options.limit:
                break
            try:
                record = _normalise_feature(feature, source_label=options.source_label)
            except (TypeError, ValueError) as exc:
                stats.invalid_features += 1
                logger.warning("sg_buildings:feature_skipped", reason=str(exc))
                continue

            batch.append(record)
            stats.processed_records += 1
            if len(batch) >= options.batch_size:
                await _persist_batch(
                    session,
                    batch,
                    jurisdiction=options.jurisdiction,
                    layer_name=options.layer_name,
                )
                await session.commit()
                stats.inserted_records += len(batch)
                logger.info(
                    "sg_buildings:batch_committed",
                    inserted=len(batch),
                    total_inserted=stats.inserted_records,
                )
                batch.clear()

        if batch:
            await _persist_batch(
                session,
                batch,
                jurisdiction=options.jurisdiction,
                layer_name=options.layer_name,
            )
            await session.commit()
            stats.inserted_records += len(batch)
            logger.info(
                "sg_buildings:batch_committed",
                inserted=len(batch),
                total_inserted=stats.inserted_records,
            )

    logger.info("sg_buildings:completed", **stats.as_dict())
    return stats


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ingest Singapore building footprints into ref_building_footprints."
    )
    parser.add_argument(
        "--input-path",
        type=Path,
        default=DEFAULT_DATASET_PATH,
        help="Path to the Master Plan 2019 Building layer GeoJSON export.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Number of footprints to insert per transaction.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional maximum number of footprints to ingest.",
    )
    parser.add_argument(
        "--no-reset",
        action="store_false",
        dest="reset",
        help="Append without clearing existing Singapore building footprints.",
    )
    parser.add_argument(
        "--source-label",
        default="ura_data_gov",
        help="Label stored in RefBuildingFootprint.source.",
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="Fetch the latest building footprint GeoJSON from data.gov.sg.",
    )
    return parser


async def _run_from_cli(args: argparse.Namespace) -> BuildingFootprintIngestionStats:
    options = BuildingFootprintIngestionOptions(
        input_path=args.input_path.resolve(),
        jurisdiction="SG",
        layer_name="ura_master_plan_2019_building",
        batch_size=args.batch_size,
        limit=args.limit,
        reset=args.reset,
        source_label=args.source_label,
        download=args.download,
    )
    logger.info(
        "sg_buildings:starting",
        input=str(options.input_path),
        batch_size=options.batch_size,
        limit=options.limit,
        reset=options.reset,
    )
    return await ingest_building_footprints(options)


def main() -> None:
    args = _build_arg_parser().parse_args()
    stats = asyncio.run(_run_from_cli(args))
    print("\nSingapore building footprint ingestion complete:")
    for key, value in stats.as_dict().items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
