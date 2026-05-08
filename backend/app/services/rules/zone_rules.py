"""Zone rules query service for Site Acquisition.

Queries the RefRule database table for zoning parameters (plot ratio, height limits,
site coverage) using the same data source as CAD Upload and compliance checking.

This replaces the hardcoded mock values in URAIntegrationService.get_zoning_info().
"""

from __future__ import annotations

import json
import math
from collections import Counter
from dataclasses import dataclass
from typing import Any, Optional

import structlog
from shapely.geometry import Point, shape
from shapely.validation import make_valid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rkp import RefBuildingFootprint, RefParcel, RefRule, RefZoningLayer

logger = structlog.get_logger(__name__)

NEAREST_PARCEL_LOOKUP_RADIUS_M = 60.0
APPROX_METERS_PER_DEGREE = 111_320.0

# Zone code mapping from URA short codes to RefRule format
ZONE_CODE_MAPPING = {
    # URA short codes → RefRule applicability zone_code
    "c": "SG:commercial",
    "c1": "SG:commercial",
    "commercial": "SG:commercial",
    "r": "SG:residential",
    "r1": "SG:residential",
    "residential": "SG:residential",
    "b": "SG:industrial",
    "b1": "SG:industrial",
    "b2": "SG:industrial",
    "industrial": "SG:industrial",
    "business": "SG:industrial",
    "mu": "SG:mixed_use",
    "mixed": "SG:mixed_use",
    "mixed_use": "SG:mixed_use",
    "mixed-use": "SG:mixed_use",
    "bp": "SG:business_park",
    "business_park": "SG:business_park",
    "business-park": "SG:business_park",
}

# Default fallback zone for unknown codes
DEFAULT_ZONE = "SG:residential"


SINGAPORE_RULE_SOURCE_REGISTRY: dict[str, list[dict[str, Any]]] = {
    "land_use": [
        {
            "authority": "URA",
            "title": "Master Plan land use layer",
            "url": "https://data.gov.sg/dataset/master-plan-2019-land-use-layer",
        },
        {
            "authority": "URA",
            "title": "Master Plan Written Statement",
            "url": "https://www.ura.gov.sg/Corporate/Planning/Master-Plan",
        },
    ],
    "plot_ratio": [
        {
            "authority": "URA",
            "title": "Master Plan GPR / intensity controls",
            "url": "https://data.gov.sg/dataset/master-plan-2019-land-use-layer",
        }
    ],
    "building_height_limit_m": [
        {
            "authority": "URA",
            "title": "Development Control Guidelines and control plans",
            "url": "https://www.ura.gov.sg/Corporate/Guidelines/Development-Control",
            "configured_values_by_zone": {
                # First normalized Singapore height-control fixture. This is
                # deliberately scoped to the current B1/industrial demo path so
                # broader zones remain source-review pending until ingested.
                "SG:industrial": "80",
            },
            "unit": "m",
        }
    ],
    "site_coverage_pct": [
        {
            "authority": "URA",
            "title": "Development Control Guidelines",
            "url": "https://www.ura.gov.sg/Corporate/Guidelines/Development-Control",
        }
    ],
    "setbacks": [
        {
            "authority": "URA",
            "title": "Development Control Guidelines - building setback controls",
            "url": "https://www.ura.gov.sg/Corporate/Guidelines/Development-Control",
            "configured_values_by_zone": {
                # First normalized Singapore setback fixture. Scoped to the
                # current B1/industrial and commercial demo paths until more
                # zone/use-specific official controls are ingested and reviewed.
                "SG:industrial": {
                    "front": "7.5",
                    "rear": "7.5",
                    "side": "3",
                },
                "SG:commercial": {
                    "front": "7.5",
                    "rear": "7.5",
                    "side": "3",
                },
            },
            "unit": "m",
        }
    ],
    "step_backs": [
        {
            "authority": "URA",
            "title": "Development Control Guidelines - building edge / storey controls",
            "url": "https://www.ura.gov.sg/Corporate/Guidelines/Development-Control",
            "configured_values_by_zone": {
                # First normalized Singapore step-back fixture. Scoped to the
                # current B1/industrial and commercial demo paths until
                # additional official zone/use controls are ingested and reviewed.
                "SG:industrial": [
                    {
                        "level": "8",
                        "depth_m": "5",
                    }
                ],
                "SG:commercial": [
                    {
                        "level": "8",
                        "depth_m": "5",
                    }
                ],
            },
            "unit": "m",
        }
    ],
    "air_rights_note": [
        {
            "authority": "URA/CAAS",
            "title": "Height control and aviation-related clearance sources",
            "url": "https://www.ura.gov.sg/Corporate/Guidelines/Development-Control",
            "resolution_workflow": "project_specific_clearance",
            "review_note": (
                "Requires site-specific aviation and height-clearance review "
                "before Capture treats this control as resolved."
            ),
        }
    ],
}


RESOLVABLE_FIELDS = (
    "land_use",
    "plot_ratio",
    "building_height_limit_m",
    "site_coverage_pct",
    "setbacks",
    "step_backs",
    "air_rights_note",
)

BUILDING_FOOTPRINT_COVERAGE_RADIUS_DEGREES = 0.00225
MIN_NEARBY_FOOTPRINTS_FOR_VACANT_SIGNAL = 3
MIN_POINT_LOOKUP_CACHE_ROWS = 1000
ENVELOPE_CONTROL_GPR_TOKENS = frozenset(
    {
        "eva",
        "envelope",
        "envelope control",
        "envelope control area",
    }
)


@dataclass(slots=True)
class _PointLookupCacheEntry:
    id: int
    bbox: tuple[float, float, float, float]


_PointLookupCacheKey = tuple[str, int, int]

_ZONING_POINT_LOOKUP_CACHE: dict[_PointLookupCacheKey, list[_PointLookupCacheEntry]] = (
    {}
)
_PARCEL_POINT_LOOKUP_CACHE: dict[_PointLookupCacheKey, list[_PointLookupCacheEntry]] = (
    {}
)
_PARCEL_ZONING_LOOKUP_CACHE: dict[
    tuple[_PointLookupCacheKey, int], "_ParcelZoningCacheEntry | None"
] = {}


@dataclass(slots=True)
class _ParcelZoningCacheEntry:
    layer_id: int
    overlap_area: float
    overlap_ratio: float | None


@dataclass
class ParcelZoningResolution:
    """Parcel-dominant zoning layer resolved from polygon overlap."""

    layer: RefZoningLayer | None
    overlap_area: float | None = None
    overlap_ratio: float | None = None
    source: str = "parcel_dominant_zoning"
    reason: str | None = None


@dataclass
class ZoningRulesResult:
    """Result of zoning rules query."""

    plot_ratio: Optional[float] = None
    building_height_limit_m: Optional[float] = None
    site_coverage_pct: Optional[float] = None
    setback_front_m: Optional[float] = None
    setback_rear_m: Optional[float] = None
    setback_side_m: Optional[float] = None
    step_backs: list[dict[str, float]] | None = None
    air_rights_note: Optional[str] = None
    zone_code: Optional[str] = None
    zone_description: Optional[str] = None
    source_reference: str = "RefRule Database"
    rules_found: int = 0
    rule_corpus_status: dict[str, object] | None = None

    @property
    def has_data(self) -> bool:
        """Check if any zoning data was found."""
        return any(
            value is not None
            for value in (
                self.plot_ratio,
                self.building_height_limit_m,
                self.site_coverage_pct,
                self.setback_front_m,
                self.setback_rear_m,
                self.setback_side_m,
                self.air_rights_note,
            )
        ) or bool(self.step_backs)


