"""Simplified geometry primitives mimicking a subset of Shapely."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence, Union

__all__ = ["Point", "Polygon", "MultiPolygon", "shape"]


class Point:
    """2D point supporting the attributes accessed in tests."""

    __slots__ = ("x", "y")

    def __init__(self, x: Union[float, int], y: Union[float, int]) -> None:
        self.x = float(x)
        self.y = float(y)

    @property
    def coords(self) -> list[tuple[float, float]]:
        return [(self.x, self.y)]


def _point_on_segment(
    px: float, py: float, x1: float, y1: float, x2: float, y2: float
) -> bool:
    if min(x1, x2) - 1e-9 <= px <= max(x1, x2) + 1e-9 and min(y1, y2) - 1e-9 <= py <= max(
        y1, y2
    ) + 1e-9:
        dx1, dy1 = px - x1, py - y1
        dx2, dy2 = x2 - x1, y2 - y1
        cross = dx1 * dy2 - dy1 * dx2
        return abs(cross) < 1e-9
    return False


@dataclass(frozen=True)
class _LinearRing:
    coords: tuple[tuple[float, float], ...]

    @classmethod
    def from_sequence(cls, sequence: Sequence[Sequence[Union[float, int]]]) -> "_LinearRing":
        points: list[tuple[float, float]] = [
            (float(x), float(y)) for x, y in sequence
        ]
        if len(points) < 3:
            raise ValueError("LinearRing requires at least three coordinates")
        if points[0] != points[-1]:
            points.append(points[0])
        return cls(tuple(points))

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        xs = [x for x, _ in self.coords]
        ys = [y for _, y in self.coords]
        return min(xs), min(ys), max(xs), max(ys)

    def area_and_centroid(self) -> tuple[float, tuple[float, float]]:
        coords = self.coords
        area = 0.0
        cx = 0.0
        cy = 0.0
        for (x1, y1), (x2, y2) in zip(coords[:-1], coords[1:]):
            cross = x1 * y2 - x2 * y1
            area += cross
            cx += (x1 + x2) * cross
            cy += (y1 + y2) * cross
        area *= 0.5
        if abs(area) < 1e-12:
            xs = [x for x, _ in coords]
            ys = [y for _, y in coords]
            return 0.0, (sum(xs) / len(xs), sum(ys) / len(ys))
        cx /= 6.0 * area
        cy /= 6.0 * area
        return area, (cx, cy)

    def contains_point(self, px: float, py: float) -> bool:
        inside = False
        coords = self.coords
        for (x1, y1), (x2, y2) in zip(coords[:-1], coords[1:]):
            if _point_on_segment(px, py, x1, y1, x2, y2):
                return True
            intersects = ((y1 > py) != (y2 > py)) and (
                px < (x2 - x1) * (py - y1) / (y2 - y1 + 1e-18) + x1
            )
            if intersects:
                inside = not inside
        return inside

    def touches_point(self, px: float, py: float) -> bool:
        for (x1, y1), (x2, y2) in zip(self.coords[:-1], self.coords[1:]):
            if _point_on_segment(px, py, x1, y1, x2, y2):
                return True
        return False


class Polygon:
    """Simple polygon with outer boundary and optional holes."""

    def __init__(self, rings: Sequence[_LinearRing]) -> None:
        if not rings:
            raise ValueError("Polygon requires at least one ring")
        self._outer = rings[0]
        self._holes = list(rings[1:])
        self._compute_geometry()

    def _compute_geometry(self) -> None:
        outer_area, outer_centroid = self._outer.area_and_centroid()
        area_sum = outer_area
        cx = outer_centroid[0] * outer_area
        cy = outer_centroid[1] * outer_area
        for hole in self._holes:
            hole_area, hole_centroid = hole.area_and_centroid()
            area_sum += hole_area
            cx += hole_centroid[0] * hole_area
            cy += hole_centroid[1] * hole_area
        if abs(area_sum) < 1e-12:
            centroid_tuple = outer_centroid
            area_sum = 0.0
        else:
            centroid_tuple = (cx / area_sum, cy / area_sum)
        self._centroid_point = Point(*centroid_tuple)
        self._area = abs(area_sum)
        self._bounds = self._outer.bounds

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        return self._bounds

    @property
    def centroid(self) -> Point:
        return self._centroid_point

    @property
    def area(self) -> float:
        return self._area

    def contains(self, point: Point) -> bool:
        px, py = point.x, point.y
        if not self._outer.contains_point(px, py):
            return False
        for hole in self._holes:
            if hole.contains_point(px, py):
                return False
        return True

    def touches(self, point: Point) -> bool:
        px, py = point.x, point.y
        if self._outer.touches_point(px, py):
            return True
        return any(hole.touches_point(px, py) for hole in self._holes)


class MultiPolygon:
    """Collection of polygons with combined bounds and centroid."""

    def __init__(self, polygons: Iterable[Polygon]):
        self._polygons = tuple(polygons)
        if not self._polygons:
            self.bounds = (0.0, 0.0, 0.0, 0.0)
            self.centroid = Point(0.0, 0.0)
            self.area = 0.0
        else:
            min_x = min(p.bounds[0] for p in self._polygons)
            min_y = min(p.bounds[1] for p in self._polygons)
            max_x = max(p.bounds[2] for p in self._polygons)
            max_y = max(p.bounds[3] for p in self._polygons)
            self.bounds = (min_x, min_y, max_x, max_y)
            total_area = sum(p.area for p in self._polygons) or 1.0
            cx = sum(p.centroid.x * p.area for p in self._polygons)
            cy = sum(p.centroid.y * p.area for p in self._polygons)
            self.centroid = Point(cx / total_area, cy / total_area)
            self.area = total_area

    def contains(self, point: Point) -> bool:
        return any(poly.contains(point) for poly in self._polygons)

    def touches(self, point: Point) -> bool:
        return any(poly.touches(point) for poly in self._polygons)


def shape(geometry: dict) -> Union[Polygon, MultiPolygon]:
    """Construct a simple geometry from a GeoJSON-like mapping."""

    if geometry is None:
        raise ValueError("Geometry is required")

    geom_type = geometry.get("type")
    coords = geometry.get("coordinates")
    if geom_type == "Polygon":
        if not isinstance(coords, Sequence):
            raise TypeError("Polygon coordinates must be a sequence")
        rings = [_LinearRing.from_sequence(ring) for ring in coords]
        return Polygon(rings)
    if geom_type == "MultiPolygon":
        if not isinstance(coords, Sequence):
            raise TypeError("MultiPolygon coordinates must be a sequence")
        polygons = [
            Polygon([_LinearRing.from_sequence(ring) for ring in polygon])
            for polygon in coords
        ]
        return MultiPolygon(polygons)
    raise NotImplementedError(f"Geometry type '{geom_type}' not supported in stub")
