"""Export endpoints."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_viewer
from app.core.database import get_session
from app.core.export import (
    DEFAULT_PENDING_WATERMARK,
    ExportFormat,
    ExportOptions,
    LayerMapping,
    LocalExportStorage,
    ProjectGeometryMissing,
    generate_project_export,
)
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/export", tags=["export"])
logger = logging.getLogger(__name__)


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


def _build_layer_mapping(payload: LayerMapPayload | None) -> LayerMapping:
    base_mapping = LayerMapping()
    if payload is None:
        return base_mapping
    return LayerMapping(
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

    try:
        fmt = ExportFormat(payload.format)
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail="Unsupported export format"
        ) from exc

    layer_mapping = _build_layer_mapping(payload.layer_map)
    options = ExportOptions(
        format=fmt,
        include_source=payload.include_source,
        include_approved_overlays=payload.include_approved_overlays,
        include_pending_overlays=payload.include_pending_overlays,
        include_rejected_overlays=payload.include_rejected_overlays,
        layer_mapping=layer_mapping,
        pending_watermark=payload.pending_watermark or DEFAULT_PENDING_WATERMARK,
    )

    storage = LocalExportStorage()
    try:
        artifact = await generate_project_export(
            session,
            project_id=project_id,
            options=options,
            storage=storage,
        )
    except ProjectGeometryMissing as exc:
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
        response.headers["X-Export-Watermark"] = str(watermark)
    return response


__all__ = ["router"]
