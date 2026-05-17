"""Export endpoints."""

from __future__ import annotations

import logging
import unicodedata
from importlib import import_module
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_viewer
from app.core.database import get_session

router = APIRouter(prefix="/export", tags=["export"])
logger = logging.getLogger(__name__)

_UNRESOLVED = object()
_EXPORT_SYMBOLS = {
    "DEFAULT_PENDING_WATERMARK",
    "ExportFormat",
    "ExportOptions",
    "LayerMapping",
    "LocalExportStorage",
    "ProjectGeometryMissing",
    "generate_project_export",
}


def _load_export_symbol(name: str) -> Any:
    """Resolve export-core symbols lazily so route import stays lightweight."""

    existing = globals().get(name, _UNRESOLVED)
    if existing is not _UNRESOLVED:
        return existing

    module = import_module("app.core.export")
    resolved = getattr(module, name)
    globals()[name] = resolved
    return resolved


def __getattr__(name: str) -> Any:
    if name not in _EXPORT_SYMBOLS:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
    return _load_export_symbol(name)


class LayerMapPayload(BaseModel):
    """Layer and style configuration supplied by the client."""

    source: dict[str, str] = Field(default_factory=dict)
    overlays: dict[str, str] = Field(default_factory=dict)
    styles: dict[str, dict[str, Any]] = Field(default_factory=dict)
    default_source_layer: str | None = None
    default_overlay_layer: str | None = None


class ExportRequestPayload(BaseModel):
    """Request payload for the export endpoint."""

    format: str = Field(..., description="Target export format")
    include_source: bool = True
    include_approved_overlays: bool = True
    include_pending_overlays: bool = False
    include_rejected_overlays: bool = False
    layer_map: LayerMapPayload | None = None
    pending_watermark: str | None = None

    @field_validator("format")
    @classmethod
    def _normalise_format(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if not cleaned:
            raise ValueError("format must not be empty")
        return cleaned


def _build_layer_mapping(payload: LayerMapPayload | None) -> Any:
    layer_mapping_cls = _load_export_symbol("LayerMapping")
    base_mapping = layer_mapping_cls()
    if payload is None:
        return base_mapping
    return layer_mapping_cls(
        source=dict(payload.source),
        overlays=dict(payload.overlays),
        styles={key: dict(value) for key, value in payload.styles.items()},
        default_source_layer=payload.default_source_layer
        or base_mapping.default_source_layer,
        default_overlay_layer=payload.default_overlay_layer
        or base_mapping.default_overlay_layer,
    )


@router.post("/{project_id}")
async def export_project(
    project_id: int,
    payload: ExportRequestPayload,
    session: AsyncSession = Depends(get_session),
    _: str = Depends(require_viewer),
) -> FileResponse:
    """Generate and stream a CAD/BIM export for the given project."""

    export_format_cls = _load_export_symbol("ExportFormat")
    try:
        fmt = export_format_cls(payload.format)
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail="Unsupported export format"
        ) from exc

    layer_mapping = _build_layer_mapping(payload.layer_map)
    options_cls = _load_export_symbol("ExportOptions")
    default_pending_watermark = _load_export_symbol("DEFAULT_PENDING_WATERMARK")
    options = options_cls(
        format=fmt,
        include_source=payload.include_source,
        include_approved_overlays=payload.include_approved_overlays,
        include_pending_overlays=payload.include_pending_overlays,
        include_rejected_overlays=payload.include_rejected_overlays,
        layer_mapping=layer_mapping,
        pending_watermark=payload.pending_watermark or default_pending_watermark,
    )

    storage = _load_export_symbol("LocalExportStorage")()
    project_geometry_missing = _load_export_symbol("ProjectGeometryMissing")
    generate_project_export_fn = _load_export_symbol("generate_project_export")
    try:
        artifact = await generate_project_export_fn(
            session,
            project_id=project_id,
            options=options,
            storage=storage,
        )
    except project_geometry_missing as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    response = FileResponse(
        path=artifact.path,
        media_type=artifact.media_type,
        filename=artifact.filename,
    )
    renderer = artifact.manifest.get("renderer")
    if renderer:
        response.headers["X-Export-Renderer"] = str(renderer)
        if str(renderer).lower() == "fallback":
            response.headers["X-Export-Fallback"] = "1"
            logger.warning(
                "export_renderer_fallback",
                extra={
                    "project_id": project_id,
                    "requested_format": options.format.value,
                },
            )
    watermark = artifact.manifest.get("watermark")
    if watermark:
        response.headers["X-Export-Watermark"] = _normalise_header_value(str(watermark))
    return response


__all__ = ["router"]


def _normalise_header_value(value: str) -> str:
    """Return an ASCII-safe header value."""

    try:
        value.encode("latin-1")
        return value
    except UnicodeEncodeError:
        normalised = unicodedata.normalize("NFKD", value)
        ascii_value = normalised.encode("ascii", "ignore").decode("ascii")
        return ascii_value or value.encode("latin-1", "ignore").decode("latin-1")
