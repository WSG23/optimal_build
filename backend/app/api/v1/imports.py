"""Endpoints for CAD/BIM import and parse workflows."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.imports import ImportRecord
from app.schemas.imports import DetectedFloor, ImportResult, ParseStatusResponse
from jobs import job_queue
from jobs.parse_cad import parse_import_job
from app.services.storage import get_storage_service

router = APIRouter()


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


def _analyse_payload(data: bytes) -> tuple[List[Dict[str, Any]], List[str], List[Dict[str, Any]]]:
    """Parse the uploaded payload to determine floors, units and layer metadata."""

    try:
        decoded = data.decode("utf-8")
    except UnicodeDecodeError:
        return [], [], []

    try:
        payload = json.loads(decoded)
    except json.JSONDecodeError:
        return [], [], []

    floors: List[Dict[str, Any]] = []
    seen_units: Dict[str, None] = {}
    layer_metadata: List[Dict[str, Any]] = []

    raw_layers = payload.get("layers")
    if isinstance(raw_layers, list):
        for layer in raw_layers:
            if not isinstance(layer, dict):
                continue
            layer_metadata.append(layer)
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


@router.post("/import", response_model=ImportResult, status_code=status.HTTP_201_CREATED)
async def upload_import(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
) -> ImportResult:
    """Persist an uploaded CAD/BIM payload and return detection metadata."""

    raw_payload = await file.read()
    if not raw_payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty upload payload")

    detected_floors, detected_units, layer_metadata = _analyse_payload(raw_payload)
    stored_layer_metadata = layer_metadata or detected_floors

    import_id = str(uuid4())

    record = ImportRecord(
        id=import_id,
        filename=file.filename or "upload.bin",
        content_type=file.content_type,
        size_bytes=len(raw_payload),
        layer_metadata=stored_layer_metadata,
        detected_floors=detected_floors,
        detected_units=detected_units,
    )

    storage_service = get_storage_service()
    storage_result = await storage_service.store_import_file(
        import_id=import_id,
        filename=record.filename,
        payload=raw_payload,
        layer_metadata=stored_layer_metadata,
    )
    record.storage_path = storage_result.uri

    session.add(record)
    await session.commit()
    await session.refresh(record)

    return ImportResult(
        import_id=record.id,
        filename=record.filename,
        content_type=record.content_type,
        size_bytes=record.size_bytes,
        storage_path=record.storage_path,
        uploaded_at=record.uploaded_at,
        layer_metadata=record.layer_metadata or [],
        detected_floors=[DetectedFloor(**floor) for floor in record.detected_floors or []],
        detected_units=record.detected_units or [],
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
