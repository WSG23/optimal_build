"""Endpoints for CAD/BIM import and parse workflows."""

from __future__ import annotations

import asyncio
import json
from collections import Counter
from collections.abc import Iterable, Mapping
from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Header,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_reviewer, require_viewer
from app.core.audit.ledger import append_event
from app.core.database import get_session
from app.models.imports import ImportRecord
from app.schemas.imports import DetectedFloor, ImportResult, ParseStatusResponse
from app.services.storage import get_storage_service
from app.utils.logging import get_logger
from backend._compat.datetime import UTC
from backend.jobs import job_queue
from backend.jobs.parse_cad import (
    detect_dxf_metadata,
    detect_ifc_metadata,
    parse_import_job,
)
from backend.jobs.raster_vector import vectorize_floorplan
from pydantic import BaseModel, Field


class MetricOverridePayload(BaseModel):
    site_area_sqm: float | None = Field(default=None, gt=0)
    gross_floor_area_sqm: float | None = Field(default=None, gt=0)
    max_height_m: float | None = Field(default=None, gt=0)
    front_setback_m: float | None = Field(default=None, gt=0)

    def normalized(self) -> dict[str, float]:
        values = self.model_dump(exclude_none=True)
        return {key: float(value) for key, value in values.items()}


router = APIRouter()
logger = get_logger(__name__)

SUPPORTED_IMPORT_SUFFIXES: tuple[str, ...] = (".dxf", ".ifc", ".json")
SUPPORTED_IMPORT_MEDIA_HINTS: tuple[str, ...] = ("dxf", "ifc", "json")


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
    seen_units: dict[str, None],
) -> dict[str, Any]:
    """Create a floor summary while tracking unique units."""

    collected: list[str] = []
    if unit_ids:
        for unit in unit_ids:
            if unit not in seen_units:
                seen_units[unit] = None
            collected.append(unit)
    return {"name": name, "unit_ids": collected}


