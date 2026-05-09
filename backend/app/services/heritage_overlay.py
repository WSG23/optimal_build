"""Heritage overlay lookup service backed by processed GeoJSON polygons."""

from __future__ import annotations

import json
import re
from html import unescape
from dataclasses import dataclass
from importlib import resources
from typing import Any, Iterable, Optional

try:  # pragma: no cover - shapely is optional in lightweight environments
    from shapely.geometry import Point, shape  # type: ignore
    from shapely.strtree import STRtree  # type: ignore

    _SHAPELY_AVAILABLE = True
except ModuleNotFoundError:  # pragma: no cover - fall back when shapely missing
    Point = Any
    STRtree: Any = None
    _SHAPELY_AVAILABLE = False

    def shape(_geometry: Any) -> None:
        return None


def _resource_text(path: str) -> Optional[str]:
    """Read a text resource from ``app.data`` if available."""

    try:
        return resources.files("app.data").joinpath(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except OSError:
        return None


def _safe_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_address_text(value: Any) -> str:
    """Normalize address fragments for conservative metadata matching."""

    if value is None:
        return ""
    text = unescape(str(value)).lower()
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _digits_only(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\D+", "", str(value))


def _attribute_value(attributes: dict[str, Any] | None, key: str) -> str:
    """Extract direct or KML table-backed attribute values."""

    if not attributes:
        return ""

    for candidate in (key, key.upper(), key.lower()):
        value = attributes.get(candidate)
        if value not in (None, ""):
            return str(value).strip()

    description = str(
        attributes.get("Description") or attributes.get("description") or ""
    )
    if not description:
        return ""

    pattern = rf"<th>\s*{re.escape(key)}\s*</th>\s*<td>(.*?)</td>"
    match = re.search(pattern, description, re.IGNORECASE | re.DOTALL)
    if not match:
        return ""

    return re.sub(
        r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", match.group(1)))
    ).strip()


@dataclass(frozen=True)
class HeritageOverlay:
    """A single conservation overlay with polygon metadata."""

    name: str
    risk: str
    notes: tuple[str, ...]
    source: str | None
    geometry: Any  # shapely geometry
    bbox: tuple[float, float, float, float]
    centroid: tuple[float, float]
    heritage_premium_pct: float | None = None
    attributes: dict[str, Any] | None = None

    def contains(self, point: Point) -> bool:
        if not _SHAPELY_AVAILABLE or self.geometry is None:
            return False
        try:
            # touches() handles points that lie on the polygon boundary
            return bool(self.geometry.contains(point) or self.geometry.touches(point))
        except Exception:
            return False


class HeritageOverlayService:
    """Loads heritage overlays and provides lookup helpers using a spatial index."""

    def __init__(self) -> None:
        overlays = list(self._load_geojson_overlays())
        if not overlays:
            overlays = list(self._load_legacy_overlays())

        self._overlays: tuple[HeritageOverlay, ...] = tuple(overlays)
        geometries = [
            overlay.geometry
            for overlay in self._overlays
            if overlay.geometry is not None
        ]
        self._index = STRtree(geometries) if geometries else None
        self._geom_to_overlay = {
            id(overlay.geometry): overlay
            for overlay in self._overlays
            if overlay.geometry is not None
        }

    # ------------------------------------------------------------------
    # Loaders
    # ------------------------------------------------------------------
    def _load_geojson_overlays(self) -> Iterable[HeritageOverlay]:
        if not _SHAPELY_AVAILABLE:
            return []

        text = _resource_text("heritage_overlays.geojson")
        if not text:
            return []

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return []

        features = data.get("features") or []
        overlays: list[HeritageOverlay] = []
        for feature in features:
            geometry = feature.get("geometry")
            properties = feature.get("properties") or {}
            if not geometry:
                continue
            try:
                geom = shape(geometry)
            except Exception:
                continue

            bbox = geom.bounds if geom else (0.0, 0.0, 0.0, 0.0)
            centroid = (geom.centroid.x, geom.centroid.y) if geom else (0.0, 0.0)
            overlays.append(
                HeritageOverlay(
                    name=str(properties.get("name", "Unknown Heritage Overlay")),
                    risk=str(properties.get("risk", "medium")),
                    notes=tuple(
                        str(note) for note in properties.get("notes", []) if note
                    ),
                    source=properties.get("source"),
                    geometry=geom,
                    bbox=bbox,
                    centroid=centroid,
                    heritage_premium_pct=_safe_float(
                        properties.get("heritage_premium_pct")
                    ),
                    attributes={
                        k: v for k, v in (properties.get("attributes") or {}).items()
                    },
                )
            )
        return overlays

    def _load_legacy_overlays(self) -> Iterable[HeritageOverlay]:
        if not _SHAPELY_AVAILABLE:
            return []

        text = _resource_text("heritage_overlays.json")
        if not text:
            return []
        try:
            raw = json.loads(text)
        except json.JSONDecodeError:
            return []

        overlays: list[HeritageOverlay] = []
        for entry in raw:
            bbox = entry.get("bbox") or {}
            # Extract bbox coordinates with type checking
            min_lon_val = bbox.get("min_lon")
            min_lat_val = bbox.get("min_lat")
            max_lon_val = bbox.get("max_lon")
            max_lat_val = bbox.get("max_lat")

            # Skip if any coordinate is missing
            if (
                min_lon_val is None
                or min_lat_val is None
                or max_lon_val is None
                or max_lat_val is None
            ):
                continue

            try:
                min_lon = float(min_lon_val)
                min_lat = float(min_lat_val)
                max_lon = float(max_lon_val)
                max_lat = float(max_lat_val)
            except (TypeError, ValueError):
                continue

            geom = shape(
                {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [min_lon, min_lat],
                            [max_lon, min_lat],
                            [max_lon, max_lat],
                            [min_lon, max_lat],
                            [min_lon, min_lat],
                        ]
                    ],
                }
            )
            overlays.append(
                HeritageOverlay(
                    name=str(entry.get("name", "Unknown Heritage Overlay")),
                    risk=str(entry.get("risk", "medium")),
                    notes=tuple(str(note) for note in entry.get("notes", []) if note),
                    source=entry.get("source"),
                    geometry=geom,
                    bbox=geom.bounds,
                    centroid=(geom.centroid.x, geom.centroid.y),
                    heritage_premium_pct=_safe_float(entry.get("heritage_premium_pct")),
                    attributes={},
                )
            )
        return overlays

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def _payload(self, overlay: HeritageOverlay) -> dict[str, Any]:
        return {
            "name": overlay.name,
            "risk": overlay.risk,
            "notes": list(overlay.notes),
            "source": overlay.source,
            "heritage_premium_pct": overlay.heritage_premium_pct,
            "centroid": overlay.centroid,
            "bbox": overlay.bbox,
            "attributes": overlay.attributes,
        }

    def _address_payload(self, overlay: HeritageOverlay) -> dict[str, Any]:
        payload = self._payload(overlay)
        record_name = _attribute_value(overlay.attributes, "NAME")
        if record_name and payload["name"] in {
            "Heritage Site",
            "National Monument",
            "Unknown Heritage Overlay",
        }:
            payload["name"] = record_name
        payload["matched_by"] = "address_metadata"
        return payload

    def lookup(self, latitude: float, longitude: float) -> Optional[dict[str, Any]]:
        if not _SHAPELY_AVAILABLE or not self._overlays:
            return None

        point = Point(longitude, latitude)
        candidates: Iterable[Any]
        if self._index is not None:
            candidates = self._index.query(point)
        else:
            candidates = (
                overlay.geometry
                for overlay in self._overlays
                if overlay.geometry is not None
            )

        for geom in candidates:
            overlay = self._geom_to_overlay.get(id(geom))
            if overlay and overlay.contains(point):
                return self._payload(overlay)
        return None

    def lookup_address(
        self,
        full_address: str,
        *,
        postal_code: str | None = None,
        street_name: str | None = None,
        block_number: str | None = None,
    ) -> Optional[dict[str, Any]]:
        """Match heritage markers by address metadata when point lookup misses.

        The processed heritage file includes point markers whose geometry can be
        offset from a geocoded parcel or building entrance. This fallback only
        matches exact postal code or street + block metadata to avoid broad
        neighbourhood-level false positives.
        """

        if not self._overlays:
            return None

        normalized_address = _normalize_address_text(full_address)
        normalized_postal = _digits_only(postal_code)
        normalized_street = _normalize_address_text(street_name)
        normalized_block = _digits_only(block_number)

        for overlay in self._overlays:
            attributes = overlay.attributes or {}
            overlay_postal = _digits_only(
                _attribute_value(attributes, "ADDRESSPOSTALCODE")
            )
            if normalized_postal and overlay_postal == normalized_postal:
                return self._address_payload(overlay)

            overlay_street = _normalize_address_text(
                _attribute_value(attributes, "ADDRESSSTREETNAME")
            )
            overlay_block = _digits_only(
                _attribute_value(attributes, "ADDRESSBLOCKHOUSENUMBER")
            )
            if not overlay_street or not overlay_block:
                continue

            street_matches = overlay_street == normalized_street or (
                overlay_street in normalized_address
            )
            block_matches = overlay_block == normalized_block
            if street_matches and block_matches:
                return self._address_payload(overlay)

        return None


__all__ = ["HeritageOverlayService", "HeritageOverlay"]
