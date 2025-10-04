"""Overlay feasibility evaluation job."""

from __future__ import annotations

import inspect
import time
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.core.audit.ledger import append_event
from app.core.config import settings
from app.core.database import get_session
from app.core.geometry import GeometrySerializer
from app.core.metrics import OVERLAY_BASELINE_SECONDS
from app.core.models.geometry import GeometryGraph
from app.models.overlay import OverlayRunLock, OverlaySourceGeometry, OverlaySuggestion
from backend._compat.datetime import UTC
from backend.jobs import job
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

ENGINE_VERSION = "2024.1"


@dataclass
class OverlayRunResult:
    """Summary of a run of the overlay engine."""

    project_id: int
    evaluated: int = 0
    created: int = 0
    updated: int = 0

    def as_dict(self) -> dict[str, Any]:
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
            existing_by_code: dict[str, OverlaySuggestion] = {
                suggestion.code: suggestion for suggestion in source.suggestions
            }
            for payload in suggestions:
                code = payload["code"]
                target_ids = _string_list(payload.get("target_ids"))
                props = _coerce_mapping(payload.get("props"))
                rule_refs = _string_list(payload.get("rule_refs"))
                existing = existing_by_code.get(code)
                if existing is None:
                    suggestion = OverlaySuggestion(
                        project_id=project_id,
                        source_geometry_id=source.id,
                        code=code,
                        type=payload.get("type"),
                        title=payload["title"],
                        rationale=payload.get("rationale"),
                        severity=payload.get("severity"),
                        status="pending",
                        engine_version=ENGINE_VERSION,
                        engine_payload=payload.get("engine_payload", {}),
                        target_ids=target_ids,
                        props=props,
                        rule_refs=rule_refs,
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
                    existing.type = payload.get("type")
                    existing.engine_version = ENGINE_VERSION
                    existing.engine_payload = payload.get("engine_payload", {})
                    existing.target_ids = target_ids
                    existing.props = props
                    existing.rule_refs = rule_refs
                    existing.score = payload.get("score")
                    existing.geometry_checksum = fingerprint
                    result.updated += 1
        finally:
            lock.is_active = False
            lock.released_at = datetime.now(UTC)
    duration = time.perf_counter() - started_at
    baseline_seconds = float(result.evaluated) * OVERLAY_BASELINE_SECONDS
    await append_event(
        session,
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
    await session.commit()
    return result


def _acquire_lock(
    session: AsyncSession, source: OverlaySourceGeometry
) -> OverlayRunLock:
    """Create or refresh a lock for the geometry run."""

    now = datetime.now(UTC)
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


def _evaluate_geometry(geometry: GeometryGraph) -> list[dict[str, object]]:
    """Simple heuristic feasibility engine that produces overlay suggestions."""

    suggestions: dict[str, dict[str, object]] = {}
    site_level_id = next(iter(geometry.levels.keys()), None)
    site_metadata = _collect_site_metadata(geometry)

    if site_metadata.get("heritage_zone"):
        target_ids = _string_list(site_level_id)
        suggestions["heritage_conservation"] = {
            "code": "heritage_conservation",
            "type": "review",
            "title": "Heritage conservation review",
            "rationale": "Site flagged as a heritage zone in the source geometry.",
            "severity": "high",
            "score": 0.9,
            "target_ids": target_ids,
            "props": {
                "trigger": "heritage_zone",
                "heritage_zone": bool(site_metadata.get("heritage_zone")),
            },
            "rule_refs": ["heritage.zone.compliance"],
            "engine_payload": {
                "triggers": ["heritage_zone"],
                "nodes": target_ids,
            },
        }

    flood_zone = site_metadata.get("flood_zone")
    if isinstance(flood_zone, str) and flood_zone.lower() in {
        "coastal",
        "river",
        "flood",
    }:
        target_ids = _string_list(site_level_id)
        suggestions["flood_mitigation"] = {
            "code": "flood_mitigation",
            "type": "mitigation",
            "title": "Flood mitigation measures",
            "rationale": "Source geometry reports exposure to flood risk.",
            "severity": "medium",
            "score": 0.75,
            "target_ids": target_ids,
            "props": {
                "trigger": "flood_zone",
                "flood_zone": flood_zone,
            },
            "rule_refs": ["water.management.flood_zone"],
            "engine_payload": {
                "triggers": ["flood_zone"],
                "value": flood_zone,
                "nodes": target_ids,
            },
        }

    site_area = site_metadata.get("site_area_sqm") or site_metadata.get("site_area")
    try:
        site_area_value = float(site_area) if site_area is not None else None
    except (TypeError, ValueError):
        site_area_value = None
    if site_area_value is not None and site_area_value > 10000:
        target_ids = _string_list(site_level_id)
        suggestions["large_site_review"] = {
            "code": "large_site_review",
            "type": "review",
            "title": "Large site planning review",
            "rationale": "Sites exceeding 10,000 sqm require planning authority review.",
            "severity": "medium",
            "score": 0.7,
            "target_ids": target_ids,
            "props": {
                "trigger": "site_area",
                "site_area_sqm": site_area_value,
                "threshold_sqm": 10000,
            },
            "rule_refs": ["planning.large_site.threshold"],
            "engine_payload": {
                "triggers": ["site_area"],
                "value": site_area_value,
                "nodes": target_ids,
            },
        }

    tall_building_trigger = _find_tall_building_trigger(geometry)
    if tall_building_trigger:
        building_target_ids = _string_list(tall_building_trigger["entity_id"])
        suggestions["tall_building_review"] = {
            "code": "tall_building_review",
            "type": "assessment",
            "title": "Tall building impact assessment",
            "rationale": "A building element exceeds the 45m trigger height.",
            "severity": "medium",
            "score": 0.8,
            "target_ids": building_target_ids,
            "props": {
                "trigger": "building_height",
                "height_m": tall_building_trigger["height"],
                "threshold_m": 45,
            },
            "rule_refs": ["building.height.trigger"],
            "engine_payload": {
                "triggers": ["building_height"],
                "value": tall_building_trigger["height"],
                "nodes": building_target_ids,
            },
        }

        if isinstance(flood_zone, str) and flood_zone.lower() == "coastal":
            coastal_targets = _string_list(
                site_level_id, tall_building_trigger["entity_id"]
            )
            suggestions["coastal_evacuation_plan"] = {
                "code": "coastal_evacuation_plan",
                "type": "preparedness",
                "title": "Coastal evacuation planning",
                "rationale": "Coastal flood risk combined with tall structures requires evacuation planning.",
                "severity": "medium",
                "score": 0.65,
                "target_ids": coastal_targets,
                "props": {
                    "trigger": "flood_zone+building_height",
                    "flood_zone": flood_zone,
                    "height_m": tall_building_trigger["height"],
                },
                "rule_refs": ["safety.coastal_evacuation.guidance"],
                "engine_payload": {
                    "triggers": ["flood_zone", "building_height"],
                    "value": {
                        "flood_zone": flood_zone,
                        "height": tall_building_trigger["height"],
                    },
                    "nodes": coastal_targets,
                },
            }

    ordered_codes = sorted(suggestions.keys())
    return [suggestions[code] for code in ordered_codes]


def _find_tall_building_trigger(geometry: GeometryGraph) -> dict[str, object] | None:
    """Locate a tall building node, if any."""

    for space in geometry.spaces.values():
        height = _coerce_float(
            space.metadata.get("height_m") or space.metadata.get("height")
        )
        if height is not None and height >= 45:
            return {"entity_id": space.id, "height": height}
    for fixture in geometry.fixtures.values():
        height = _coerce_float(
            fixture.metadata.get("height_m") or fixture.metadata.get("height")
        )
        if height is not None and height >= 45:
            return {"entity_id": fixture.id, "height": height}
    return None


def _collect_site_metadata(geometry: GeometryGraph) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
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


def _string_list(*values: object) -> list[str]:
    """Normalise one or more raw values into a deduplicated list of strings."""

    items: list[str] = []
    for value in values:
        if isinstance(value, (list, tuple, set)):
            for entry in value:
                if entry in (None, ""):
                    continue
                items.append(str(entry))
        elif value not in (None, ""):
            items.append(str(value))
    deduped: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


def _coerce_mapping(value: object) -> dict[str, Any]:
    """Return a shallow copy of mapping inputs."""

    if isinstance(value, dict):
        return dict(value)
    return {}


def _resolve_session_dependency() -> Callable[[], Any]:
    """Return the dependency callable used to acquire database sessions."""

    try:  # pragma: no cover - FastAPI is optional in some environments
        from app.main import app as fastapi_app  # type: ignore
    except Exception:  # pragma: no cover - fallback when app isn't available
        fastapi_app = None

    if fastapi_app is not None:
        override = fastapi_app.dependency_overrides.get(get_session)
        if override is not None:
            return override
    return get_session


@asynccontextmanager
async def _job_session() -> AsyncIterator[AsyncSession]:
    """Yield a session using the active dependency overrides when available."""

    dependency = _resolve_session_dependency()
    resource = dependency()

    if inspect.isasyncgen(resource):
        generator = resource
        try:
            session = await anext(generator)  # type: ignore[arg-type]
        except StopAsyncIteration as exc:  # pragma: no cover - defensive guard
            raise RuntimeError("Session dependency did not yield a session") from exc
        try:
            yield session
        finally:
            await generator.aclose()
        return

    if inspect.isawaitable(resource):
        session = await resource
        try:
            yield session
        finally:
            close = getattr(session, "close", None)
            if callable(close):
                result = close()
                if inspect.isawaitable(result):
                    await result
        return

    if isinstance(resource, AsyncSession):
        try:
            yield resource
        finally:
            await resource.close()
        return

    raise TypeError(
        "Session dependency must return an AsyncSession, coroutine, or async generator"
    )


@job(name="jobs.overlay_run.run_for_project", queue=settings.OVERLAY_QUEUE_DEFAULT)
async def run_overlay_job(project_id: int) -> dict[str, Any]:
    """Job wrapper that executes the overlay engine using a standalone session."""

    async with _job_session() as session:
        result = await run_overlay_for_project(session, project_id=project_id)
        return {"status": "completed", **result.as_dict()}


__all__ = [
    "run_overlay_for_project",
    "OverlayRunResult",
    "ENGINE_VERSION",
    "run_overlay_job",
]
