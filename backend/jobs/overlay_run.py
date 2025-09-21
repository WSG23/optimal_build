"""Overlay feasibility evaluation job."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import time
from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.core.geometry import GeometrySerializer
from app.core.metrics import OVERLAY_BASELINE_SECONDS
from app.core.models.geometry import GeometryGraph
from app.core.config import settings
from app.models.audit import AuditLog
from app.models.overlay import (
    OverlayRunLock,
    OverlaySourceGeometry,
    OverlaySuggestion,
)
from jobs import job

ENGINE_VERSION = "2024.1"


@dataclass
class OverlayRunResult:
    """Summary of a run of the overlay engine."""

    project_id: int
    evaluated: int = 0
    created: int = 0
    updated: int = 0

    def as_dict(self) -> Dict[str, Any]:
        """Return a serialisable representation."""

        return {
            "project_id": self.project_id,
            "evaluated": self.evaluated,
            "created": self.created,
            "updated": self.updated,
        }


async def run_overlay_for_project(
    session: AsyncSession,
    *,
    project_id: int,
) -> OverlayRunResult:
    """Execute the feasibility engine and persist overlay suggestions."""

    stmt = (
        select(OverlaySourceGeometry)
        .where(OverlaySourceGeometry.project_id == project_id)
        .options(
            selectinload(OverlaySourceGeometry.suggestions),
            selectinload(OverlaySourceGeometry.locks),
        )
    )
    records = (await session.execute(stmt)).scalars().unique().all()
    result = OverlayRunResult(project_id=project_id)
    if not records:
        return result

    started_at = time.perf_counter()
    for source in records:
        geometry = GeometrySerializer.from_export(source.graph)
        fingerprint = geometry.fingerprint()
        source.checksum = fingerprint
        lock = _acquire_lock(session, source)
        try:
            suggestions = _evaluate_geometry(geometry)
            result.evaluated += 1
            existing_by_code: Dict[str, OverlaySuggestion] = {
                suggestion.code: suggestion for suggestion in source.suggestions
            }
            for payload in suggestions:
                code = payload["code"]
                existing = existing_by_code.get(code)
                if existing is None:
                    suggestion = OverlaySuggestion(
                        project_id=project_id,
                        source_geometry_id=source.id,
                        code=code,
                        title=payload["title"],
                        rationale=payload.get("rationale"),
                        severity=payload.get("severity"),
                        status="pending",
                        engine_version=ENGINE_VERSION,
                        engine_payload=payload.get("engine_payload", {}),
                        score=payload.get("score"),
                        geometry_checksum=fingerprint,
                    )
                    source.suggestions.append(suggestion)
                    session.add(suggestion)
                    result.created += 1
                else:
                    existing.title = payload["title"]
                    existing.rationale = payload.get("rationale")
                    existing.severity = payload.get("severity")
                    existing.engine_version = ENGINE_VERSION
                    existing.engine_payload = payload.get("engine_payload", {})
                    existing.score = payload.get("score")
                    existing.geometry_checksum = fingerprint
                    result.updated += 1
        finally:
            lock.is_active = False
            lock.released_at = datetime.now(timezone.utc)
    duration = time.perf_counter() - started_at
    baseline_seconds = float(result.evaluated) * OVERLAY_BASELINE_SECONDS
    log = AuditLog(
        project_id=project_id,
        event_type="overlay_run",
        baseline_seconds=baseline_seconds if baseline_seconds > 0 else None,
        actual_seconds=duration,
        context={
            "evaluated": result.evaluated,
            "created": result.created,
            "updated": result.updated,
        },
    )
    session.add(log)
    await session.commit()
    return result


def _acquire_lock(session: AsyncSession, source: OverlaySourceGeometry) -> OverlayRunLock:
    """Create or refresh a lock for the geometry run."""

    now = datetime.now(timezone.utc)
    for lock in source.locks:
        if lock.lock_kind == "evaluation":
            lock.acquired_at = now
            lock.is_active = True
            lock.released_at = None
            return lock
    lock = OverlayRunLock(
        project_id=source.project_id,
        source_geometry_id=source.id,
        lock_kind="evaluation",
        acquired_at=now,
        is_active=True,
    )
    session.add(lock)
    source.locks.append(lock)
    return lock


def _evaluate_geometry(geometry: GeometryGraph) -> List[Dict[str, object]]:
    """Simple heuristic feasibility engine that produces overlay suggestions."""

    suggestions: Dict[str, Dict[str, object]] = {}
    site_level_id = next(iter(geometry.levels.keys()), None)
    site_metadata = _collect_site_metadata(geometry)

    if site_metadata.get("heritage_zone"):
        suggestions["heritage_conservation"] = {
            "code": "heritage_conservation",
            "title": "Heritage conservation review",
            "rationale": "Site flagged as a heritage zone in the source geometry.",
            "severity": "high",
            "score": 0.9,
            "engine_payload": {
                "triggers": ["heritage_zone"],
                "nodes": [site_level_id] if site_level_id else [],
            },
        }

    flood_zone = site_metadata.get("flood_zone")
    if isinstance(flood_zone, str) and flood_zone.lower() in {"coastal", "river", "flood"}:
        suggestions["flood_mitigation"] = {
            "code": "flood_mitigation",
            "title": "Flood mitigation measures",
            "rationale": "Source geometry reports exposure to flood risk.",
            "severity": "medium",
            "score": 0.75,
            "engine_payload": {
                "triggers": ["flood_zone"],
                "value": flood_zone,
                "nodes": [site_level_id] if site_level_id else [],
            },
        }

    site_area = site_metadata.get("site_area_sqm") or site_metadata.get("site_area")
    try:
        site_area_value = float(site_area) if site_area is not None else None
    except (TypeError, ValueError):
        site_area_value = None
    if site_area_value is not None and site_area_value > 10000:
        suggestions["large_site_review"] = {
            "code": "large_site_review",
            "title": "Large site planning review",
            "rationale": "Sites exceeding 10,000 sqm require planning authority review.",
            "severity": "medium",
            "score": 0.7,
            "engine_payload": {
                "triggers": ["site_area"],
                "value": site_area_value,
                "nodes": [site_level_id] if site_level_id else [],
            },
        }

    tall_building_trigger = _find_tall_building_trigger(geometry)
    if tall_building_trigger:
        suggestions["tall_building_review"] = {
            "code": "tall_building_review",
            "title": "Tall building impact assessment",
            "rationale": "A building element exceeds the 45m trigger height.",
            "severity": "medium",
            "score": 0.8,
            "engine_payload": {
                "triggers": ["building_height"],
                "value": tall_building_trigger["height"],
                "nodes": [tall_building_trigger["entity_id"]],
            },
        }

    ordered_codes = sorted(suggestions.keys())
    return [suggestions[code] for code in ordered_codes]


def _find_tall_building_trigger(geometry: GeometryGraph) -> Dict[str, object] | None:
    """Locate a tall building node, if any."""

    for space in geometry.spaces.values():
        height = _coerce_float(space.metadata.get("height_m") or space.metadata.get("height"))
        if height is not None and height > 45:
            return {"entity_id": space.id, "height": height}
    for fixture in geometry.fixtures.values():
        height = _coerce_float(fixture.metadata.get("height_m") or fixture.metadata.get("height"))
        if height is not None and height > 45:
            return {"entity_id": fixture.id, "height": height}
    return None


def _collect_site_metadata(geometry: GeometryGraph) -> Dict[str, Any]:
    metadata: Dict[str, Any] = {}
    for level in geometry.levels.values():
        metadata.update(level.metadata)
    return metadata


def _coerce_float(value: object) -> float | None:
    """Safely coerce a value to float."""

    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


@job(name="jobs.overlay_run.run_for_project", queue=settings.OVERLAY_QUEUE_DEFAULT)
async def run_overlay_job(project_id: int) -> Dict[str, Any]:
    """Job wrapper that executes the overlay engine using a standalone session."""

    async with AsyncSessionLocal() as session:
        result = await run_overlay_for_project(session, project_id=project_id)
        return {"status": "completed", **result.as_dict()}


__all__ = [
    "run_overlay_for_project",
    "OverlayRunResult",
    "ENGINE_VERSION",
    "run_overlay_job",
]
