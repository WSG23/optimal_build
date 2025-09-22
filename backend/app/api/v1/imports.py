"""Endpoints for CAD/BIM import and parse workflows."""

from __future__ import annotations

import asyncio
import json
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Tuple
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit.ledger import append_event
from app.core.database import get_session
from app.models.imports import ImportRecord
from app.schemas.imports import DetectedFloor, ImportResult, ParseStatusResponse
from app.services.storage import get_storage_service
from app.utils.logging import get_logger
from jobs import job_queue
from jobs.parse_cad import detect_dxf_metadata, detect_ifc_metadata, parse_import_job
from jobs.raster_vector import vectorize_floorplan

router = APIRouter()
logger = get_logger(__name__)


def _extract_unit_id(unit: Any) -> str | None:
    """Return a unit identifier from diverse payload representations."""

    if isinstance(unit, dict):
        for key in ("id", "name", "label", "unit", "number", "ref"):
            value = unit.get(key)
            if value:
                return str(value)
    elif isinstance(unit, (str, int, float)):
        return str(unit)
    return None


def _normalise_floor(
    *,
    name: str,
    unit_ids: Iterable[str] | None = None,
    seen_units: Dict[str, None],
) -> Dict[str, Any]:
    """Create a floor summary while tracking unique units."""

    collected: List[str] = []
    if unit_ids:
        for unit in unit_ids:
            if unit not in seen_units:
                seen_units[unit] = None
            collected.append(unit)
    return {"name": name, "unit_ids": collected}


def _detect_json_payload(payload: Mapping[str, Any]) -> Tuple[List[Dict[str, Any]], List[str], List[Dict[str, Any]]]:
    """Inspect a JSON payload and extract quick-look floor and unit metadata."""

    floors: List[Dict[str, Any]] = []
    seen_units: Dict[str, None] = {}
    layer_metadata: List[Dict[str, Any]] = []

    raw_layers = payload.get("layers")
    if isinstance(raw_layers, list):
        for layer in raw_layers:
            if not isinstance(layer, dict):
                continue
            layer_metadata.append(dict(layer))
            layer_type = str(layer.get("type", "")).lower()
            if layer_type not in {"floor", "level", "storey", "story"}:
                continue
            floor_name = str(
                layer.get("name")
                or layer.get("label")
                or layer.get("id")
                or "Floor"
            )
            unit_ids = []
            for unit in layer.get("units", []):
                unit_id = _extract_unit_id(unit)
                if unit_id is None:
                    continue
                if unit_id not in seen_units:
                    seen_units[unit_id] = None
                unit_ids.append(unit_id)
            floors.append({"name": floor_name, "unit_ids": unit_ids})

    raw_floors = payload.get("floors")
    if isinstance(raw_floors, list):
        for entry in raw_floors:
            if isinstance(entry, dict):
                name = str(entry.get("name") or entry.get("label") or entry.get("id") or "Floor")
                units = []
                for unit in entry.get("units", []):
                    unit_id = _extract_unit_id(unit)
                    if unit_id is None:
                        continue
                    if unit_id not in seen_units:
                        seen_units[unit_id] = None
                    units.append(unit_id)
                floors.append({"name": name, "unit_ids": units})
            else:
                floors.append(_normalise_floor(name=str(entry), seen_units=seen_units))

    raw_units = payload.get("units")
    if isinstance(raw_units, list):
        for unit in raw_units:
            unit_id = _extract_unit_id(unit)
            if unit_id is None or unit_id in seen_units:
                continue
            seen_units[unit_id] = None

    ordered_units = list(seen_units.keys())
    return floors, ordered_units, layer_metadata


def _detect_import_metadata(
    filename: str | None,
    content_type: str | None,
    payload: bytes,
) -> Tuple[List[Dict[str, Any]], List[str], List[Dict[str, Any]]]:
    """Determine floors, units and layer metadata for diverse import payloads."""

    name = (filename or "").lower()
    media_type = (content_type or "").lower()

    if name.endswith(".json") or "json" in media_type:
        try:
            decoded = payload.decode("utf-8")
        except UnicodeDecodeError:
            return [], [], []
        try:
            json_payload = json.loads(decoded)
        except json.JSONDecodeError:
            return [], [], []
        if isinstance(json_payload, Mapping):
            return _detect_json_payload(json_payload)
        return [], [], []

    if name.endswith(".dxf") or "dxf" in media_type:
        try:
            return detect_dxf_metadata(payload)
        except Exception:  # pragma: no cover - optional dependency guard
            return [], [], []

    if name.endswith(".ifc") or "ifc" in media_type:
        try:
            return detect_ifc_metadata(payload)
        except Exception:  # pragma: no cover - optional dependency guard
            return [], [], []

    return [], [], []


