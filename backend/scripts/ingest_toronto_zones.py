"""Ingest Toronto zoning overlays into ``ref_zoning_layers``.

Supports local GeoJSON or fetch via Toronto Open Data (SODA/CKAN).
Defaults to EPSG:4326; override to 26917 (NAD83 / UTM zone 17N) if using projected data.

Example (local GeoJSON) ::

    PYTHONPATH=$REPO_ROOT \\
      .venv/bin/python -m backend.scripts.ingest_toronto_zones \\
      --input-path data/toronto/zoning.geojson \\
      --layer-name toronto_zoning \\
      --source-epsg 4326 \\
      --persist

Example (SODA fetch) ::

    PYTHONPATH=$REPO_ROOT \\
      .venv/bin/python -m backend.scripts.ingest_toronto_zones \\
      --dataset-id <DATASET_ID> \\
      --app-token "$TORONTO_SODA_APP_TOKEN" \\
      --layer-name toronto_zoning \\
      --persist
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Optional, Sequence, Tuple

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

try:  # pragma: no cover
    from geoalchemy2.shape import from_shape
except ModuleNotFoundError:  # pragma: no cover
    from_shape = None  # type: ignore


logger = structlog.get_logger(__name__)

SODA_BASE = "https://ckan0.cf.opendata.inter.prod-toronto.ca/datastore/odata3.0"
SODA_DEFAULT_ZONING_ID = None  # set when dataset confirmed


@dataclass(slots=True)
class ZoningIngestionOptions:
    input_path: Path | None
    dataset_id: str | None
    app_token: str
    layer_name: str
    source_epsg: int
    max_features: int | None
    persist: bool
    reset_layer: bool


@dataclass(slots=True)
class ZoneRecord:
    zone_code: str
    geometry_feature: dict[str, Any]
    shapely_geometry: BaseGeometry
    attributes: dict[str, Any]


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


def _extract_declared_crs_name(geojson: dict[str, Any]) -> Optional[str]:
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
    declared_crs = _extract_declared_crs_name(geojson)
    if declared_crs:
        normalized = declared_crs.lower()
        if "4326" in normalized or "wgs84" in normalized:
            return False, f"declared_crs={declared_crs}"
        if "26917" in normalized or "utm" in normalized:
            return True, f"declared_crs={declared_crs}"

    sample = _sample_first_coordinate(geojson)
    if sample is not None:
        lon, lat = sample
        if abs(lon) <= 180 and abs(lat) <= 90:
            return False, "sample_within_wgs84_range"
        if lon > 1000 or lat > 1000:
            return True, "sample_outside_wgs84_range"

    return True, "no_crs_metadata"


def _force_multipolygon(geometry: BaseGeometry) -> MultiPolygon:
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


def _transform_coordinates(geojson: dict[str, Any], source_epsg: int) -> dict[str, Any]:
    transformer = Transformer.from_crs(
        f"EPSG:{source_epsg}", "EPSG:4326", always_xy=True
    )

    def transform_coords(coords: Any) -> Any:
        if isinstance(coords, (list, tuple)):
            if coords and isinstance(coords[0], (int, float)):
                if len(coords) >= 2:
                    x, y = float(coords[0]), float(coords[1])
                    lon, lat = transformer.transform(x, y)
                    return [lon, lat] + list(coords[2:])
                return coords
            return [transform_coords(c) for c in coords]
        return coords

    transformed = geojson.copy()
    for feature in transformed.get("features", []):
        geometry = feature.get("geometry")
        if geometry and "coordinates" in geometry:
            geometry["coordinates"] = transform_coords(geometry["coordinates"])

    transformed["crs"] = {
        "type": "name",
        "properties": {"name": "EPSG:4326"},
    }
    return transformed


def _normalise_zone_feature(feature: dict[str, Any]) -> ZoneRecord:
    geometry_payload = feature.get("geometry")
    if not isinstance(geometry_payload, dict):
        raise ValueError("Feature missing geometry")

    raw_geometry = make_valid(shape(geometry_payload))
    if raw_geometry.is_empty:
        raise ValueError("Geometry is empty after validation")

    multipolygon = _force_multipolygon(raw_geometry)
    properties = feature.get("properties") or {}

    zone_code = (
        properties.get("ZONE_CODE")  # Generic field
        or properties.get("ZONE")  # Generic field
        or properties.get("ZN_ZONE")  # Toronto primary zone code
        or properties.get("GEN_ZONE")  # Toronto general zone
        or properties.get("OBJECTID")  # Generic field
        or properties.get("_id")  # Toronto feature ID
    )
    if not zone_code:
        raise ValueError("Feature missing zone identifier")

    attributes = {
        "zone_code": (
            properties.get("ZONE_CODE")
            or properties.get("ZONE")
            or properties.get("ZN_ZONE")
            or properties.get("GEN_ZONE")
        ),
        "zone_desc": properties.get("ZONE_DESC"),
        "bylaw": properties.get("BYLAW"),
        "shape_area": properties.get("shape_area") or properties.get("ZN_AREA"),
        # Toronto-specific fields
        "gen_zone": properties.get("GEN_ZONE"),
        "zn_zone": properties.get("ZN_ZONE"),
        "zn_holding": properties.get("ZN_HOLDING"),
        "holding_id": properties.get("HOLDING_ID"),
        "frontage": properties.get("FRONTAGE"),
        "units": properties.get("UNITS"),
        "density": properties.get("DENSITY"),
        "coverage": properties.get("COVERAGE"),
        "fsi_total": properties.get("FSI_TOTAL"),
        "prcnt_comm": properties.get("PRCNT_COMM"),
        "prcnt_res": properties.get("PRCNT_RES"),
        "prcnt_emmp": properties.get("PRCNT_EMMP"),
        "prcnt_offc": properties.get("PRCNT_OFFC"),
    }

    geometry_feature = {
        "type": "Feature",
        "geometry": shapely_mapping(multipolygon),
        "properties": {"zone_code": zone_code},
    }

    return ZoneRecord(
        zone_code=str(zone_code),
        geometry_feature=geometry_feature,
        shapely_geometry=multipolygon,
        attributes=attributes,
    )


async def _persist_zone_records(
    records: Sequence[ZoneRecord],
    *,
    jurisdiction: str,
    layer_name: str,
    reset_layer: bool,
) -> int:
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


async def _fetch_zones_from_soda(
    dataset_id: str,
    app_token: str,
    max_features: int | None,
) -> dict[str, Any]:
    if not dataset_id:
        raise ValueError("dataset_id is required for SODA/CKAN fetches")

    params: dict[str, str] = {"$format": "geojson"}
    if max_features is not None:
        params["$top"] = str(max_features)

    headers = {}
    if app_token and app_token != "public":
        headers["X-App-Token"] = app_token

    url = f"{SODA_BASE}/{dataset_id}"
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

    return data


async def ingest_toronto_zones(options: ZoningIngestionOptions) -> dict[str, Any]:
    if options.input_path:
        data_bytes = options.input_path.read_bytes()
        geojson = json.loads(data_bytes)
    else:
        geojson = await _fetch_zones_from_soda(
            dataset_id=options.dataset_id or "",
            app_token=options.app_token,
            max_features=options.max_features,
        )

    needs_transform, reason = _should_transform_to_wgs84(geojson)
    if needs_transform:
        logger.info("toronto_zones:transform_auto", reason=reason)
        geojson = _transform_coordinates(geojson, options.source_epsg)
    else:
        logger.info("toronto_zones:transform_skipped", reason=reason)

    persisted = 0
    feature_count = len(geojson.get("features", []))
    if options.persist:
        zone_records: list[ZoneRecord] = []
        for feature in geojson.get("features", []):
            try:
                zone_records.append(_normalise_zone_feature(feature))
            except ValueError as exc:
                logger.warning("toronto_zones:zone_skip", reason=str(exc))

        if zone_records:
            persisted = await _persist_zone_records(
                zone_records,
                jurisdiction="TOR",
                layer_name=options.layer_name,
                reset_layer=options.reset_layer,
            )
            logger.info(
                "toronto_zones:ref_zoning_persisted",
                persisted_records=persisted,
                layer_name=options.layer_name,
            )
        else:
            logger.warning("toronto_zones:zone_records_empty")

    logger.info(
        "toronto_zones:completed",
        processed_records=feature_count,
        persisted_records=persisted,
        layer_name=options.layer_name,
    )

    return {
        "status": "success",
        "processed_records": feature_count,
        "persisted_records": persisted,
        "layer_name": options.layer_name,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest Toronto zoning overlays into ref_zoning_layers."
    )
    parser.add_argument(
        "--input-path",
        type=Path,
        default=None,
        help="Path to zoning GeoJSON. If omitted, fetches from SODA/CKAN.",
    )
    parser.add_argument(
        "--dataset-id",
        type=str,
        default=SODA_DEFAULT_ZONING_ID,
        help="Dataset ID for zoning polygons (Toronto).",
    )
    parser.add_argument(
        "--app-token",
        type=str,
        default=None,
        help="Optional app token (defaults to TORONTO_SODA_APP_TOKEN).",
    )
    parser.add_argument(
        "--layer-name",
        type=str,
        default="toronto_zoning",
        help="Layer name stored in ref_zoning_layers (default: toronto_zoning).",
    )
    parser.add_argument(
        "--max-features",
        type=int,
        default=None,
        help="Maximum features to fetch (for testing).",
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
        help="Do not delete existing TOR rows for the layer before inserting.",
    )
    parser.add_argument(
        "--source-epsg",
        type=int,
        default=4326,
        help="EPSG code of the source dataset (default: 4326; use 26917 for UTM).",
    )
    parser.set_defaults(reset_layer=True)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    app_token = args.app_token or os.getenv("TORONTO_SODA_APP_TOKEN", "public")

    options = ZoningIngestionOptions(
        input_path=args.input_path.resolve() if args.input_path else None,
        dataset_id=args.dataset_id,
        app_token=app_token,
        layer_name=args.layer_name,
        source_epsg=args.source_epsg,
        max_features=args.max_features,
        persist=args.persist,
        reset_layer=args.reset_layer,
    )

    result = asyncio.run(ingest_toronto_zones(options))

    print("\nToronto Zoning Ingestion Result:")
    print("-" * 60)
    for key, value in result.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
