"""Helpers to persist parsed geometry into overlay source tables."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from backend._compat.datetime import UTC
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit.ledger import append_event
from app.core.geometry import GeometrySerializer
from app.models.imports import ImportRecord
from app.models.overlay import OverlaySourceGeometry
from app.utils.logging import get_logger

logger = get_logger(__name__)


def _coerce_mapping(value: object) -> dict[str, Any]:
    """Return a shallow copy when ``value`` behaves like a mapping."""

    if isinstance(value, Mapping):
        return dict(value)
    return {}


def _clean_metadata(payload: dict[str, Any]) -> dict[str, Any]:
    """Remove ``None`` and empty container values from ``payload``."""

    return {
        key: value
        for key, value in payload.items()
        if value is not None and value != {} and value != []
    }


async def ingest_parsed_import_geometry(
    session: AsyncSession,
    *,
    project_id: int,
    import_record: ImportRecord,
    parse_payload: Mapping[str, Any] | None = None,
    source_key: str | None = None,
) -> OverlaySourceGeometry:
    """Persist the parsed import geometry as an overlay source record."""

    payload = parse_payload or import_record.parse_result or {}
    if not isinstance(payload, Mapping):
        raise ValueError("Parsed payload must be a mapping")

    graph_payload = payload.get("graph")
    if not isinstance(graph_payload, Mapping):
        raise ValueError("Parsed payload missing graph data")

    geometry = GeometrySerializer.from_export(graph_payload)
    export_payload = GeometrySerializer.to_export(geometry)
    checksum = geometry.fingerprint()

    parsed_metadata = _coerce_mapping(payload.get("metadata"))
    metadata = _clean_metadata(
        {
            "import_id": import_record.id,
            "filename": import_record.filename,
            "content_type": import_record.content_type,
            "size_bytes": import_record.size_bytes,
            "uploaded_at": (
                import_record.uploaded_at.isoformat()
                if getattr(import_record, "uploaded_at", None)
                else None
            ),
            "floors": payload.get("floors"),
            "units": payload.get("units"),
            "parser": parsed_metadata.get("source"),
            "parse_metadata": parsed_metadata,
            "vector_summary": import_record.vector_summary,
            "zone_code": getattr(import_record, "zone_code", None),
            "metric_overrides": getattr(import_record, "metric_overrides", None),
            "ingested_at": datetime.now(UTC).isoformat(),
        }
    )

    key = source_key or f"import:{import_record.id}"
    stmt = select(OverlaySourceGeometry).where(
        OverlaySourceGeometry.project_id == project_id,
        OverlaySourceGeometry.source_geometry_key == key,
    )
    existing = (await session.execute(stmt)).scalars().first()

    if existing is None:
        record = OverlaySourceGeometry(
            project_id=project_id,
            source_geometry_key=key,
            graph=export_payload,
            metadata=metadata,
            checksum=checksum,
        )
        session.add(record)
    else:
        existing.graph = export_payload
        existing.metadata = metadata
        existing.checksum = checksum
        record = existing

    await session.flush()

    event_context = _clean_metadata(
        {
            "import_id": import_record.id,
            "overlay_source_id": record.id,
            "source_geometry_key": record.source_geometry_key,
            "checksum": checksum,
            "floors": payload.get("floors"),
            "units": payload.get("units"),
            "parser": metadata.get("parser"),
            "zone_code": getattr(import_record, "zone_code", None),
            "metric_overrides": getattr(import_record, "metric_overrides", None),
        }
    )
    await append_event(
        session,
        project_id=project_id,
        event_type="geometry_ingested",
        context=event_context,
    )

    logger.info(
        "overlay_geometry_ingested",
        project_id=project_id,
        import_id=import_record.id,
        overlay_source_id=record.id,
        checksum=checksum,
    )

    return record


__all__ = ["ingest_parsed_import_geometry"]
