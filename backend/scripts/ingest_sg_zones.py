"""Ingest Singapore URA Master Plan land-use polygons into ref_zoning_layers.

The default source is data.gov.sg's "Master Plan 2019 Land Use layer" dataset.
The script can either fetch the public download URL or ingest a local GeoJSON
file that was already downloaded.
"""

from __future__ import annotations

import argparse
import asyncio
import html
import importlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Sequence

import httpx
import structlog
from shapely.geometry import GeometryCollection, MultiPolygon, Polygon, shape
from shapely.geometry import mapping as shapely_mapping
from shapely.geometry.base import BaseGeometry
from shapely.validation import make_valid

from app.core.database import AsyncSessionLocal
from app.models.rkp import RefZoningLayer

try:  # pragma: no cover - optional dependency when PostGIS disabled
    geoalchemy_shape = importlib.import_module("geoalchemy2.shape")
except ModuleNotFoundError:  # pragma: no cover
    from_shape = None
else:
    from_shape = getattr(geoalchemy_shape, "from_shape", None)

logger = structlog.get_logger(__name__)

SG_MASTER_PLAN_2019_DATASET_ID = "d_90d86daa5bfaa371668b84fa5f01424f"
DATA_GOV_POLL_DOWNLOAD_URL = (
    "https://api-open.data.gov.sg/v1/public/api/datasets/"
    f"{SG_MASTER_PLAN_2019_DATASET_ID}/poll-download"
)
DEFAULT_OUTPUT_PATH = Path("data/sg/zoning/master_plan_2019_land_use.geojson")


@dataclass(slots=True)
class SGZoneIngestionOptions:
    input_path: Path | None
    output_path: Path
    layer_name: str
    max_features: int | None
    persist: bool
    reset_layer: bool
    download: bool


@dataclass(slots=True)
class SGZoneRecord:
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


async def _download_master_plan_geojson(output_path: Path) -> Path:
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
                polygons.extend(child.geoms)
            elif isinstance(child, Polygon):
                polygons.append(child)
        if polygons:
            return MultiPolygon(polygons)
    raise ValueError(f"Unsupported geometry type: {geometry.geom_type}")


def _extract_description_attributes(description: object) -> dict[str, str]:
    if not isinstance(description, str) or not description:
        return {}
    rows = re.findall(
        r"<th[^>]*>\s*([^<]+?)\s*</th>\s*<td[^>]*>\s*(.*?)\s*</td>",
        description,
        flags=re.IGNORECASE | re.DOTALL,
    )
    attrs: dict[str, str] = {}
    for key, value in rows:
        cleaned_key = html.unescape(re.sub(r"<[^>]+>", "", key)).strip()
        cleaned_value = html.unescape(re.sub(r"<[^>]+>", "", value)).strip()
        if cleaned_key:
            attrs[cleaned_key] = cleaned_value
    return attrs


def _property_value(properties: dict[str, Any], key: str) -> Any:
    if key in properties:
        return properties[key]
    for candidate_key, value in properties.items():
        if candidate_key.lower() == key.lower():
            return value
    return None


def _normalise_zone_code(land_use: str) -> str:
    normalized = land_use.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")
    if not normalized:
        raise ValueError("Land-use description is empty")
    if normalized in {"business_1", "business_2", "business_park"}:
        return f"SG:{normalized}"
    if normalized.startswith("residential"):
        return "SG:residential"
    if normalized.startswith("commercial"):
        return "SG:commercial"
    if normalized.startswith("white") or normalized == "mixed_use":
        return "SG:mixed_use"
    if "industrial" in normalized:
        return "SG:industrial"
    return f"SG:{normalized}"


def _normalise_zone_feature(feature: dict[str, Any]) -> SGZoneRecord:
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
    description_attrs = _extract_description_attributes(properties.get("Description"))
    merged = {**description_attrs, **properties}

    land_use = _property_value(merged, "LU_DESC")
    if not isinstance(land_use, str) or not land_use.strip():
        raise ValueError("Feature missing LU_DESC")

    gpr = _property_value(merged, "GPR")
    zone_code = _normalise_zone_code(land_use)
    attributes = {
        "LU_DESC": land_use.strip().title(),
        "LU_TEXT": _property_value(merged, "LU_TEXT"),
        "GPR": str(gpr).strip() if gpr is not None else None,
        "WHI_Q_MX": _property_value(merged, "WHI_Q_MX"),
        "GPR_B_MN": _property_value(merged, "GPR_B_MN"),
        "INC_CRC": _property_value(merged, "INC_CRC"),
        "FMEL_UPD_D": _property_value(merged, "FMEL_UPD_D"),
        "OBJECTID": _property_value(merged, "OBJECTID"),
        "source_dataset_id": SG_MASTER_PLAN_2019_DATASET_ID,
        "source_title": "URA Master Plan 2019 Land Use layer",
    }
    attributes = {
        key: value for key, value in attributes.items() if value not in (None, "")
    }

    geometry_feature = {
        "type": "Feature",
        "geometry": shapely_mapping(multipolygon),
        "properties": {
            "zone_code": zone_code,
            "LU_DESC": attributes.get("LU_DESC"),
            "GPR": attributes.get("GPR"),
        },
    }
    return SGZoneRecord(
        zone_code=zone_code,
        geometry_feature=geometry_feature,
        shapely_geometry=multipolygon,
        attributes=attributes,
    )


