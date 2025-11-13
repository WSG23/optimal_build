"""Utility helpers for generating developer preview assets."""

from __future__ import annotations

import json
import math
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence
from uuid import UUID

from backend._compat.datetime import utcnow
from PIL import Image, ImageDraw

_BASE_DIR = Path(__file__).resolve().parents[2]
_PREVIEW_DIR = _BASE_DIR / "static" / "dev-previews"
_PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
PREVIEW_STORAGE_DIR = _PREVIEW_DIR

_DEFAULT_LAYER_COLOURS = [
    "#6366F1",
    "#22C55E",
    "#F97316",
    "#0EA5E9",
    "#A855F7",
    "#FACC15",
    "#EF4444",
    "#14B8A6",
]

SUPPORTED_GEOMETRY_DETAIL_LEVELS = frozenset({"simple", "medium"})
DEFAULT_GEOMETRY_DETAIL_LEVEL = "medium"
_FLOOR_LINE_SPACING_M = 3.5
_PODIUM_MAX_HEIGHT_M = 6.0
_SETBACK_THRESHOLD_M = 60.0
_MIN_EFFECTIVE_HEIGHT_M = 3.0


def normalise_geometry_detail_level(value: str | None) -> str:
    """Return a supported geometry detail level."""

    if not value:
        return DEFAULT_GEOMETRY_DETAIL_LEVEL
    candidate = value.strip().lower()
    if candidate in SUPPORTED_GEOMETRY_DETAIL_LEVELS:
        return candidate
    return DEFAULT_GEOMETRY_DETAIL_LEVEL


@dataclass(slots=True, frozen=True)
class PreviewAssets:
    """Paths generated for a preview job render."""

    preview_url: str
    metadata_url: str
    thumbnail_url: str
    asset_version: str


def _regular_polygon_vertices(
    area: float, *, sides: int = 8, rotation_degrees: float = 0.0
) -> list[tuple[float, float]]:
    """Return coordinates for a regular polygon approximating the supplied area."""

    safe_area = max(area, 1.0)
    central_angle = 2 * math.pi / max(sides, 3)
    radius = math.sqrt((2 * safe_area) / (sides * math.sin(central_angle)))
    rotation_radians = math.radians(rotation_degrees)

    points: list[tuple[float, float]] = []
    for index in range(sides):
        theta = rotation_radians + index * central_angle
        points.append((radius * math.cos(theta), radius * math.sin(theta)))
    return points


def _build_floor_line_heights(height: float) -> list[float]:
    """Return the relative heights for decorative floor lines."""

    total = max(height, 0.0)
    if total <= _FLOOR_LINE_SPACING_M:
        return []
    lines: list[float] = []
    level = _FLOOR_LINE_SPACING_M
    while level < total:
        lines.append(round(level, 3))
        level += _FLOOR_LINE_SPACING_M
    return lines


def _build_profile_sections(height: float) -> list[tuple[float, float]]:
    """Return (height, scale) tuples describing setback profile sections."""

    effective_height = max(height, _MIN_EFFECTIVE_HEIGHT_M)
    profile: list[tuple[float, float]] = [(0.0, 1.05 if effective_height >= 6 else 1.0)]

    podium_height = min(_PODIUM_MAX_HEIGHT_M, effective_height)
    if effective_height > podium_height:
        profile.append((podium_height, 1.0))

    if effective_height > _SETBACK_THRESHOLD_M:
        first = max(podium_height, effective_height / 3)
        second = max(first + 0.1, (2 * effective_height) / 3)
        profile.append((first, 0.85))
        profile.append((second, 0.75))
        top_scale = 0.72
    else:
        top_scale = 0.95

    if not profile or profile[-1][0] != effective_height:
        profile.append((effective_height, top_scale))

    deduped: list[tuple[float, float]] = []
    for height_offset, scale in profile:
        if deduped and math.isclose(deduped[-1][0], height_offset, abs_tol=1e-3):
            deduped[-1] = (height_offset, scale)
        else:
            deduped.append((height_offset, scale))
    return deduped


