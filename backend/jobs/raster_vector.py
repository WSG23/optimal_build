"""Utilities for vectorising raster or vector floorplans."""

from __future__ import annotations

import asyncio
import math
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from io import BytesIO
from itertools import chain
from typing import Any
from xml.etree import ElementTree as ET

try:  # pragma: no cover - optional dependency
    import fitz  # type: ignore  # PyMuPDF
except ModuleNotFoundError:  # pragma: no cover - available in production environments
    fitz = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    from PIL import Image
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    Image = None  # type: ignore[assignment]

from backend.jobs import job

Point = tuple[float, float]


@dataclass(slots=True)
class VectorPath:
    """A vectorised path consisting of ordered coordinates."""

    points: list[Point]
    layer: str | None = None
    stroke_width: float | None = None

    def to_payload(self) -> dict[str, Any]:
        return {
            "points": [[float(x), float(y)] for x, y in self.points],
            "layer": self.layer,
            "stroke_width": self.stroke_width,
        }


@dataclass(slots=True)
class WallCandidate:
    """A baseline wall approximation extracted from vector or bitmap data."""

    start: Point
    end: Point
    thickness: float
    confidence: float
    source: str = "vector"

    def to_payload(self) -> dict[str, Any]:
        return {
            "start": [float(self.start[0]), float(self.start[1])],
            "end": [float(self.end[0]), float(self.end[1])],
            "thickness": float(self.thickness),
            "confidence": float(self.confidence),
            "source": self.source,
        }


@dataclass(slots=True)
class RasterVectorOptions:
    """Configuration toggles for raster to vector processing."""

    infer_walls: bool = False
    minimum_wall_length: float = 1.0
    bitmap_threshold: float = 0.65


@dataclass(slots=True)
class RasterVectorResult:
    """Result produced by :func:`vectorize_floorplan`."""

    paths: list[VectorPath]
    walls: list[WallCandidate]
    bounds: tuple[float, float] | None
    source: str
    options: RasterVectorOptions = field(default_factory=RasterVectorOptions)

    def to_payload(self) -> dict[str, Any]:
        bounds_payload: dict[str, float] | None = None
        if self.bounds is not None:
            bounds_payload = {
                "width": float(self.bounds[0]),
                "height": float(self.bounds[1]),
            }
        return {
            "source": self.source,
            "paths": [path.to_payload() for path in self.paths],
            "walls": [wall.to_payload() for wall in self.walls],
            "bounds": bounds_payload,
            "options": {
                "infer_walls": self.options.infer_walls,
                "minimum_wall_length": self.options.minimum_wall_length,
                "bitmap_threshold": self.options.bitmap_threshold,
                "bitmap_walls": any(wall.source == "bitmap" for wall in self.walls),
            },
        }


def _parse_svg_length(raw: str | None) -> float | None:
    if raw is None:
        return None
    token = raw.strip()
    if not token:
        return None
    match = re.match(r"[-+]?[0-9]*\.?[0-9]+", token)
    if match is None:
        return None
    try:
        return float(match.group(0))
    except ValueError:  # pragma: no cover - defensive guard
        return None


def _parse_svg_points(raw: str) -> list[Point]:
    points: list[Point] = []
    tokens = [
        token.strip() for token in raw.replace("\n", " ").split(" ") if token.strip()
    ]
    for token in tokens:
        if "," in token:
            x_str, y_str = token.split(",", 1)
            try:
                points.append((float(x_str), float(y_str)))
            except ValueError:  # pragma: no cover - defensive guard
                continue
    return points


def _parse_svg_path_d(raw: str) -> list[Point]:
    commands = raw.replace(",", " ").split()
    points: list[Point] = []
    iterator = iter(commands)
    current: Point | None = None
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
        elif cmd == "C":
            try:
                next(iterator)
                next(iterator)
                x = float(next(iterator))
                y = float(next(iterator))
            except (StopIteration, ValueError):  # pragma: no cover - defensive guard
                break
            current = (x, y)
            points.append(current)
        elif cmd == "Z" and points:
            points.append(points[0])
    return points


def _extract_svg_paths(root: ET.Element) -> list[VectorPath]:
    paths: list[VectorPath] = []
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