async def _persist_zone_records(
    records: Sequence[SGZoneRecord],
    *,
    layer_name: str,
    reset_layer: bool,
) -> int:
    if not records:
        return 0
    async with AsyncSessionLocal() as session:
        if reset_layer:
            await session.execute(
                RefZoningLayer.__table__.delete().where(
                    RefZoningLayer.jurisdiction == "SG",
                    RefZoningLayer.layer_name == layer_name,
                )
            )
        has_geometry_column = getattr(RefZoningLayer, "geometry", None) is not None
        payloads: list[dict[str, Any]] = []
        for record in records:
            payload: dict[str, Any] = {
                "jurisdiction": "SG",
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


async def ingest_sg_zones(options: SGZoneIngestionOptions) -> dict[str, Any]:
    input_path = options.input_path
    if options.download or input_path is None:
        input_path = await _download_master_plan_geojson(options.output_path)

    records: list[SGZoneRecord] = []
    skipped = 0
    for index, feature in enumerate(_iter_geojson_features(input_path)):
        if options.max_features is not None and index >= options.max_features:
            break
        try:
            records.append(_normalise_zone_feature(feature))
        except ValueError as exc:
            skipped += 1
            logger.warning("sg_zones:zone_skip", reason=str(exc))

    persisted = 0
    if options.persist:
        persisted = await _persist_zone_records(
            records,
            layer_name=options.layer_name,
            reset_layer=options.reset_layer,
        )

    logger.info(
        "sg_zones:completed",
        processed_records=len(records) + skipped,
        persisted_records=persisted,
        skipped_records=skipped,
        layer_name=options.layer_name,
        input_path=str(input_path),
    )
    return {
        "status": "success",
        "processed_records": len(records) + skipped,
        "persisted_records": persisted,
        "skipped_records": skipped,
        "layer_name": options.layer_name,
        "input_path": str(input_path),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest Singapore URA Master Plan land-use polygons."
    )
    parser.add_argument(
        "--input-path",
        type=Path,
        default=None,
        help="Path to local URA Master Plan land-use GeoJSON.",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Path to save downloaded GeoJSON when fetching from data.gov.sg.",
    )
    parser.add_argument(
        "--layer-name",
        type=str,
        default="ura_master_plan_2019_land_use",
        help="Layer name stored in ref_zoning_layers.",
    )
    parser.add_argument(
        "--max-features",
        type=int,
        default=None,
        help="Maximum features to process, useful for tests or smoke runs.",
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download the data.gov.sg GeoJSON before ingesting.",
    )
    parser.add_argument(
        "--persist",
        action="store_true",
        help="Persist polygons into ref_zoning_layers.",
    )
    parser.add_argument(
        "--no-reset-layer",
        action="store_false",
        dest="reset_layer",
        help="Do not delete existing SG rows for the layer before inserting.",
    )
    parser.set_defaults(reset_layer=True)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    input_path = args.input_path.resolve() if args.input_path else None
    output_path = args.output_path.resolve()
    should_download = args.download or input_path is None
    if not should_download and input_path is not None and not input_path.exists():
        raise FileNotFoundError(input_path)

    result = asyncio.run(
        ingest_sg_zones(
            SGZoneIngestionOptions(
                input_path=input_path,
                output_path=output_path,
                layer_name=args.layer_name,
                max_features=args.max_features,
                persist=args.persist,
                reset_layer=args.reset_layer,
                download=should_download,
            )
        )
    )
    print("\nSingapore URA Zoning Ingestion Result:")
    print("-" * 60)
    for key, value in result.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    # Keep import side effects deterministic in tests; runtime env is consumed by
    # the app settings and database layers.
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    main()