def _build_simple_geometry(
    *,
    footprint_area: float,
    base_elevation: float,
    preview_height: float,
) -> tuple[dict[str, object], list[tuple[float, float, float]], float]:
    """Return geometry metadata for the legacy box prism."""

    side = math.sqrt(max(footprint_area, 1.0))
    half = side / 2
    top_height = base_elevation + preview_height

    base_vertices = [
        (-half, -half, base_elevation),
        (half, -half, base_elevation),
        (half, half, base_elevation),
        (-half, half, base_elevation),
    ]
    top_vertices = [(x, y, top_height) for (x, y, _z) in base_vertices]
    vertices = base_vertices + top_vertices

    footprint = [
        [-half, -half],
        [half, -half],
        [half, half],
        [-half, half],
        [-half, -half],
    ]
    faces = [
        [0, 1, 2],
        [0, 2, 3],
        [4, 5, 6],
        [4, 6, 7],
        [0, 1, 5],
        [0, 5, 4],
        [1, 2, 6],
        [1, 6, 5],
        [2, 3, 7],
        [2, 7, 6],
        [3, 0, 4],
        [3, 4, 7],
    ]
    geometry = {
        "detail_level": "simple",
        "base_elevation": base_elevation,
        "height": preview_height,
        "preview_height": preview_height,
        "footprint": {"type": "Polygon", "coordinates": [footprint]},
        "top_footprint": {"type": "Polygon", "coordinates": [footprint]},
        "prism": {
            "vertices": [[x, y, z] for x, y, z in vertices],
            "faces": faces,
        },
        "floor_lines": [],
    }
    return geometry, vertices, preview_height


def _build_medium_geometry(
    *,
    footprint_area: float,
    base_elevation: float,
    height: float,
) -> tuple[dict[str, object], list[tuple[float, float, float]], float]:
    """Return octagonal geometry with podium + setback detail."""

    polygon = _regular_polygon_vertices(
        max(footprint_area, 1.0), sides=8, rotation_degrees=22.5
    )
    profile = _build_profile_sections(height)
    preview_height = profile[-1][0]
    num_points = len(polygon)
    vertices: list[tuple[float, float, float]] = []

    for height_offset, scale in profile:
        z = base_elevation + height_offset
        for x, y in polygon:
            vertices.append((x * scale, y * scale, z))

    faces: list[list[int]] = []
    ring_count = len(profile)
    for ring_index in range(ring_count - 1):
        lower_offset = ring_index * num_points
        upper_offset = (ring_index + 1) * num_points
        for idx in range(num_points):
            nxt = (idx + 1) % num_points
            faces.append(
                [
                    lower_offset + idx,
                    lower_offset + nxt,
                    upper_offset + nxt,
                ]
            )
            faces.append(
                [
                    lower_offset + idx,
                    upper_offset + nxt,
                    upper_offset + idx,
                ]
            )

    # Bottom cap (fan)
    for idx in range(1, num_points - 1):
        faces.append([0, idx, idx + 1])

    # Top cap (fan with reversed orientation)
    top_offset = (ring_count - 1) * num_points
    for idx in range(1, num_points - 1):
        faces.append([top_offset, top_offset + idx + 1, top_offset + idx])

    footprint = [list(point) for point in polygon] + [list(polygon[0])]
    top_scale = profile[-1][1]
    top_polygon = [
        [point[0] * top_scale, point[1] * top_scale] for point in polygon
    ] + [[polygon[0][0] * top_scale, polygon[0][1] * top_scale]]

    floor_line_heights = [
        base_elevation + rel_height for rel_height in _build_floor_line_heights(height)
    ]

    geometry = {
        "detail_level": "medium",
        "base_elevation": base_elevation,
        "height": height,
        "preview_height": preview_height,
        "footprint": {"type": "Polygon", "coordinates": [footprint]},
        "top_footprint": {"type": "Polygon", "coordinates": [top_polygon]},
        "floor_lines": floor_line_heights,
        "prism": {
            "vertices": [[x, y, z] for x, y, z in vertices],
            "faces": faces,
        },
    }
    return geometry, vertices, preview_height


