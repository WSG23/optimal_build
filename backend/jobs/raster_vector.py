"""Utilities for vectorising raster or vector floorplans."""

from __future__ import annotations

import math
import asyncio
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple
from xml.etree import ElementTree as ET

try:  # pragma: no cover - optional dependency
    import fitz  # type: ignore  # PyMuPDF
except ModuleNotFoundError:  # pragma: no cover - available in production environments
    fitz = None  # type: ignore[assignment]

from jobs import job


Point = Tuple[float, float]


@dataclass(slots=True)
class VectorPath:
    """A vectorised path consisting of ordered coordinates."""

    points: List[Point]
    layer: Optional[str] = None
    stroke_width: Optional[float] = None


@dataclass(slots=True)
class WallCandidate:
    """A baseline wall approximation extracted from vector data."""

    start: Point
    end: Point
    thickness: float
    confidence: float


@dataclass(slots=True)
class RasterVectorResult:
    """Result produced by :func:`vectorize_floorplan`."""

    paths: List[VectorPath]
    walls: List[WallCandidate]


def _parse_svg_points(raw: str) -> List[Point]:
    points: List[Point] = []
    tokens = [token.strip() for token in raw.replace("\n", " ").split(" ") if token.strip()]
    for token in tokens:
        if "," in token:
            x_str, y_str = token.split(",", 1)
            try:
                points.append((float(x_str), float(y_str)))
            except ValueError:  # pragma: no cover - defensive guard
                continue
    return points


def _parse_svg_path_d(raw: str) -> List[Point]:
    commands = raw.replace(",", " ").split()
    points: List[Point] = []
    iterator = iter(commands)
    current: Optional[Point] = None
    for token in iterator:
        cmd = token.upper()
        if cmd in {"M", "L"}:
            try:
                x = float(next(iterator))
                y = float(next(iterator))
            except (StopIteration, ValueError):  # pragma: no cover - defensive guard
                break
            current = (x, y)
            points.append(current)
        elif cmd == "H" and current is not None:
            try:
                x = float(next(iterator))
            except (StopIteration, ValueError):
                break
            current = (x, current[1])
            points.append(current)
        elif cmd == "V" and current is not None:
            try:
                y = float(next(iterator))
            except (StopIteration, ValueError):
                break
            current = (current[0], y)
            points.append(current)
        elif cmd == "Z" and points:
            points.append(points[0])
    return points


def _extract_svg_paths(svg_payload: str) -> List[VectorPath]:
    root = ET.fromstring(svg_payload)
    paths: List[VectorPath] = []
    for element in root.iter():
        tag = element.tag.split("}")[-1]
        if tag == "path" and element.attrib.get("d"):
            points = _parse_svg_path_d(element.attrib["d"])
            if points:
                stroke_raw = element.attrib.get("stroke-width", "1")
                try:
                    stroke = float(stroke_raw)
                except ValueError:  # pragma: no cover - defensive guard
                    stroke = 1.0
                paths.append(
                    VectorPath(
                        points=points,
                        layer=element.attrib.get("id"),
                        stroke_width=stroke,
                    )
                )
        elif tag in {"polyline", "polygon"} and element.attrib.get("points"):
            points = _parse_svg_points(element.attrib["points"])
            if tag == "polygon" and points and points[0] != points[-1]:
                points.append(points[0])
            if points:
                stroke_raw = element.attrib.get("stroke-width", "1")
                try:
                    stroke = float(stroke_raw)
                except ValueError:  # pragma: no cover - defensive guard
                    stroke = 1.0
                paths.append(
                    VectorPath(
                        points=points,
                        layer=element.attrib.get("id"),
                        stroke_width=stroke,
                    )
                )
    return paths


def _extract_pdf_paths(pdf_payload: bytes) -> List[VectorPath]:
    if fitz is None:  # pragma: no cover - optional dependency
        raise RuntimeError("PDF vectorization requires PyMuPDF (fitz)")
    paths: List[VectorPath] = []
    document = fitz.open(stream=pdf_payload, filetype="pdf")  # type: ignore[arg-type]
    for page in document:  # pragma: no cover - depends on pymupdf
        for item in page.get_drawings():
            points: List[Point] = []
            for path in item["items"]:
                if path[0] == "l":
                    points.append((float(path[1][0]), float(path[1][1])))
            if points:
                paths.append(VectorPath(points=points, layer=str(page.number)))
    return paths


def detect_baseline_walls(paths: Sequence[VectorPath]) -> List[WallCandidate]:
    """Detect baseline walls from vector paths."""

    walls: List[WallCandidate] = []
    for path in paths:
        if len(path.points) < 2:
            continue
        for start, end in zip(path.points, path.points[1:]):
            dx = end[0] - start[0]
            dy = end[1] - start[1]
            length = math.hypot(dx, dy)
            if length < 0.5:
                continue
            thickness = path.stroke_width or 0.2
            confidence = min(1.0, max(thickness / 0.5, length / 10.0))
            walls.append(
                WallCandidate(
                    start=start,
                    end=end,
                    thickness=thickness,
                    confidence=round(confidence, 3),
                )
            )
    return walls


def _vectorize_svg(svg_payload: bytes) -> RasterVectorResult:
    content = svg_payload.decode("utf-8")
    paths = _extract_svg_paths(content)
    return RasterVectorResult(paths=paths, walls=detect_baseline_walls(paths))


def _vectorize_pdf(pdf_payload: bytes) -> RasterVectorResult:
    paths = _extract_pdf_paths(pdf_payload)
    return RasterVectorResult(paths=paths, walls=detect_baseline_walls(paths))


@job(name="jobs.raster_vector.vectorize_floorplan", queue="imports:vector")
async def vectorize_floorplan(payload: bytes, *, content_type: str, filename: Optional[str] = None) -> RasterVectorResult:
    """Convert a PDF/SVG payload into vector paths and baseline walls."""

    content_type = content_type.lower()
    name = (filename or "").lower()
    if content_type == "image/svg+xml" or name.endswith(".svg"):
        return await asyncio.get_running_loop().run_in_executor(None, _vectorize_svg, payload)
    if content_type == "application/pdf" or name.endswith(".pdf"):
        return await asyncio.get_running_loop().run_in_executor(None, _vectorize_pdf, payload)
    raise RuntimeError("Unsupported floorplan media type")


__all__ = [
    "RasterVectorResult",
    "VectorPath",
    "WallCandidate",
    "detect_baseline_walls",
    "vectorize_floorplan",
]
