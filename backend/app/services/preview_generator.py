"""Utility helpers for generating developer preview assets."""

from __future__ import annotations

import base64
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence
from uuid import UUID

from backend._compat.datetime import utcnow

_BASE_DIR = Path(__file__).resolve().parents[2]
_PREVIEW_DIR = _BASE_DIR / "static" / "dev-previews"
_PREVIEW_DIR.mkdir(parents=True, exist_ok=True)

_EMPTY_PIXEL = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M/wHwAFgwJ/lmp3YAAAAABJRU5ErkJggg=="
)


@dataclass(slots=True, frozen=True)
class PreviewAssets:
    """Paths generated for a preview job render."""

    preview_url: str
    thumbnail_url: str


def _serialise_layer(
    layer: Mapping[str, object], *, index: int
) -> tuple[dict[str, object], list[tuple[float, float, float]]]:
    raw = dict(layer)
    name = str(raw.get("asset_type") or raw.get("name") or f"Layer {index}")
    height = float(raw.get("estimated_height_m") or raw.get("height") or 0.0)
    gfa = float(
        raw.get("gfa_sqm")
        or raw.get("nia_sqm")
        or raw.get("floor_area_sqm")
        or 100.0
    )

    footprint_area = max(gfa, 1.0)
    side = math.sqrt(footprint_area)
    half = side / 2

    base_vertices = [
        (-half, -half, 0.0),
        (half, -half, 0.0),
        (half, half, 0.0),
        (-half, half, 0.0),
    ]
    top_vertices = [(x, y, height) for (x, y, _z) in base_vertices]
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


def _calculate_bounds(vertices: Sequence[tuple[float, float, float]]) -> dict[str, dict[str, float]]:
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
    radius = max(math.hypot(dx, dy), dz) * 1.25 or 10.0
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


def build_preview_payload(
    property_id: UUID,
    massing_layers: Iterable[Mapping[str, object]],
) -> dict[str, object]:
    """Generate a structured preview payload from massing layer metadata."""

    serialised_layers: list[dict[str, object]] = []
    all_vertices: list[tuple[float, float, float]] = []
    for idx, layer in enumerate(massing_layers, start=1):
        serialised, vertices = _serialise_layer(layer, index=idx)
        serialised_layers.append(serialised)
        all_vertices.extend(vertices)

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
    property_id: UUID, massing_layers: Iterable[Mapping[str, object]]
) -> PreviewAssets:
    """Persist preview artefacts for a property and return accessible URLs."""

    payload = build_preview_payload(property_id, massing_layers)

    json_path = _PREVIEW_DIR / f"{property_id}.json"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    thumbnail_path = _PREVIEW_DIR / f"{property_id}.png"
    thumbnail_path.write_bytes(_EMPTY_PIXEL)

    return PreviewAssets(
        preview_url=f"/static/dev-previews/{property_id}.json",
        thumbnail_url=f"/static/dev-previews/{property_id}.png",
    )


__all__ = ["build_preview_payload", "ensure_preview_asset", "PreviewAssets"]