def _is_vectorizable(filename: str | None, content_type: str | None) -> bool:
    """Return ``True`` if a file is eligible for raster vector processing."""

    name = (filename or "").lower()
    media_type = (content_type or "").lower()
    if name.endswith(".pdf") or "pdf" in media_type:
        return True
    if name.endswith(".svg") or "svg" in media_type:
        return True
    return False


def _summarise_vector_payload(
    payload: Mapping[str, Any],
    *,
    infer_walls: bool,
    requested: bool,
) -> Dict[str, Any]:
    """Generate a compact summary describing extracted vector geometry."""

    options_raw = payload.get("options")
    bitmap_flag = False
    infer_flag = infer_walls
    if isinstance(options_raw, Mapping):
        bitmap_flag = bool(options_raw.get("bitmap_walls"))
        infer_flag = bool(options_raw.get("infer_walls", infer_walls))
    return {
        "paths": len(payload.get("paths") or []),
        "walls": len(payload.get("walls") or []),
        "source": payload.get("source"),
        "bounds": payload.get("bounds"),
        "options": {
            "requested": requested,
            "infer_walls": infer_flag,
            "bitmap_walls": bitmap_flag,
        },
    }


def _derive_vector_layers(payload: Mapping[str, Any]) -> List[Dict[str, Any]]:
    """Derive layer metadata from vectorized PDF payloads."""

    layer_counts: Counter[str] = Counter()
    paths = payload.get("paths")
    if isinstance(paths, list):
        for entry in paths:
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


def _normalise_units(units: object) -> List[str]:
    """Return a list of unit identifiers from diverse representations."""

    collected: List[str] = []
    if isinstance(units, Mapping):
        iterable = list(units.values())
    elif isinstance(units, (list, tuple, set)):
        iterable = list(units)
    elif units in (None, ""):
        iterable = []
    else:
        iterable = [units]
    for entry in iterable:
        unit_id = _extract_unit_id(entry)
        if unit_id is None:
            continue
        collected.append(unit_id)
    return collected


def _coerce_mapping_payload(value: object) -> Mapping[str, Any] | None:
    """Best-effort conversion of model instances into dictionaries."""

    if isinstance(value, Mapping):
        return value
    for attr in ("model_dump", "dict"):
        if hasattr(value, attr):
            method = getattr(value, attr)
            try:
                result = method()
            except TypeError:
                result = method(mode="python") if attr == "model_dump" else method()
            except Exception:  # pragma: no cover - defensive
                return None
            if isinstance(result, Mapping):
                return result
    return None


def _build_parse_summary(record: ImportRecord) -> Dict[str, Any]:
    """Aggregate import detection metadata for downstream consumers."""

    parse_metadata = _coerce_mapping_payload(record.parse_result) or {}

    floors_raw = record.detected_floors or parse_metadata.get("detected_floors") or []
    floor_breakdown: List[Dict[str, Any]] = []
    seen_units: Dict[str, None] = {}

    for index, entry in enumerate(floors_raw, start=1):
        data = _coerce_mapping_payload(entry)
        if data is None:
            name = str(entry) if entry not in (None, "") else f"Floor {index}"
            unit_ids: List[str] = []
        else:
            name = str(
                data.get("name")
                or data.get("label")
                or data.get("id")
                or f"Floor {index}"
            )
            raw_units = data.get("unit_ids") or data.get("units")
            unit_ids = _normalise_units(raw_units)
        for unit_id in unit_ids:
            if unit_id not in seen_units:
                seen_units[unit_id] = None
        floor_breakdown.append(
            {
                "name": name,
                "unit_count": len(unit_ids),
                "unit_ids": unit_ids,
            }
        )

    units_raw = record.detected_units or parse_metadata.get("detected_units") or []
    if isinstance(units_raw, list):
        iterable_units = units_raw
    else:
        iterable_units = [units_raw]
    for unit in iterable_units:
        unit_id = _extract_unit_id(unit)
        if unit_id and unit_id not in seen_units:
            seen_units[unit_id] = None

    summary: Dict[str, Any] = {
        "floors": len(floor_breakdown),
        "units": len(seen_units),
        "floor_breakdown": floor_breakdown,
    }
    layer_metadata = record.layer_metadata or parse_metadata.get("layer_metadata") or []
    if layer_metadata:
        if isinstance(layer_metadata, list):
            layer_count = len(layer_metadata)
        else:
            layer_count = 1
        summary["layers"] = layer_count
    if record.parse_status:
        summary["status"] = record.parse_status
    return summary