def _parse_svg_bounds(root: ET.Element) -> tuple[float, float] | None:
    width = _parse_svg_length(root.attrib.get("width"))
    height = _parse_svg_length(root.attrib.get("height"))
    if width is not None and height is not None:
        return float(width), float(height)
    view_box = root.attrib.get("viewBox")
    if view_box:
        parts = [part for part in view_box.replace(",", " ").split(" ") if part]
        if len(parts) >= 4:
            try:
                return float(parts[2]), float(parts[3])
            except ValueError:  # pragma: no cover - defensive guard
                return None
    return None


def detect_baseline_walls(
    paths: Sequence[VectorPath],
    *,
    minimum_length: float = 0.5,
    source: str = "vector",
) -> list[WallCandidate]:
    """Detect baseline walls from vector paths."""

    walls: list[WallCandidate] = []
    for path in paths:
        if len(path.points) < 2:
            continue
        for start, end in zip(path.points, path.points[1:], strict=False):
            dx = end[0] - start[0]
            dy = end[1] - start[1]
            length = math.hypot(dx, dy)
            if length < minimum_length:
                continue
            thickness = path.stroke_width or 0.2
            confidence = min(
                1.0,
                max(
                    thickness / max(minimum_length, 0.1),
                    length / max(minimum_length * 3.0, 1.0),
                ),
            )
            walls.append(
                WallCandidate(
                    start=start,
                    end=end,
                    thickness=float(thickness),
                    confidence=round(confidence, 3),
                    source=source,
                )
            )
    return walls


def _normalise_segment(start: Point, end: Point) -> tuple[Point, Point]:
    if (start[0], start[1]) <= (end[0], end[1]):
        return start, end
    return end, start


def _merge_walls(*collections: Iterable[WallCandidate]) -> list[WallCandidate]:
    dedup: dict[tuple[float, float, float, float], WallCandidate] = {}
    for candidate in chain.from_iterable(collections):
        ordered_start, ordered_end = _normalise_segment(candidate.start, candidate.end)
        key = (
            round(ordered_start[0], 1),
            round(ordered_start[1], 1),
            round(ordered_end[0], 1),
            round(ordered_end[1], 1),
        )
        if key not in dedup or candidate.confidence > dedup[key].confidence:
            dedup[key] = WallCandidate(
                start=ordered_start,
                end=ordered_end,
                thickness=candidate.thickness,
                confidence=candidate.confidence,
                source=candidate.source,
            )
    return list(dedup.values())


def _iter_runs(values: Sequence[bool]) -> Iterable[tuple[int, int]]:
    start: int | None = None
    for index, flag in enumerate(values):
        if flag:
            if start is None:
                start = index
        elif start is not None:
            yield start, index
            start = None
    if start is not None:
        yield start, len(values)


def _detect_walls_from_binary(
    binary: Sequence[Sequence[bool]],
    width: float,
    height: float,
    options: RasterVectorOptions,
) -> list[WallCandidate]:
    if not binary:
        return []
    pixel_height = len(binary)
    pixel_width = len(binary[0]) if binary[0] else 0
    if pixel_width == 0 or pixel_height == 0:
        return []

    scale_x = width / pixel_width if pixel_width else 1.0
    scale_y = height / pixel_height if pixel_height else 1.0
    min_horizontal = max(
        3, int(math.ceil(options.minimum_wall_length / max(scale_x, 1e-6)))
    )
    min_vertical = max(
        3, int(math.ceil(options.minimum_wall_length / max(scale_y, 1e-6)))
    )

    def make_candidate(
        start_point: Point, end_point: Point, length_units: float
    ) -> WallCandidate:
        confidence = min(
            1.0,
            length_units / max(options.minimum_wall_length * 4.0, max(width, height)),
        )
        thickness = max(scale_x, scale_y)
        ordered_start, ordered_end = _normalise_segment(start_point, end_point)
        return WallCandidate(
            start=ordered_start,
            end=ordered_end,
            thickness=float(thickness),
            confidence=round(confidence, 3),
            source="bitmap",
        )

    dedup: dict[tuple[float, float, float, float], WallCandidate] = {}

    for y, row in enumerate(binary):
        for start, end in _iter_runs(row):
            length = end - start
            if length < min_horizontal:
                continue
            x0 = start * scale_x
            x1 = (end - 1) * scale_x
            y_center = height - (y + 0.5) * scale_y
            candidate = make_candidate((x0, y_center), (x1, y_center), length * scale_x)
            key = (
                round(candidate.start[0], 1),
                round(candidate.start[1], 1),
                round(candidate.end[0], 1),
                round(candidate.end[1], 1),
            )
            existing = dedup.get(key)
            if existing is None or candidate.confidence > existing.confidence:
                dedup[key] = candidate

    for x in range(pixel_width):
        column = [binary[y][x] for y in range(pixel_height)]
        for start, end in _iter_runs(column):
            length = end - start
            if length < min_vertical:
                continue
            x_center = (x + 0.5) * scale_x
            y0 = height - (start + 0.5) * scale_y
            y1 = height - (end - 0.5) * scale_y
            candidate = make_candidate((x_center, y0), (x_center, y1), length * scale_y)
            key = (
                round(candidate.start[0], 1),
                round(candidate.start[1], 1),
                round(candidate.end[0], 1),
                round(candidate.end[1], 1),
            )
            existing = dedup.get(key)
            if existing is None or candidate.confidence > existing.confidence:
                dedup[key] = candidate

    return list(dedup.values())