def _serialise_layer(
    layer: Mapping[str, object],
    *,
    index: int,
    base_elevation: float = 0.0,
    detail_level: str = DEFAULT_GEOMETRY_DETAIL_LEVEL,
) -> tuple[dict[str, object], list[tuple[float, float, float]], float]:
    raw = dict(layer)
    name = str(raw.get("asset_type") or raw.get("name") or f"Layer {index}")
    requested_height = float(raw.get("estimated_height_m") or raw.get("height") or 0.0)
    gfa = float(
        raw.get("gfa_sqm") or raw.get("nia_sqm") or raw.get("floor_area_sqm") or 100.0
    )

    preview_height = max(requested_height, 0.0)
    normalised_level = normalise_geometry_detail_level(detail_level)
    if normalised_level == "medium":
        geometry, vertices, preview_height = _build_medium_geometry(
            footprint_area=gfa,
            base_elevation=base_elevation,
            height=requested_height,
        )
    else:
        preview_height = max(requested_height, 0.5)
        geometry, vertices, preview_height = _build_simple_geometry(
            footprint_area=gfa,
            base_elevation=base_elevation,
            preview_height=preview_height,
        )

    serialised = {
        "id": raw.get("id") or f"layer-{index}",
        "name": name,
        "color": raw.get("color"),
        "metrics": {
            "allocation_pct": raw.get("allocation_pct"),
            "gfa_sqm": gfa,
            "nia_sqm": raw.get("nia_sqm"),
            "estimated_height_m": requested_height,
            "estimated_floors": raw.get("estimated_floors"),
        },
        "geometry": geometry,
    }

    return serialised, vertices, preview_height


def _calculate_bounds(
    vertices: Sequence[tuple[float, float, float]]
) -> dict[str, dict[str, float]]:
    xs = [x for x, _y, _z in vertices]
    ys = [y for _x, y, _z in vertices]
    zs = [z for _x, _y, z in vertices]
    return {
        "min": {"x": min(xs), "y": min(ys), "z": min(zs)},
        "max": {"x": max(xs), "y": max(ys), "z": max(zs)},
    }


def _camera_orbit_from_bounds(bounds: dict[str, dict[str, float]]) -> dict[str, float]:
    dx = bounds["max"]["x"] - bounds["min"]["x"]
    dy = bounds["max"]["y"] - bounds["min"]["y"]
    dz = bounds["max"]["z"] - bounds["min"]["z"]
    radius = max(math.hypot(dx, dz), dy) * 1.25 or 10.0
    center_x = (bounds["max"]["x"] + bounds["min"]["x"]) / 2
    center_y = (bounds["max"]["y"] + bounds["min"]["y"]) / 2
    center_z = (bounds["max"]["z"] + bounds["min"]["z"]) / 2
    return {
        "theta": 45.0,
        "phi": 45.0,
        "radius": radius,
        "target_x": center_x,
        "target_y": center_y,
        "target_z": center_z,
    }


def _normalise_hex_colour(
    raw: str | None, index: int
) -> tuple[float, float, float, float]:
    colour = raw or _DEFAULT_LAYER_COLOURS[index % len(_DEFAULT_LAYER_COLOURS)]
    if colour.startswith("#"):
        colour = colour[1:]
    if len(colour) == 3:
        colour = "".join(ch * 2 for ch in colour)
    try:
        r = int(colour[0:2], 16) / 255.0
        g = int(colour[2:4], 16) / 255.0
        b = int(colour[4:6], 16) / 255.0
    except ValueError:
        r, g, b = (0.45, 0.45, 0.62)
    return (round(r, 4), round(g, 4), round(b, 4), 0.92)


def _align4(buffer: bytearray) -> None:
    while len(buffer) % 4:
        buffer.append(0)


