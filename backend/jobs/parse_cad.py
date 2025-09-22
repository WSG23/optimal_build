"""CAD and BIM parsing jobs."""

from __future__ import annotations

import asyncio
import json
import math
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple
from urllib.parse import urlparse

try:  # pragma: no cover - optional dependency
    import ezdxf  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - available in production environments
    ezdxf = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    import ifcopenshell  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - available in production environments
    ifcopenshell = None  # type: ignore[assignment]

from app.core.database import AsyncSessionLocal
from app.core.geometry import GeometrySerializer, GraphBuilder
from app.core.models.geometry import GeometryGraph
from app.models.imports import ImportRecord
from app.services.overlay_ingest import ingest_parsed_import_geometry
from app.services.storage import get_storage_service
from jobs import job


@dataclass(slots=True)
class ParsedGeometry:
    """Result emitted by the parsing pipeline."""

    graph: GeometryGraph
    floors: List[Dict[str, Any]]
    units: List[str]
    layers: List[Dict[str, Any]]
    metadata: Dict[str, Any]


@dataclass(slots=True)
class DxfSpaceCandidate:
    """Representation of a DXF entity that can be treated as a space."""

    identifier: str
    boundary: List[Dict[str, float]]
    layer: Optional[str]


@dataclass(slots=True)
class DxfQuicklook:
    """Summary metadata extracted from a DXF payload."""

    candidates: List[DxfSpaceCandidate]
    floors: List[Dict[str, Any]]
    units: List[str]
    layers: List[Dict[str, Any]]


@dataclass(slots=True)
class IfcSpaceCandidate:
    """Representation of an IFC space detected within a storey."""

    identifier: str
    name: str
    level_id: Optional[str]
    metadata: Dict[str, Any]


@dataclass(slots=True)
class IfcQuicklook:
    """Summary metadata extracted from an IFC payload."""

    storeys: List[Dict[str, Any]]
    spaces: List[IfcSpaceCandidate]
    floors: List[Dict[str, Any]]
    units: List[str]
    layers: List[Dict[str, Any]]


def _resolve_local_path(storage_path: str) -> Path:
    storage_service = get_storage_service()
    parsed = urlparse(storage_path)
    if parsed.scheme in {"", "file"}:
        path = Path(parsed.path)
        return path if path.is_absolute() else storage_service.local_base_path / path
    if parsed.scheme == "s3":
        key = parsed.path.lstrip("/")
        return storage_service.local_base_path / key
    # Fall back to treating the value as a relative path beneath the storage root
    return storage_service.local_base_path / storage_path


async def _load_payload(record: ImportRecord) -> bytes:
    path = _resolve_local_path(record.storage_path)
    return await asyncio.to_thread(path.read_bytes)


def _normalise_name(value: Any, fallback: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return fallback


def _ensure_unique(identifier: str, seen: Dict[str, None]) -> str:
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
    stream = BytesIO(payload)
    if hasattr(ezdxf, "read"):
        try:
            stream.seek(0)
            return ezdxf.read(stream=stream)
        except TypeError:
            stream.seek(0)
            return ezdxf.read(stream)
    stream.seek(0)
    with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as handle:
        handle.write(payload)
        tmp_name = handle.name
    try:
        return ezdxf.readfile(tmp_name)
    finally:  # pragma: no cover - cleanup guard
        try:
            os.remove(tmp_name)
        except OSError:
            pass


def _extract_dxf_layer_metadata(doc) -> List[Dict[str, Any]]:  # pragma: no cover - depends on ezdxf
    metadata: List[Dict[str, Any]] = []
    layers = getattr(doc, "layers", None)
    if layers is None:
        return metadata
    if hasattr(layers, "names"):
        names = layers.names()
        getter = getattr(layers, "get", None)
        for name in names:
            if not name:
                continue
            entry: Dict[str, Any] = {"name": str(name)}
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


def _collect_dxf_space_candidates(doc) -> Tuple[List[DxfSpaceCandidate], Dict[str, List[str]]]:  # pragma: no cover - depends on ezdxf
    candidates: List[DxfSpaceCandidate] = []
    layer_units: Dict[str, List[str]] = {}
    modelspace = doc.modelspace()
    for index, entity in enumerate(modelspace, start=1):
        if entity.dxftype() != "LWPOLYLINE":
            continue
        points: List[Dict[str, float]] = []
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
        candidates.append(DxfSpaceCandidate(identifier=space_id, boundary=points, layer=layer_name))
    return candidates, layer_units


def _derive_dxf_floors(
    layer_metadata: Sequence[Mapping[str, Any]],
    unit_ids: Sequence[str],
    layer_units: Mapping[str, List[str]],
) -> List[Dict[str, Any]]:
    floors: List[Dict[str, Any]] = []
    seen_units: Dict[str, None] = {}
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


def _prepare_dxf_quicklook(payload: bytes) -> DxfQuicklook:
    doc = _read_dxf_document(payload)
    layer_metadata = _extract_dxf_layer_metadata(doc)
    candidates, layer_units = _collect_dxf_space_candidates(doc)
    unit_ids = [candidate.identifier for candidate in candidates]
    floors = _derive_dxf_floors(layer_metadata, unit_ids, layer_units)
    return DxfQuicklook(candidates=candidates, floors=floors, units=unit_ids, layers=layer_metadata)


def detect_dxf_metadata(payload: bytes) -> Tuple[List[Dict[str, Any]], List[str], List[Dict[str, Any]]]:
    quicklook = _prepare_dxf_quicklook(payload)
    return quicklook.floors, quicklook.units, quicklook.layers


def _load_ifc_model(payload: bytes):
    if ifcopenshell is None:  # pragma: no cover - optional dependency
        raise RuntimeError("ifcopenshell is required to parse IFC payloads")
    text = payload.decode("utf-8", errors="ignore")
    return ifcopenshell.file.from_string(text)  # type: ignore[attr-defined]


def _extract_ifc_layer_metadata(model) -> List[Dict[str, Any]]:  # pragma: no cover - depends on ifcopenshell
    metadata: List[Dict[str, Any]] = []
    try:
        assignments = model.by_type("IfcPresentationLayerAssignment")
    except Exception:  # pragma: no cover - defensive guard
        assignments = []
    seen: Dict[str, int] = {}
    for assignment in assignments:
        name = getattr(assignment, "Name", None) or getattr(assignment, "Description", None)
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
                "type": assignment.is_a() if hasattr(assignment, "is_a") else "IfcPresentationLayerAssignment",
            }
        )
    return metadata


