"""CAD and BIM parsing jobs."""

from __future__ import annotations

import asyncio
import json
import math
import os
import tempfile
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from backend._compat import compat_dataclass
from backend._compat.datetime import UTC

try:  # pragma: no cover - optional dependency
    import ezdxf  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - available in production environments
    ezdxf = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    import ifcopenshell  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - available in production environments
    ifcopenshell = None  # type: ignore[assignment]

from app.core import database as app_database
from app.core.geometry import GeometrySerializer, GraphBuilder
from app.core.models.geometry import GeometryGraph
from app.models.imports import ImportRecord
from app.services.overlay_ingest import ingest_parsed_import_geometry
from app.services.storage import get_storage_service
from backend.jobs import job


@compat_dataclass(slots=True)
class ParsedGeometry:
    """Result emitted by the parsing pipeline."""

    graph: GeometryGraph
    floors: list[dict[str, Any]]
    units: list[str]
    layers: list[dict[str, Any]]
    metadata: dict[str, Any]


@compat_dataclass(slots=True)
class DxfSpaceCandidate:
    """Representation of a DXF entity that can be treated as a space."""

    identifier: str
    boundary: list[dict[str, float]]
    layer: str | None
    metadata: dict[str, Any]


@compat_dataclass(slots=True)
class DxfQuicklook:
    """Summary metadata extracted from a DXF payload."""

    candidates: list[DxfSpaceCandidate]
    floors: list[dict[str, Any]]
    units: list[str]
    layers: list[dict[str, Any]]
    metadata: dict[str, Any]


@compat_dataclass(slots=True)
class IfcSpaceCandidate:
    """Representation of an IFC space detected within a storey."""

    identifier: str
    name: str
    level_id: str | None
    metadata: dict[str, Any]


@compat_dataclass(slots=True)
class IfcQuicklook:
    """Summary metadata extracted from an IFC payload."""

    storeys: list[dict[str, Any]]
    spaces: list[IfcSpaceCandidate]
    floors: list[dict[str, Any]]
    units: list[str]
    layers: list[dict[str, Any]]


def _resolve_local_path(storage_path: str) -> Path:
    storage_service = get_storage_service()
    parsed = urlparse(storage_path)
    if parsed.scheme in {"", "file"}:
        # For local paths (no scheme or file://), return as-is
        path = Path(parsed.path if parsed.path else storage_path)
        # If path doesn't exist but starts with bucket name, try without it
        # (backwards compatibility for old URIs that included bucket in path)
        if not path.exists() and storage_service.bucket:
            # Try stripping the bucket prefix if present
            path_str = str(path)
            bucket_prefix = f"{storage_service.bucket}/"
            if path_str.startswith(bucket_prefix):
                path = Path(path_str[len(bucket_prefix) :])
        return path
    if parsed.scheme == "s3":
        # For s3://bucket/path, netloc is bucket, path is /path
        bucket = parsed.netloc
        key = parsed.path.lstrip("/")
        # Combine bucket and key for local path
        if bucket:
            return storage_service.local_base_path / bucket / key
        return storage_service.local_base_path / key
    # Fall back to treating the value as a relative path beneath the storage root
    return storage_service.local_base_path / storage_path


async def _load_payload(record: ImportRecord) -> bytes:
    path = _resolve_local_path(record.storage_path)
    payload = await asyncio.to_thread(path.read_bytes)
    if not isinstance(payload, bytes):
        raise TypeError(
            f"Expected bytes from {path}, got {type(payload).__name__}: {repr(payload)[:100]}"
        )
    return payload


def _load_vector_payload(storage_path: str) -> dict[str, Any]:
    path = _resolve_local_path(storage_path)
    payload = json.loads(path.read_text())
    if not isinstance(payload, Mapping):
        raise ValueError("Vector payload must be a mapping")
    return dict(payload)


def _normalise_name(value: Any, fallback: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return fallback


def _ensure_unique(identifier: str, seen: dict[str, None]) -> str:
    base = identifier
    counter = 1
    while identifier in seen:
        counter += 1
        identifier = f"{base}-{counter}"
    seen[identifier] = None
    return identifier


def _read_dxf_document(payload: bytes):
    if ezdxf is None:  # pragma: no cover - optional dependency
        raise RuntimeError("ezdxf is required to parse DXF payloads")
    if not isinstance(payload, bytes):
        raise TypeError(
            f"DXF payload must be bytes, got {type(payload).__name__}: {repr(payload)[:200]}"
        )

    # Write to temp file and use recover mode for robustness
    with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False, mode="wb") as handle:
        handle.write(payload)
        tmp_name = handle.name

    try:
        # Try recover mode first to handle malformed DXF files
        if hasattr(ezdxf, "recover") and hasattr(ezdxf.recover, "readfile"):
            try:
                result = ezdxf.recover.readfile(tmp_name)
                # recover.readfile returns (doc, auditor) tuple
                if isinstance(result, tuple):
                    return result[0]
                return result
            except Exception as e:
                # If recover fails, log and try normal read
                import sys

                print(
                    f"DXF recover failed: {e}, trying normal read",
                    file=sys.stderr,
                    flush=True,
                )

        # Fallback to normal read
        return ezdxf.readfile(tmp_name)
    finally:  # pragma: no cover - cleanup guard
        try:
            os.remove(tmp_name)
        except OSError:
            pass