def _build_box_geometry(
    vertices: Sequence[Sequence[float]],
) -> tuple[list[float], list[float], list[int], list[float], list[float]]:
    xs = [vertex[0] for vertex in vertices]
    ys = [vertex[1] for vertex in vertices]
    zs = [vertex[2] for vertex in vertices]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    min_z, max_z = min(zs), max(zs)

    corners = [
        (min_x, min_y, min_z),
        (max_x, min_y, min_z),
        (max_x, min_y, max_z),
        (min_x, min_y, max_z),
        (min_x, max_y, min_z),
        (max_x, max_y, min_z),
        (max_x, max_y, max_z),
        (min_x, max_y, max_z),
    ]

    faces = [
        ((0, 1, 2, 3), (0.0, -1.0, 0.0)),  # bottom
        ((4, 5, 6, 7), (0.0, 1.0, 0.0)),  # top
        ((0, 1, 5, 4), (0.0, 0.0, -1.0)),  # back
        ((1, 2, 6, 5), (1.0, 0.0, 0.0)),  # right
        ((2, 3, 7, 6), (0.0, 0.0, 1.0)),  # front
        ((3, 0, 4, 7), (-1.0, 0.0, 0.0)),  # left
    ]

    positions: list[float] = []
    normals: list[float] = []
    indices: list[int] = []

    for face_vertices, normal in faces:
        start_index = len(positions) // 3
        for vertex_index in face_vertices:
            x, y, z = corners[vertex_index]
            positions.extend([x, y, z])
            normals.extend(normal)
        indices.extend(
            [
                start_index,
                start_index + 1,
                start_index + 2,
                start_index,
                start_index + 2,
                start_index + 3,
            ]
        )

    return (
        positions,
        normals,
        indices,
        [min_x, min_y, min_z],
        [max_x, max_y, max_z],
    )


def _convert_vertices(vertices: Sequence[Sequence[float]]) -> list[list[float]]:
    converted: list[list[float]] = []
    for vertex in vertices:
        if not isinstance(vertex, Sequence) or len(vertex) != 3:
            raise ValueError("Invalid vertex payload")
        x, y, z = float(vertex[0]), float(vertex[1]), float(vertex[2])
        converted.append([x, z, y])
    return converted


def _triangulate_faces(faces: Sequence[Sequence[object]]) -> list[list[int]]:
    triangles: list[list[int]] = []
    for face in faces:
        if not isinstance(face, Sequence):
            continue
        indices: list[int] = []
        for value in face:
            if isinstance(value, (int, float)):
                indices.append(int(value))
        if len(indices) < 3:
            continue
        for offset in range(1, len(indices) - 1):
            triangles.append([indices[0], indices[offset], indices[offset + 1]])
    return triangles


def _compute_vertex_normals(
    vertices: Sequence[Sequence[float]], triangles: Sequence[Sequence[int]]
) -> list[list[float]]:
    normals = [[0.0, 0.0, 0.0] for _ in vertices]
    for tri in triangles:
        try:
            i0, i1, i2 = tri
            v0 = vertices[i0]
            v1 = vertices[i1]
            v2 = vertices[i2]
        except (ValueError, IndexError):
            continue
        ax, ay, az = v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2]
        bx, by, bz = v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2]
        nx = ay * bz - az * by
        ny = az * bx - ax * bz
        nz = ax * by - ay * bx
        for idx in tri:
            if 0 <= idx < len(normals):
                normals[idx][0] += nx
                normals[idx][1] += ny
                normals[idx][2] += nz

    for normal in normals:
        length = math.sqrt(
            normal[0] * normal[0] + normal[1] * normal[1] + normal[2] * normal[2]
        )
        if length > 0:
            normal[0] /= length
            normal[1] /= length
            normal[2] /= length
        else:
            normal[1] = 1.0
    return normals


def _build_vertex_colors(
    base_colour: tuple[float, float, float, float],
    vertices: Sequence[Sequence[float]],
    floor_lines: Sequence[float] | None,
) -> list[float]:
    heights = [vertex[1] for vertex in vertices]
    min_height = min(heights)
    max_height = max(heights)
    span = max(max_height - min_height, 1.0)
    line_values = sorted(
        float(value) for value in (floor_lines or []) if isinstance(value, (int, float))
    )
    colours: list[float] = []
    for height in heights:
        ratio = (height - min_height) / span
        brightness = 0.65 + 0.3 * ratio
        if line_values:
            for value in line_values:
                if abs(height - value) <= 0.15:
                    brightness = min(brightness, 0.5)
                    break
        r = min(max(base_colour[0] * brightness, 0.0), 1.0)
        g = min(max(base_colour[1] * brightness, 0.0), 1.0)
        b = min(max(base_colour[2] * brightness, 0.0), 1.0)
        colours.extend([r, g, b, base_colour[3]])
    return colours