def _detect_bitmap_walls(
    page: fitz.Page, options: RasterVectorOptions
) -> list[WallCandidate]:
    try:
        pixmap = page.get_pixmap(alpha=False)
    except Exception:  # pragma: no cover - defensive guard
        return []
    if pixmap.width <= 0 or pixmap.height <= 0:
        return []

    samples = memoryview(pixmap.samples)
    components = pixmap.n
    threshold = int(255 * options.bitmap_threshold)
    binary: list[list[bool]] = []
    for y in range(pixmap.height):
        row: list[bool] = []
        offset = y * pixmap.width * components
        for x in range(pixmap.width):
            index = offset + x * components
            r = samples[index]
            if components == 1:
                luminance = r
            else:
                g = samples[index + 1]
                b = samples[index + 2]
                luminance = int(0.299 * r + 0.587 * g + 0.114 * b)
            row.append(luminance <= threshold)
        binary.append(row)

    rect = page.rect
    return _detect_walls_from_binary(binary, rect.width, rect.height, options)


def _vectorize_bitmap_image(
    image_payload: bytes, options: RasterVectorOptions, source: str
) -> RasterVectorResult:
    if Image is None:  # pragma: no cover - optional dependency
        raise RuntimeError("Raster image vectorization requires Pillow")

    with Image.open(BytesIO(image_payload)) as image:  # type: ignore[attr-defined]
        grayscale = image.convert("L")
        width, height = grayscale.size

        bounds: tuple[float, float] | None
        if width <= 0 or height <= 0:
            bounds = None
        else:
            bounds = (float(width), float(height))

        walls: list[WallCandidate] = []
        if options.infer_walls and width > 0 and height > 0:
            threshold = int(255 * options.bitmap_threshold)
            data = list(grayscale.getdata())
            binary: list[list[bool]] = []
            for y in range(height):
                offset = y * width
                row_values = data[offset : offset + width]
                binary.append([value <= threshold for value in row_values])
            walls = _detect_walls_from_binary(
                binary, float(width), float(height), options
            )

    return RasterVectorResult(
        paths=[], walls=walls, bounds=bounds, source=source, options=options
    )


def _extract_pdf_page_paths(page: fitz.Page, page_index: int) -> list[VectorPath]:
    paths: list[VectorPath] = []
    layer = f"page-{page_index + 1}"
    for drawing in page.get_drawings():  # pragma: no cover - depends on pymupdf
        stroke_raw = drawing.get("width")
        stroke_width = (
            float(stroke_raw) if isinstance(stroke_raw, (int, float)) else None
        )
        segments: list[list[Point]] = []
        current: list[Point] = []
        for command in drawing["items"]:
            operator = command[0]
            if operator == "m":
                if current:
                    segments.append(current)
                    current = []
                point = command[1]
                current.append((float(point[0]), float(point[1])))
            elif operator == "l":
                point = command[1]
                current.append((float(point[0]), float(point[1])))
            elif operator == "c":
                point = command[3]
                current.append((float(point[0]), float(point[1])))
            elif operator == "re":
                x0, y0, x1, y1 = map(float, command[1])
                if current:
                    segments.append(current)
                current = []
                segments.append([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)])
            elif operator == "h" and current:
                current.append(current[0])
            elif operator == "n":
                if current:
                    segments.append(current)
                    current = []
        if current:
            segments.append(current)
        for segment in segments:
            if len(segment) >= 2:
                paths.append(
                    VectorPath(
                        points=segment,
                        layer=layer,
                        stroke_width=stroke_width,
                    )
                )
    return paths