def _extract_dxf_layer_metadata(
    doc,
) -> list[dict[str, Any]]:  # pragma: no cover - depends on ezdxf
    metadata: list[dict[str, Any]] = []
    layers = getattr(doc, "layers", None)
    if layers is None:
        return metadata
    if hasattr(layers, "names"):
        names = layers.names()
        getter = getattr(layers, "get", None)
        for name in names:
            if not name:
                continue
            entry: dict[str, Any] = {"name": str(name)}
            layer_obj = None
            if callable(getter):
                try:
                    layer_obj = getter(name)
                except Exception:  # pragma: no cover - defensive guard
                    layer_obj = None
            if layer_obj is not None:
                color = getattr(layer_obj.dxf, "color", None)
                if isinstance(color, int) and color != 0:
                    entry["color"] = color
                linetype = getattr(layer_obj.dxf, "linetype", None)
                if linetype:
                    entry["linetype"] = linetype
            metadata.append(entry)
    else:
        for layer in layers:
            dxf = getattr(layer, "dxf", layer)
            name = getattr(dxf, "name", None)
            if not name:
                continue
            entry = {"name": str(name)}
            color = getattr(dxf, "color", None)
            if isinstance(color, int) and color != 0:
                entry["color"] = color
            linetype = getattr(dxf, "linetype", None)
            if linetype:
                entry["linetype"] = linetype
            metadata.append(entry)
    return metadata


def _collect_dxf_space_candidates(
    doc,
) -> tuple[
    list[DxfSpaceCandidate], dict[str, list[str]]
]:  # pragma: no cover - depends on ezdxf
    candidates: list[DxfSpaceCandidate] = []
    layer_units: dict[str, list[str]] = {}
    modelspace = doc.modelspace()
    for index, entity in enumerate(modelspace, start=1):
        if entity.dxftype() != "LWPOLYLINE":
            continue
        points: list[dict[str, float]] = []
        try:
            raw_points = entity.get_points("xy")  # type: ignore[arg-type]
        except Exception:  # pragma: no cover - defensive guard
            raw_points = []
        for point in raw_points:
            try:
                x_val = float(point[0])
                y_val = float(point[1])
            except (TypeError, ValueError):  # pragma: no cover - defensive guard
                continue
            points.append({"x": x_val, "y": y_val})
        if not points:
            continue
        space_id = f"entity-{index:03d}"
        layer_name = str(getattr(entity.dxf, "layer", "") or "").strip() or None
        if layer_name:
            layer_units.setdefault(layer_name.lower(), []).append(space_id)
        candidates.append(
            DxfSpaceCandidate(
                identifier=space_id,
                boundary=points,
                layer=layer_name,
                metadata={},
            )
        )
    return candidates, layer_units


def _derive_dxf_floors(
    layer_metadata: Sequence[Mapping[str, Any]],
    unit_ids: Sequence[str],
    layer_units: Mapping[str, list[str]],
) -> list[dict[str, Any]]:
    floors: list[dict[str, Any]] = []
    seen_units: dict[str, None] = {}
    for entry in layer_metadata:
        name_raw = entry.get("name")
        if not isinstance(name_raw, str):
            continue
        layer_name = name_raw.strip()
        if not layer_name:
            continue
        lower = layer_name.lower()
        if not any(token in lower for token in ("level", "floor", "storey", "story")):
            continue
        units_for_layer = list(layer_units.get(lower, []))
        for unit_id in units_for_layer:
            if unit_id not in seen_units:
                seen_units[unit_id] = None
        floors.append({"name": layer_name, "unit_ids": units_for_layer})
    if not floors:
        floors.append({"name": "Model Space", "unit_ids": list(unit_ids)})
        return floors
    remaining = [unit for unit in unit_ids if unit not in seen_units]
    if remaining:
        floors.append({"name": "Unassigned", "unit_ids": remaining})
    return floors


def _polygon_area(points: Sequence[Mapping[str, float]]) -> float:
    """Return the area enclosed by ``points`` using the shoelace formula."""

    if len(points) < 3:
        return 0.0
    area = 0.0
    for index, point in enumerate(points):
        next_point = points[(index + 1) % len(points)]
        x1 = float(point.get("x", 0.0))
        y1 = float(point.get("y", 0.0))
        x2 = float(next_point.get("x", 0.0))
        y2 = float(next_point.get("y", 0.0))
        area += x1 * y2 - x2 * y1
    return abs(area) * 0.5