def _prepare_ifc_quicklook(payload: bytes) -> IfcQuicklook:
    model = _load_ifc_model(payload)
    storeys_payload: List[Dict[str, Any]] = []
    spaces: List[IfcSpaceCandidate] = []
    floors_summary: List[Dict[str, Any]] = []
    units: List[str] = []
    seen_units: Dict[str, None] = {}

    for storey in model.by_type("IfcBuildingStorey"):  # pragma: no cover - depends on ifcopenshell
        level_id = _normalise_name(getattr(storey, "GlobalId", None), f"Level-{storey.id()}")
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
                "metadata": {"ifc_type": storey.is_a()} if hasattr(storey, "is_a") else {},
            }
        )

        floor_units: List[str] = []
        related = getattr(storey, "ContainsElements", []) or []
        for rel in related:
            for element in getattr(rel, "RelatedElements", []) or []:
                if not hasattr(element, "is_a") or not element.is_a("IfcSpace"):
                    continue
                space_id = _normalise_name(getattr(element, "GlobalId", None), f"Space-{element.id()}")
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

    for element in model.by_type("IfcSpace"):  # pragma: no cover - depends on ifcopenshell
        if not hasattr(element, "is_a") or not element.is_a("IfcSpace"):
            continue
        space_id = _normalise_name(getattr(element, "GlobalId", None), f"Space-{element.id()}")
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


def detect_ifc_metadata(payload: bytes) -> Tuple[List[Dict[str, Any]], List[str], List[Dict[str, Any]]]:
    quicklook = _prepare_ifc_quicklook(payload)
    return quicklook.floors, quicklook.units, quicklook.layers


def _estimate_space_geometry(offset_x: float, offset_y: float, area: Optional[float]) -> List[Dict[str, float]]:
    side = max(math.sqrt(area) if area and area > 0 else 4.0, 3.0)
    width = side
    height = max(area / width if area else side, 3.0)
    return [
        {"x": offset_x, "y": offset_y},
        {"x": offset_x + width, "y": offset_y},
        {"x": offset_x + width, "y": offset_y + height},
        {"x": offset_x, "y": offset_y + height},
    ]