def _build_custom_mesh(
    *,
    name: str,
    colour: tuple[float, float, float, float],
    vertices: Sequence[Sequence[float]],
    faces: Sequence[Sequence[object]],
    floor_lines: Sequence[float] | None,
    base_elevation: float,
) -> dict[str, object] | None:
    try:
        converted = _convert_vertices(vertices)
    except ValueError:
        return None

    triangles = _triangulate_faces(faces)
    if not triangles:
        return None

    normals = _compute_vertex_normals(converted, triangles)
    positions = [component for vertex in converted for component in vertex]
    normals_flat = [component for normal in normals for component in normal]
    indices = [int(value) for tri in triangles for value in tri]

    min_x = min(vertex[0] for vertex in converted)
    min_y = min(vertex[1] for vertex in converted)
    min_z = min(vertex[2] for vertex in converted)
    max_x = max(vertex[0] for vertex in converted)
    max_y = max(vertex[1] for vertex in converted)
    max_z = max(vertex[2] for vertex in converted)

    vertex_colours = _build_vertex_colors(colour, converted, floor_lines)

    return {
        "name": name,
        "positions": positions,
        "normals": normals_flat,
        "indices": indices,
        "color": colour,
        "vertex_colors": vertex_colours,
        "min": [min_x, min_y, min_z],
        "max": [max_x, max_y, max_z],
    }


def _build_layer_mesh(
    layer: Mapping[str, object],
    *,
    index: int,
) -> dict[str, object] | None:
    geometry = layer.get("geometry")
    if not isinstance(geometry, Mapping):
        return None
    prism = geometry.get("prism")
    if not isinstance(prism, Mapping):
        return None
    vertices = prism.get("vertices")
    if not isinstance(vertices, Sequence):
        return None
    faces = prism.get("faces")
    name = str(layer.get("name") or layer.get("id") or f"Layer {index}")
    colour = _normalise_hex_colour(layer.get("color"), index)
    floor_lines = geometry.get("floor_lines")
    base_elevation = float(geometry.get("base_elevation") or 0.0)

    if isinstance(faces, Sequence) and faces:
        return _build_custom_mesh(
            name=name,
            colour=colour,
            vertices=vertices,
            faces=faces,
            floor_lines=floor_lines,
            base_elevation=base_elevation,
        )

    # Convert original XYZ (with Z up) into glTF coordinates (Y up) for legacy boxes.
    converted: list[list[float]] = []
    for vertex in vertices:
        if not isinstance(vertex, Sequence) or len(vertex) != 3:
            return None
        x, y, z = float(vertex[0]), float(vertex[1]), float(vertex[2])
        converted.append([x, z, y])

    positions, normals, indices, mins, maxs = _build_box_geometry(converted)
    return {
        "name": name,
        "positions": positions,
        "normals": normals,
        "indices": indices,
        "color": colour,
        "min": mins,
        "max": maxs,
    }