@router.post("/import", response_model=ImportResult, status_code=status.HTTP_201_CREATED)
async def upload_import(
    file: UploadFile = File(...),
    enable_raster_processing: bool = Form(True),
    infer_walls: bool = Form(False),
    project_id: int | None = Form(default=None),
    session: AsyncSession = Depends(get_session),
) -> ImportResult:
    """Persist an uploaded CAD/BIM payload and return detection metadata."""

    raw_payload = await file.read()
    if not raw_payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty upload payload")

    filename = file.filename or "upload.bin"
    content_type = file.content_type

    detected_floors, detected_units, layer_metadata = await asyncio.to_thread(
        _detect_import_metadata,
        filename,
        content_type,
        raw_payload,
    )

    import_id = str(uuid4())

    record = ImportRecord(
        id=import_id,
        filename=filename,
        content_type=content_type,
        size_bytes=len(raw_payload),
        layer_metadata=[],
        detected_floors=detected_floors,
        detected_units=detected_units,
    )

    vector_payload: Dict[str, Any] | None = None
    vector_summary: Dict[str, Any] | None = None
    if enable_raster_processing and _is_vectorizable(filename, content_type):
        try:
            dispatch = await job_queue.enqueue(
                vectorize_floorplan,
                payload=raw_payload,
                content_type=content_type or "",
                filename=filename,
                infer_walls=infer_walls,
            )
            if dispatch.result and isinstance(dispatch.result, Mapping):
                vector_payload = dict(dispatch.result)
            elif dispatch.status != "completed":
                inline_result = await vectorize_floorplan(
                    raw_payload,
                    content_type=content_type or "",
                    filename=filename,
                    infer_walls=infer_walls,
                )
                if isinstance(inline_result, Mapping):
                    vector_payload = dict(inline_result)
        except Exception as exc:  # pragma: no cover - defensive logging surface
            logger.warning(
                "vectorization_failed",
                import_id=import_id,
                filename=record.filename,
                error=str(exc),
            )

        if vector_payload is not None:
            vector_summary = _summarise_vector_payload(
                vector_payload,
                infer_walls=infer_walls,
                requested=True,
            )
            if not layer_metadata:
                derived_layers = _derive_vector_layers(vector_payload)
                if derived_layers:
                    layer_metadata = derived_layers

    stored_layer_metadata = layer_metadata or detected_floors
    record.layer_metadata = stored_layer_metadata

    storage_service = get_storage_service()
    storage_result = await storage_service.store_import_file(
        import_id=import_id,
        filename=record.filename,
        payload=raw_payload,
        layer_metadata=stored_layer_metadata,
        vector_payload=vector_payload,
    )
    record.storage_path = storage_result.uri
    record.vector_storage_path = storage_result.vector_data_uri
    if vector_summary is not None:
        record.vector_summary = vector_summary

    session.add(record)

    if project_id is not None:
        await append_event(
            session,
            project_id=project_id,
            event_type="import_uploaded",
            context={
                "import_id": record.id,
                "filename": record.filename,
                "size_bytes": record.size_bytes,
                "detected_floors": len(record.detected_floors or []),
                "detected_units": len(record.detected_units or []),
                "vectorized": vector_summary is not None,
            },
        )

    await session.commit()
    await session.refresh(record)

    return ImportResult(
        import_id=record.id,
        filename=record.filename,
        content_type=record.content_type,
        size_bytes=record.size_bytes,
        storage_path=record.storage_path,
        vector_storage_path=record.vector_storage_path,
        uploaded_at=record.uploaded_at,
        layer_metadata=record.layer_metadata or [],
        detected_floors=[DetectedFloor(**floor) for floor in record.detected_floors or []],
        detected_units=record.detected_units or [],
        vector_summary=record.vector_summary or vector_summary,
        parse_status=record.parse_status,
    )


@router.post("/parse/{import_id}", response_model=ParseStatusResponse)
async def enqueue_parse(
    import_id: str,
    session: AsyncSession = Depends(get_session),
) -> ParseStatusResponse:
    """Trigger parsing of an uploaded model."""

    record = await session.get(ImportRecord, import_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import not found")

    record.parse_requested_at = datetime.now(timezone.utc)
    record.parse_status = "queued"
    await session.commit()

    dispatch = await job_queue.enqueue(parse_import_job, import_id=import_id)

    # Refresh to reflect changes applied by the job if it ran inline.
    await session.refresh(record)

    response = ParseStatusResponse(
        import_id=record.id,
        status=record.parse_status,
        requested_at=record.parse_requested_at,
        completed_at=record.parse_completed_at,
        result=record.parse_result,
        error=record.parse_error,
        job_id=dispatch.task_id,
    )
    if dispatch.result and isinstance(dispatch.result, dict):
        response.result = dispatch.result
        response.status = "completed"
    return response


@router.get("/parse/{import_id}", response_model=ParseStatusResponse)
async def get_parse_status(
    import_id: str,
    session: AsyncSession = Depends(get_session),
) -> ParseStatusResponse:
    """Retrieve the status of a parse job."""

    record = await session.get(ImportRecord, import_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import not found")

    return ParseStatusResponse(
        import_id=record.id,
        status=record.parse_status,
        requested_at=record.parse_requested_at,
        completed_at=record.parse_completed_at,
        result=record.parse_result,
        error=record.parse_error,
        job_id=None,
    )


__all__ = ["router"]
