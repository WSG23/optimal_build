"""Overlay feasibility evaluation job."""

from __future__ import annotations

import inspect
import time
from collections.abc import AsyncIterator, Callable, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.core.audit.ledger import append_event
from app.core.config import settings
from app.core.database import get_session
from app.core.geometry import GeometrySerializer
from app.core.metrics import OVERLAY_BASELINE_SECONDS
from app.core.models.geometry import GeometryGraph
from app.models.overlay import OverlayRunLock, OverlaySourceGeometry, OverlaySuggestion
from app.models.rkp import RefRule
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


@dataclass
class RuleContext:
    """Context required to evaluate jurisdictional rules."""

    zone_code: str | None
    rules: Sequence[RefRule]
    metrics: dict[str, float]


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
    rule_cache: dict[str, Sequence[RefRule]] = {}
    for source in records:
        geometry = GeometrySerializer.from_export(source.graph)
        fingerprint = geometry.fingerprint()
        source.checksum = fingerprint
        lock = _acquire_lock(session, source)
        try:
            metadata = _coerce_mapping(source.metadata)
            zone_code = _extract_zone_code(metadata)
            rules = await _load_rules_for_zone(session, zone_code, rule_cache)
            metrics = _build_rule_metrics(geometry, metadata)
            rule_context = (
                RuleContext(zone_code=zone_code, rules=rules, metrics=metrics)
                if rules
                else None
            )
            suggestions = _evaluate_geometry(geometry, rule_context=rule_context)
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


def _space_area(space) -> float | None:
    """Compute the polygon area for a space boundary."""

    metadata = getattr(space, "metadata", None)
    if isinstance(metadata, dict):
        stored_area = metadata.get("area_sqm")
        if isinstance(stored_area, (int, float)):
            return float(stored_area)
        unit_scale = metadata.get("unit_scale_to_m")
    else:
        unit_scale = None
    boundary = getattr(space, "boundary", None)
    if not boundary or len(boundary) < 3:
        return None
    area = 0.0
    points = list(boundary)
    for index, (x1, y1) in enumerate(points):
        x2, y2 = points[(index + 1) % len(points)]
        area += x1 * y2 - x2 * y1
    area = abs(area) * 0.5
    if isinstance(unit_scale, (int, float)) and unit_scale not in (0, 1):
        return area * (float(unit_scale) ** 2)
    return area


def _extract_zone_code(metadata: dict[str, Any]) -> str:
    """Determine the zone code applicable to the evaluated geometry."""

    parse_meta = _coerce_mapping(metadata.get("parse_metadata"))
    raw_zone = (
        metadata.get("zone_code")
        or parse_meta.get("zone_code")
        or parse_meta.get("zone")
    )
    if isinstance(raw_zone, str) and raw_zone.strip():
        zone = raw_zone.strip()
        if not zone.upper().startswith("SG:"):
            zone = f"SG:{zone}"
        return zone
    # Default to residential zoning when no metadata is provided so the demo rules fire.
    return "SG:residential"


async def _load_rules_for_zone(
    session: AsyncSession,
    zone_code: str,
    cache: dict[str, Sequence[RefRule]],
) -> Sequence[RefRule]:
    """Fetch and cache published rules for the specified zone code."""

    if zone_code in cache:
        return cache[zone_code]

    stmt = (
        select(RefRule)
        .where(RefRule.jurisdiction == "SG")
        .where(RefRule.review_status == "approved")
        .where(RefRule.is_published.is_(True))
    )
    result = await session.execute(stmt)
    zone_rules: list[RefRule] = []
    for rule in result.scalars().all():
        if not rule.applicability:
            zone_rules.append(rule)
            continue
        if not isinstance(rule.applicability, dict):
            continue
        rule_zone = rule.applicability.get("zone_code")
        if rule_zone == zone_code:
            zone_rules.append(rule)
    cache[zone_code] = zone_rules
    return zone_rules


