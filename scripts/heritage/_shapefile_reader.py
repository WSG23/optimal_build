"""Minimal shapefile + DBF reader tailored for URA conservation polygons."""

from __future__ import annotations

import struct
from collections.abc import Iterable, Iterator, Sequence
from pathlib import Path
from typing import Any


def _iter_records(shp_path: Path) -> Iterator[bytes]:
    with shp_path.open("rb") as handle:
        header = handle.read(100)
        if len(header) < 100:
            raise ValueError(f"Invalid shapefile header in {shp_path}")
        file_shape_type = struct.unpack("<i", header[32:36])[0]
        if file_shape_type not in (5, 15):  # Polygon, PolygonZ
            raise ValueError(f"Unsupported shape type {file_shape_type} in {shp_path}")

        while True:
            record_header = handle.read(8)
            if len(record_header) < 8:
                break
            _record_number, content_length = struct.unpack(">2i", record_header)
            content = handle.read(content_length * 2)
            if not content:
                break
            yield content


def _split_rings(
    points: Sequence[tuple[float, float]], parts: Sequence[int]
) -> list[list[tuple[float, float]]]:
    rings: list[list[tuple[float, float]]] = []
    num_points = len(points)
    for index, start in enumerate(parts):
        end = parts[index + 1] if index + 1 < len(parts) else num_points
        ring = [points[i] for i in range(start, end)]
        if not ring:
            continue
        if ring[0] != ring[-1]:
            ring.append(ring[0])
        rings.append(ring)
    return rings


def _signed_area(coords: Sequence[tuple[float, float]]) -> float:
    area = 0.0
    for (x1, y1), (x2, y2) in zip(coords, coords[1:], strict=False):
        area += (x1 * y2) - (x2 * y1)
    return area / 2.0


def _group_polygon_rings(
    rings: Sequence[Sequence[tuple[float, float]]]
) -> list[tuple[list[tuple[float, float]], list[list[tuple[float, float]]]]]:
    polygons: list[
        tuple[list[tuple[float, float]], list[list[tuple[float, float]]]]
    ] = []
    current_outer: list[tuple[float, float]] | None = None
    current_holes: list[list[tuple[float, float]]] = []

    for ring in rings:
        area = _signed_area(ring)
        if area >= 0:
            if current_outer is not None:
                polygons.append((current_outer, current_holes))
            current_outer = list(ring)
            current_holes = []
        else:
            if current_outer is None:
                continue
            current_holes.append(list(ring))

    if current_outer is not None:
        polygons.append((current_outer, current_holes))

    return polygons


def load_polygons(shp_path: str | Path) -> list[dict[str, Any]]:
    """Return GeoJSON-like polygon geometries extracted from a shapefile."""

    shp_path = Path(shp_path)
    features: list[dict[str, Any]] = []

    for content in _iter_records(shp_path):
        shape_type = struct.unpack("<i", content[0:4])[0]
        if shape_type == 0:  # Null shape
            continue
        if shape_type not in (5, 15):
            raise ValueError(f"Unsupported record shape type {shape_type}")
        bbox = struct.unpack("<4d", content[4:36])
        num_parts = struct.unpack("<i", content[36:40])[0]
        num_points = struct.unpack("<i", content[40:44])[0]
        parts = (
            struct.unpack(f"<{num_parts}i", content[44 : 44 + num_parts * 4])
            if num_parts
            else (0,)
        )
        points_offset = 44 + num_parts * 4
        points: list[tuple[float, float]] = []
        for idx in range(num_points):
            start = points_offset + idx * 16
            x, y = struct.unpack("<2d", content[start : start + 16])
            points.append((x, y))

        rings = _split_rings(points, parts if isinstance(parts, tuple) else list(parts))
        grouped = _group_polygon_rings(rings)
        if not grouped:
            continue
        if len(grouped) == 1:
            outer, holes = grouped[0]
            geometry: dict[str, Any] = {
                "type": "Polygon",
                "coordinates": [outer] + holes,
            }
        else:
            geometry = {
                "type": "MultiPolygon",
                "coordinates": [[outer] + holes for outer, holes in grouped],
            }
        features.append(
            {
                "geometry": geometry,
                "bbox": list(bbox),
            }
        )
    return features


def load_dbf(dbf_path: str | Path) -> list[dict[str, Any]]:
    """Read accompanying DBF records."""

    dbf_path = Path(dbf_path)
    with dbf_path.open("rb") as handle:
        header = handle.read(32)
        if len(header) < 32:
            raise ValueError(f"Invalid DBF header in {dbf_path}")
        num_records = struct.unpack("<I", header[4:8])[0]
        header_length = struct.unpack("<H", header[8:10])[0]
        record_length = struct.unpack("<H", header[10:12])[0]

        num_fields = (header_length - 33) // 32
        fields = []
        for _ in range(num_fields):
            field_desc = handle.read(32)
            if not field_desc or field_desc[0] == 0x0D:
                break
            name = field_desc[:11].split(b"\x00", 1)[0].decode("latin-1").strip()
            field_type = chr(field_desc[11])
            length = field_desc[16]
            decimal = field_desc[17]
            fields.append((name, field_type, length, decimal))

        # Skip header terminator
        terminator = handle.read(1)
        if terminator not in {b"\x0D", b""}:
            handle.seek(-1, 1)

        records: list[dict[str, Any]] = []
        for _ in range(num_records):
            raw = handle.read(record_length)
            if not raw:
                break
            if raw[0:1] == b"*":  # deleted record
                continue
            offset = 1
            record: dict[str, Any] = {}
            for name, field_type, length, decimal in fields:
                value_bytes = raw[offset : offset + length]
                offset += length
                value = value_bytes.decode("latin-1").strip()
                if not value:
                    record[name] = None
                    continue
                if field_type == "N":
                    try:
                        record[name] = int(value) if decimal == 0 else float(value)
                    except ValueError:
                        record[name] = value
                elif field_type == "F":
                    try:
                        record[name] = float(value)
                    except ValueError:
                        record[name] = value
                else:
                    record[name] = value
            records.append(record)
    return records


def iter_shapes(
    shp_path: str | Path, dbf_path: str | Path
) -> Iterable[tuple[dict[str, Any], dict[str, Any]]]:
    geometries = load_polygons(shp_path)
    attributes = load_dbf(dbf_path)
    return zip(geometries, attributes, strict=False)