def _estimate_length_scale(candidates: Sequence[DxfSpaceCandidate]) -> float:
    """Estimate the conversion factor from DXF units to metres."""

    lengths: list[float] = []
    for candidate in candidates:
        boundary = candidate.boundary
        if len(boundary) < 2:
            continue
        for index, point in enumerate(boundary):
            next_point = boundary[(index + 1) % len(boundary)]
            dx = float(next_point.get("x", 0.0)) - float(point.get("x", 0.0))
            dy = float(next_point.get("y", 0.0)) - float(point.get("y", 0.0))
            length = math.hypot(dx, dy)
            if length > 0:
                lengths.append(length)
    if not lengths:
        return 1.0
    lengths.sort()
    median = lengths[len(lengths) // 2]
    # Assume millimetres when edges are significantly larger than 50 units.
    if median > 50:
        return 0.001
    return 1.0


def _compute_candidate_metrics(
    candidates: Sequence[DxfSpaceCandidate],
    scale_to_m: float,
) -> tuple[dict[str, float], dict[str, float]]:
    """Compute per-space areas and aggregated metrics."""

    space_areas: dict[str, float] = {}
    bounds: dict[str, float] = {}
    min_x = min_y = float("inf")
    max_x = max_y = float("-inf")

    for candidate in candidates:
        boundary = candidate.boundary
        for point in boundary:
            x_val = float(point.get("x", 0.0))
            y_val = float(point.get("y", 0.0))
            min_x = min(min_x, x_val)
            min_y = min(min_y, y_val)
            max_x = max(max_x, x_val)
            max_y = max(max_y, y_val)
        raw_area = _polygon_area(boundary)
        area_m2 = raw_area * (scale_to_m**2)
        if area_m2 > 0:
            space_areas[candidate.identifier] = area_m2
            candidate.metadata["area_sqm"] = area_m2
        else:
            candidate.metadata.pop("area_sqm", None)

    if min_x == float("inf") or min_y == float("inf"):
        bounds = {}
    else:
        bounds = {
            "min_x": min_x * scale_to_m,
            "min_y": min_y * scale_to_m,
            "max_x": max_x * scale_to_m,
            "max_y": max_y * scale_to_m,
        }
    return space_areas, bounds


def _prepare_dxf_quicklook(payload: bytes) -> DxfQuicklook:
    doc = _read_dxf_document(payload)
    layer_metadata = _extract_dxf_layer_metadata(doc)
    candidates, layer_units = _collect_dxf_space_candidates(doc)
    unit_ids = [candidate.identifier for candidate in candidates]
    floors = _derive_dxf_floors(layer_metadata, unit_ids, layer_units)
    metadata: dict[str, Any] = {
        "unit_count": len(unit_ids),
        "layer_count": len(layer_metadata),
    }
    scale_to_m = _estimate_length_scale(candidates)
    metadata["unit_scale_to_m"] = scale_to_m
    space_areas, bounds = _compute_candidate_metrics(candidates, scale_to_m)
    if space_areas:
        metadata["gross_floor_area_sqm"] = sum(space_areas.values())
    if bounds:
        metadata["site_bounds"] = bounds
        width = bounds["max_x"] - bounds["min_x"]
        height = bounds["max_y"] - bounds["min_y"]
        site_area = width * height
        if site_area > 0:
            metadata["site_area_sqm"] = site_area
    metadata["space_areas_sqm"] = space_areas
    return DxfQuicklook(
        candidates=candidates,
        floors=floors,
        units=unit_ids,
        layers=layer_metadata,
        metadata=metadata,
    )


def detect_dxf_metadata(
    payload: bytes,
) -> tuple[list[dict[str, Any]], list[str], list[dict[str, Any]]]:
    quicklook = _prepare_dxf_quicklook(payload)
    return quicklook.floors, quicklook.units, quicklook.layers


def _load_ifc_model(payload: bytes):
    if ifcopenshell is None:  # pragma: no cover - optional dependency
        raise RuntimeError("ifcopenshell is required to parse IFC payloads")
    text = payload.decode("utf-8", errors="ignore")
    return ifcopenshell.file.from_string(text)  # type: ignore[attr-defined]


def _extract_ifc_layer_metadata(
    model,
) -> list[dict[str, Any]]:  # pragma: no cover - depends on ifcopenshell
    metadata: list[dict[str, Any]] = []
    try:
        assignments = model.by_type("IfcPresentationLayerAssignment")
    except Exception:  # pragma: no cover - defensive guard
        assignments = []
    seen: dict[str, int] = {}
    for assignment in assignments:
        name = getattr(assignment, "Name", None) or getattr(
            assignment, "Description", None
        )
        base_name = str(name) if name else f"Layer-{assignment.id()}"
        candidate = base_name
        counter = 1
        while candidate in seen:
            counter += 1
            candidate = f"{base_name}-{counter}"
        seen[candidate] = counter
        assigned_items = getattr(assignment, "AssignedItems", []) or []
        metadata.append(
            {
                "name": candidate,
                "item_count": len(assigned_items),
                "type": (
                    assignment.is_a()
                    if hasattr(assignment, "is_a")
                    else "IfcPresentationLayerAssignment"
                ),
            }
        )
    return metadata


def _prepare_ifc_quicklook(payload: bytes) -> IfcQuicklook:
    model = _load_ifc_model(payload)
    storeys_payload: list[dict[str, Any]] = []
    spaces: list[IfcSpaceCandidate] = []
    floors_summary: list[dict[str, Any]] = []
    units: list[str] = []
    seen_units: dict[str, None] = {}

    for storey in model.by_type(
        "IfcBuildingStorey"
    ):  # pragma: no cover - depends on ifcopenshell
        level_id = _normalise_name(
            getattr(storey, "GlobalId", None), f"Level-{storey.id()}"
        )
        floor_name = _normalise_name(getattr(storey, "Name", None), level_id)
        elevation_raw = getattr(storey, "Elevation", 0.0)
        try:
            elevation = float(elevation_raw)
        except (TypeError, ValueError):  # pragma: no cover - defensive guard
            elevation = 0.0
        storeys_payload.append(
            {
                "id": level_id,
                "name": floor_name,
                "elevation": elevation,
                "metadata": (
                    {"ifc_type": storey.is_a()} if hasattr(storey, "is_a") else {}
                ),
            }
        )

        floor_units: list[str] = []
        related = getattr(storey, "ContainsElements", []) or []
        for rel in related:
            for element in getattr(rel, "RelatedElements", []) or []:
                if not hasattr(element, "is_a") or not element.is_a("IfcSpace"):
                    continue
                space_id = _normalise_name(
                    getattr(element, "GlobalId", None), f"Space-{element.id()}"
                )
                if space_id not in seen_units:
                    seen_units[space_id] = None
                    units.append(space_id)
                floor_units.append(space_id)
                spaces.append(
                    IfcSpaceCandidate(
                        identifier=space_id,
                        name=_normalise_name(getattr(element, "Name", None), space_id),
                        level_id=level_id,
                        metadata={"ifc_type": element.is_a()},
                    )
                )
        floors_summary.append({"name": floor_name, "unit_ids": floor_units})

    for element in model.by_type(
        "IfcSpace"
    ):  # pragma: no cover - depends on ifcopenshell
        if not hasattr(element, "is_a") or not element.is_a("IfcSpace"):
            continue
        space_id = _normalise_name(
            getattr(element, "GlobalId", None), f"Space-{element.id()}"
        )
        if space_id in seen_units:
            continue
        seen_units[space_id] = None
        units.append(space_id)
        spaces.append(
            IfcSpaceCandidate(
                identifier=space_id,
                name=_normalise_name(getattr(element, "Name", None), space_id),
                level_id=None,
                metadata={"ifc_type": element.is_a()},
            )
        )

    if not floors_summary and units:
        floors_summary.append({"name": "Default Storey", "unit_ids": list(units)})
    else:
        orphan_units = [space.identifier for space in spaces if space.level_id is None]
        if orphan_units:
            floors_summary.append({"name": "Unassigned", "unit_ids": orphan_units})

    layer_metadata = _extract_ifc_layer_metadata(model)
    return IfcQuicklook(
        storeys=storeys_payload,
        spaces=spaces,
        floors=floors_summary,
        units=units,
        layers=layer_metadata,
    )


def detect_ifc_metadata(
    payload: bytes,
) -> tuple[list[dict[str, Any]], list[str], list[dict[str, Any]]]:
    quicklook = _prepare_ifc_quicklook(payload)
    return quicklook.floors, quicklook.units, quicklook.layers


def _estimate_space_geometry(
    offset_x: float, offset_y: float, area: float | None
) -> list[dict[str, float]]:
    side = max(math.sqrt(area) if area and area > 0 else 4.0, 3.0)
    width = side
    height = max(area / width if area else side, 3.0)
    return [
        {"x": offset_x, "y": offset_y},
        {"x": offset_x + width, "y": offset_y},
        {"x": offset_x + width, "y": offset_y + height},
        {"x": offset_x, "y": offset_y + height},
    ]


def _derive_vector_layers(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    layer_counts: Counter[str] = Counter()
    paths = payload.get("paths")
    if isinstance(paths, Sequence):
        for entry in paths:  # type: ignore[assignment]
            if not isinstance(entry, Mapping):
                continue
            layer_name = entry.get("layer")
            if layer_name in (None, ""):
                continue
            layer_counts[str(layer_name)] += 1
    return [
        {"name": name, "path_count": count, "source": "vector_paths"}
        for name, count in sorted(layer_counts.items())
    ]


def _build_graph_from_floorplan(data: Mapping[str, Any]) -> ParsedGeometry:
    builder = GraphBuilder.new()
    floors_summary: list[dict[str, Any]] = []
    unit_ids: list[str] = []
    seen_units: dict[str, None] = {}

    site_metadata: dict[str, Any] = {}
    project_name = data.get("project")
    if project_name not in (None, ""):
        site_metadata["project"] = project_name

    raw_layers = data.get("layers") if isinstance(data.get("layers"), Sequence) else []
    layer_metadata: list[dict[str, Any]] = []
    floor_layers: list[Mapping[str, Any]] = []
    for item in raw_layers:  # type: ignore[assignment]
        if not isinstance(item, Mapping):
            continue
        layer_payload = dict(item)
        layer_metadata.append(layer_payload)
        layer_type = str(item.get("type", "")).lower()
        if layer_type in {"site", "reference", "context"}:
            layer_metadata = item.get("metadata")
            if isinstance(layer_metadata, Mapping):
                for key, value in layer_metadata.items():
                    site_metadata[key] = value
        if layer_type in {"floor", "level", "storey", "story"}:
            floor_layers.append(item)

    entries: list[Mapping[str, Any]] = list(floor_layers)
    extra_floors = (
        data.get("floors") if isinstance(data.get("floors"), Sequence) else []
    )
    for item in extra_floors:  # type: ignore[assignment]
        if isinstance(item, Mapping):
            entries.append(item)

    offset_y = 0.0
    for index, entry in enumerate(entries, start=1):
        floor_name = _normalise_name(entry.get("name"), f"Floor {index}")
        level_id = _normalise_name(entry.get("id") or floor_name, f"L{index:02d}")
        level_metadata = dict(site_metadata)
        entry_metadata = entry.get("metadata")
        if isinstance(entry_metadata, Mapping):
            level_metadata.update(entry_metadata)
        level_metadata.setdefault("layer_type", str(entry.get("type", "")))

        level_payload = {
            "id": level_id,
            "name": floor_name,
            "elevation": float(
                entry.get("metadata", {}).get("elevation", (index - 1) * 3.5)
            ),
            "metadata": level_metadata,
        }
        builder.add_level(level_payload)

        floor_units: Iterable[Any] = (
            entry.get("units", []) if isinstance(entry.get("units"), Iterable) else []
        )
        floor_summary_units: list[str] = []
        offset_x = 0.0
        for raw_unit in floor_units:
            if isinstance(raw_unit, Mapping):
                unit_identifier = (
                    raw_unit.get("id") or raw_unit.get("name") or raw_unit.get("label")
                )
                area_value = raw_unit.get("area_m2") or raw_unit.get("area")
            else:
                unit_identifier = raw_unit
                area_value = None
            unit_id = _ensure_unique(
                _normalise_name(
                    unit_identifier, f"{level_id}-unit-{len(unit_ids) + 1}"
                ),
                seen_units,
            )
            unit_ids.append(unit_id)
            floor_summary_units.append(unit_id)

            try:
                area_float = float(area_value) if area_value is not None else None
            except (TypeError, ValueError):
                area_float = None

            boundary = _estimate_space_geometry(offset_x, offset_y, area_float)
            space_metadata: dict[str, Any] = {"source_floor": floor_name}
            if isinstance(raw_unit, Mapping):
                for key, value in raw_unit.items():
                    if key in {"id", "name", "label"}:
                        continue
                    if key in {"area", "area_m2"}:
                        continue
                    space_metadata[key] = value
            if area_float is not None:
                space_metadata.setdefault("area_sqm", area_float)

            space_payload = {
                "id": unit_id,
                "name": unit_id,
                "level_id": level_id,
                "boundary": boundary,
                "metadata": space_metadata,
            }
            builder.add_space(space_payload)
            builder.add_relationship(
                {
                    "type": "contains",
                    "source_id": level_id,
                    "target_id": unit_id,
                    "attributes": {"relationship": "unit"},
                }
            )
            offset_x += max(boundary[1]["x"] - boundary[0]["x"], 3.0) + 1.5

        floors_summary.append({"name": floor_name, "unit_ids": floor_summary_units})
        offset_y += 6.5

    builder.validate_integrity()
    return ParsedGeometry(
        graph=builder.graph,
        floors=floors_summary,
        units=unit_ids,
        layers=layer_metadata,
        metadata={
            "source": "json_floorplan",
            "floors": len(floors_summary),
            "layers": len(layer_metadata),
        },
    )


def _parse_json_payload(data: Mapping[str, Any]) -> ParsedGeometry:
    if "layers" in data or "floors" in data:
        return _build_graph_from_floorplan(data)
    builder = GraphBuilder.new()
    builder.build_from_payload(data)
    builder.validate_integrity()
    graph = builder.graph
    return ParsedGeometry(
        graph=graph,
        floors=[
            {"name": level.name or level.id, "unit_ids": []}
            for level in graph.levels.values()
        ],
        units=list(graph.spaces.keys()),
        layers=[],
        metadata={"source": "json_geometry", "floors": len(graph.levels)},
    )


def _coerce_vector_point(value: Any) -> dict[str, float] | None:
    """Convert vector payload points into mapping form."""

    if isinstance(value, Mapping):
        x = value.get("x")
        y = value.get("y")
        if isinstance(x, (int, float)) and isinstance(y, (int, float)):
            return {"x": float(x), "y": float(y)}
        return None
    if isinstance(value, Sequence) and not isinstance(value, (bytes, str)):
        values = list(value)
        if len(values) != 2:
            return None
        try:
            return {"x": float(values[0]), "y": float(values[1])}
        except (TypeError, ValueError):
            return None
    return None


def _is_closed_path(points: Sequence[dict[str, float]]) -> bool:
    if len(points) < 4:
        return False
    first = points[0]
    last = points[-1]
    return bool(
        math.isfinite(first["x"])
        and math.isfinite(first["y"])
        and math.isfinite(last["x"])
        and math.isfinite(last["y"])
        and math.isclose(first["x"], last["x"], rel_tol=1e-6, abs_tol=1e-6)
        and math.isclose(first["y"], last["y"], rel_tol=1e-6, abs_tol=1e-6)
    )


def _parse_vector_payload(payload: Mapping[str, Any]) -> ParsedGeometry:
    builder = GraphBuilder.new()
    level_id = "VectorLevel"
    level_name = "Vector Floor"

    level_metadata: dict[str, Any] = {"source": payload.get("source", "vector")}
    bounds = payload.get("bounds")
    if isinstance(bounds, Mapping):
        level_metadata["bounds"] = {
            key: float(value)
            for key, value in bounds.items()
            if isinstance(value, (int, float))
        }

    builder.add_level(
        {
            "id": level_id,
            "name": level_name,
            "elevation": 0.0,
            "metadata": level_metadata,
        }
    )

    wall_ids: list[str] = []
    seen_walls: dict[str, None] = {}
    walls = payload.get("walls")
    if isinstance(walls, Sequence):
        for index, entry in enumerate(walls, start=1):  # type: ignore[assignment]
            if not isinstance(entry, Mapping):
                continue
            start = _coerce_vector_point(entry.get("start"))
            end = _coerce_vector_point(entry.get("end"))
            if start is None or end is None:
                continue
            raw_identifier = entry.get("id") or entry.get("name")
            wall_id = _ensure_unique(
                _normalise_name(raw_identifier, f"W{index:03d}"),
                seen_walls,
            )
            metadata: dict[str, Any] = {}
            for key in ("thickness", "confidence"):
                value = entry.get(key)
                if isinstance(value, (int, float)):
                    metadata[key] = float(value)
            for key in ("source", "layer"):
                value = entry.get(key)
                if value not in (None, ""):
                    metadata[key] = value
            extra_metadata = entry.get("metadata")
            if isinstance(extra_metadata, Mapping):
                metadata.update({key: value for key, value in extra_metadata.items()})
            try:
                builder.add_wall(
                    {
                        "id": wall_id,
                        "level_id": level_id,
                        "start": start,
                        "end": end,
                        "metadata": metadata,
                    }
                )
            except (TypeError, ValueError):
                continue
            wall_ids.append(wall_id)

    space_ids: list[str] = []
    seen_spaces: dict[str, None] = {}
    paths = payload.get("paths")
    if isinstance(paths, Sequence):
        for index, entry in enumerate(paths, start=1):  # type: ignore[assignment]
            if not isinstance(entry, Mapping):
                continue
            points_raw = entry.get("points")
            if not isinstance(points_raw, Sequence):
                continue
            boundary: list[dict[str, float]] = []
            for point in points_raw:  # type: ignore[assignment]
                coerced = _coerce_vector_point(point)
                if coerced is None:
                    boundary = []
                    break
                boundary.append(coerced)
            if not boundary or not _is_closed_path(boundary):
                continue

            raw_identifier = entry.get("id") or entry.get("name") or entry.get("layer")
            space_id = _ensure_unique(
                _normalise_name(raw_identifier, f"S{index:03d}"),
                seen_spaces,
            )
            metadata: dict[str, Any] = {"source": "vector_path"}
            extra_metadata = entry.get("metadata")
            if isinstance(extra_metadata, Mapping):
                metadata.update({key: value for key, value in extra_metadata.items()})
            layer_name = entry.get("layer")
            if layer_name not in (None, ""):
                metadata["layer"] = layer_name
            stroke_width = entry.get("stroke_width")
            if isinstance(stroke_width, (int, float)):
                metadata["stroke_width"] = float(stroke_width)
            metadata["path_index"] = index - 1

            try:
                builder.add_space(
                    {
                        "id": space_id,
                        "level_id": level_id,
                        "boundary": boundary,
                        "metadata": metadata,
                    }
                )
            except (TypeError, ValueError):
                continue
            space_ids.append(space_id)

    builder.validate_integrity()

    layer_metadata = _derive_vector_layers(payload)

    floors_summary = [{"name": level_name, "unit_ids": list(space_ids)}]

    metadata: dict[str, Any] = {
        "source": "vector_payload",
        "walls": len(wall_ids),
        "spaces": len(space_ids),
        "paths": len(paths) if isinstance(paths, Sequence) else 0,
        "layers": len(layer_metadata),
    }
    if isinstance(bounds, Mapping):
        metadata["bounds"] = level_metadata.get("bounds")
    options = payload.get("options")
    if isinstance(options, Mapping):
        metadata["vector_options"] = dict(options)

    return ParsedGeometry(
        graph=builder.graph,
        floors=floors_summary,
        units=list(space_ids),
        layers=layer_metadata,
        metadata=metadata,
    )


def _parse_dxf_payload(payload: bytes) -> ParsedGeometry:
    quicklook = _prepare_dxf_quicklook(payload)
    builder = GraphBuilder.new()
    builder.add_level({"id": "L1", "name": "Model Space", "elevation": 0.0})
    raw_space_areas = quicklook.metadata.get("space_areas_sqm") or {}
    space_areas = dict(raw_space_areas) if isinstance(raw_space_areas, Mapping) else {}
    unit_scale = float(quicklook.metadata.get("unit_scale_to_m") or 1.0)
    for candidate in quicklook.candidates:  # pragma: no cover - depends on ezdxf
        area_sqm = space_areas.get(candidate.identifier)
        space_metadata = dict(candidate.metadata)
        space_metadata.update(
            {
                "source_entity": "LWPOLYLINE",
                "unit_scale_to_m": unit_scale,
            }
        )
        if candidate.layer:
            space_metadata.setdefault("source_layer", candidate.layer)
        if area_sqm is not None:
            space_metadata["area_sqm"] = area_sqm
        builder.add_space(
            {
                "id": candidate.identifier,
                "level_id": "L1",
                "boundary": candidate.boundary,
                "metadata": space_metadata,
            }
        )
    builder.validate_integrity()
    parse_metadata: dict[str, Any] = {
        "site_area_sqm": quicklook.metadata.get("site_area_sqm"),
        "gross_floor_area_sqm": quicklook.metadata.get("gross_floor_area_sqm"),
        "unit_scale_to_m": unit_scale,
    }
    return ParsedGeometry(
        graph=builder.graph,
        floors=quicklook.floors,
        units=quicklook.units,
        layers=quicklook.layers,
        metadata={
            "source": "dxf",
            "entities": len(quicklook.units),
            "layers": len(quicklook.layers),
            "site_area_sqm": quicklook.metadata.get("site_area_sqm"),
            "gross_floor_area_sqm": quicklook.metadata.get("gross_floor_area_sqm"),
            "site_bounds": quicklook.metadata.get("site_bounds"),
            "unit_scale_to_m": unit_scale,
            "parse_metadata": {
                key: value for key, value in parse_metadata.items() if value is not None
            },
        },
    )


def _parse_ifc_payload(payload: bytes) -> ParsedGeometry:
    quicklook = _prepare_ifc_quicklook(payload)
    builder = GraphBuilder.new()
    added_levels: dict[str, None] = {}

    for storey in quicklook.storeys:  # pragma: no cover - depends on ifcopenshell
        level_id = storey["id"]
        if level_id in added_levels:
            continue
        level_payload = {
            "id": level_id,
            "name": storey.get("name", level_id),
            "elevation": float(storey.get("elevation", 0.0)),
            "metadata": dict(storey.get("metadata", {})),
        }
        builder.add_level(level_payload)
        added_levels[level_id] = None

    default_level_id: str | None = None
    if not added_levels and quicklook.units:
        default_level_id = "DefaultStorey"
        builder.add_level(
            {"id": default_level_id, "name": "Default Storey", "elevation": 0.0}
        )
        added_levels[default_level_id] = None

    if any(space.level_id is None for space in quicklook.spaces):
        default_level_id = default_level_id or "Unassigned"
        if default_level_id not in added_levels:
            builder.add_level(
                {"id": default_level_id, "name": "Unassigned", "elevation": 0.0}
            )
            added_levels[default_level_id] = None

    for candidate in quicklook.spaces:  # pragma: no cover - depends on ifcopenshell
        level_id = candidate.level_id or default_level_id
        if level_id is None:
            continue
        if level_id not in added_levels:
            builder.add_level({"id": level_id, "name": level_id, "elevation": 0.0})
            added_levels[level_id] = None
        builder.add_space(
            {
                "id": candidate.identifier,
                "name": candidate.name,
                "level_id": level_id,
                "boundary": [],
                "metadata": dict(candidate.metadata),
            }
        )

    builder.validate_integrity()
    return ParsedGeometry(
        graph=builder.graph,
        floors=quicklook.floors,
        units=quicklook.units,
        layers=quicklook.layers,
        metadata={
            "source": "ifc",
            "floors": len(quicklook.floors),
            "layers": len(quicklook.layers),
        },
    )


def _parse_payload(
    record: ImportRecord,
    payload: bytes,
    vector_payload: Mapping[str, Any] | None = None,
) -> ParsedGeometry:
    filename = (record.filename or "").lower()
    content_type = (record.content_type or "").lower()
    if filename.endswith(".json") or content_type == "application/json":
        data = json.loads(payload.decode("utf-8"))
        return _parse_json_payload(data)
    if filename.endswith(".dxf") or "dxf" in content_type:
        return _parse_dxf_payload(payload)
    if filename.endswith(".ifc") or "ifc" in content_type:
        return _parse_ifc_payload(payload)
    is_pdf = filename.endswith(".pdf") or "pdf" in content_type
    is_svg = filename.endswith(".svg") or "svg" in content_type
    if vector_payload is not None and (is_pdf or is_svg):
        return _parse_vector_payload(vector_payload)
    raise RuntimeError(f"Unsupported import format for '{record.filename}'")


async def _persist_result(
    session, record: ImportRecord, parsed: ParsedGeometry
) -> dict[str, Any]:
    graph_payload = GeometrySerializer.to_export(parsed.graph)
    record.parse_status = "completed"
    record.parse_result = {
        "floors": len(parsed.floors),
        "units": len(parsed.units),
        "detected_floors": parsed.floors,
        "detected_units": parsed.units,
        "layer_metadata": parsed.layers,
        "graph": graph_payload,
        "metadata": parsed.metadata,
    }
    if parsed.layers:
        record.layer_metadata = parsed.layers
    if parsed.floors:
        record.detected_floors = parsed.floors
    if parsed.units:
        record.detected_units = parsed.units
    record.parse_error = None
    record.parse_completed_at = datetime.now(UTC)
    await session.flush()
    result = record.parse_result or {}
    return dict(result)


@job(name="jobs.parse_cad.parse_import", queue="imports:parse")
async def parse_import_job(import_id: str) -> dict[str, Any]:
    """Parse an uploaded import payload and persist the resulting geometry."""

    session_factory = app_database.AsyncSessionLocal
    async with session_factory() as session:
        record = await session.get(ImportRecord, import_id)
        if record is None:
            raise RuntimeError(f"Import '{import_id}' not found")
        record.parse_status = "running"
        await session.commit()

        try:
            payload = await _load_payload(record)
            vector_payload: dict[str, Any] | None = None
            if record.vector_storage_path:
                try:
                    vector_payload = await asyncio.to_thread(
                        _load_vector_payload,
                        record.vector_storage_path,
                    )
                except FileNotFoundError:
                    vector_payload = None
            parsed = await asyncio.to_thread(
                _parse_payload,
                record,
                payload,
                vector_payload,
            )
            result = await _persist_result(session, record, parsed)
            if getattr(record, "project_id", None) is not None:
                overlay_record = await ingest_parsed_import_geometry(
                    session,
                    project_id=int(record.project_id),
                    import_record=record,
                    parse_payload=result,
                )
                if isinstance(result, dict):
                    enriched = dict(result)
                    metadata_section = dict(enriched.get("metadata") or {})
                    metadata_section.update(
                        {
                            "overlay_source_id": overlay_record.id,
                            "overlay_checksum": overlay_record.checksum,
                            "source_geometry_key": overlay_record.source_geometry_key,
                        }
                    )
                    enriched["metadata"] = metadata_section
                    record.parse_result = enriched
                    result = enriched
            await session.commit()
            await session.refresh(record)
            return result
        except Exception as exc:  # pragma: no cover - defensive logging surface
            record.parse_status = "failed"
            record.parse_error = str(exc)
            record.parse_completed_at = datetime.now(UTC)
            await session.commit()
            raise


__all__ = [
    "parse_import_job",
    "ParsedGeometry",
    "detect_dxf_metadata",
    "detect_ifc_metadata",
]