@dataclass
class SiteDevelopmentResult:
    """Parcel-level existing-asset signal from reference building footprints."""

    status: str
    building_count: int = 0
    footprint_area_sqm: float | None = None
    source: str | None = None
    reason: str | None = None


def normalize_zone_code(
    zone_code: Optional[str], jurisdiction: str = "SG"
) -> Optional[str]:
    """Normalize zone code to RefRule applicability format.

    Args:
        zone_code: Raw zone code from URA service (e.g., "C", "R", "B1", "Commercial")
        jurisdiction: Jurisdiction code (default "SG")

    Returns:
        Normalized zone code (e.g., "SG:commercial") or None
    """
    if not zone_code:
        return None

    # Clean and lowercase
    clean_code = zone_code.strip().lower()

    # Check mapping
    if clean_code in ZONE_CODE_MAPPING:
        return ZONE_CODE_MAPPING[clean_code]

    # If already in correct format (e.g., "SG:residential")
    if clean_code.startswith(f"{jurisdiction.lower()}:"):
        _, zone_part = clean_code.split(":", 1)
        return f"{jurisdiction.upper()}:{zone_part}"

    # Try to construct from jurisdiction + code
    constructed = f"{jurisdiction}:{clean_code}".lower()
    return constructed


def _extract_zone_description(zone_code: Optional[str]) -> Optional[str]:
    """Extract human-readable description from zone code."""
    if not zone_code:
        return None

    # Extract the part after jurisdiction prefix
    if ":" in zone_code:
        zone_type = zone_code.split(":", 1)[1]
    else:
        zone_type = zone_code

    # Format as title case with spaces
    return zone_type.replace("_", " ").title()


def _zone_aliases(zone_code: str, raw_zone_code: Optional[str]) -> set[str]:
    aliases = {zone_code.lower()}
    if ":" in zone_code:
        aliases.add(zone_code.split(":", 1)[1].lower())
    if raw_zone_code:
        raw = raw_zone_code.strip().lower()
        if raw:
            aliases.add(raw)
            normalized_raw = normalize_zone_code(raw_zone_code)
            if normalized_raw:
                aliases.add(normalized_raw.lower())
                if ":" in normalized_raw:
                    aliases.add(normalized_raw.split(":", 1)[1].lower())
    return aliases


