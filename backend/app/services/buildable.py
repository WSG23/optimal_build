"""Buildable screening calculations."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.rkp import RefParcel, RefRule, RefZoningLayer
from app.schemas.buildable import (
    BuildableCalculation,
    BuildableDefaults,
    BuildableMetrics,
    BuildableRule,
    BuildableRuleProvenance,
    ZoneSource,
)
from sqlalchemy import select


@dataclass
class ResolvedZone:
    """Context required to calculate buildable capacity."""

    zone_code: Optional[str]
    parcel: Optional[RefParcel]
    zone_layers: Sequence[RefZoningLayer]
    input_kind: str
    geometry_properties: Optional[Dict[str, Any]] = None


async def calculate_buildable(
    session: AsyncSession,
    resolved: ResolvedZone,
    defaults: BuildableDefaults,
    *,
    typ_floor_to_floor_m: Optional[float] = None,
    efficiency_ratio: Optional[float] = None,
) -> BuildableCalculation:
    """Compute buildable metrics and surface applicable rules."""

    attributes = _merge_layer_attributes(resolved.zone_layers)
    rules, overrides = await _load_rules_for_zone(session, resolved.zone_code)
    if overrides.front_setback_m is not None:
        attributes["front_setback_min_m"] = overrides.front_setback_m

    area_m2 = await _parcel_area(session, resolved.parcel)
    if area_m2 is None:
        area_m2 = defaults.site_area_m2
    plot_ratio = overrides.plot_ratio
    if plot_ratio is None:
        plot_ratio = _extract_plot_ratio(attributes) or defaults.plot_ratio

    site_coverage = overrides.site_coverage
    if site_coverage is None:
        site_coverage = _extract_site_coverage(attributes) or defaults.site_coverage
    site_coverage = max(0.0, min(site_coverage, 1.0))
    gfa_cap = _round_half_up(area_m2 * plot_ratio) if area_m2 else 0
    footprint = _round_half_up(area_m2 * site_coverage) if area_m2 else 0

    storey_limit = overrides.storey_limit
    if storey_limit is None:
        storey_limit = _extract_storey_limit(attributes)

    height_limit = overrides.height_limit_m
    if height_limit is None:
        height_limit = _extract_height_limit(attributes)
    floor_height = (
        typ_floor_to_floor_m
        if typ_floor_to_floor_m is not None and typ_floor_to_floor_m > 0
        else defaults.floor_height_m
    )
    floors_from_height = _floors_from_height(height_limit, floor_height)
    floors_from_ratio = _floors_from_ratio(gfa_cap, footprint)

    floor_candidates = [
        value
        for value in (storey_limit, floors_from_height, floors_from_ratio)
        if value is not None and value > 0
    ]
    floors_max = min(floor_candidates) if floor_candidates else 0
    efficiency_factor = (
        efficiency_ratio
        if efficiency_ratio is not None and efficiency_ratio > 0
        else defaults.efficiency_factor
    )
    efficiency_factor = max(0.0, min(efficiency_factor, 1.0))
    nsa_est = _round_half_up(gfa_cap * efficiency_factor) if gfa_cap else 0

    zone_source = _build_zone_source(resolved)

    metrics = BuildableMetrics(
        gfa_cap_m2=gfa_cap,
        floors_max=floors_max,
        footprint_m2=footprint,
        nsa_est_m2=nsa_est,
    )

    return BuildableCalculation(metrics=metrics, zone_source=zone_source, rules=rules)


async def _load_rules_for_zone(
    session: AsyncSession, zone_code: Optional[str]
) -> Tuple[List[BuildableRule], "_RuleOverrides"]:
    if not zone_code:
        return [], _RuleOverrides()

    stmt = (
        select(RefRule)
        .where(RefRule.topic == "zoning")
        .where(RefRule.review_status == "approved")
        .where(RefRule.is_published.is_(True))
    )
    result = await session.execute(stmt)

    overrides = _RuleOverrides()
    rules: List[BuildableRule] = []
    for record in result.scalars():
        if not _zone_matches(record.applicability, zone_code):
            continue
        _apply_rule_override(overrides, record)
        provenance = BuildableRuleProvenance(
            rule_id=record.id,
            clause_ref=record.clause_ref,
            document_id=record.document_id,
            pages=_determine_pages(record),
            seed_tag=_determine_seed_tag(record),
        )
        rules.append(
            BuildableRule(
                id=record.id,
                authority=record.authority,
                parameter_key=record.parameter_key,
                operator=record.operator,
                value=record.value,
                unit=record.unit,
                provenance=provenance,
            )
        )
    rules.sort(key=lambda item: (item.parameter_key, item.id))
    return rules, overrides


def _determine_seed_tag(rule: RefRule) -> Optional[str]:
    provenance = (
        rule.source_provenance if isinstance(rule.source_provenance, dict) else None
    )
    if provenance and isinstance(provenance.get("seed_tag"), str):
        return provenance["seed_tag"]
    return rule.topic


def _determine_pages(rule: RefRule) -> Optional[List[int]]:
    provenance = (
        rule.source_provenance if isinstance(rule.source_provenance, dict) else None
    )
    if not provenance:
        return None
    pages = provenance.get("pages")
    if not isinstance(pages, (list, tuple)):
        return None
    result: List[int] = []
    for item in pages:
        try:
            number = int(item)
        except (TypeError, ValueError):
            continue
        result.append(number)
    return result or None


def _merge_layer_attributes(layers: Sequence[RefZoningLayer]) -> Dict[str, Any]:
    merged: Dict[str, Any] = {}
    for layer in layers:
        if layer.attributes and isinstance(layer.attributes, dict):
            merged.update(layer.attributes)
    return merged


async def _parcel_area(
    session: AsyncSession, parcel: Optional[RefParcel]
) -> Optional[float]:
    if settings.BUILDABLE_USE_POSTGIS:
        from app.services.postgis import parcel_area as _parcel_area_postgis

        return await _parcel_area_postgis(session, parcel)

    if parcel is None or parcel.area_m2 is None:
        return None
    try:
        return float(parcel.area_m2)
    except (TypeError, ValueError):
        return None


async def _load_layers_for_zone(
    session: AsyncSession, zone_code: str
) -> List[RefZoningLayer]:
    if settings.BUILDABLE_USE_POSTGIS:
        from app.services.postgis import load_layers_for_zone as _load_layers_postgis

        return await _load_layers_postgis(session, zone_code)

    stmt = select(RefZoningLayer).where(RefZoningLayer.zone_code == zone_code)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def load_layers_for_zone(
    session: AsyncSession, zone_code: str
) -> List[RefZoningLayer]:
    """Public wrapper around :func:`_load_layers_for_zone` for API usage."""

    return await _load_layers_for_zone(session, zone_code)


def _extract_plot_ratio(attributes: Dict[str, Any]) -> Optional[float]:
    return _first_positive(
        attributes,
        [
            "plot_ratio",
            "gross_plot_ratio",
            "max_plot_ratio",
            "floor_area_ratio",
            "far",
        ],
    )


def _extract_site_coverage(attributes: Dict[str, Any]) -> Optional[float]:
    coverage = _first_positive(
        attributes,
        [
            "site_coverage",
            "site_coverage_ratio",
            "site_coverage_fraction",
            "site_coverage_pct",
            "site_coverage_percent",
        ],
    )
    if coverage is None:
        return None
    if coverage > 1:
        coverage = coverage / 100.0
    return coverage


def _extract_storey_limit(attributes: Dict[str, Any]) -> Optional[int]:
    value = _first_positive(
        attributes,
        [
            "floors_max",
            "max_storeys",
            "storey_limit",
            "storeys",
            "max_floors",
        ],
    )
    return int(value) if value else None


def _extract_height_limit(attributes: Dict[str, Any]) -> Optional[float]:
    return _first_positive(
        attributes,
        [
            "height_m",
            "max_height_m",
            "height_limit_m",
            "building_height_m",
        ],
    )


def _first_positive(attributes: Dict[str, Any], keys: Iterable[str]) -> Optional[float]:
    for key in keys:
        value = attributes.get(key)
        number = _coerce_float(value)
        if number is not None and number > 0:
            return number
    return None


def _coerce_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _round_half_up(value: float) -> int:
    return int(Decimal(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _floors_from_height(
    height_limit: Optional[float], floor_height: float
) -> Optional[int]:
    if not height_limit or height_limit <= 0 or floor_height <= 0:
        return None
    floors = int(math.floor(height_limit / floor_height))
    return max(floors, 1) if floors > 0 else 1


def _floors_from_ratio(gfa_cap: int, footprint: int) -> Optional[int]:
    if gfa_cap <= 0 or footprint <= 0:
        return None
    return max(1, math.ceil(gfa_cap / footprint))


def _build_zone_source(resolved: ResolvedZone) -> ZoneSource:
    layer = resolved.zone_layers[0] if resolved.zone_layers else None
    kind = (
        "parcel"
        if resolved.parcel
        else ("geometry" if resolved.input_kind == "geometry" else "unknown")
    )
    note: Optional[str] = None
    if resolved.input_kind == "geometry" and resolved.geometry_properties:
        if isinstance(resolved.geometry_properties.get("note"), str):
            note = resolved.geometry_properties["note"]
        elif "zone_code" in resolved.geometry_properties:
            note = f"geometry zone_code={resolved.geometry_properties['zone_code']}"
    return ZoneSource(
        kind=kind,
        layer_name=layer.layer_name if layer else None,
        jurisdiction=layer.jurisdiction if layer else None,
        parcel_ref=resolved.parcel.parcel_ref if resolved.parcel else None,
        parcel_source=resolved.parcel.source if resolved.parcel else None,
        note=note,
    )


def _zone_matches(applicability: Any, zone_code: str) -> bool:
    if not applicability:
        return False
    zone_code_normalised = str(zone_code).lower()
    if isinstance(applicability, str):
        return applicability.lower() == zone_code_normalised
    if isinstance(applicability, dict):
        candidate_keys = (
            "zone_code",
            "zone_codes",
            "zones",
            "zone",
        )
        for key in candidate_keys:
            if key not in applicability:
                continue
            value = applicability[key]
            if isinstance(value, str) and value.lower() == zone_code_normalised:
                return True
            if isinstance(value, (list, tuple, set)):
                for item in value:
                    if isinstance(item, str) and item.lower() == zone_code_normalised:
                        return True
    return False


@dataclass
class _RuleOverrides:
    plot_ratio: Optional[float] = None
    site_coverage: Optional[float] = None
    height_limit_m: Optional[float] = None
    storey_limit: Optional[int] = None
    front_setback_m: Optional[float] = None


_NUMBER_PATTERN = re.compile(r"[-+]?(?:\d+\.?\d*|\d*\.?\d+)(?:[eE][-+]?\d+)?")


def _apply_rule_override(overrides: _RuleOverrides, rule: RefRule) -> None:
    parameter_key = (rule.parameter_key or "").lower()
    value = _coerce_rule_float(rule.value)
    if value is None or value <= 0:
        return

    unit = (rule.unit or "").strip().lower()
    if parameter_key == "zoning.max_far":
        if overrides.plot_ratio is None or value < overrides.plot_ratio:
            overrides.plot_ratio = value
    elif parameter_key == "zoning.site_coverage.max_percent":
        fraction = _normalise_percentage(value, unit)
        if fraction is not None:
            if overrides.site_coverage is None or fraction < overrides.site_coverage:
                overrides.site_coverage = fraction
    elif parameter_key == "zoning.max_building_height_m":
        if unit in {"storey", "storeys", "story", "stories"}:
            storeys = int(math.floor(value))
            if storeys > 0 and (
                overrides.storey_limit is None or storeys < overrides.storey_limit
            ):
                overrides.storey_limit = storeys
        else:
            if overrides.height_limit_m is None or value < overrides.height_limit_m:
                overrides.height_limit_m = value
    elif parameter_key == "zoning.setback.front_min_m":
        metres = _convert_to_metres(value, unit)
        if metres is not None:
            if overrides.front_setback_m is None or metres > overrides.front_setback_m:
                overrides.front_setback_m = metres


def _coerce_rule_float(value: Any) -> Optional[float]:
    if isinstance(value, (int, float)):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    if isinstance(value, str):
        match = _NUMBER_PATTERN.search(value.replace(",", ""))
        if match:
            try:
                return float(match.group())
            except ValueError:
                return None
    return None


def _normalise_percentage(value: float, unit: str) -> Optional[float]:
    if value <= 0:
        return None
    percent_units = {"%", "percent", "percentage", "pct"}
    if unit in percent_units:
        if value > 1:
            value = value / 100.0
    elif value > 1:
        value = value / 100.0
    return max(0.0, min(value, 1.0))


def _convert_to_metres(value: float, unit: str) -> Optional[float]:
    if value <= 0:
        return None
    metre_units = {"m", "metre", "metres", "meter", "meters"}
    if not unit or unit in metre_units:
        return value
    return None


__all__ = ["ResolvedZone", "calculate_buildable", "load_layers_for_zone"]