def _build_gltf_document(
    property_id: UUID,
    asset_version: str,
    layers: Sequence[Mapping[str, object]],
) -> tuple[dict[str, object], bytes]:
    buffer = bytearray()
    buffer_views: list[dict[str, object]] = []
    accessors: list[dict[str, object]] = []
    meshes: list[dict[str, object]] = []
    materials: list[dict[str, object]] = []
    nodes: list[dict[str, object]] = []

    for index, layer in enumerate(layers):
        mesh_data = _build_layer_mesh(layer, index=index)
        if mesh_data is None:
            continue

        positions = mesh_data["positions"]
        normals = mesh_data["normals"]
        indices = mesh_data["indices"]
        colour = mesh_data["color"]

        # Positions
        pos_bytes = struct.pack("<" + "f" * len(positions), *positions)
        pos_offset = len(buffer)
        buffer.extend(pos_bytes)
        _align4(buffer)
        buffer_view_index = len(buffer_views)
        buffer_views.append(
            {
                "buffer": 0,
                "byteOffset": pos_offset,
                "byteLength": len(pos_bytes),
                "target": 34962,
            }
        )
        pos_accessor_index = len(accessors)
        accessors.append(
            {
                "bufferView": buffer_view_index,
                "componentType": 5126,
                "count": len(positions) // 3,
                "type": "VEC3",
                "min": mesh_data["min"],
                "max": mesh_data["max"],
            }
        )

        # Normals
        normal_bytes = struct.pack("<" + "f" * len(normals), *normals)
        normal_offset = len(buffer)
        buffer.extend(normal_bytes)
        _align4(buffer)
        buffer_view_index = len(buffer_views)
        buffer_views.append(
            {
                "buffer": 0,
                "byteOffset": normal_offset,
                "byteLength": len(normal_bytes),
                "target": 34962,
            }
        )
        normal_accessor_index = len(accessors)
        accessors.append(
            {
                "bufferView": buffer_view_index,
                "componentType": 5126,
                "count": len(normals) // 3,
                "type": "VEC3",
            }
        )

        color_accessor_index = None
        vertex_colors = mesh_data.get("vertex_colors")
        if isinstance(vertex_colors, list) and vertex_colors:
            color_bytes = struct.pack("<" + "f" * len(vertex_colors), *vertex_colors)
            color_offset = len(buffer)
            buffer.extend(color_bytes)
            _align4(buffer)
            buffer_view_index = len(buffer_views)
            buffer_views.append(
                {
                    "buffer": 0,
                    "byteOffset": color_offset,
                    "byteLength": len(color_bytes),
                    "target": 34962,
                }
            )
            color_accessor_index = len(accessors)
            accessors.append(
                {
                    "bufferView": buffer_view_index,
                    "componentType": 5126,
                    "count": len(vertex_colors) // 4,
                    "type": "VEC4",
                }
            )

        # Indices
        index_bytes = struct.pack("<" + "H" * len(indices), *indices)
        index_offset = len(buffer)
        buffer.extend(index_bytes)
        _align4(buffer)
        buffer_view_index = len(buffer_views)
        buffer_views.append(
            {
                "buffer": 0,
                "byteOffset": index_offset,
                "byteLength": len(index_bytes),
                "target": 34963,
            }
        )
        index_accessor_index = len(accessors)
        accessors.append(
            {
                "bufferView": buffer_view_index,
                "componentType": 5123,
                "count": len(indices),
                "type": "SCALAR",
            }
        )

        material_index = len(materials)
        materials.append(
            {
                "name": mesh_data["name"],
                "pbrMetallicRoughness": {
                    "baseColorFactor": list(colour),
                    "metallicFactor": 0.0,
                    "roughnessFactor": 0.6,
                },
                "doubleSided": True,
            }
        )

        mesh_index = len(meshes)
        attributes = {
            "POSITION": pos_accessor_index,
            "NORMAL": normal_accessor_index,
        }
        if color_accessor_index is not None:
            attributes["COLOR_0"] = color_accessor_index
        meshes.append(
            {
                "name": mesh_data["name"],
                "primitives": [
                    {
                        "attributes": attributes,
                        "indices": index_accessor_index,
                        "material": material_index,
                        "mode": 4,  # TRIANGLES
                    }
                ],
            }
        )
        nodes.append({"name": mesh_data["name"], "mesh": mesh_index})

    gltf: dict[str, object] = {
        "asset": {
            "version": "2.0",
            "generator": "optimal-build-preview-1.0",
        },
        "scene": 0,
        "scenes": [{"name": str(property_id), "nodes": list(range(len(nodes)))}],
        "nodes": nodes,
        "meshes": meshes,
        "materials": materials,
        "buffers": [
            {
                "byteLength": len(buffer),
                "uri": "preview.bin",
            }
        ],
        "bufferViews": buffer_views,
        "accessors": accessors,
    }

    if not nodes:
        raise ValueError("Preview payload missing valid geometry layers")

    return gltf, bytes(buffer)


