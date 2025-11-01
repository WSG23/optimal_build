"""Lightweight geometry toolkit stub compatible with Shapely APIs used in tests."""

from .geometry import Point, shape, Polygon, MultiPolygon
from .strtree import STRtree

__all__ = ["Point", "Polygon", "MultiPolygon", "shape", "STRtree"]
