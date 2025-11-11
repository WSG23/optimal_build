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


@dataclass(slots=True, frozen=True)
class PreviewAssets:
    """Paths generated for a preview job render."""

    preview_url: str
    metadata_url: str
    thumbnail_url: str
    asset_version: str


def _serialise_layer(
    layer: Mapping[str, object], *, index: int, base_elevation: float = 0.0
) -> tuple[dict[str, object], list[tuple[float, float, float]]]:
    raw = dict(layer)
    name = str(raw.get("asset_type") or raw.get("name") or f"Layer {index}")
    height = float(raw.get("estimated_height_m") or raw.get("height") or 0.0)
    gfa = float(
        raw.get("gfa_sqm") or raw.get("nia_sqm") or raw.get("floor_area_sqm") or 100.0
    )

    footprint_area = max(gfa, 1.0)
    side = math.sqrt(footprint_area)
    half = side / 2

    base_vertices = [
        (-half, -half, base_elevation),
        (half, -half, base_elevation),
        (half, half, base_elevation),
        (-half, half, base_elevation),
    ]
    top_vertices = [(x, y, base_elevation + height) for (x, y, _z) in base_vertices]
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

    serialised = {
        "id": raw.get("id") or f"layer-{index}",
        "name": name,
        "color": raw.get("color"),
        "metrics": {
            "allocation_pct": raw.get("allocation_pct"),
            "gfa_sqm": gfa,
            "nia_sqm": raw.get("nia_sqm"),
            "estimated_height_m": height,
            "estimated_floors": raw.get("estimated_floors"),
        },
        "geometry": {
            "footprint": {
                "type": "Polygon",
                "coordinates": [footprint],
            },
            "prism": {
                "vertices": [[x, y, z] for x, y, z in vertices],
                "faces": faces,
            },
        },
    }

    return serialised, vertices


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

    # Convert original XYZ (with Z up) into glTF coordinates (Y up).
    converted: list[list[float]] = []
    for vertex in vertices:
        if not isinstance(vertex, Sequence) or len(vertex) != 3:
            return None
        x, y, z = float(vertex[0]), float(vertex[1]), float(vertex[2])
        converted.append([x, z, y])

    positions, normals, indices, mins, maxs = _build_box_geometry(converted)
    colour = _normalise_hex_colour(layer.get("color"), index)
    name = str(layer.get("name") or layer.get("id") or f"Layer {index}")
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
        meshes.append(
            {
                "name": mesh_data["name"],
                "primitives": [
                    {
                        "attributes": {
                            "POSITION": pos_accessor_index,
                            "NORMAL": normal_accessor_index,
                        },
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
    size = 320
    image = Image.new("RGBA", (size, size), (245, 246, 248, 255))
    draw = ImageDraw.Draw(image)

    footprints: list[list[tuple[float, float]]] = []
    colours: list[tuple[int, int, int, int]] = []

    for index, layer in enumerate(layers):
        geometry = layer.get("geometry")
        footprint = None
        if isinstance(geometry, Mapping):
            footprint_data = geometry.get("footprint")
            if isinstance(footprint_data, Mapping):
                coords = footprint_data.get("coordinates")
                if (
                    isinstance(coords, Sequence)
                    and coords
                    and isinstance(coords[0], Sequence)
                ):
                    footprint = [
                        (float(point[0]), float(point[1]))
                        for point in coords[0]
                        if isinstance(point, Sequence) and len(point) >= 2
                    ]
        if not footprint:
            continue

        colour = _normalise_hex_colour(layer.get("color"), index)
        rgba = tuple(int(channel * 255) for channel in colour[:3]) + (235,)
        footprints.append(footprint)
        colours.append(rgba)

    if not footprints:
        image.save(asset_dir / "thumbnail.png", "PNG")
        return

    xs = [point[0] for footprint in footprints for point in footprint]
    ys = [point[1] for footprint in footprints for point in footprint]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span = max(max_x - min_x, max_y - min_y) or 1.0
    scale = (size * 0.7) / span
    offset_x = size / 2
    offset_y = size / 2

    for footprint, colour in zip(footprints, colours, strict=True):
        screen_points = []
        for x, y in footprint:
            screen_x = offset_x + (x - (min_x + max_x) / 2) * scale
            screen_y = offset_y - (y - (min_y + max_y) / 2) * scale
            screen_points.append((screen_x, screen_y))
        draw.polygon(screen_points, fill=colour, outline=(40, 40, 70, 180))

    image = image.resize((256, 256), Image.LANCZOS)
    image.save(asset_dir / "thumbnail.png", "PNG")


def build_preview_payload(
    property_id: UUID,
    massing_layers: Iterable[Mapping[str, object]],
) -> dict[str, object]:
    """Generate a structured preview payload from massing layer metadata.

    Layers are stacked vertically: first layer at ground level (z=0),
    subsequent layers stacked on top of previous layer's height.
    """

    serialised_layers: list[dict[str, object]] = []
    all_vertices: list[tuple[float, float, float]] = []
    current_elevation = 0.0

    for idx, layer in enumerate(massing_layers, start=1):
        serialised, vertices = _serialise_layer(
            layer, index=idx, base_elevation=current_elevation
        )
        serialised_layers.append(serialised)
        all_vertices.extend(vertices)

        # Stack next layer on top of this one
        layer_height = float(
            layer.get("estimated_height_m") or layer.get("height") or 0.0
        )
        current_elevation += layer_height

    if not serialised_layers:
        raise ValueError("Preview payload requires at least one massing layer")

    bounds = _calculate_bounds(all_vertices)
    payload = {
        "schema_version": "1.0",
        "property_id": str(property_id),
        "generated_at": utcnow().isoformat().replace("+00:00", "Z"),
        "bounding_box": bounds,
        "camera_orbit_hint": _camera_orbit_from_bounds(bounds),
        "layers": serialised_layers,
    }
    return payload


def ensure_preview_asset(
    property_id: UUID,
    job_id: UUID,
    massing_layers: Iterable[Mapping[str, object]],
) -> PreviewAssets:
    """Persist preview artefacts for a property and return accessible URLs."""

    payload = build_preview_payload(property_id, massing_layers)

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


__all__ = ["build_preview_payload", "ensure_preview_asset", "PreviewAssets"]
