"""CAD and BIM parsing jobs."""

from __future__ import annotations

import asyncio
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence
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
from app.services.storage import get_storage_service
from jobs import job


@dataclass(slots=True)
class ParsedGeometry:
    """Result emitted by the parsing pipeline."""

    graph: GeometryGraph
    floors: List[Dict[str, Any]]
    units: List[str]
    metadata: Dict[str, Any]


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

    raw_layers = data.get("layers") if isinstance(data.get("layers"), Sequence) else []
    floor_layers: List[Mapping[str, Any]] = []
    for item in raw_layers:  # type: ignore[assignment]
        if not isinstance(item, Mapping):
            continue
        layer_type = str(item.get("type", "")).lower()
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
        level_payload = {
            "id": level_id,
            "name": floor_name,
            "elevation": float(entry.get("metadata", {}).get("elevation", (index - 1) * 3.5)),
            "metadata": dict(entry.get("metadata", {})),
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
            space_payload = {
                "id": unit_id,
                "name": unit_id,
                "level_id": level_id,
                "boundary": boundary,
                "metadata": {
                    "source_floor": floor_name,
                    "area_sqm": area_float,
                },
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
        metadata={"source": "json_floorplan", "floors": len(floors_summary)},
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
        metadata={"source": "json_geometry", "floors": len(graph.levels)},
    )


def _parse_dxf_payload(payload: bytes) -> ParsedGeometry:
    if ezdxf is None:  # pragma: no cover - optional dependency
        raise RuntimeError("ezdxf is required to parse DXF payloads")
    doc = ezdxf.read(stream=payload) if hasattr(ezdxf, "read") else ezdxf.readfile(payload)  # type: ignore[arg-type]
    modelspace = doc.modelspace()
    builder = GraphBuilder.new()
    builder.add_level({"id": "L1", "name": "Model Space", "elevation": 0.0})
    unit_ids: List[str] = []
    floors = [{"name": "Model Space", "unit_ids": unit_ids}]
    for index, entity in enumerate(modelspace, start=1):  # pragma: no cover - depends on ezdxf
        if entity.dxftype() != "LWPOLYLINE":
            continue
        points = [
            {"x": float(point[0]), "y": float(point[1])}
            for point in entity.get_points("xy")  # type: ignore[arg-type]
        ]
        space_id = f"entity-{index:03d}"
        unit_ids.append(space_id)
        builder.add_space({
            "id": space_id,
            "level_id": "L1",
            "boundary": points,
            "metadata": {"source_entity": entity.dxftype()},
        })
    builder.validate_integrity()
    return ParsedGeometry(
        graph=builder.graph,
        floors=floors,
        units=unit_ids,
        metadata={"source": "dxf", "entities": len(unit_ids)},
    )


def _parse_ifc_payload(payload: bytes) -> ParsedGeometry:
    if ifcopenshell is None:  # pragma: no cover - optional dependency
        raise RuntimeError("ifcopenshell is required to parse IFC payloads")
    model = ifcopenshell.file.from_string(payload.decode("utf-8"))  # type: ignore[attr-defined]
    builder = GraphBuilder.new()
    unit_ids: List[str] = []
    floors_summary: List[Dict[str, Any]] = []
    for storey in model.by_type("IfcBuildingStorey"):  # pragma: no cover - depends on ifcopenshell
        level_id = _normalise_name(storey.GlobalId, f"Level-{storey.id()}")
        builder.add_level(
            {
                "id": level_id,
                "name": getattr(storey, "Name", level_id),
                "elevation": float(getattr(storey, "Elevation", 0.0)),
            }
        )
        floor_units: List[str] = []
        related = getattr(storey, "ContainsElements", [])
        for rel in related:
            for element in getattr(rel, "RelatedElements", []):
                if element.is_a("IfcSpace"):
                    space_id = _normalise_name(element.GlobalId, f"Space-{element.id()}")
                    unit_ids.append(space_id)
                    floor_units.append(space_id)
                    builder.add_space(
                        {
                            "id": space_id,
                            "name": getattr(element, "Name", space_id),
                            "level_id": level_id,
                            "boundary": [],
                            "metadata": {"ifc_type": element.is_a()},
                        }
                    )
        floors_summary.append({"name": getattr(storey, "Name", level_id), "unit_ids": floor_units})
    builder.validate_integrity()
    return ParsedGeometry(
        graph=builder.graph,
        floors=floors_summary,
        units=unit_ids,
        metadata={"source": "ifc", "floors": len(floors_summary)},
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
        "graph": graph_payload,
        "metadata": parsed.metadata,
    }
    record.parse_error = None
    record.parse_completed_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(record)
    return record.parse_result or {}


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
            return await _persist_result(session, record, parsed)
        except Exception as exc:  # pragma: no cover - defensive logging surface
            record.parse_status = "failed"
            record.parse_error = str(exc)
            record.parse_completed_at = datetime.now(timezone.utc)
            await session.commit()
            raise


__all__ = ["parse_import_job", "ParsedGeometry"]