def _build_rule_metrics(
    geometry: GeometryGraph,
    metadata: dict[str, Any],
) -> dict[str, float]:
    """Derive metrics used for rule evaluation."""

    metrics: dict[str, float] = {}
    footprint_by_level: dict[str, float] = {}
    max_height: float | None = None
    total_area = 0.0
    points: list[tuple[float, float]] = []

    for space in geometry.spaces.values():
        area = _space_area(space)
        if area is not None:
            total_area += area
            level = space.level_id or "default"
            footprint_by_level[level] = footprint_by_level.get(level, 0.0) + area
            if space.boundary:
                points.extend(space.boundary)
        raw_height = space.metadata.get("height_m") or space.metadata.get("height")
        height = _coerce_float(raw_height)
        if height is not None:
            max_height = height if max_height is None else max(max_height, height)

    metrics["total_unit_area_sqm"] = total_area if total_area > 0 else None
    if max_height is not None:
        metrics["max_height_m"] = max_height

    parse_meta = _coerce_mapping(metadata.get("parse_metadata"))
    land_area = _coerce_float(metadata.get("site_area_sqm")) or _coerce_float(
        parse_meta.get("site_area_sqm")
    )

    if not land_area and points:
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        width = max(xs) - min(xs) if xs else 0.0
        depth = max(ys) - min(ys) if ys else 0.0
        if width > 0 and depth > 0:
            land_area = width * depth

    if land_area:
        metrics["land_area_sqm"] = land_area

    gross_floor_area = _coerce_float(
        metadata.get("gross_floor_area_sqm")
    ) or _coerce_float(parse_meta.get("gross_floor_area_sqm"))
    if gross_floor_area is None and total_area > 0:
        gross_floor_area = total_area
    if gross_floor_area is not None:
        metrics["gross_floor_area_sqm"] = gross_floor_area

    if gross_floor_area is not None and land_area:
        try:
            metrics["plot_ratio"] = gross_floor_area / land_area
        except ZeroDivisionError:
            pass

    footprint_area = None
    if footprint_by_level:
        footprint_area = max(footprint_by_level.values())
    elif total_area > 0:
        footprint_area = total_area

    if footprint_area is not None and land_area:
        try:
            metrics["site_coverage_percent"] = (footprint_area / land_area) * 100
        except ZeroDivisionError:
            pass
    return metrics


_PARAMETER_METRIC_MAP: dict[str, str] = {
    "zoning.max_far": "plot_ratio",
    "zoning.max_building_height_m": "max_height_m",
    "zoning.setback.front_min_m": "front_setback_m",
    "zoning.site_coverage.max_percent": "site_coverage_percent",
}

_METRIC_LABELS: dict[str, str] = {
    "plot_ratio": "Plot ratio",
    "max_height_m": "Building height (m)",
    "front_setback_m": "Front setback (m)",
    "site_coverage_percent": "Site coverage (%)",
}

_METRIC_SEVERITY: dict[str, str] = {
    "plot_ratio": "high",
    "max_height_m": "high",
    "front_setback_m": "medium",
    "site_coverage_percent": "medium",
}


def _evaluate_geometry(
    geometry: GeometryGraph,
    rule_context: RuleContext | None = None,
) -> list[dict[str, object]]:
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

    spaces = list(geometry.spaces.values())
    if spaces:
        total_area = 0.0
        residential_count = 0
        for index, space in enumerate(spaces, start=1):
            area = _space_area(space)
            if area is not None:
                total_area += area
            if space.metadata.get("category") == "residential":
                residential_count += 1
            code = f"unit_space_{space.id or index}"
            if code in suggestions:
                continue
            title = space.name or f"Unit {index}"
            props = {
                "space_id": space.id,
                "level_id": space.level_id or site_level_id,
            }
            engine_payload: dict[str, object] = {
                "space_id": space.id,
            }
            if area is not None:
                rounded_area = round(area, 1)
                props["area_sqm"] = rounded_area
                engine_payload["area_sqm"] = rounded_area
            severity = "medium" if area is not None and area >= 120 else "low"
            score = (area / 200.0) if area is not None else None
            suggestions[code] = {
                "code": code,
                "type": "assessment",
                "title": title,
                "rationale": "Auto-generated unit summary based on parsed CAD boundaries.",
                "severity": severity,
                "score": score,
                "target_ids": _string_list(space.id),
                "props": props,
                "rule_refs": ["occupancy.unit.summary"],
                "engine_payload": engine_payload,
            }

        if total_area > 0:
            suggestions.setdefault(
                "unit_area_summary",
                {
                    "code": "unit_area_summary",
                    "type": "summary",
                    "title": "Unit area coverage",
                    "rationale": "Summarises total detected unit area for quick QA.",
                    "severity": "low",
                    "score": min(1.0, total_area / 1000.0),
                    "target_ids": _string_list(site_level_id),
                    "props": {
                        "total_unit_area_sqm": round(total_area, 1),
                        "unit_count": len(spaces),
                        "residential_units": residential_count,
                    },
                    "rule_refs": ["occupancy.area.summary"],
                    "engine_payload": {
                        "area_sqm": round(total_area, 1),
                        "unit_count": len(spaces),
                    },
                },
            )

    if rule_context and rule_context.rules:
        rule_suggestions = _evaluate_rules_for_geometry(
            rule_context=rule_context,
            site_level_id=site_level_id,
        )
        for overlay in rule_suggestions:
            suggestions[overlay["code"]] = overlay

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


def _coerce_float(value: object) -> float | None:
    """Attempt to coerce a value to ``float``."""

    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _unit_suffix(unit: str | None) -> str:
    """Return a human-readable suffix for numeric values."""

    if not unit:
        return ""
    stripped = str(unit).strip()
    return f" {stripped}" if stripped else ""


