"""Buildable screening calculations."""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Iterable, List, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rkp import RefParcel, RefRule, RefZoningLayer
from app.schemas.buildable import (
    BuildableCalculation,
    BuildableDefaults,
    BuildableMetrics,
    BuildableRule,
    BuildableRuleProvenance,
    ZoneSource,
)


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
) -> BuildableCalculation:
    """Compute buildable metrics and surface applicable rules."""

    attributes = _merge_layer_attributes(resolved.zone_layers)
    area_m2 = _parcel_area(resolved.parcel) or defaults.site_area_m2
    plot_ratio = _extract_plot_ratio(attributes) or defaults.plot_ratio
    site_coverage = _extract_site_coverage(attributes) or defaults.site_coverage
    site_coverage = max(0.0, min(site_coverage, 1.0))
    gfa_cap = _round_half_up(area_m2 * plot_ratio) if area_m2 else 0
    footprint = _round_half_up(area_m2 * site_coverage) if area_m2 else 0

    storey_limit = _extract_storey_limit(attributes)
    height_limit = _extract_height_limit(attributes)
    floors_from_height = _floors_from_height(height_limit, defaults.floor_height_m)
    floors_from_ratio = _floors_from_ratio(gfa_cap, footprint)

    floor_candidates = [
        value
        for value in (storey_limit, floors_from_height, floors_from_ratio)
        if value is not None and value > 0
    ]
    floors_max = min(floor_candidates) if floor_candidates else 0
    nsa_est = _round_half_up(gfa_cap * defaults.efficiency_factor) if gfa_cap else 0

    zone_source = _build_zone_source(resolved)
    rules = await _load_rules_for_zone(session, resolved.zone_code)

    metrics = BuildableMetrics(
        gfa_cap_m2=gfa_cap,
        floors_max=floors_max,
        footprint_m2=footprint,
        nsa_est_m2=nsa_est,
    )

    return BuildableCalculation(metrics=metrics, zone_source=zone_source, rules=rules)


async def _load_rules_for_zone(session: AsyncSession, zone_code: Optional[str]) -> List[BuildableRule]:
    if not zone_code:
        return []

    result = await session.execute(select(RefRule))
    rules: List[BuildableRule] = []
    for record in result.scalars().all():
        if not _zone_matches(record.applicability, zone_code):
            continue
        provenance = BuildableRuleProvenance(
            rule_id=record.id,
            clause_ref=record.clause_ref,
            document_id=record.document_id,
            seed_tag=_determine_seed_tag(record),
        )
        rules.append(
            BuildableRule(
                id=record.id,
                parameter_key=record.parameter_key,
                operator=record.operator,
                value=record.value,
                unit=record.unit,
                provenance=provenance,
            )
        )
    rules.sort(key=lambda item: (item.parameter_key, item.id))
    return rules


def _determine_seed_tag(rule: RefRule) -> Optional[str]:
    provenance = rule.source_provenance if isinstance(rule.source_provenance, dict) else None
    if provenance and isinstance(provenance.get("seed_tag"), str):
        return provenance["seed_tag"]
    return rule.topic


def _merge_layer_attributes(layers: Sequence[RefZoningLayer]) -> Dict[str, Any]:
    merged: Dict[str, Any] = {}
    for layer in layers:
        if layer.attributes and isinstance(layer.attributes, dict):
            merged.update(layer.attributes)
    return merged


def _parcel_area(parcel: Optional[RefParcel]) -> Optional[float]:
    if parcel is None or parcel.area_m2 is None:
        return None
    try:
        return float(parcel.area_m2)
    except (TypeError, ValueError):
        return None


def _extract_plot_ratio(attributes: Dict[str, Any]) -> Optional[float]:
    return _first_positive(attributes, [
        "plot_ratio",
        "gross_plot_ratio",
        "max_plot_ratio",
        "floor_area_ratio",
        "far",
    ])


def _extract_site_coverage(attributes: Dict[str, Any]) -> Optional[float]:
    coverage = _first_positive(attributes, [
        "site_coverage",
        "site_coverage_ratio",
        "site_coverage_fraction",
        "site_coverage_pct",
        "site_coverage_percent",
    ])
    if coverage is None:
        return None
    if coverage > 1:
        coverage = coverage / 100.0
    return coverage


def _extract_storey_limit(attributes: Dict[str, Any]) -> Optional[int]:
    value = _first_positive(attributes, [
        "floors_max",
        "max_storeys",
        "storey_limit",
        "storeys",
        "max_floors",
    ])
    return int(value) if value else None


def _extract_height_limit(attributes: Dict[str, Any]) -> Optional[float]:
    return _first_positive(attributes, [
        "height_m",
        "max_height_m",
        "height_limit_m",
        "building_height_m",
    ])


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


def _floors_from_height(height_limit: Optional[float], floor_height: float) -> Optional[int]:
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
    kind = "parcel" if resolved.parcel else ("geometry" if resolved.input_kind == "geometry" else "unknown")
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


__all__ = ["ResolvedZone", "calculate_buildable"]
