"""Minimal STRtree implementation backed by linear scans."""

from __future__ import annotations

from typing import Iterable, List

from .geometry import Point

__all__ = ["STRtree"]


class STRtree:
    """Simplified spatial index that performs bounding-box filtering."""

    def __init__(self, geometries: Iterable[object]) -> None:
        self._geometries: List[object] = list(geometries)

    def query(self, point: Point) -> list[object]:
        px, py = point.x, point.y
        matches: list[object] = []
        for geom in self._geometries:
            bounds = getattr(geom, "bounds", None)
            if not bounds:
                continue
            min_x, min_y, max_x, max_y = bounds
            if min_x - 1e-9 <= px <= max_x + 1e-9 and min_y - 1e-9 <= py <= max_y + 1e-9:
                matches.append(geom)
        return matches
