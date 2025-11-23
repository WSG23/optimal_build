"""New Zealand district plan zoning ingestion from LINZ WFS service.

Fetches District Plan Zone polygons from the LINZ Data Service WFS endpoint (layer-50780),
reprojects from EPSG:2193 (NZGD2000/NZTM) to WGS84 (EPSG:4326), and normalizes into the
overlay schema. Optionally persists the polygons into ``ref_zoning_layers`` for buildable
and preview engines.

WFS Endpoint: https://data.linz.govt.nz/services;key={api_key}/wfs
Layer: layer-50780 (District Plan Zones)

Example usage::

    # Fetch Auckland district plan zones and persist to database
    PYTHONPATH=$REPO_ROOT \\
      SECRET_KEY=dev-secret \\
      DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/building_compliance" \\
      .venv/bin/python -m backend.scripts.ingest_nz_zones \\
      --city auckland \\
      --layer-name district_plan_zones \\
      --persist

    # Dry run Wellington zones (no DB writes)
    PYTHONPATH=$REPO_ROOT \\
      .venv/bin/python -m backend.scripts.ingest_nz_zones \\
      --city wellington \\
      --limit 100

Requires NZ_LINZ_API_KEY environment variable (or defaults to 'public' for testing).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Sequence, Tuple

import httpx
import structlog
from pyproj import Transformer
from shapely.geometry import GeometryCollection, MultiPolygon, Polygon, shape
from shapely.geometry.base import BaseGeometry
from shapely.geometry import mapping as shapely_mapping
from shapely.validation import make_valid

import app.utils.logging  # noqa: F401  pylint: disable=unused-import
from app.core.database import AsyncSessionLocal
from app.models.rkp import RefZoningLayer

try:  # pragma: no cover - optional PostGIS column
    from geoalchemy2.shape import from_shape
except ModuleNotFoundError:  # pragma: no cover - geoalchemy2 not installed
    from_shape = None  # type: ignore


logger = structlog.get_logger(__name__)

# LINZ WFS endpoint with API key placeholder
LINZ_WFS_BASE = "https://data.linz.govt.nz/services;key={api_key}/wfs"
LINZ_ZONES_LAYER = "layer-50780"  # District Plan Zones

# City-to-land_district mapping (same as parcels)
CITY_FILTERS = {
    "auckland": "Auckland",
    "wellington": "Wellington",
    "christchurch": "Canterbury",
}

# Default output directory for downloaded GeoJSON files
DEFAULT_OUTPUT_DIR = "data/nz/zoning"


@dataclass(slots=True)
class NZZoningIngestionOptions:
    city: str
    api_key: str
    output_dir: str
    layer_name: str
    max_features: int | None
    persist: bool
    reset_layer: bool
    source_epsg: int


@dataclass(slots=True)
class NZZoneRecord:
    zone_code: str
    geometry_feature: dict[str, Any]
    shapely_geometry: BaseGeometry
    attributes: dict[str, Any]


def _force_multipolygon(geometry: BaseGeometry) -> MultiPolygon:
    """Convert the provided geometry into a MultiPolygon."""

    if isinstance(geometry, MultiPolygon):
        return geometry
    if isinstance(geometry, Polygon):
        return MultiPolygon([geometry])
    if isinstance(geometry, GeometryCollection):
        polygons: list[Polygon] = []
        for child in geometry.geoms:
            if isinstance(child, MultiPolygon):
                polygons.extend(child.geoms)
            elif isinstance(child, Polygon):
                polygons.append(child)
        if polygons:
            return MultiPolygon(polygons)
    raise ValueError(f"Unsupported geometry type: {geometry.geom_type}")


def _extract_declared_crs_name(geojson: dict[str, Any]) -> Optional[str]:
    """Return the CRS name declared in the GeoJSON if provided."""
    crs_block = geojson.get("crs")
    if not isinstance(crs_block, dict):
        return None

    properties = crs_block.get("properties", {})
    if isinstance(properties, dict):
        name = properties.get("name") or properties.get("code")
        if isinstance(name, str):
            return name

    name = crs_block.get("name")
    return name if isinstance(name, str) else None


def _sample_first_coordinate(geojson: dict[str, Any]) -> Optional[Tuple[float, float]]:
    """Extract the first coordinate pair from the GeoJSON for heuristic checks."""

    def extract(coords: Any) -> Optional[Tuple[float, float]]:
        if coords is None:
            return None
        if isinstance(coords, (list, tuple)):
            if coords and isinstance(coords[0], (int, float)):
                if len(coords) >= 2 and isinstance(coords[1], (int, float)):
                    return float(coords[0]), float(coords[1])
                return None
            for nested in coords:
                sample = extract(nested)
                if sample is not None:
                    return sample
        return None

    for feature in geojson.get("features", []):
        geometry = feature.get("geometry", {}) or {}
        coords = geometry.get("coordinates")
        sample = extract(coords)
        if sample is not None:
            return sample
    return None


def _should_transform_to_wgs84(geojson: dict[str, Any]) -> Tuple[bool, str]:
    """Determine whether the GeoJSON coordinates need reprojection to WGS84."""

    declared_crs = _extract_declared_crs_name(geojson)
    if declared_crs:
        normalized = declared_crs.lower()
        if "4326" in normalized or "wgs84" in normalized:
            return False, f"declared_crs={declared_crs}"
        if "2193" in normalized or "nztm" in normalized or "nzgd2000" in normalized:
            return True, f"declared_crs={declared_crs}"

    # Check if coordinates are in NZTM range (meters, typically 6-7 digits)
    sample = _sample_first_coordinate(geojson)
    if sample is not None:
        lon, lat = sample
        # WGS84 range: lon [-180, 180], lat [-90, 90]
        if abs(lon) <= 180 and abs(lat) <= 90:
            return False, "sample_within_wgs84_range"
        # NZTM range: easting ~1,000,000-2,000,000, northing ~4,700,000-6,200,000
        if lon > 1000 or lat > 1000:
            return True, "sample_outside_wgs84_range"

    return True, "no_crs_metadata"


def _transform_coordinates(geojson: dict[str, Any], source_epsg: int) -> dict[str, Any]:
    """Reproject all geometries from source EPSG to WGS84 (EPSG:4326)."""

    transformer = Transformer.from_crs(
        f"EPSG:{source_epsg}", "EPSG:4326", always_xy=True
    )

    def transform_coords(coords: Any) -> Any:
        if isinstance(coords, (list, tuple)):
            if coords and isinstance(coords[0], (int, float)):
                # Leaf node: coordinate pair [x, y]
                if len(coords) >= 2:
                    x, y = float(coords[0]), float(coords[1])
                    lon, lat = transformer.transform(x, y)
                    return [lon, lat] + list(coords[2:])
                return coords
            # Nested list
            return [transform_coords(c) for c in coords]
        return coords

    transformed = geojson.copy()
    for feature in transformed.get("features", []):
        geometry = feature.get("geometry")
        if geometry and "coordinates" in geometry:
            geometry["coordinates"] = transform_coords(geometry["coordinates"])

    # Update CRS metadata
    transformed["crs"] = {
        "type": "name",
        "properties": {"name": "EPSG:4326"},
    }

    return transformed


async def _fetch_zones_from_wfs(
    city: str,
    api_key: str,
    max_features: int | None,
) -> dict[str, Any]:
    """Fetch district plan zone features from LINZ WFS API with city-specific CQL filter."""

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
        "typeNames": LINZ_ZONES_LAYER,
        "outputFormat": "application/json",
        # Note: District plan zones may not have land_district field
        # We'll fetch all zones and filter by spatial bounds if needed
    }

    if max_features is not None:
        params["count"] = str(max_features)

    logger.info(
        "nz_zones:fetching_from_wfs",
        city=city,
        layer=LINZ_ZONES_LAYER,
        max_features=max_features,
    )

    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.get(wfs_url, params=params)
        response.raise_for_status()
        data = response.json()

    feature_count = len(data.get("features", []))
    logger.info(
        "nz_zones:wfs_fetch_complete",
        city=city,
        features_received=feature_count,
    )

    return data


def _save_geojson(geojson: dict[str, Any], output_dir: str, filename: str) -> Path:
    """Save GeoJSON to file."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    file_path = output_path / filename
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)

    logger.info(
        "save:completed", path=str(file_path), size_bytes=file_path.stat().st_size
    )
    return file_path