def _build_graph_from_floorplan(data: Mapping[str, Any]) -> ParsedGeometry:
    builder = GraphBuilder.new()
    floors_summary: List[Dict[str, Any]] = []
    unit_ids: List[str] = []
    seen_units: Dict[str, None] = {}

    site_metadata: Dict[str, Any] = {}
    project_name = data.get("project")
    if project_name not in (None, ""):
        site_metadata["project"] = project_name

    raw_layers = data.get("layers") if isinstance(data.get("layers"), Sequence) else []
    layer_metadata: List[Dict[str, Any]] = []
    floor_layers: List[Mapping[str, Any]] = []
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

    entries: List[Mapping[str, Any]] = list(floor_layers)
    extra_floors = data.get("floors") if isinstance(data.get("floors"), Sequence) else []
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
            "elevation": float(entry.get("metadata", {}).get("elevation", (index - 1) * 3.5)),
            "metadata": level_metadata,
        }
        builder.add_level(level_payload)

        floor_units: Iterable[Any] = entry.get("units", []) if isinstance(entry.get("units"), Iterable) else []
        floor_summary_units: List[str] = []
        offset_x = 0.0
        for raw_unit in floor_units:
            if isinstance(raw_unit, Mapping):
                unit_identifier = raw_unit.get("id") or raw_unit.get("name") or raw_unit.get("label")
                area_value = raw_unit.get("area_m2") or raw_unit.get("area")
            else:
                unit_identifier = raw_unit
                area_value = None
            unit_id = _ensure_unique(_normalise_name(unit_identifier, f"{level_id}-unit-{len(unit_ids) + 1}"), seen_units)
            unit_ids.append(unit_id)
            floor_summary_units.append(unit_id)

            try:
                area_float = float(area_value) if area_value is not None else None
            except (TypeError, ValueError):
                area_float = None

            boundary = _estimate_space_geometry(offset_x, offset_y, area_float)
            space_metadata: Dict[str, Any] = {"source_floor": floor_name}
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
        floors=[{"name": level.name or level.id, "unit_ids": []} for level in graph.levels.values()],
        units=list(graph.spaces.keys()),
        layers=[],
        metadata={"source": "json_geometry", "floors": len(graph.levels)},
    )


def _parse_dxf_payload(payload: bytes) -> ParsedGeometry:
    quicklook = _prepare_dxf_quicklook(payload)
    builder = GraphBuilder.new()
    builder.add_level({"id": "L1", "name": "Model Space", "elevation": 0.0})
    for candidate in quicklook.candidates:  # pragma: no cover - depends on ezdxf
        builder.add_space(
            {
                "id": candidate.identifier,
                "level_id": "L1",
                "boundary": candidate.boundary,
                "metadata": {
                    "source_entity": "LWPOLYLINE",
                    "source_layer": candidate.layer,
                },
            }
        )
    builder.validate_integrity()
    return ParsedGeometry(
        graph=builder.graph,
        floors=quicklook.floors,
        units=quicklook.units,
        layers=quicklook.layers,
        metadata={
            "source": "dxf",
            "entities": len(quicklook.units),
            "layers": len(quicklook.layers),
        },
    )


def _parse_ifc_payload(payload: bytes) -> ParsedGeometry:
    quicklook = _prepare_ifc_quicklook(payload)
    builder = GraphBuilder.new()
    added_levels: Dict[str, None] = {}

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

    default_level_id: Optional[str] = None
    if not added_levels and quicklook.units:
        default_level_id = "DefaultStorey"
        builder.add_level({"id": default_level_id, "name": "Default Storey", "elevation": 0.0})
        added_levels[default_level_id] = None

    if any(space.level_id is None for space in quicklook.spaces):
        default_level_id = default_level_id or "Unassigned"
        if default_level_id not in added_levels:
            builder.add_level({"id": default_level_id, "name": "Unassigned", "elevation": 0.0})
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


def _parse_payload(record: ImportRecord, payload: bytes) -> ParsedGeometry:
    filename = (record.filename or "").lower()
    content_type = (record.content_type or "").lower()
    if filename.endswith(".json") or content_type == "application/json":
        data = json.loads(payload.decode("utf-8"))
        return _parse_json_payload(data)
    if filename.endswith(".dxf") or "dxf" in content_type:
        return _parse_dxf_payload(payload)
    if filename.endswith(".ifc") or "ifc" in content_type:
        return _parse_ifc_payload(payload)
    raise RuntimeError(f"Unsupported import format for '{record.filename}'")


async def _persist_result(session, record: ImportRecord, parsed: ParsedGeometry) -> Dict[str, Any]:
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
    record.parse_completed_at = datetime.now(timezone.utc)
    await session.flush()
    result = record.parse_result or {}
    return dict(result)


@job(name="jobs.parse_cad.parse_import", queue="imports:parse")
async def parse_import_job(import_id: str) -> Dict[str, Any]:
    """Parse an uploaded import payload and persist the resulting geometry."""

    async with AsyncSessionLocal() as session:
        record = await session.get(ImportRecord, import_id)
        if record is None:
            raise RuntimeError(f"Import '{import_id}' not found")
        record.parse_status = "running"
        await session.commit()

        try:
            payload = await _load_payload(record)
            parsed = await asyncio.to_thread(_parse_payload, record, payload)
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
            record.parse_completed_at = datetime.now(timezone.utc)
            await session.commit()
            raise


__all__ = [
    "parse_import_job",
    "ParsedGeometry",
    "detect_dxf_metadata",
    "detect_ifc_metadata",
]