def _write_thumbnail(
    asset_dir: Path,
    layers: Sequence[Mapping[str, object]],
) -> None:
    size = 512
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    def iso_project(x: float, y: float, z: float) -> tuple[float, float]:
        angle = math.radians(45)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        iso_x = (x - y) * cos_a
        iso_y = (x + y) * sin_a - z * 0.9
        return iso_x, iso_y

    shapes: list[dict[str, object]] = []
    iso_points: list[tuple[float, float]] = []

    for index, layer in enumerate(layers):
        geometry = layer.get("geometry")
        if not isinstance(geometry, Mapping):
            continue
        footprint_data = geometry.get("footprint")
        if not isinstance(footprint_data, Mapping):
            continue
        coords = footprint_data.get("coordinates")
        if (
            not isinstance(coords, Sequence)
            or not coords
            or not isinstance(coords[0], Sequence)
        ):
            continue
        base_polygon = [
            (float(point[0]), float(point[1]))
            for point in coords[0]
            if isinstance(point, Sequence) and len(point) >= 2
        ]
        if len(base_polygon) < 3:
            continue
        top_coords = geometry.get("top_footprint", footprint_data)
        if isinstance(top_coords, Mapping):
            top_polygon = [
                (float(point[0]), float(point[1]))
                for point in top_coords.get("coordinates", [coords[0]])[0]
                if isinstance(point, Sequence) and len(point) >= 2
            ]
        else:
            top_polygon = base_polygon

        base_elevation = float(geometry.get("base_elevation") or 0.0)
        preview_height = float(
            geometry.get("preview_height") or geometry.get("height") or 0.0
        )
        top_elevation = base_elevation + preview_height
        colour = _normalise_hex_colour(layer.get("color"), index)

        shapes.append(
            {
                "base": base_polygon,
                "top": top_polygon,
                "base_elevation": base_elevation,
                "top_elevation": top_elevation,
                "colour": colour,
            }
        )

        for x, y in base_polygon:
            iso_points.append(iso_project(x, y, base_elevation))
        for x, y in top_polygon:
            iso_points.append(iso_project(x, y, top_elevation))

    if not shapes or not iso_points:
        image.save(asset_dir / "thumbnail.png", "PNG")
        return

    min_x = min(point[0] for point in iso_points)
    max_x = max(point[0] for point in iso_points)
    min_y = min(point[1] for point in iso_points)
    max_y = max(point[1] for point in iso_points)
    span = max(max_x - min_x, max_y - min_y) or 1.0
    margin = size * 0.12
    scale = (size - 2 * margin) / span
    offset_x = size / 2 - ((min_x + max_x) / 2) * scale
    offset_y = size / 2 + ((min_y + max_y) / 2) * scale

    def to_screen(point: tuple[float, float]) -> tuple[float, float]:
        return (
            offset_x + point[0] * scale,
            offset_y - point[1] * scale,
        )

    # Subtle drop shadow
    shadow_width = (max_x - min_x) * scale * 0.8
    shadow_height = shadow_width * 0.3
    shadow_rect = [
        (size / 2 - shadow_width / 2, size - margin * 0.6),
        (size / 2 + shadow_width / 2, size - margin * 0.6 + shadow_height),
    ]
    draw.ellipse(shadow_rect, fill=(15, 25, 55, 90))

    for shape in sorted(shapes, key=lambda item: item["top_elevation"]):
        base = [
            to_screen(iso_project(x, y, shape["base_elevation"]))
            for x, y in shape["base"]
        ]
        top = [
            to_screen(iso_project(x, y, shape["top_elevation"]))
            for x, y in shape["top"]
        ]

        base_colour = tuple(int(channel * 255) for channel in shape["colour"][:3])
        top_colour = tuple(
            min(int(channel * 255 * 1.1), 255) for channel in shape["colour"][:3]
        )

        draw.polygon(base, fill=base_colour + (120,), outline=(20, 30, 60, 160))
        draw.polygon(top, fill=top_colour + (200,), outline=(35, 45, 75, 210))

        for idx in range(min(len(base), len(top))):
            draw.line(
                [base[idx], top[idx]],
                fill=(25, 35, 65, 200),
                width=2,
            )

    image = image.resize((256, 256), Image.LANCZOS)
    image.save(asset_dir / "thumbnail.png", "PNG")