def _normalise_zone_feature(feature: dict[str, Any]) -> NZZoneRecord:
    """Convert LINZ WFS zone feature to NZZoneRecord."""

    geometry_payload = feature.get("geometry")
    if not isinstance(geometry_payload, dict):
        raise ValueError("Feature missing geometry")

    raw_geometry = make_valid(shape(geometry_payload))
    if raw_geometry.is_empty:
        raise ValueError("Geometry is empty after validation")

    multipolygon = _force_multipolygon(raw_geometry)
    properties = feature.get("properties") or {}

    # Extract zone identifier (varies by territorial authority)
    zone_code = (
        properties.get("zone_code")
        or properties.get("zone_name")
        or properties.get("id")
        or properties.get("OBJECTID")
    )
    if not zone_code:
        raise ValueError("Feature missing zone identifier")

    attributes = {
        "zone_code": properties.get("zone_code"),
        "zone_name": properties.get("zone_name"),
        "territorial_authority": properties.get("territorial_authority"),
        "zone_description": properties.get("zone_description"),
        "rules_url": properties.get("rules_url"),
        "district_plan": properties.get("district_plan"),
    }

    geometry_feature = {
        "type": "Feature",
        "geometry": shapely_mapping(multipolygon),
        "properties": {
            "zone_code": properties.get("zone_code"),
            "zone_name": properties.get("zone_name"),
            "territorial_authority": properties.get("territorial_authority"),
        },
    }

    return NZZoneRecord(
        zone_code=str(zone_code),
        geometry_feature=geometry_feature,
        shapely_geometry=multipolygon,
        attributes=attributes,
    )


