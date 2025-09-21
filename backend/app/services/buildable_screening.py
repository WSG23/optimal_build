"""Helpers for performing buildable screening without external dependencies."""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Protocol

from app.services.rules_logic import collect_layer_metadata, ZoningLayerLike


class ParcelLike(Protocol):
    """Protocol describing the fields accessed on parcel records."""

    bounds_json: Mapping[str, Any] | None



def _ensure_mapping(value: Any) -> Mapping[str, Any] | None:
    if isinstance(value, Mapping):
        return value
    return None


def zone_code_from_parcel(parcel: ParcelLike | None) -> str | None:
    """Extract a zone code from the parcel bounds payload if present."""

    if parcel is None:
        return None
    bounds = _ensure_mapping(parcel.bounds_json) or {}
    zone = bounds.get("zone_code")
    if zone:
        return str(zone)
    return None


def zone_code_from_geometry(geometry: Mapping[str, Any] | None) -> str | None:
    """Return the zone code encoded within a GeoJSON feature payload."""

    if geometry is None:
        return None
    properties = _ensure_mapping(geometry.get("properties"))
    if not properties:
        return None
    zone = properties.get("zone_code")
    if zone:
        return str(zone)
    return None


def compose_buildable_response(
    *,
    address: str | None,
    geometry: Mapping[str, Any] | None,
    zone_code: str | None,
    layers: Iterable[ZoningLayerLike],
) -> dict[str, Any]:
    """Build the standard API response for buildable screening."""

    overlays: list[str] = []
    hints: list[str] = []
    if zone_code:
        overlays, hints = collect_layer_metadata(layers)

    input_kind = "address" if address else "geometry"
    return {
        "input_kind": input_kind,
        "zone_code": zone_code,
        "overlays": overlays,
        "advisory_hints": hints,
    }


__all__ = [
    "ParcelLike",
    "compose_buildable_response",
    "zone_code_from_geometry",
    "zone_code_from_parcel",
]
