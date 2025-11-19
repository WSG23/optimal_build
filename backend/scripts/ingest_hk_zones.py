"""Hong Kong zoning ingestion from Planning Department WFS service.

Fetches Regulated Area polygons from the CSDI WFS endpoint, reprojects from
EPSG:2326 (HK80 Grid) to WGS84 (EPSG:4326), and normalizes into the overlay schema.

WFS Endpoint: https://www.ozp.tpb.gov.hk/arcgis/services/DATA/RA_PLAN_CSDI/MapServer/WFSServer
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Tuple
from xml.etree import ElementTree

import httpx
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

# WFS endpoint for Digital Planning Data of Regulated Areas
_DEFAULT_WFS_URL = os.getenv(
    "HK_ZONES_WFS_URL",
    "https://www.ozp.tpb.gov.hk/arcgis/services/DATA/RA_PLAN_CSDI/MapServer/WFSServer",
)

# Output directory for downloaded data
_DEFAULT_OUTPUT_DIR = os.getenv(
    "HK_ZONES_OUTPUT_DIR",
    str(Path(__file__).parent.parent.parent / "data" / "hk" / "zoning"),
)


@dataclass
class HKIngestionOptions:
    wfs_url: str
    output_dir: str
    typename: str
    max_features: int
    skip_transform: bool
    force_transform: bool


def _get_capabilities(wfs_url: str) -> dict[str, Any]:
    """Fetch WFS GetCapabilities to discover available layers."""
    params = {"service": "WFS", "request": "GetCapabilities"}

    logger.info("wfs:get_capabilities", url=wfs_url)

    with httpx.Client(timeout=60.0) as client:
        response = client.get(wfs_url, params=params)
        response.raise_for_status()

    # Parse XML to extract layer names
    root = ElementTree.fromstring(response.content)

    # Find all FeatureType elements (namespace varies by WFS version)
    namespaces = {
        "wfs": "http://www.opengis.net/wfs/2.0",
        "wfs11": "http://www.opengis.net/wfs",
    }

    layers = []
    for _ns_prefix, ns_uri in namespaces.items():
        for feature_type in root.findall(f".//{{{ns_uri}}}FeatureType"):
            name_elem = feature_type.find(f"{{{ns_uri}}}Name")
            title_elem = feature_type.find(f"{{{ns_uri}}}Title")
            if name_elem is not None:
                layers.append(
                    {
                        "name": name_elem.text,
                        "title": title_elem.text if title_elem is not None else None,
                    }
                )

    # Also try without namespace for simpler responses
    if not layers:
        for feature_type in root.findall(".//FeatureType"):
            name_elem = feature_type.find("Name")
            title_elem = feature_type.find("Title")
            if name_elem is not None:
                layers.append(
                    {
                        "name": name_elem.text,
                        "title": title_elem.text if title_elem is not None else None,
                    }
                )

    logger.info("wfs:capabilities_parsed", layer_count=len(layers))
    return {"layers": layers, "raw_xml_length": len(response.content)}


def _fetch_features_geojson(
    wfs_url: str,
    typename: str,
    max_features: int,
) -> dict[str, Any]:
    """Fetch features from WFS as GeoJSON."""
    params = {
        "service": "WFS",
        "request": "GetFeature",
        "typenames": typename,
        "outputFormat": "GEOJSON",
        "count": str(max_features),
    }

    logger.info(
        "wfs:get_features",
        url=wfs_url,
        typename=typename,
        max_features=max_features,
    )

    with httpx.Client(timeout=300.0) as client:
        response = client.get(wfs_url, params=params)
        response.raise_for_status()

    # Try to parse as JSON
    try:
        geojson = response.json()
        feature_count = len(geojson.get("features", []))
        logger.info("wfs:features_fetched", feature_count=feature_count)
        return geojson
    except json.JSONDecodeError:
        # Some WFS servers return GML instead of GeoJSON
        logger.warning(
            "wfs:geojson_parse_failed",
            content_type=response.headers.get("content-type"),
            content_length=len(response.content),
        )
        # Save raw response for debugging
        return {
            "type": "FeatureCollection",
            "features": [],
            "_raw_response": response.text[:1000],
            "_error": "Response was not valid GeoJSON",
        }


def _transform_coordinates(geojson: dict[str, Any]) -> dict[str, Any]:
    """Transform coordinates from EPSG:2326 (HK80 Grid) to EPSG:4326 (WGS84).

    Requires pyproj to be installed.
    """
    try:
        from pyproj import Transformer
    except ImportError:
        logger.warning(
            "transform:pyproj_not_installed",
            message="Install pyproj for coordinate transformation: pip install pyproj",
        )
        return geojson

    # HK80 Grid (EPSG:2326) to WGS84 (EPSG:4326)
    transformer = Transformer.from_crs("EPSG:2326", "EPSG:4326", always_xy=True)

    def transform_coords(coords: list) -> list:
        """Recursively transform coordinates."""
        if not coords:
            return coords
        # Check if this is a coordinate pair [x, y] or [x, y, z]
        if isinstance(coords[0], (int, float)):
            x, y = coords[0], coords[1]
            lon, lat = transformer.transform(x, y)
            return [lon, lat] + coords[2:] if len(coords) > 2 else [lon, lat]
        # Otherwise it's a list of coordinates
        return [transform_coords(c) for c in coords]

    transformed_features = []
    for feature in geojson.get("features", []):
        geometry = feature.get("geometry", {})
        if geometry and "coordinates" in geometry:
            geometry["coordinates"] = transform_coords(geometry["coordinates"])
        transformed_features.append(feature)

    geojson["features"] = transformed_features
    geojson["crs"] = {"type": "name", "properties": {"name": "EPSG:4326"}}

    logger.info(
        "transform:completed",
        feature_count=len(transformed_features),
        from_crs="EPSG:2326",
        to_crs="EPSG:4326",
    )

    return geojson


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
        if "2326" in normalized or "hk80" in normalized:
            return True, f"declared_crs={declared_crs}"

    sample = _sample_first_coordinate(geojson)
    if sample is not None:
        lon, lat = sample
        if abs(lon) <= 180 and abs(lat) <= 90:
            return False, "sample_within_wgs84_range"
        return True, "sample_outside_wgs84_range"

    return True, "no_crs_metadata"


def ingest_hk_zones(options: HKIngestionOptions) -> dict[str, Any]:
    """Ingest Hong Kong zoning data from WFS service.

    1. Fetch capabilities to discover layers
    2. Download features as GeoJSON
    3. Transform coordinates to WGS84
    4. Save to output directory
    """

    logger.info(
        "hk_ingest:init",
        wfs_url=options.wfs_url,
        output_dir=options.output_dir,
        typename=options.typename,
        max_features=options.max_features,
        geospatial_token_present=bool(settings.HK_GEOSPATIAL_TOKEN),
    )

    # Step 1: Get capabilities
    capabilities = _get_capabilities(options.wfs_url)

    if not capabilities["layers"]:
        logger.warning("hk_ingest:no_layers_found")
        return {
            "status": "error",
            "message": "No layers found in WFS capabilities",
            "capabilities": capabilities,
        }

    # Log available layers
    for layer in capabilities["layers"]:
        logger.info("hk_ingest:layer_found", name=layer["name"], title=layer["title"])

    # Step 2: Fetch features
    geojson = _fetch_features_geojson(
        options.wfs_url,
        options.typename,
        options.max_features,
    )

    feature_count = len(geojson.get("features", []))

    if feature_count == 0:
        logger.warning(
            "hk_ingest:no_features",
            typename=options.typename,
            error=geojson.get("_error"),
        )
        return {
            "status": "warning",
            "message": "No features returned from WFS",
            "typename": options.typename,
            "available_layers": [layer["name"] for layer in capabilities["layers"]],
        }

    # Step 3: Transform coordinates when needed
    if options.skip_transform:
        logger.info("hk_ingest:transform_skipped", reason="cli_skip")
    else:
        if options.force_transform:
            logger.info("hk_ingest:transform_forced")
            geojson = _transform_coordinates(geojson)
        else:
            needs_transform, reason = _should_transform_to_wgs84(geojson)
            if needs_transform:
                logger.info("hk_ingest:transform_auto", reason=reason)
                geojson = _transform_coordinates(geojson)
            else:
                logger.info("hk_ingest:transform_auto_skipped", reason=reason)

    # Step 4: Save to file
    output_file = _save_geojson(
        geojson,
        options.output_dir,
        f"regulated_areas_{options.typename.replace(':', '_')}.geojson",
    )

    logger.info(
        "hk_ingest:completed",
        processed_records=feature_count,
        output_file=str(output_file),
    )

    return {
        "status": "success",
        "processed_records": feature_count,
        "output_file": str(output_file),
        "typename": options.typename,
        "available_layers": [layer["name"] for layer in capabilities["layers"]],
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest Hong Kong zoning data from WFS service."
    )
    parser.add_argument(
        "--wfs-url",
        default=_DEFAULT_WFS_URL,
        help="WFS service URL for Planning Department data.",
    )
    parser.add_argument(
        "--output-dir",
        default=_DEFAULT_OUTPUT_DIR,
        help="Directory to save downloaded GeoJSON files.",
    )
    parser.add_argument(
        "--typename",
        default="RA_PLAN_CSDI:REGULATED_AREA",
        help="WFS typename to fetch (layer name from capabilities).",
    )
    parser.add_argument(
        "--max-features",
        type=int,
        default=10000,
        help="Maximum number of features to fetch.",
    )
    parser.add_argument(
        "--skip-transform",
        action="store_true",
        help="Skip coordinate transformation (keep original CRS).",
    )
    parser.add_argument(
        "--force-transform",
        action="store_true",
        help="Force coordinate transformation even when CRS appears to be WGS84.",
    )
    parser.add_argument(
        "--list-layers",
        action="store_true",
        help="Only list available layers from WFS capabilities.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    if args.list_layers:
        # Just fetch and display capabilities
        capabilities = _get_capabilities(args.wfs_url)
        print("\nAvailable WFS Layers:")
        print("-" * 60)
        for layer in capabilities["layers"]:
            print(f"  Name:  {layer['name']}")
            print(f"  Title: {layer['title']}")
            print()
        return

    options = HKIngestionOptions(
        wfs_url=args.wfs_url,
        output_dir=args.output_dir,
        typename=args.typename,
        max_features=args.max_features,
        skip_transform=args.skip_transform,
        force_transform=args.force_transform,
    )

    result = ingest_hk_zones(options)

    # Print summary
    print("\nIngestion Result:")
    print("-" * 60)
    for key, value in result.items():
        if key == "available_layers":
            print(f"  {key}: {', '.join(value)}")
        else:
            print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