def _extract_pdf_paths(
    pdf_payload: bytes, options: RasterVectorOptions
) -> RasterVectorResult:
    if fitz is None:  # pragma: no cover - optional dependency
        raise RuntimeError("PDF vectorization requires PyMuPDF (fitz)")
    document = fitz.open(stream=pdf_payload, filetype="pdf")  # type: ignore[arg-type]
    paths: list[VectorPath] = []
    vector_walls: list[WallCandidate] = []
    bitmap_walls: list[WallCandidate] = []
    bounds: tuple[float, float] | None = None
    for index, page in enumerate(document):  # pragma: no cover - depends on pymupdf
        page_paths = _extract_pdf_page_paths(page, index)
        paths.extend(page_paths)
        vector_walls.extend(
            detect_baseline_walls(
                page_paths, minimum_length=options.minimum_wall_length, source="vector"
            )
        )
        if options.infer_walls:
            bitmap_walls.extend(_detect_bitmap_walls(page, options))
        if bounds is None:
            rect = page.rect
            bounds = (float(rect.width), float(rect.height))
    merged_walls = _merge_walls(vector_walls, bitmap_walls)
    return RasterVectorResult(
        paths=paths, walls=merged_walls, bounds=bounds, source="pdf", options=options
    )


def _extract_svg_result(
    svg_payload: bytes, options: RasterVectorOptions
) -> RasterVectorResult:
    content = svg_payload.decode("utf-8")
    root = ET.fromstring(content)
    paths = _extract_svg_paths(root)
    bounds = _parse_svg_bounds(root)
    walls = detect_baseline_walls(
        paths, minimum_length=options.minimum_wall_length, source="vector"
    )
    return RasterVectorResult(
        paths=paths, walls=walls, bounds=bounds, source="svg", options=options
    )


def _vectorize_pdf(
    pdf_payload: bytes, options: RasterVectorOptions
) -> RasterVectorResult:
    return _extract_pdf_paths(pdf_payload, options)


def _vectorize_svg(
    svg_payload: bytes, options: RasterVectorOptions
) -> RasterVectorResult:
    return _extract_svg_result(svg_payload, options)


@job(name="jobs.raster_vector.vectorize_floorplan", queue="imports:vector")
async def vectorize_floorplan(
    payload: bytes,
    *,
    content_type: str,
    filename: str | None = None,
    infer_walls: bool = False,
    minimum_wall_length: float = 1.0,
) -> dict[str, Any]:
    """Convert PDF/SVG or raster image payloads into vector paths and walls."""

    options = RasterVectorOptions(
        infer_walls=infer_walls, minimum_wall_length=minimum_wall_length
    )
    content_type = (content_type or "").lower()
    name = (filename or "").lower()
    loop = asyncio.get_running_loop()
    if content_type == "image/svg+xml" or name.endswith(".svg"):
        result = await loop.run_in_executor(None, _vectorize_svg, payload, options)
        return result.to_payload()
    if content_type in {"image/jpeg", "image/jpg"} or name.endswith((".jpg", ".jpeg")):
        result = await loop.run_in_executor(
            None, _vectorize_bitmap_image, payload, options, "jpeg"
        )
        return result.to_payload()
    if content_type == "image/png" or name.endswith(".png"):
        result = await loop.run_in_executor(
            None, _vectorize_bitmap_image, payload, options, "png"
        )
        return result.to_payload()
    if content_type == "application/pdf" or name.endswith(".pdf"):
        result = await loop.run_in_executor(None, _vectorize_pdf, payload, options)
        return result.to_payload()
    raise RuntimeError("Unsupported floorplan media type")


__all__ = [
    "RasterVectorOptions",
    "RasterVectorResult",
    "VectorPath",
    "WallCandidate",
    "detect_baseline_walls",
    "vectorize_floorplan",
]