def _iter_geojson_geometries(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []

    geo_type = payload.get("type")
    if geo_type == "Feature":
        geometry = payload.get("geometry")
        return [geometry] if isinstance(geometry, dict) else []
    if geo_type == "FeatureCollection":
        geometries: list[dict[str, Any]] = []
        features = payload.get("features")
        if isinstance(features, list):
            for feature in features:
                geometries.extend(_iter_geojson_geometries(feature))
        return geometries
    if geo_type == "GeometryCollection":
        geometries = payload.get("geometries")
        return (
            [entry for entry in geometries if isinstance(entry, dict)]
            if isinstance(geometries, list)
            else []
        )
    if geo_type in {"Polygon", "MultiPolygon"}:
        return [payload]
    return []


def _point_on_segment(
    lon: float,
    lat: float,
    start: Any,
    end: Any,
    *,
    epsilon: float = 1e-10,
) -> bool:
    if (
        not isinstance(start, (list, tuple))
        or not isinstance(end, (list, tuple))
        or len(start) < 2
        or len(end) < 2
    ):
        return False
    try:
        x1, y1 = float(start[0]), float(start[1])
        x2, y2 = float(end[0]), float(end[1])
    except (TypeError, ValueError):
        return False
    cross = (lat - y1) * (x2 - x1) - (lon - x1) * (y2 - y1)
    if abs(cross) > epsilon:
        return False
    return (
        min(x1, x2) - epsilon <= lon <= max(x1, x2) + epsilon
        and min(y1, y2) - epsilon <= lat <= max(y1, y2) + epsilon
    )


def _point_in_ring(lon: float, lat: float, ring: Any) -> bool:
    if not isinstance(ring, list) or len(ring) < 4:
        return False

    inside = False
    previous = ring[-1]
    for current in ring:
        if _point_on_segment(lon, lat, previous, current):
            return True
        if (
            isinstance(previous, (list, tuple))
            and isinstance(current, (list, tuple))
            and len(previous) >= 2
            and len(current) >= 2
        ):
            try:
                x1, y1 = float(previous[0]), float(previous[1])
                x2, y2 = float(current[0]), float(current[1])
            except (TypeError, ValueError):
                previous = current
                continue
            intersects = (y1 > lat) != (y2 > lat)
            if intersects:
                x_intersection = (x2 - x1) * (lat - y1) / (y2 - y1) + x1
                if lon <= x_intersection:
                    inside = not inside
        previous = current
    return inside


def _point_in_polygon(lon: float, lat: float, polygon: Any) -> bool:
    if not isinstance(polygon, list) or not polygon:
        return False
    shell = polygon[0]
    if not _point_in_ring(lon, lat, shell):
        return False
    holes = polygon[1:]
    return not any(_point_in_ring(lon, lat, hole) for hole in holes)


def _geojson_contains_point(payload: Any, *, latitude: float, longitude: float) -> bool:
    for geometry in _iter_geojson_geometries(payload):
        coordinates = geometry.get("coordinates")
        geo_type = geometry.get("type")
        if geo_type == "Polygon" and _point_in_polygon(
            longitude, latitude, coordinates
        ):
            return True
        if geo_type == "MultiPolygon" and isinstance(coordinates, list):
            if any(
                _point_in_polygon(longitude, latitude, polygon)
                for polygon in coordinates
            ):
                return True
    return False


def _geojson_bbox(payload: Any) -> tuple[float, float, float, float] | None:
    points: list[tuple[float, float]] = []

    def collect_coordinates(value: Any) -> None:
        if (
            isinstance(value, (list, tuple))
            and len(value) >= 2
            and isinstance(value[0], (int, float))
            and isinstance(value[1], (int, float))
        ):
            points.append((float(value[0]), float(value[1])))
            return
        if isinstance(value, (list, tuple)):
            for child in value:
                collect_coordinates(child)

    for geometry in _iter_geojson_geometries(payload):
        collect_coordinates(geometry.get("coordinates"))
    if not points:
        return None
    lons = [point[0] for point in points]
    lats = [point[1] for point in points]
    return min(lons), min(lats), max(lons), max(lats)


def _bbox_contains_point(
    bbox: tuple[float, float, float, float],
    *,
    latitude: float,
    longitude: float,
) -> bool:
    min_lon, min_lat, max_lon, max_lat = bbox
    return min_lon <= longitude <= max_lon and min_lat <= latitude <= max_lat


def _bbox_intersects(
    left: tuple[float, float, float, float],
    right: tuple[float, float, float, float],
) -> bool:
    left_min_lon, left_min_lat, left_max_lon, left_max_lat = left
    right_min_lon, right_min_lat, right_max_lon, right_max_lat = right
    return not (
        left_max_lon < right_min_lon
        or left_min_lon > right_max_lon
        or left_max_lat < right_min_lat
        or left_min_lat > right_max_lat
    )


def _bbox_distance_m(
    bbox: tuple[float, float, float, float],
    *,
    latitude: float,
    longitude: float,
) -> float:
    min_lon, min_lat, max_lon, max_lat = bbox
    clamped_lon = min(max(longitude, min_lon), max_lon)
    clamped_lat = min(max(latitude, min_lat), max_lat)
    lat_delta_m = (latitude - clamped_lat) * APPROX_METERS_PER_DEGREE
    lon_delta_m = (
        (longitude - clamped_lon)
        * APPROX_METERS_PER_DEGREE
        * math.cos(math.radians(latitude))
    )
    return math.hypot(lat_delta_m, lon_delta_m)


def _geojson_distance_to_point_m(
    payload: Any,
    *,
    latitude: float,
    longitude: float,
) -> float | None:
    point = Point(longitude, latitude)
    best_distance: float | None = None
    for geometry in _geojson_shapes(payload):
        if geometry.is_empty:
            continue
        try:
            distance_degrees = float(geometry.distance(point))
        except Exception:
            continue
        distance_m = distance_degrees * APPROX_METERS_PER_DEGREE
        if best_distance is None or distance_m < best_distance:
            best_distance = distance_m
    return best_distance


async def _point_lookup_cache_key(
    session: AsyncSession,
    model: type[RefZoningLayer] | type[RefParcel],
    *,
    jurisdiction: str,
) -> _PointLookupCacheKey:
    count_value, max_id_value = (
        await session.execute(
            select(func.count(model.id), func.max(model.id)).where(
                model.jurisdiction == jurisdiction
            )
        )
    ).one()
    return jurisdiction, int(count_value or 0), int(max_id_value or 0)


def _geojson_intersects(left: Any, right: Any) -> bool:
    try:
        left_geometries = [
            make_valid(shape(geometry)) for geometry in _iter_geojson_geometries(left)
        ]
        right_geometries = [
            make_valid(shape(geometry)) for geometry in _iter_geojson_geometries(right)
        ]
    except Exception:
        return False
    return any(
        not left_geometry.is_empty
        and not right_geometry.is_empty
        and left_geometry.intersects(right_geometry)
        for left_geometry in left_geometries
        for right_geometry in right_geometries
    )


def _geojson_shapes(payload: Any) -> list[Any]:
    try:
        return [
            make_valid(shape(geometry))
            for geometry in _iter_geojson_geometries(payload)
        ]
    except Exception:
        return []


def _geojson_intersection_area(left: Any, right: Any) -> float:
    left_geometries = _geojson_shapes(left)
    right_geometries = _geojson_shapes(right)
    overlap_area = 0.0
    for left_geometry in left_geometries:
        if left_geometry.is_empty:
            continue
        for right_geometry in right_geometries:
            if right_geometry.is_empty:
                continue
            try:
                intersection = left_geometry.intersection(right_geometry)
            except Exception:
                continue
            if not intersection.is_empty:
                overlap_area += float(intersection.area)
    return overlap_area


def _geojson_area(payload: Any) -> float:
    return sum(
        float(geometry.area)
        for geometry in _geojson_shapes(payload)
        if not geometry.is_empty
    )


async def find_zoning_layer_for_point(
    session: AsyncSession,
    *,
    latitude: float,
    longitude: float,
    jurisdiction: str = "SG",
) -> RefZoningLayer | None:
    """Resolve an imported zoning layer containing the supplied WGS84 point."""

    geometry_column = getattr(RefZoningLayer, "geometry", None)
    if geometry_column is not None:
        point = func.ST_SetSRID(func.ST_Point(longitude, latitude), 4326)
        stmt = (
            select(RefZoningLayer)
            .where(RefZoningLayer.jurisdiction == jurisdiction)
            .where(func.ST_Covers(geometry_column, point))
        )
        try:
            result = await session.execute(stmt)
            layer = result.scalars().first()
            if layer is not None:
                return layer
        except Exception:
            logger.debug(
                "PostGIS zoning-layer point lookup failed; falling back to GeoJSON bounds",
                jurisdiction=jurisdiction,
                latitude=latitude,
                longitude=longitude,
            )

    cache_key = await _point_lookup_cache_key(
        session,
        RefZoningLayer,
        jurisdiction=jurisdiction,
    )
    if cache_key[1] < MIN_POINT_LOOKUP_CACHE_ROWS:
        stmt = select(RefZoningLayer).where(RefZoningLayer.jurisdiction == jurisdiction)
        result = await session.execute(stmt)
        for layer in result.scalars().all():
            try:
                if _geojson_contains_point(
                    layer.bounds_json,
                    latitude=latitude,
                    longitude=longitude,
                ):
                    return layer
            except Exception:
                logger.debug(
                    "Skipping invalid zoning-layer GeoJSON bounds",
                    layer_id=layer.id,
                    jurisdiction=jurisdiction,
                )
        return None

    cache = _ZONING_POINT_LOOKUP_CACHE.get(cache_key)
    if cache is None:
        stmt = select(RefZoningLayer.id, RefZoningLayer.bounds_json).where(
            RefZoningLayer.jurisdiction == jurisdiction
        )
        result = await session.execute(stmt)
        cache = []
        for layer_id, bounds_json in result.all():
            bbox = _geojson_bbox(bounds_json)
            if bbox is not None:
                cache.append(_PointLookupCacheEntry(id=layer_id, bbox=bbox))
        _ZONING_POINT_LOOKUP_CACHE[cache_key] = cache

    candidate_ids = [
        entry.id
        for entry in cache
        if _bbox_contains_point(
            entry.bbox,
            latitude=latitude,
            longitude=longitude,
        )
    ]
    for layer_id in candidate_ids:
        layer = await session.get(RefZoningLayer, layer_id)
        if layer is None:
            continue
        try:
            if _geojson_contains_point(
                layer.bounds_json,
                latitude=latitude,
                longitude=longitude,
            ):
                return layer
        except Exception:
            logger.debug(
                "Skipping invalid zoning-layer GeoJSON bounds",
                layer_id=layer.id,
                jurisdiction=jurisdiction,
            )
    return None


async def find_dominant_zoning_layer_for_parcel(
    session: AsyncSession,
    parcel: RefParcel | None,
    *,
    jurisdiction: str = "SG",
) -> ParcelZoningResolution:
    """Resolve the zoning layer with the largest overlap across the parcel.

    Raw geocoder points can land on a driveway, edge, road reserve, or open-space
    sliver. Parcel-level overlap is a more stable Capture default because it
    answers which planning polygon controls the intended parcel, not just which
    polygon contains the marker pixel.
    """

    if parcel is None:
        return ParcelZoningResolution(
            layer=None,
            reason="parcel_unavailable",
        )

    parcel_geometry_column = getattr(RefParcel, "geometry", None)
    zoning_geometry_column = getattr(RefZoningLayer, "geometry", None)
    if parcel_geometry_column is not None and zoning_geometry_column is not None:
        stmt = (
            select(
                RefZoningLayer,
                func.ST_Area(
                    func.ST_Intersection(zoning_geometry_column, parcel_geometry_column)
                ).label("overlap_area"),
                (
                    func.ST_Area(
                        func.ST_Intersection(
                            zoning_geometry_column,
                            parcel_geometry_column,
                        )
                    )
                    / func.nullif(func.ST_Area(parcel_geometry_column), 0)
                ).label("overlap_ratio"),
            )
            .select_from(RefZoningLayer)
            .join(RefParcel, RefParcel.id == parcel.id)
            .where(RefZoningLayer.jurisdiction == jurisdiction)
            .where(func.ST_Intersects(zoning_geometry_column, parcel_geometry_column))
            .order_by(
                func.ST_Area(
                    func.ST_Intersection(zoning_geometry_column, parcel_geometry_column)
                ).desc()
            )
            .limit(1)
        )
        try:
            result = await session.execute(stmt)
            row = result.first()
            if row is not None:
                layer, overlap_area, overlap_ratio = row
                return ParcelZoningResolution(
                    layer=layer,
                    overlap_area=float(overlap_area) if overlap_area else None,
                    overlap_ratio=float(overlap_ratio) if overlap_ratio else None,
                )
        except Exception:
            logger.debug(
                "PostGIS parcel zoning lookup failed; falling back to GeoJSON overlap",
                jurisdiction=jurisdiction,
                parcel_id=parcel.id,
            )

    parcel_bbox = _geojson_bbox(parcel.bounds_json)
    if parcel_bbox is None:
        return ParcelZoningResolution(
            layer=None,
            reason="parcel_bounds_unavailable",
        )

    cache_key = await _point_lookup_cache_key(
        session,
        RefZoningLayer,
        jurisdiction=jurisdiction,
    )
    parcel_cache_key = (cache_key, int(parcel.id or 0))
    cached = _PARCEL_ZONING_LOOKUP_CACHE.get(parcel_cache_key)
    if parcel_cache_key in _PARCEL_ZONING_LOOKUP_CACHE:
        if cached is None:
            return ParcelZoningResolution(
                layer=None,
                reason="no_zoning_layer_intersects_parcel",
            )
        layer = await session.get(RefZoningLayer, cached.layer_id)
        return ParcelZoningResolution(
            layer=layer,
            overlap_area=cached.overlap_area,
            overlap_ratio=cached.overlap_ratio,
            reason=None if layer is not None else "cached_zoning_layer_missing",
        )

    if cache_key[1] >= MIN_POINT_LOOKUP_CACHE_ROWS:
        cache = _ZONING_POINT_LOOKUP_CACHE.get(cache_key)
        if cache is None:
            stmt = select(RefZoningLayer.id, RefZoningLayer.bounds_json).where(
                RefZoningLayer.jurisdiction == jurisdiction
            )
            result = await session.execute(stmt)
            cache = []
            for layer_id, bounds_json in result.all():
                bbox = _geojson_bbox(bounds_json)
                if bbox is not None:
                    cache.append(_PointLookupCacheEntry(id=layer_id, bbox=bbox))
            _ZONING_POINT_LOOKUP_CACHE[cache_key] = cache
        candidate_ids = [
            entry.id for entry in cache if _bbox_intersects(entry.bbox, parcel_bbox)
        ]
        candidates = [
            layer
            for layer_id in candidate_ids
            if (layer := await session.get(RefZoningLayer, layer_id)) is not None
        ]
    else:
        stmt = select(RefZoningLayer).where(RefZoningLayer.jurisdiction == jurisdiction)
        result = await session.execute(stmt)
        candidates = [
            layer
            for layer in result.scalars().all()
            if (layer_bbox := _geojson_bbox(layer.bounds_json)) is not None
            and _bbox_intersects(layer_bbox, parcel_bbox)
        ]

    parcel_area = _geojson_area(parcel.bounds_json)
    best_layer: RefZoningLayer | None = None
    best_overlap_area = 0.0
    for layer in candidates:
        overlap_area = _geojson_intersection_area(parcel.bounds_json, layer.bounds_json)
        if overlap_area > best_overlap_area:
            best_layer = layer
            best_overlap_area = overlap_area

    if best_layer is None or best_overlap_area <= 0:
        _PARCEL_ZONING_LOOKUP_CACHE[parcel_cache_key] = None
        return ParcelZoningResolution(
            layer=None,
            reason="no_zoning_layer_intersects_parcel",
        )

    overlap_ratio = best_overlap_area / parcel_area if parcel_area > 0 else None
    _PARCEL_ZONING_LOOKUP_CACHE[parcel_cache_key] = _ParcelZoningCacheEntry(
        layer_id=best_layer.id,
        overlap_area=best_overlap_area,
        overlap_ratio=overlap_ratio,
    )
    return ParcelZoningResolution(
        layer=best_layer,
        overlap_area=best_overlap_area,
        overlap_ratio=overlap_ratio,
    )


async def find_parcel_for_point(
    session: AsyncSession,
    *,
    latitude: float,
    longitude: float,
    jurisdiction: str = "SG",
) -> RefParcel | None:
    """Resolve an imported reference parcel containing the supplied WGS84 point."""

    geometry_column = getattr(RefParcel, "geometry", None)
    if geometry_column is not None:
        point = func.ST_SetSRID(func.ST_Point(longitude, latitude), 4326)
        stmt = (
            select(RefParcel)
            .where(RefParcel.jurisdiction == jurisdiction)
            .where(func.ST_Covers(geometry_column, point))
        )
        try:
            result = await session.execute(stmt)
            parcel = result.scalars().first()
            if parcel is not None:
                return parcel
        except Exception:
            logger.debug(
                "PostGIS parcel point lookup failed; falling back to GeoJSON bounds",
                jurisdiction=jurisdiction,
                latitude=latitude,
                longitude=longitude,
            )

    cache_key = await _point_lookup_cache_key(
        session,
        RefParcel,
        jurisdiction=jurisdiction,
    )
    if cache_key[1] < MIN_POINT_LOOKUP_CACHE_ROWS:
        stmt = select(RefParcel).where(RefParcel.jurisdiction == jurisdiction)
        result = await session.execute(stmt)
        for parcel in result.scalars().all():
            try:
                if _geojson_contains_point(
                    parcel.bounds_json,
                    latitude=latitude,
                    longitude=longitude,
                ):
                    return parcel
            except Exception:
                logger.debug(
                    "Skipping invalid parcel GeoJSON bounds",
                    parcel_id=parcel.id,
                    jurisdiction=jurisdiction,
                )
        return None

    cache = _PARCEL_POINT_LOOKUP_CACHE.get(cache_key)
    if cache is None:
        stmt = select(RefParcel.id, RefParcel.bounds_json).where(
            RefParcel.jurisdiction == jurisdiction
        )
        result = await session.execute(stmt)
        cache = []
        for parcel_id, bounds_json in result.all():
            bbox = _geojson_bbox(bounds_json)
            if bbox is not None:
                cache.append(_PointLookupCacheEntry(id=parcel_id, bbox=bbox))
        _PARCEL_POINT_LOOKUP_CACHE[cache_key] = cache

    candidate_ids = [
        entry.id
        for entry in cache
        if _bbox_contains_point(
            entry.bbox,
            latitude=latitude,
            longitude=longitude,
        )
    ]
    for parcel_id in candidate_ids:
        parcel = await session.get(RefParcel, parcel_id)
        if parcel is None:
            continue
        try:
            if _geojson_contains_point(
                parcel.bounds_json,
                latitude=latitude,
                longitude=longitude,
            ):
                return parcel
        except Exception:
            logger.debug(
                "Skipping invalid parcel GeoJSON bounds",
                parcel_id=parcel.id,
                jurisdiction=jurisdiction,
            )
    return None


async def find_nearest_parcel_for_point(
    session: AsyncSession,
    *,
    latitude: float,
    longitude: float,
    jurisdiction: str = "SG",
    max_distance_m: float = NEAREST_PARCEL_LOOKUP_RADIUS_M,
) -> RefParcel | None:
    """Resolve the nearest imported parcel when a geocoder point lands just off-parcel."""

    cache_key = await _point_lookup_cache_key(
        session,
        RefParcel,
        jurisdiction=jurisdiction,
    )
    if cache_key[1] < MIN_POINT_LOOKUP_CACHE_ROWS:
        stmt = select(RefParcel).where(RefParcel.jurisdiction == jurisdiction)
        result = await session.execute(stmt)
        candidates = result.scalars().all()
    else:
        cache = _PARCEL_POINT_LOOKUP_CACHE.get(cache_key)
        if cache is None:
            stmt = select(RefParcel.id, RefParcel.bounds_json).where(
                RefParcel.jurisdiction == jurisdiction
            )
            result = await session.execute(stmt)
            cache = []
            for parcel_id, bounds_json in result.all():
                bbox = _geojson_bbox(bounds_json)
                if bbox is not None:
                    cache.append(_PointLookupCacheEntry(id=parcel_id, bbox=bbox))
            _PARCEL_POINT_LOOKUP_CACHE[cache_key] = cache

        candidate_ids = [
            entry.id
            for entry in cache
            if _bbox_distance_m(
                entry.bbox,
                latitude=latitude,
                longitude=longitude,
            )
            <= max_distance_m
        ]
        candidates = [
            parcel
            for parcel_id in candidate_ids
            if (parcel := await session.get(RefParcel, parcel_id)) is not None
        ]

    best_parcel: RefParcel | None = None
    best_distance_m: float | None = None
    for parcel in candidates:
        bbox = _geojson_bbox(parcel.bounds_json)
        if (
            bbox is not None
            and _bbox_distance_m(
                bbox,
                latitude=latitude,
                longitude=longitude,
            )
            > max_distance_m
        ):
            continue
        distance_m = _geojson_distance_to_point_m(
            parcel.bounds_json,
            latitude=latitude,
            longitude=longitude,
        )
        if distance_m is None or distance_m > max_distance_m:
            continue
        if best_distance_m is None or distance_m < best_distance_m:
            best_parcel = parcel
            best_distance_m = distance_m

    return best_parcel


async def classify_site_development_for_parcel(
    session: AsyncSession,
    parcel: RefParcel | None,
    *,
    jurisdiction: str = "SG",
) -> SiteDevelopmentResult:
    """Classify whether a parcel appears vacant or developed from footprints."""

    if parcel is None:
        return SiteDevelopmentResult(
            status="uncertain",
            source="ref_building_footprints",
            reason="parcel_unavailable",
        )

    footprint_total = int(
        await session.scalar(
            select(func.count(RefBuildingFootprint.id)).where(
                RefBuildingFootprint.jurisdiction == jurisdiction
            )
        )
        or 0
    )
    if footprint_total == 0:
        return SiteDevelopmentResult(
            status="uncertain",
            source="ref_building_footprints",
            reason="building_footprints_not_loaded",
        )

    parcel_geometry_column = getattr(RefParcel, "geometry", None)
    footprint_geometry_column = getattr(RefBuildingFootprint, "geometry", None)
    if parcel_geometry_column is not None and footprint_geometry_column is not None:
        stmt = (
            select(
                func.count(RefBuildingFootprint.id),
                func.sum(RefBuildingFootprint.area_m2),
            )
            .select_from(RefBuildingFootprint)
            .join(
                RefParcel,
                RefParcel.id == parcel.id,
            )
            .where(RefBuildingFootprint.jurisdiction == jurisdiction)
            .where(
                func.ST_Intersects(footprint_geometry_column, parcel_geometry_column)
            )
        )
        try:
            result = await session.execute(stmt)
            count, area = result.one()
            building_count = int(count or 0)
            footprint_area = float(area) if area is not None else None
            if building_count == 0:
                return await _classify_absent_footprint_signal(
                    session,
                    parcel,
                    jurisdiction=jurisdiction,
                )
            return SiteDevelopmentResult(
                status="developed",
                building_count=building_count,
                footprint_area_sqm=footprint_area,
                source="ref_building_footprints",
                reason=None,
            )
        except Exception:
            logger.debug(
                "PostGIS building-footprint parcel lookup failed; falling back to GeoJSON bounds",
                jurisdiction=jurisdiction,
                parcel_id=parcel.id,
            )

    bbox = _geojson_bbox(parcel.bounds_json)
    stmt = select(RefBuildingFootprint).where(
        RefBuildingFootprint.jurisdiction == jurisdiction
    )
    if bbox is not None:
        min_lon, min_lat, max_lon, max_lat = bbox
        stmt = stmt.where(
            RefBuildingFootprint.centroid_lon >= min_lon,
            RefBuildingFootprint.centroid_lon <= max_lon,
            RefBuildingFootprint.centroid_lat >= min_lat,
            RefBuildingFootprint.centroid_lat <= max_lat,
        )
    result = await session.execute(stmt)
    building_count = 0
    footprint_area = 0.0
    for footprint in result.scalars().all():
        try:
            intersects = _geojson_intersects(parcel.bounds_json, footprint.bounds_json)
        except Exception:
            intersects = False
        if not intersects:
            continue
        building_count += 1
        try:
            footprint_area += float(footprint.area_m2 or 0)
        except (TypeError, ValueError):
            pass

    if building_count == 0:
        return await _classify_absent_footprint_signal(
            session,
            parcel,
            jurisdiction=jurisdiction,
        )

    return SiteDevelopmentResult(
        status="developed",
        building_count=building_count,
        footprint_area_sqm=footprint_area,
        source="ref_building_footprints",
        reason=None,
    )


async def _classify_absent_footprint_signal(
    session: AsyncSession,
    parcel: RefParcel,
    *,
    jurisdiction: str,
) -> SiteDevelopmentResult:
    """Classify no-intersection cases only when local footprint coverage is dense."""

    bbox = _geojson_bbox(parcel.bounds_json)
    if bbox is None:
        return SiteDevelopmentResult(
            status="uncertain",
            source="ref_building_footprints",
            reason="parcel_bounds_unavailable_for_footprint_coverage_check",
        )

    min_lon, min_lat, max_lon, max_lat = bbox
    radius = BUILDING_FOOTPRINT_COVERAGE_RADIUS_DEGREES
    nearby_count = int(
        await session.scalar(
            select(func.count(RefBuildingFootprint.id))
            .where(RefBuildingFootprint.jurisdiction == jurisdiction)
            .where(RefBuildingFootprint.centroid_lon >= min_lon - radius)
            .where(RefBuildingFootprint.centroid_lon <= max_lon + radius)
            .where(RefBuildingFootprint.centroid_lat >= min_lat - radius)
            .where(RefBuildingFootprint.centroid_lat <= max_lat + radius)
        )
        or 0
    )
    if nearby_count < MIN_NEARBY_FOOTPRINTS_FOR_VACANT_SIGNAL:
        return SiteDevelopmentResult(
            status="uncertain",
            source="ref_building_footprints",
            reason="building_footprint_coverage_sparse_near_parcel",
        )

    return SiteDevelopmentResult(
        status="vacant",
        source="ref_building_footprints",
        reason="no_footprint_intersects_parcel",
    )


def _coerce_attr_float(
    attributes: dict[str, object], keys: tuple[str, ...]
) -> Optional[float]:
    lowered = {str(key).lower(): value for key, value in attributes.items()}
    for key in keys:
        value = lowered.get(key.lower())
        if value in (None, ""):
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def _raw_attr_value(attributes: dict[str, object], keys: tuple[str, ...]) -> object:
    lowered = {str(key).lower(): value for key, value in attributes.items()}
    for key in keys:
        value = lowered.get(key.lower())
        if value not in (None, ""):
            return value
    return None


def _intensity_control_status(
    attributes: dict[str, object],
) -> dict[str, object] | None:
    raw_gpr = _raw_attr_value(
        attributes,
        ("gpr", "GPR", "plot_ratio", "plotRatio", "gross_plot_ratio", "max_far"),
    )
    if raw_gpr in (None, ""):
        return None
    if _coerce_registry_float(raw_gpr) is not None:
        return None

    raw_text = str(raw_gpr).strip()
    normalized = raw_text.lower().replace("_", " ").replace("-", " ")
    status = (
        "envelope_control_area"
        if normalized in ENVELOPE_CONTROL_GPR_TOKENS
        else "non_numeric_intensity_control"
    )
    return {
        "field": "GPR",
        "raw_value": raw_text,
        "status": status,
        "reason": (
            "URA Master Plan records this site with envelope controls instead of a numeric GPR."
            if status == "envelope_control_area"
            else "URA Master Plan intensity field is non-numeric and cannot be used as plot ratio."
        ),
    }


def _coerce_attr_string(
    attributes: dict[str, object], keys: tuple[str, ...]
) -> Optional[str]:
    lowered = {str(key).lower(): value for key, value in attributes.items()}
    for key in keys:
        value = lowered.get(key.lower())
        if value in (None, ""):
            continue
        return str(value)
    return None


def _coerce_attr_mapping(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return {str(key).lower(): entry for key, entry in value.items()}
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        if isinstance(parsed, dict):
            return {str(key).lower(): entry for key, entry in parsed.items()}
    return {}


def _coerce_attr_setbacks(
    attributes: dict[str, object],
) -> tuple[Optional[float], Optional[float], Optional[float]]:
    """Extract setback controls from captured zoning-layer attributes."""

    lowered = {str(key).lower(): value for key, value in attributes.items()}
    front = _coerce_attr_float(
        attributes,
        (
            "setback_front_m",
            "front_setback_m",
            "frontSetbackM",
            "front_setback",
            "frontSetback",
        ),
    )
    rear = _coerce_attr_float(
        attributes,
        (
            "setback_rear_m",
            "rear_setback_m",
            "rearSetbackM",
            "rear_setback",
            "rearSetback",
        ),
    )
    side = _coerce_attr_float(
        attributes,
        (
            "setback_side_m",
            "side_setback_m",
            "sideSetbackM",
            "side_setback",
            "sideSetback",
        ),
    )

    for key in ("setbacks", "setback_controls", "setbackcontrols"):
        nested = _coerce_attr_mapping(lowered.get(key))
        if not nested:
            continue
        front = (
            front
            if front is not None
            else _coerce_registry_float(
                nested.get("front") or nested.get("front_m") or nested.get("frontminm")
            )
        )
        rear = (
            rear
            if rear is not None
            else _coerce_registry_float(
                nested.get("rear") or nested.get("rear_m") or nested.get("rearminm")
            )
        )
        side = (
            side
            if side is not None
            else _coerce_registry_float(
                nested.get("side") or nested.get("side_m") or nested.get("sideminm")
            )
        )

    return front, rear, side


def _coerce_attr_step_backs(
    attributes: dict[str, object],
) -> list[dict[str, float]]:
    """Extract step-back controls from captured zoning-layer attributes."""

    lowered = {str(key).lower(): value for key, value in attributes.items()}
    raw_value: object = None
    for key in (
        "step_backs",
        "stepbacks",
        "step_backs_json",
        "stepback_controls",
        "stepbackcontrols",
    ):
        raw_value = lowered.get(key)
        if raw_value not in (None, ""):
            break

    if isinstance(raw_value, str):
        try:
            raw_value = json.loads(raw_value)
        except json.JSONDecodeError:
            return []

    entries: list[object]
    if isinstance(raw_value, list):
        entries = raw_value
    elif isinstance(raw_value, dict):
        if isinstance(raw_value.get("items"), list):
            entries = raw_value["items"]
        elif isinstance(raw_value.get("controls"), list):
            entries = raw_value["controls"]
        else:
            entries = [raw_value]
    else:
        entries = []

    step_backs: list[dict[str, float]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        entry_lowered = {str(key).lower(): value for key, value in entry.items()}
        depth_m = _coerce_registry_float(
            entry_lowered.get("depth_m")
            or entry_lowered.get("depthm")
            or entry_lowered.get("depth")
        )
        if depth_m is None:
            continue
        level = _coerce_registry_float(
            entry_lowered.get("level")
            or entry_lowered.get("storey")
            or entry_lowered.get("floor")
        )
        step_backs.append(
            {
                "level": level or float(len(step_backs) + 1),
                "depth_m": depth_m,
            }
        )
    return step_backs


def _coerce_registry_float(value: object) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _configured_registry_value(
    field: str,
    *,
    jurisdiction: str,
    normalized_zone: str,
) -> object | None:
    if jurisdiction != "SG":
        return None

    zone_key = normalized_zone.lower()
    for source in SINGAPORE_RULE_SOURCE_REGISTRY.get(field, []):
        if not isinstance(source, dict):
            continue
        values_by_zone = source.get("configured_values_by_zone")
        if not isinstance(values_by_zone, dict):
            continue
        for candidate_zone, candidate_value in values_by_zone.items():
            if str(candidate_zone).lower() == zone_key:
                return candidate_value
    return None


async def _get_zoning_layer_for_zone(
    session: AsyncSession,
    *,
    normalized_zone: str,
    raw_zone_code: Optional[str],
    jurisdiction: str,
) -> RefZoningLayer | None:
    aliases = _zone_aliases(normalized_zone, raw_zone_code)
    stmt = select(RefZoningLayer).where(RefZoningLayer.jurisdiction == jurisdiction)
    result = await session.execute(stmt)
    for layer in result.scalars().all():
        layer_zone = (layer.zone_code or "").strip().lower()
        if layer_zone and layer_zone in aliases:
            return layer
        attributes = layer.attributes if isinstance(layer.attributes, dict) else {}
        attr_zone = _coerce_attr_string(
            attributes,
            ("zone_code", "zoneCode", "LU_DESC", "land_use", "landUse"),
        )
        if attr_zone and attr_zone.strip().lower() in aliases:
            return layer
    return None


def _official_source_gaps(
    jurisdiction: str,
    unresolved_fields: list[str],
) -> list[dict[str, object]]:
    if jurisdiction != "SG":
        return []
    gaps = []
    for field in unresolved_fields:
        candidate_sources = SINGAPORE_RULE_SOURCE_REGISTRY.get(field, [])
        requires_project_clearance = any(
            isinstance(source, dict)
            and source.get("resolution_workflow") == "project_specific_clearance"
            for source in candidate_sources
        )
        gaps.append(
            {
                "field": field,
                "reason": (
                    "project_specific_clearance_required"
                    if requires_project_clearance
                    else "not_resolved_from_current_registry"
                ),
                "candidate_sources": candidate_sources,
            }
        )
    return gaps


def _project_clearance_required(
    official_source_gaps: list[dict[str, object]],
) -> list[dict[str, object]]:
    return [
        gap
        for gap in official_source_gaps
        if gap.get("reason") == "project_specific_clearance_required"
    ]


async def get_zoning_rules_for_zone(
    session: AsyncSession,
    zone_code: Optional[str],
    jurisdiction: str = "SG",
    preferred_zoning_layer: RefZoningLayer | None = None,
) -> ZoningRulesResult:
    """Query RefRule database for zoning parameters.

    Args:
        session: Database session
        zone_code: Zone code (e.g., "C", "R", "SG:commercial", "residential")
        jurisdiction: Jurisdiction code (default "SG")

    Returns:
        ZoningRulesResult with plot_ratio, height_limit, site_coverage, and source info
    """
    normalized_zone = normalize_zone_code(zone_code, jurisdiction)

    if not normalized_zone:
        logger.warning("No zone code provided for rules lookup")
        return ZoningRulesResult(
            source_reference="No zone code provided",
        )

    zoning_layer = preferred_zoning_layer or (
        await _get_zoning_layer_for_zone(
            session,
            normalized_zone=normalized_zone,
            raw_zone_code=zone_code,
            jurisdiction=jurisdiction,
        )
    )
    zoning_layer_attributes = (
        zoning_layer.attributes
        if zoning_layer and isinstance(zoning_layer.attributes, dict)
        else {}
    )

    zoning_layer_plot_ratio = _coerce_attr_float(
        zoning_layer_attributes,
        ("gpr", "GPR", "plot_ratio", "plotRatio", "gross_plot_ratio", "max_far"),
    )
    zoning_layer_intensity_control = _intensity_control_status(zoning_layer_attributes)
    zoning_layer_height_limit = _coerce_attr_float(
        zoning_layer_attributes,
        (
            "height_m",
            "heightLimitM",
            "building_height_limit_m",
            "max_building_height_m",
        ),
    )
    zoning_layer_site_coverage = _coerce_attr_float(
        zoning_layer_attributes,
        ("site_coverage_pct", "siteCoveragePct", "max_site_coverage_pct"),
    )
    zoning_layer_zone_description = _coerce_attr_string(
        zoning_layer_attributes,
        ("LU_DESC", "land_use", "landUse", "zone_description", "zoneDescription"),
    )

    # Query RefRule for zoning/building rules.
    stmt = (
        select(RefRule)
        .where(RefRule.jurisdiction == jurisdiction)
        .where(RefRule.topic.in_(("zoning", "building")))
    )

    result = await session.execute(stmt)
    all_rules = result.scalars().all()

    # Filter rules applicable to this zone
    applicable_rules = []
    for rule in all_rules:
        if rule.applicability and isinstance(rule.applicability, dict):
            rule_zone_code = rule.applicability.get("zone_code")
            if rule_zone_code and rule_zone_code.lower() == normalized_zone.lower():
                applicable_rules.append(rule)
    approved_rules = [
        rule
        for rule in applicable_rules
        if rule.review_status == "approved" and bool(rule.is_published)
    ]
    review_counts = Counter(
        (rule.review_status or "unknown") for rule in applicable_rules
    )
    published_count = sum(1 for rule in applicable_rules if bool(rule.is_published))
    traceable_count = sum(
        1
        for rule in approved_rules
        if any(
            (rule.source_id, rule.document_id, isinstance(rule.source_provenance, dict))
        )
    )
    # Extract parameter values
    plot_ratio: Optional[float] = zoning_layer_plot_ratio
    building_height_limit_m: Optional[float] = zoning_layer_height_limit
    site_coverage_pct: Optional[float] = zoning_layer_site_coverage
    setback_front_m: Optional[float] = None
    setback_rear_m: Optional[float] = None
    setback_side_m: Optional[float] = None
    step_backs: list[dict[str, float]] = []
    air_rights_note: Optional[str] = None
    resolved_by: dict[str, str] = {}

    if zoning_layer_zone_description:
        resolved_by["land_use"] = "ref_zoning_layer"
    if zoning_layer_plot_ratio is not None:
        resolved_by["plot_ratio"] = "ref_zoning_layer"
    if zoning_layer_height_limit is not None:
        resolved_by["building_height_limit_m"] = "ref_zoning_layer"
    if zoning_layer_site_coverage is not None:
        resolved_by["site_coverage_pct"] = "ref_zoning_layer"

    (
        zoning_layer_setback_front,
        zoning_layer_setback_rear,
        zoning_layer_setback_side,
    ) = _coerce_attr_setbacks(zoning_layer_attributes)
    if any(
        value is not None
        for value in (
            zoning_layer_setback_front,
            zoning_layer_setback_rear,
            zoning_layer_setback_side,
        )
    ):
        setback_front_m = zoning_layer_setback_front
        setback_rear_m = zoning_layer_setback_rear
        setback_side_m = zoning_layer_setback_side
        resolved_by["setbacks"] = "ref_zoning_layer"

    zoning_layer_step_backs = _coerce_attr_step_backs(zoning_layer_attributes)
    if zoning_layer_step_backs:
        step_backs = zoning_layer_step_backs
        resolved_by["step_backs"] = "ref_zoning_layer"

    for rule in approved_rules:
        parameter_key = (rule.parameter_key or "").lower()
        try:
            if parameter_key == "zoning.max_far":
                plot_ratio = float(rule.value)
                resolved_by["plot_ratio"] = "ref_rule"
            elif parameter_key == "zoning.max_building_height_m":
                building_height_limit_m = float(rule.value)
                resolved_by["building_height_limit_m"] = "ref_rule"
            elif parameter_key == "zoning.site_coverage.max_percent":
                site_coverage_pct = float(rule.value)
                resolved_by["site_coverage_pct"] = "ref_rule"
            elif parameter_key == "zoning.setback.front_min_m":
                setback_front_m = float(rule.value)
                resolved_by["setbacks"] = "ref_rule"
            elif parameter_key == "zoning.setback.rear_min_m":
                setback_rear_m = float(rule.value)
                resolved_by["setbacks"] = "ref_rule"
            elif parameter_key == "zoning.setback.side_min_m":
                setback_side_m = float(rule.value)
                resolved_by["setbacks"] = "ref_rule"
            elif parameter_key.startswith("zoning.stepback."):
                applicability = (
                    rule.applicability if isinstance(rule.applicability, dict) else {}
                )
                level_value = applicability.get("level") or applicability.get("storey")
                if level_value is None:
                    level = len(step_backs) + 1
                else:
                    level = int(level_value)
                step_backs.append({"level": float(level), "depth_m": float(rule.value)})
                resolved_by["step_backs"] = "ref_rule"
            elif parameter_key.startswith("zoning.air_rights."):
                air_rights_note = str(rule.value)
                resolved_by["air_rights_note"] = "ref_rule"
        except (ValueError, TypeError) as e:
            logger.warning(
                "Failed to parse rule value",
                parameter_key=rule.parameter_key,
                value=rule.value,
                error=str(e),
            )

    if building_height_limit_m is None:
        registry_height_limit = _coerce_registry_float(
            _configured_registry_value(
                "building_height_limit_m",
                jurisdiction=jurisdiction,
                normalized_zone=normalized_zone,
            )
        )
        if registry_height_limit is not None:
            building_height_limit_m = registry_height_limit
            resolved_by["building_height_limit_m"] = "official_source_registry"

    if "setbacks" not in resolved_by:
        registry_setbacks = _configured_registry_value(
            "setbacks",
            jurisdiction=jurisdiction,
            normalized_zone=normalized_zone,
        )
        if isinstance(registry_setbacks, dict):
            setback_front_m = _coerce_registry_float(registry_setbacks.get("front"))
            setback_rear_m = _coerce_registry_float(registry_setbacks.get("rear"))
            setback_side_m = _coerce_registry_float(registry_setbacks.get("side"))
            if any(
                value is not None
                for value in (setback_front_m, setback_rear_m, setback_side_m)
            ):
                resolved_by["setbacks"] = "official_source_registry"

    if "step_backs" not in resolved_by:
        registry_step_backs = _configured_registry_value(
            "step_backs",
            jurisdiction=jurisdiction,
            normalized_zone=normalized_zone,
        )
        if isinstance(registry_step_backs, list):
            parsed_step_backs: list[dict[str, float]] = []
            for entry in registry_step_backs:
                if not isinstance(entry, dict):
                    continue
                depth_m = _coerce_registry_float(
                    entry.get("depth_m") or entry.get("depth")
                )
                if depth_m is None:
                    continue
                level = _coerce_registry_float(
                    entry.get("level") or entry.get("storey")
                )
                parsed_step_backs.append(
                    {
                        "level": level or float(len(parsed_step_backs) + 1),
                        "depth_m": depth_m,
                    }
                )
            if parsed_step_backs:
                step_backs = parsed_step_backs
                resolved_by["step_backs"] = "official_source_registry"

    if (
        not applicable_rules
        and zoning_layer is None
        and not any(
            value is not None
            for value in (
                plot_ratio,
                building_height_limit_m,
                site_coverage_pct,
                setback_front_m,
                setback_rear_m,
                setback_side_m,
                air_rights_note,
            )
        )
        and not step_backs
    ):
        logger.info(
            "No configured rule data resolved for zone",
            zone_code=normalized_zone,
            jurisdiction=jurisdiction,
            total_rules_checked=len(all_rules),
        )

    if (
        not any(
            value is not None
            for value in (
                plot_ratio,
                building_height_limit_m,
                site_coverage_pct,
                setback_front_m,
                setback_rear_m,
                setback_side_m,
                air_rights_note,
            )
        )
        and not step_backs
    ):
        coverage_state = "missing"
        confidence = "low"
    elif not approved_rules and applicable_rules:
        coverage_state = "review_pending"
        confidence = "low"
    elif set(RESOLVABLE_FIELDS).difference(resolved_by):
        coverage_state = "partial"
        confidence = "medium"
    elif traceable_count < len(approved_rules):
        coverage_state = "approved"
        confidence = "medium"
    else:
        coverage_state = "approved"
        confidence = "high"

    unresolved_fields = [
        field for field in RESOLVABLE_FIELDS if field not in resolved_by
    ]
    official_source_gaps = _official_source_gaps(jurisdiction, unresolved_fields)
    if (
        zoning_layer_intensity_control is not None
        and zoning_layer_intensity_control.get("status") == "envelope_control_area"
    ):
        for gap in official_source_gaps:
            if gap.get("field") == "plot_ratio":
                gap["reason"] = "envelope_control_area_requires_site_specific_controls"
                gap["source_value"] = zoning_layer_intensity_control.get("raw_value")
                gap["review_note"] = zoning_layer_intensity_control.get("reason")
    rule_corpus_status = {
        "zone_code": normalized_zone,
        "coverage_state": coverage_state,
        "confidence": confidence,
        "counts": {
            "applicable": len(applicable_rules),
            "approved": len(approved_rules),
            "published": published_count,
            "traceable": traceable_count,
            "needs_review": review_counts.get("needs_review", 0),
            "rejected": review_counts.get("rejected", 0),
            "zoning_layers": 1 if zoning_layer else 0,
        },
        "applied_rule_ids": [rule.id for rule in approved_rules if rule.id is not None],
        "applied_zoning_layer_id": zoning_layer.id if zoning_layer else None,
        "resolved_by": resolved_by,
        "unresolved_fields": unresolved_fields,
        "official_source_gaps": official_source_gaps,
        "project_clearance_required": _project_clearance_required(official_source_gaps),
    }
    if zoning_layer_intensity_control is not None:
        rule_corpus_status["zoning_layer_intensity_control"] = (
            zoning_layer_intensity_control
        )

    logger.info(
        "Zoning rules retrieved from configured registry",
        zone_code=normalized_zone,
        plot_ratio=plot_ratio,
        height_limit=building_height_limit_m,
        site_coverage=site_coverage_pct,
        rules_count=len(applicable_rules),
        zoning_layer_id=zoning_layer.id if zoning_layer else None,
    )

    return ZoningRulesResult(
        plot_ratio=plot_ratio,
        building_height_limit_m=building_height_limit_m,
        site_coverage_pct=site_coverage_pct,
        setback_front_m=setback_front_m,
        setback_rear_m=setback_rear_m,
        setback_side_m=setback_side_m,
        step_backs=step_backs,
        air_rights_note=air_rights_note,
        zone_code=normalized_zone,
        zone_description=(
            zoning_layer_zone_description or _extract_zone_description(normalized_zone)
        ),
        source_reference=(
            f"{jurisdiction} Rule Registry (RefRule"
            + (" + zoning layers" if zoning_layer else "")
            + ")"
        ),
        rules_found=len(approved_rules),
        rule_corpus_status=rule_corpus_status,
    )