def build_preview_payload(
    property_id: UUID,
    massing_layers: Iterable[Mapping[str, object]],
    *,
    geometry_detail_level: str = DEFAULT_GEOMETRY_DETAIL_LEVEL,
) -> dict[str, object]:
    """Generate a structured preview payload from massing layer metadata.

    Layers are stacked vertically: first layer at ground level (z=0),
    subsequent layers stacked on top of previous layer's height.
    """

    serialised_layers: list[dict[str, object]] = []
    all_vertices: list[tuple[float, float, float]] = []
    current_elevation = 0.0
    detail_level = normalise_geometry_detail_level(geometry_detail_level)

    for idx, layer in enumerate(massing_layers, start=1):
        serialised, vertices, preview_height = _serialise_layer(
            layer,
            index=idx,
            base_elevation=current_elevation,
            detail_level=detail_level,
        )
        serialised_layers.append(serialised)
        all_vertices.extend(vertices)

        current_elevation += preview_height

    if not serialised_layers:
        raise ValueError("Preview payload requires at least one massing layer")

    bounds = _calculate_bounds(all_vertices)
    payload = {
        "schema_version": "1.0",
        "property_id": str(property_id),
        "generated_at": utcnow().isoformat().replace("+00:00", "Z"),
        "bounding_box": bounds,
        "camera_orbit_hint": _camera_orbit_from_bounds(bounds),
        "geometry_detail_level": detail_level,
        "layers": serialised_layers,
    }
    return payload


def ensure_preview_asset(
    property_id: UUID,
    job_id: UUID,
    massing_layers: Iterable[Mapping[str, object]],
    *,
    geometry_detail_level: str = DEFAULT_GEOMETRY_DETAIL_LEVEL,
) -> PreviewAssets:
    """Persist preview artefacts for a property and return accessible URLs."""

    detail_level = normalise_geometry_detail_level(geometry_detail_level)
    payload = build_preview_payload(
        property_id,
        massing_layers,
        geometry_detail_level=detail_level,
    )

    asset_version = f"{utcnow().strftime('%Y%m%d%H%M%S')}-{job_id.hex[:8]}"
    asset_dir = _PREVIEW_DIR / str(property_id) / asset_version
    asset_dir.mkdir(parents=True, exist_ok=True)

    gltf_document, binary_blob = _build_gltf_document(
        property_id,
        asset_version,
        payload["layers"],  # type: ignore[arg-type]
    )

    base_url = f"/static/dev-previews/{property_id}/{asset_version}"
    payload["asset_manifest"] = {
        "gltf": f"{base_url}/preview.gltf",
        "metadata": f"{base_url}/preview.json",
        "binary": f"{base_url}/preview.bin",
        "thumbnail": f"{base_url}/thumbnail.png",
        "version": asset_version,
    }
    payload["geometry_detail_level"] = detail_level

    metadata_path = asset_dir / "preview.json"
    metadata_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    gltf_path = asset_dir / "preview.gltf"
    gltf_path.write_text(
        json.dumps(gltf_document, separators=(",", ":")), encoding="utf-8"
    )

    binary_path = asset_dir / "preview.bin"
    binary_path.write_bytes(binary_blob)

    _write_thumbnail(asset_dir, payload["layers"])  # type: ignore[arg-type]

    return PreviewAssets(
        preview_url=f"{base_url}/preview.gltf",
        metadata_url=f"{base_url}/preview.json",
        thumbnail_url=f"{base_url}/thumbnail.png",
        asset_version=asset_version,
    )


__all__ = [
    "build_preview_payload",
    "ensure_preview_asset",
    "PreviewAssets",
    "SUPPORTED_GEOMETRY_DETAIL_LEVELS",
    "normalise_geometry_detail_level",
]