def _collect_layer_floors(
    raw_layers: Iterable[object], seen_units: dict[str, None]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return floor summaries and layer metadata for standard layer payloads."""

    floors: list[dict[str, Any]] = []
    metadata: list[dict[str, Any]] = []
    for layer in raw_layers:
        if not isinstance(layer, dict):
            continue
        metadata.append(dict(layer))
        layer_type = str(layer.get("type", "")).lower()
        if layer_type not in {"floor", "level", "storey", "story"}:
            continue
        floor_name = str(
            layer.get("name") or layer.get("label") or layer.get("id") or "Floor"
        )
        unit_ids: list[str] = []
        for unit in layer.get("units", []):
            unit_id = _extract_unit_id(unit)
            if unit_id is None:
                continue
            if unit_id not in seen_units:
                seen_units[unit_id] = None
            unit_ids.append(unit_id)
        floors.append({"name": floor_name, "unit_ids": unit_ids})
    return floors, metadata


def _collect_declared_floors(
    raw_floors: Iterable[object], seen_units: dict[str, None]
) -> list[dict[str, Any]]:
    """Normalise free-form floor entries into predictable summaries."""

    floors: list[dict[str, Any]] = []
    for entry in raw_floors:
        if isinstance(entry, dict):
            name = str(
                entry.get("name") or entry.get("label") or entry.get("id") or "Floor"
            )
            units: list[str] = []
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
    return floors


def _register_unit_ids(
    raw_units: Iterable[object], seen_units: dict[str, None]
) -> None:
    """Track standalone units so they appear in the ordered summary."""

    for unit in raw_units:
        unit_id = _extract_unit_id(unit)
        if unit_id is None or unit_id in seen_units:
            continue
        seen_units[unit_id] = None


def _detect_json_payload(
    payload: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[str], list[dict[str, Any]]]:
    """Inspect a JSON payload and extract quick-look floor and unit metadata."""

    seen_units: dict[str, None] = {}
    layer_metadata: list[dict[str, Any]] = []
    floors: list[dict[str, Any]] = []

    raw_layers = payload.get("layers")
    if isinstance(raw_layers, list):
        layer_floors, metadata = _collect_layer_floors(raw_layers, seen_units)
        floors.extend(layer_floors)
        layer_metadata.extend(metadata)

    raw_floors = payload.get("floors")
    if isinstance(raw_floors, list):
        floors.extend(_collect_declared_floors(raw_floors, seen_units))

    raw_units = payload.get("units")
    if isinstance(raw_units, list):
        _register_unit_ids(raw_units, seen_units)

    ordered_units = list(seen_units.keys())
    return floors, ordered_units, layer_metadata


def _detect_import_metadata(
    filename: str | None,
    content_type: str | None,
    payload: bytes,
) -> tuple[list[dict[str, Any]], list[str], list[dict[str, Any]]]:
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


def _is_supported_import(filename: str | None, content_type: str | None) -> bool:
    """Return ``True`` when the upload is a natively supported CAD/BIM payload."""

    name = (filename or "").lower()
    if any(name.endswith(suffix) for suffix in SUPPORTED_IMPORT_SUFFIXES):
        return True

    media_type = (content_type or "").lower()
    return any(hint in media_type for hint in SUPPORTED_IMPORT_MEDIA_HINTS)


def _is_vectorizable(filename: str | None, content_type: str | None) -> bool:
    """Return ``True`` if a file is eligible for raster vector processing."""

    name = (filename or "").lower()
    media_type = (content_type or "").lower()
    if name.endswith(".pdf") or "pdf" in media_type:
        return True
    if name.endswith(".svg") or "svg" in media_type:
        return True
    if name.endswith((".jpg", ".jpeg")) or "jpeg" in media_type:
        return True
    if name.endswith(".png") or "png" in media_type:
        return True
    return False


def _summarise_vector_payload(
    payload: Mapping[str, Any],
    *,
    infer_walls: bool,
    requested: bool,
) -> dict[str, Any]:
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


def _derive_vector_layers(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
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


def _normalise_units(units: object) -> list[str]:
    """Return a list of unit identifiers from diverse representations."""

    collected: list[str] = []
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


def _normalise_floor_entry(
    index: int, entry: object, seen_units: dict[str, None]
) -> dict[str, Any]:
    """Return floor metadata, updating ``seen_units`` while normalising payloads."""

    data = _coerce_mapping_payload(entry)
    if data is None:
        name = str(entry) if entry not in (None, "") else f"Floor {index}"
        unit_ids: list[str] = []
    else:
        name = str(
            data.get("name") or data.get("label") or data.get("id") or f"Floor {index}"
        )
        raw_units = data.get("unit_ids") or data.get("units")
        unit_ids = _normalise_units(raw_units)
    for unit_id in unit_ids:
        if unit_id not in seen_units:
            seen_units[unit_id] = None
    return {"name": name, "unit_count": len(unit_ids), "unit_ids": unit_ids}


def _integrate_detected_units(
    units_payload: object, seen_units: dict[str, None]
) -> None:
    """Merge standalone unit identifiers into ``seen_units``."""

    if isinstance(units_payload, list):
        iterable = units_payload
    elif units_payload in (None, ""):
        iterable = []
    else:
        iterable = [units_payload]
    for unit in iterable:
        unit_id = _extract_unit_id(unit)
        if unit_id and unit_id not in seen_units:
            seen_units[unit_id] = None


def _layer_count_from_metadata(layer_metadata: object) -> int | None:
    """Return an integer count when layer metadata is present."""

    if not layer_metadata:
        return None
    if isinstance(layer_metadata, list):
        return len(layer_metadata)
    return 1


def _normalise_zone_code(value: str | None) -> str | None:
    """Normalise zone codes to the ``PREFIX:suffix`` canonical format."""

    if value is None:
        return None
    zone = value.strip()
    if not zone:
        return None
    if ":" in zone:
        prefix, suffix = zone.split(":", 1)
        prefix = prefix.strip().upper() or "SG"
        suffix = suffix.strip().lower()
    else:
        prefix = "SG"
        suffix = zone.lower()
    return f"{prefix}:{suffix}"


def _coerce_positive(value: float | None) -> float | None:
    if value is None:
        return None
    try:
        candidate = float(value)
    except (TypeError, ValueError):
        return None
    return candidate if candidate > 0 else None


def _import_result_from_record(record: ImportRecord) -> ImportResult:
    floors_raw = record.detected_floors or []
    floors = [
        DetectedFloor(
            name=str(floor.get("name", f"Floor {index}")),
            unit_ids=list(floor.get("unit_ids") or []),
        )
        for index, floor in enumerate(floors_raw, start=1)
        if isinstance(floor, Mapping)
    ]

    return ImportResult(
        import_id=record.id,
        filename=record.filename,
        content_type=record.content_type,
        size_bytes=record.size_bytes,
        storage_path=record.storage_path,
        vector_storage_path=record.vector_storage_path,
        uploaded_at=record.uploaded_at,
        layer_metadata=list(record.layer_metadata or []),
        detected_floors=floors,
        detected_units=list(record.detected_units or []),
        vector_summary=record.vector_summary,
        zone_code=getattr(record, "zone_code", None),
        metric_overrides=getattr(record, "metric_overrides", None),
        parse_status=record.parse_status,
    )


def _build_parse_summary(record: ImportRecord) -> dict[str, Any]:
    """Aggregate import detection metadata for downstream consumers."""

    parse_metadata = _coerce_mapping_payload(record.parse_result) or {}

    floors_raw = record.detected_floors or parse_metadata.get("detected_floors") or []
    floor_breakdown: list[dict[str, Any]] = []
    seen_units: dict[str, None] = {}

    for index, entry in enumerate(floors_raw, start=1):
        floor_breakdown.append(_normalise_floor_entry(index, entry, seen_units))

    units_raw = record.detected_units or parse_metadata.get("detected_units") or []
    _integrate_detected_units(units_raw, seen_units)

    summary: dict[str, Any] = {
        "floors": len(floor_breakdown),
        "units": len(seen_units),
        "floor_breakdown": floor_breakdown,
    }
    layer_metadata = record.layer_metadata or parse_metadata.get("layer_metadata") or []
    layer_count = _layer_count_from_metadata(layer_metadata)
    if layer_count:
        summary["layers"] = layer_count
    if record.parse_status:
        summary["status"] = record.parse_status
    return summary


async def _vectorize_payload_if_requested(
    *,
    enable_raster_processing: bool,
    raw_payload: bytes,
    filename: str,
    content_type: str | None,
    infer_walls: bool,
    import_id: str,
    layer_metadata: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, list[dict[str, Any]] | None,]:
    """Return vectorization artefacts when requested and successful."""

    if not enable_raster_processing or not _is_vectorizable(filename, content_type):
        return None, None, None

    vector_payload: dict[str, Any] | None = None
    safe_content_type = content_type or ""

    try:
        dispatch = await job_queue.enqueue(
            vectorize_floorplan,
            payload=raw_payload,
            content_type=safe_content_type,
            filename=filename,
            infer_walls=infer_walls,
        )
        if dispatch.result and isinstance(dispatch.result, Mapping):
            vector_payload = dict(dispatch.result)
        elif dispatch.status != "completed":
            inline_result = await vectorize_floorplan(
                raw_payload,
                content_type=safe_content_type,
                filename=filename,
                infer_walls=infer_walls,
            )
            if isinstance(inline_result, Mapping):
                vector_payload = dict(inline_result)
    except Exception as exc:  # pragma: no cover - defensive logging surface
        logger.warning(
            "vectorization_failed",
            import_id=import_id,
            filename=filename,
            error=str(exc),
        )

    if vector_payload is None:
        return None, None, None

    vector_summary = _summarise_vector_payload(
        vector_payload,
        infer_walls=infer_walls,
        requested=True,
    )
    derived_layers: list[dict[str, Any]] | None = None
    if not layer_metadata:
        derived_layers = _derive_vector_layers(vector_payload)
    return vector_payload, vector_summary, derived_layers


@router.post(
    "/import", response_model=ImportResult, status_code=status.HTTP_201_CREATED
)
async def upload_import(
    file: UploadFile = File(...),
    enable_raster_processing: bool = Form(True),
    infer_walls: bool = Form(False),
    project_id: int | None = Form(default=None),
    zone_code: str | None = Form(default=None),
    site_area_sqm: float | None = Form(default=None),
    gross_floor_area_sqm: float | None = Form(default=None),
    max_height_m: float | None = Form(default=None),
    front_setback_m: float | None = Form(default=None),
    zone_header: str | None = Header(default=None, alias="X-Zone-Code"),
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_reviewer),
) -> ImportResult:
    """Persist an uploaded CAD/BIM payload and return detection metadata."""

    raw_payload = await file.read()
    if not raw_payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Empty upload payload"
        )

    filename = file.filename or "upload.bin"
    content_type = file.content_type

    if not (
        _is_supported_import(filename, content_type)
        or _is_vectorizable(filename, content_type)
    ):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file type. Upload DXF, IFC, or JSON exports, or supply a PDF/SVG/JPEG for vectorisation.",
        )

    detected_floors, detected_units, layer_metadata = await asyncio.to_thread(
        _detect_import_metadata,
        filename,
        content_type,
        raw_payload,
    )

    import_id = str(uuid4())
    selected_zone = zone_code or zone_header
    normalised_zone = _normalise_zone_code(selected_zone)

    overrides: dict[str, float] = {}
    for key, value in {
        "site_area_sqm": site_area_sqm,
        "gross_floor_area_sqm": gross_floor_area_sqm,
        "max_height_m": max_height_m,
        "front_setback_m": front_setback_m,
    }.items():
        coerced = _coerce_positive(value)
        if coerced is not None:
            overrides[key] = coerced

    record = ImportRecord(
        id=import_id,
        project_id=project_id,
        zone_code=normalised_zone,
        metric_overrides=overrides or None,
        filename=file.filename or "upload.bin",
        content_type=file.content_type,
        size_bytes=len(raw_payload),
        layer_metadata=[],
        detected_floors=detected_floors,
        detected_units=detected_units,
    )

    (
        vector_payload,
        vector_summary,
        derived_layers,
    ) = await _vectorize_payload_if_requested(
        enable_raster_processing=enable_raster_processing,
        raw_payload=raw_payload,
        filename=filename,
        content_type=content_type,
        infer_walls=infer_walls,
        import_id=import_id,
        layer_metadata=layer_metadata,
    )
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
                "zone_code": normalised_zone,
                "metric_overrides": overrides or None,
            },
        )

    await session.commit()
    await session.refresh(record)

    return _import_result_from_record(record)


@router.get("/import/latest", response_model=ImportResult)
async def get_latest_import(
    project_id: int = Query(..., gt=0),
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_viewer),
) -> ImportResult:
    stmt = (
        select(ImportRecord)
        .where(ImportRecord.project_id == project_id)
        .order_by(ImportRecord.uploaded_at.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    record = result.scalars().first()
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Import not found"
        )
    return _import_result_from_record(record)


@router.post("/import/{import_id}/overrides", response_model=ImportResult)
async def update_import_overrides(
    import_id: str,
    payload: MetricOverridePayload,
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_reviewer),
) -> ImportResult:
    record = await session.get(ImportRecord, import_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Import not found"
        )

    overrides = dict(record.metric_overrides or {})
    overrides.update(payload.normalized())
    overrides = {key: value for key, value in overrides.items() if value is not None}
    record.metric_overrides = overrides or None

    if record.parse_result and isinstance(record.parse_result, dict):
        metadata = dict(record.parse_result.get("metadata") or {})
        parse_meta = dict(metadata.get("parse_metadata") or {})
        if overrides:
            parse_meta["overrides"] = dict(overrides)
            metadata["metric_overrides"] = dict(overrides)
        else:
            parse_meta.pop("overrides", None)
            metadata.pop("metric_overrides", None)
        metadata["parse_metadata"] = parse_meta
        record.parse_result["metadata"] = metadata

    if record.project_id is not None:
        await append_event(
            session,
            project_id=record.project_id,
            event_type="import_override",
            context={
                "import_id": record.id,
                "metric_overrides": overrides or {},
            },
        )

    await session.commit()
    await session.refresh(record)
    return _import_result_from_record(record)


@router.post("/parse/{import_id}", response_model=ParseStatusResponse)
async def enqueue_parse(
    import_id: str,
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_reviewer),
) -> ParseStatusResponse:
    """Trigger parsing of an uploaded model."""

    record = await session.get(ImportRecord, import_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Import not found"
        )

    record.parse_requested_at = datetime.now(UTC)
    record.parse_status = "queued"
    await session.commit()

    try:
        dispatch = await job_queue.enqueue(parse_import_job, import_id=import_id)
    except Exception as exc:  # pragma: no cover - defensive inline failure path
        logger.exception(
            "parse_enqueue_failed",
            import_id=import_id,
            error=str(exc),
        )
        await session.refresh(record)
        if record.parse_status != "failed":
            record.parse_status = "failed"
            record.parse_error = record.parse_error or str(exc)
            await session.commit()
        return ParseStatusResponse(
            import_id=record.id,
            status=record.parse_status or "failed",
            requested_at=record.parse_requested_at,
            completed_at=record.parse_completed_at,
            result=record.parse_result,
            error=record.parse_error or str(exc),
            job_id=None,
        )

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
    _: str = Depends(require_viewer),
) -> ParseStatusResponse:
    """Retrieve the status of a parse job."""

    record = await session.get(ImportRecord, import_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Import not found"
        )

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