def _humanise_parameter_key(parameter_key: str) -> str:
    """Convert a parameter key into a readable label."""

    return parameter_key.replace(".", " ").replace("_", " ").replace("  ", " ").title()


def _compare_rule(value: float, operator: str, threshold: float) -> bool:
    """Return ``True`` when ``value`` satisfies the rule ``operator`` and ``threshold``."""

    tolerance = 1e-6
    op = (operator or "").strip()
    if op == "<=":
        return value <= threshold + tolerance
    if op == "<":
        return value < threshold - tolerance
    if op == ">=":
        return value + tolerance >= threshold
    if op == ">":
        return value > threshold + tolerance
    if op in {"=", "=="}:
        return abs(value - threshold) <= tolerance
    return True


def _evaluate_rules_for_geometry(
    rule_context: RuleContext,
    site_level_id: str | None,
) -> list[dict[str, object]]:
    """Generate overlays for each rule violation (or missing metric) detected."""

    overlays: list[dict[str, object]] = []
    missing_reported: set[str] = set()
    metrics = rule_context.metrics

    for rule in rule_context.rules:
        metric_key = _PARAMETER_METRIC_MAP.get(rule.parameter_key)
        if metric_key is None:
            continue
        limit_value = _coerce_float(rule.value)
        if limit_value is None:
            continue
        measured_value = metrics.get(metric_key)
        if measured_value is None:
            if metric_key not in missing_reported:
                overlays.append(
                    _build_missing_metric_overlay(
                        metric_key=metric_key,
                        parameter_key=rule.parameter_key,
                        zone_code=rule_context.zone_code,
                        site_level_id=site_level_id,
                    )
                )
                missing_reported.add(metric_key)
            continue
        if not _compare_rule(measured_value, rule.operator, limit_value):
            overlays.append(
                _build_rule_violation_overlay(
                    rule=rule,
                    metric_key=metric_key,
                    measured=measured_value,
                    limit_value=limit_value,
                    zone_code=rule_context.zone_code,
                    site_level_id=site_level_id,
                )
            )

    return overlays


def _build_rule_violation_overlay(
    *,
    rule: RefRule,
    metric_key: str,
    measured: float,
    limit_value: float,
    zone_code: str | None,
    site_level_id: str | None,
) -> dict[str, object]:
    """Create an overlay payload describing a rule violation."""

    label = _METRIC_LABELS.get(metric_key, _humanise_parameter_key(rule.parameter_key))
    severity = _METRIC_SEVERITY.get(metric_key, "medium")
    unit_suffix = _unit_suffix(rule.unit)
    code = f"rule_violation_{rule.parameter_key.replace('.', '_')}"

    rationale = (
        f"{label} {measured:.2f}{unit_suffix} violates "
        f"requirement {rule.operator} {limit_value:.2f}{unit_suffix}"
    )
    if zone_code:
        rationale += f" for {zone_code} zoning."
    else:
        rationale += "."

    score = None
    if limit_value:
        try:
            score = measured / limit_value
        except ZeroDivisionError:
            score = None

    return {
        "code": code,
        "type": "regulatory",
        "title": f"{label} exceeds limit",
        "rationale": rationale,
        "severity": severity,
        "score": score,
        "target_ids": _string_list(site_level_id),
        "props": {
            "parameter_key": rule.parameter_key,
            "measured_value": measured,
            "limit_value": limit_value,
            "operator": rule.operator,
            "unit": rule.unit,
            "zone_code": zone_code,
        },
        "rule_refs": [rule.parameter_key],
        "engine_payload": {
            "rule_id": rule.id,
            "parameter_key": rule.parameter_key,
            "measured": measured,
            "limit": limit_value,
            "operator": rule.operator,
            "unit": rule.unit,
        },
    }


def _build_missing_metric_overlay(
    *,
    metric_key: str,
    parameter_key: str,
    zone_code: str | None,
    site_level_id: str | None,
) -> dict[str, object]:
    """Create an overlay prompting the reviewer to supply missing inputs."""

    label = _METRIC_LABELS.get(metric_key, _humanise_parameter_key(parameter_key))
    rationale = f"Provide {label.lower()} data so rules can be evaluated accurately."
    if zone_code:
        rationale += f" This is required for {zone_code} compliance."

    return {
        "code": f"rule_data_missing_{metric_key}",
        "type": "data",
        "title": f"Provide {label.lower()} data",
        "rationale": rationale,
        "severity": "low",
        "target_ids": _string_list(site_level_id),
        "props": {
            "metric": metric_key,
            "parameter_key": parameter_key,
            "zone_code": zone_code,
        },
        "rule_refs": [parameter_key],
        "engine_payload": {
            "missing_metric": metric_key,
            "parameter_key": parameter_key,
            "zone_code": zone_code,
        },
    }


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