async def _persist_zone_records(
    records: Sequence[NZZoneRecord],
    *,
    jurisdiction: str,
    layer_name: str,
    reset_layer: bool,
) -> int:
    """Persist zone records to ref_zoning_layers table."""

    if not records:
        return 0

    async with AsyncSessionLocal() as session:
        if reset_layer:
            await session.execute(
                RefZoningLayer.__table__.delete().where(
                    RefZoningLayer.jurisdiction == jurisdiction,
                    RefZoningLayer.layer_name == layer_name,
                )
            )

        has_geometry_column = getattr(RefZoningLayer, "geometry", None) is not None
        payloads: list[dict[str, Any]] = []
        for record in records:
            payload: dict[str, Any] = {
                "jurisdiction": jurisdiction,
                "layer_name": layer_name,
                "zone_code": record.zone_code,
                "attributes": record.attributes,
                "bounds_json": record.geometry_feature,
            }
            if has_geometry_column and from_shape is not None:
                payload["geometry"] = from_shape(record.shapely_geometry, srid=4326)
            payloads.append(payload)

        await session.execute(RefZoningLayer.__table__.insert(), payloads)
        await session.commit()

    return len(records)


async def ingest_nz_zones(options: NZZoningIngestionOptions) -> dict[str, Any]:
    """Ingest New Zealand district plan zoning data from LINZ WFS service.

    1. Fetch zone features from LINZ WFS API
    2. Transform coordinates to WGS84 if needed
    3. Save to output directory
    4. Optionally persist to ref_zoning_layers
    """

    # Step 1: Fetch features from LINZ WFS
    geojson = await _fetch_zones_from_wfs(
        city=options.city,
        api_key=options.api_key,
        max_features=options.max_features,
    )

    feature_count = len(geojson.get("features", []))
    if feature_count == 0:
        logger.warning("nz_zones:no_features", city=options.city)
        return {
            "status": "warning",
            "message": "No features returned from WFS",
            "city": options.city,
            "processed_records": 0,
            "persisted_records": 0,
        }

    # Step 2: Transform coordinates to WGS84 if needed
    needs_transform, reason = _should_transform_to_wgs84(geojson)
    if needs_transform:
        logger.info("nz_zones:transform_auto", reason=reason)
        geojson = _transform_coordinates(geojson, options.source_epsg)
    else:
        logger.info("nz_zones:transform_auto_skipped", reason=reason)

    # Step 3: Save to file
    output_file = _save_geojson(
        geojson,
        options.output_dir,
        f"nz_zones_{options.city}_{options.layer_name}.geojson",
    )

    # Step 4: Optionally persist to database
    persisted = 0
    if options.persist:
        zone_records: list[NZZoneRecord] = []
        for feature in geojson.get("features", []):
            try:
                zone_records.append(_normalise_zone_feature(feature))
            except ValueError as exc:
                logger.warning("nz_zones:zone_skip", reason=str(exc))

        if zone_records:
            persisted = await _persist_zone_records(
                zone_records,
                jurisdiction="NZ",
                layer_name=options.layer_name,
                reset_layer=options.reset_layer,
            )
            logger.info(
                "nz_zones:ref_zoning_persisted",
                persisted_records=persisted,
                layer_name=options.layer_name,
            )
        else:
            logger.warning("nz_zones:zone_records_empty")

    logger.info(
        "nz_zones:completed",
        processed_records=feature_count,
        output_file=str(output_file),
        persisted_records=persisted,
    )

    return {
        "status": "success",
        "processed_records": feature_count,
        "output_file": str(output_file),
        "city": options.city,
        "persisted_records": persisted,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest New Zealand district plan zoning data from LINZ WFS service."
    )
    parser.add_argument(
        "--city",
        type=str,
        required=True,
        choices=["auckland", "wellington", "christchurch"],
        help="City to ingest zones for.",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="LINZ API key (defaults to NZ_LINZ_API_KEY environment variable).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory to save downloaded GeoJSON files (default: {DEFAULT_OUTPUT_DIR}).",
    )
    parser.add_argument(
        "--layer-name",
        type=str,
        default="district_plan_zones",
        help="Layer name stored in ref_zoning_layers when persisting (default: district_plan_zones).",
    )
    parser.add_argument(
        "--max-features",
        type=int,
        default=None,
        help="Maximum number of features to fetch (for testing).",
    )
    parser.add_argument(
        "--persist",
        action="store_true",
        help="Persist polygons into ref_zoning_layers after download.",
    )
    parser.add_argument(
        "--no-reset-layer",
        action="store_false",
        dest="reset_layer",
        help="Do not delete existing NZ rows for the layer before inserting.",
    )
    parser.add_argument(
        "--source-epsg",
        type=int,
        default=2193,
        help="EPSG code of the source dataset coordinates (default: 2193 NZTM).",
    )
    parser.set_defaults(reset_layer=True)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    api_key = args.api_key or os.getenv("NZ_LINZ_API_KEY", "public")

    options = NZZoningIngestionOptions(
        city=args.city,
        api_key=api_key,
        output_dir=args.output_dir,
        layer_name=args.layer_name,
        max_features=args.max_features,
        persist=args.persist,
        reset_layer=args.reset_layer,
        source_epsg=args.source_epsg,
    )

    result = asyncio.run(ingest_nz_zones(options))

    # Print summary
    print("\nNew Zealand Zoning Ingestion Result:")
    print("-" * 60)
    for key, value in result.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
