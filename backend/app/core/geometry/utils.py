"""Geometry utilities for deriving parcel metrics."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.core.models.geometry import GeometryGraph


def _coerce_float(value: Any) -> float | None:
    """Attempt to coerce arbitrary input to ``float``."""

    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def derive_setback_overrides(
    graph: GeometryGraph,
    site_bounds: Mapping[str, Any] | None,
) -> dict[str, float]:
    """Return heuristic setback distances from geometry extents.

    Values are expressed in metres and only include ``front``, ``side`` and
    ``rear`` setbacks when both the site bounds and space boundaries are present.
    """

    if not isinstance(site_bounds, Mapping):
        return {}

    min_x = _coerce_float(site_bounds.get("min_x"))
    max_x = _coerce_float(site_bounds.get("max_x"))
    min_y = _coerce_float(site_bounds.get("min_y"))
    max_y = _coerce_float(site_bounds.get("max_y"))
    if None in (min_x, max_x, min_y, max_y):
        return {}
    # Type narrowing: after None check, all values are guaranteed float
    assert (
        min_x is not None
        and max_x is not None
        and min_y is not None
        and max_y is not None
    )

    building_min_x = float("inf")
    building_max_x = float("-inf")
    building_min_y = float("inf")
    building_max_y = float("-inf")

    for space in graph.spaces.values():
        # Skip spaces on SITE layer - they define the boundary, not the building
        source_layer = space.metadata.get("source_layer", "").upper()
        if source_layer == "SITE":
            continue
        boundary = getattr(space, "boundary", None) or []
        if not boundary:
            continue
        scale = _coerce_float(space.metadata.get("unit_scale_to_m")) or 1.0
        if scale <= 0:
            scale = 1.0
        for x_raw, y_raw in boundary:
            x_val = float(x_raw) * scale
            y_val = float(y_raw) * scale
            building_min_x = min(building_min_x, x_val)
            building_max_x = max(building_max_x, x_val)
            building_min_y = min(building_min_y, y_val)
            building_max_y = max(building_max_y, y_val)

    if building_min_x == float("inf") or building_min_y == float("inf"):
        return {}

    def _gap(edge_start: float, edge_end: float) -> float:
        return max(edge_end - edge_start, 0.0)

    front_gap = _gap(min_y, building_min_y)
    rear_gap = _gap(building_max_y, max_y)
    left_gap = _gap(min_x, building_min_x)
    right_gap = _gap(building_max_x, max_x)

    side_gap_candidates = [gap for gap in (left_gap, right_gap) if gap >= 0.0]
    side_gap = min(side_gap_candidates) if side_gap_candidates else 0.0

    def _rounded(value: float) -> float:
        return round(value, 2)

    return {
        key: _rounded(value)
        for key, value in {
            "front_setback_m": front_gap,
            "side_setback_m": side_gap,
            "rear_setback_m": rear_gap,
        }.items()
        if value >= 0.0
    }


__all__ = ["derive_setback_overrides"]
