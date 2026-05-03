"""Zone rules query service for Site Acquisition.

Queries the RefRule database table for zoning parameters (plot ratio, height limits,
site coverage) using the same data source as CAD Upload and compliance checking.

This replaces the hardcoded mock values in URAIntegrationService.get_zoning_info().
"""

from __future__ import annotations

from dataclasses import dataclass
from collections import Counter
from typing import Any, Optional

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rkp import RefRule, RefZoningLayer

logger = structlog.get_logger(__name__)

# Zone code mapping from URA short codes to RefRule format
ZONE_CODE_MAPPING = {
    # URA short codes → RefRule applicability zone_code
    "c": "SG:commercial",
    "c1": "SG:commercial",
    "commercial": "SG:commercial",
    "r": "SG:residential",
    "r1": "SG:residential",
    "residential": "SG:residential",
    "b": "SG:industrial",
    "b1": "SG:industrial",
    "b2": "SG:industrial",
    "industrial": "SG:industrial",
    "business": "SG:industrial",
    "mu": "SG:mixed_use",
    "mixed": "SG:mixed_use",
    "mixed_use": "SG:mixed_use",
    "mixed-use": "SG:mixed_use",
    "bp": "SG:business_park",
    "business_park": "SG:business_park",
    "business-park": "SG:business_park",
}

# Default fallback zone for unknown codes
DEFAULT_ZONE = "SG:residential"


SINGAPORE_RULE_SOURCE_REGISTRY: dict[str, list[dict[str, Any]]] = {
    "land_use": [
        {
            "authority": "URA",
            "title": "Master Plan land use layer",
            "url": "https://data.gov.sg/dataset/master-plan-2019-land-use-layer",
        },
        {
            "authority": "URA",
            "title": "Master Plan Written Statement",
            "url": "https://www.ura.gov.sg/Corporate/Planning/Master-Plan",
        },
    ],
    "plot_ratio": [
        {
            "authority": "URA",
            "title": "Master Plan GPR / intensity controls",
            "url": "https://data.gov.sg/dataset/master-plan-2019-land-use-layer",
        }
    ],
    "building_height_limit_m": [
        {
            "authority": "URA",
            "title": "Development Control Guidelines and control plans",
            "url": "https://www.ura.gov.sg/Corporate/Guidelines/Development-Control",
            "configured_values_by_zone": {
                # First normalized Singapore height-control fixture. This is
                # deliberately scoped to the current B1/industrial demo path so
                # broader zones remain source-review pending until ingested.
                "SG:industrial": "80",
            },
            "unit": "m",
        }
    ],
    "site_coverage_pct": [
        {
            "authority": "URA",
            "title": "Development Control Guidelines",
            "url": "https://www.ura.gov.sg/Corporate/Guidelines/Development-Control",
        }
    ],
    "setbacks": [
        {
            "authority": "URA",
            "title": "Development Control Guidelines - building setback controls",
            "url": "https://www.ura.gov.sg/Corporate/Guidelines/Development-Control",
            "configured_values_by_zone": {
                # First normalized Singapore setback fixture. Scoped to the
                # current B1/industrial demo path until more zone/use-specific
                # official controls are ingested and reviewed.
                "SG:industrial": {
                    "front": "7.5",
                    "rear": "7.5",
                    "side": "3",
                },
            },
            "unit": "m",
        }
    ],
    "step_backs": [
        {
            "authority": "URA",
            "title": "Development Control Guidelines - building edge / storey controls",
            "url": "https://www.ura.gov.sg/Corporate/Guidelines/Development-Control",
        }
    ],
    "air_rights_note": [
        {
            "authority": "URA/CAAS",
            "title": "Height control and aviation-related clearance sources",
            "url": "https://www.ura.gov.sg/Corporate/Guidelines/Development-Control",
        }
    ],
}


RESOLVABLE_FIELDS = (
    "land_use",
    "plot_ratio",
    "building_height_limit_m",
    "site_coverage_pct",
    "setbacks",
    "step_backs",
    "air_rights_note",
)


@dataclass
class ZoningRulesResult:
    """Result of zoning rules query."""

    plot_ratio: Optional[float] = None
    building_height_limit_m: Optional[float] = None
    site_coverage_pct: Optional[float] = None
    setback_front_m: Optional[float] = None
    setback_rear_m: Optional[float] = None
    setback_side_m: Optional[float] = None
    step_backs: list[dict[str, float]] | None = None
    air_rights_note: Optional[str] = None
    zone_code: Optional[str] = None
    zone_description: Optional[str] = None
    source_reference: str = "RefRule Database"
    rules_found: int = 0
    rule_corpus_status: dict[str, object] | None = None

    @property
    def has_data(self) -> bool:
        """Check if any zoning data was found."""
        return any(
            value is not None
            for value in (
                self.plot_ratio,
                self.building_height_limit_m,
                self.site_coverage_pct,
                self.setback_front_m,
                self.setback_rear_m,
                self.setback_side_m,
                self.air_rights_note,
            )
        ) or bool(self.step_backs)


def normalize_zone_code(
    zone_code: Optional[str], jurisdiction: str = "SG"
) -> Optional[str]:
    """Normalize zone code to RefRule applicability format.

    Args:
        zone_code: Raw zone code from URA service (e.g., "C", "R", "B1", "Commercial")
        jurisdiction: Jurisdiction code (default "SG")

    Returns:
        Normalized zone code (e.g., "SG:commercial") or None
    """
    if not zone_code:
        return None

    # Clean and lowercase
    clean_code = zone_code.strip().lower()

    # Check mapping
    if clean_code in ZONE_CODE_MAPPING:
        return ZONE_CODE_MAPPING[clean_code]

    # If already in correct format (e.g., "SG:residential")
    if clean_code.startswith(f"{jurisdiction.lower()}:"):
        return clean_code

    # Try to construct from jurisdiction + code
    constructed = f"{jurisdiction}:{clean_code}".lower()
    return constructed


def _extract_zone_description(zone_code: Optional[str]) -> Optional[str]:
    """Extract human-readable description from zone code."""
    if not zone_code:
        return None

    # Extract the part after jurisdiction prefix
    if ":" in zone_code:
        zone_type = zone_code.split(":", 1)[1]
    else:
        zone_type = zone_code

    # Format as title case with spaces
    return zone_type.replace("_", " ").title()


def _zone_aliases(zone_code: str, raw_zone_code: Optional[str]) -> set[str]:
    aliases = {zone_code.lower()}
    if ":" in zone_code:
        aliases.add(zone_code.split(":", 1)[1].lower())
    if raw_zone_code:
        raw = raw_zone_code.strip().lower()
        if raw:
            aliases.add(raw)
            normalized_raw = normalize_zone_code(raw_zone_code)
            if normalized_raw:
                aliases.add(normalized_raw.lower())
                if ":" in normalized_raw:
                    aliases.add(normalized_raw.split(":", 1)[1].lower())
    return aliases


def _coerce_attr_float(
    attributes: dict[str, object], keys: tuple[str, ...]
) -> Optional[float]:
    lowered = {str(key).lower(): value for key, value in attributes.items()}
    for key in keys:
        value = lowered.get(key.lower())
        if value in (None, ""):
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def _coerce_attr_string(
    attributes: dict[str, object], keys: tuple[str, ...]
) -> Optional[str]:
    lowered = {str(key).lower(): value for key, value in attributes.items()}
    for key in keys:
        value = lowered.get(key.lower())
        if value in (None, ""):
            continue
        return str(value)
    return None


async def _get_zoning_layer_for_zone(
    session: AsyncSession,
    *,
    normalized_zone: str,
    raw_zone_code: Optional[str],
    jurisdiction: str,
) -> RefZoningLayer | None:
    aliases = _zone_aliases(normalized_zone, raw_zone_code)
    stmt = select(RefZoningLayer).where(RefZoningLayer.jurisdiction == jurisdiction)
    result = await session.execute(stmt)
    for layer in result.scalars().all():
        layer_zone = (layer.zone_code or "").strip().lower()
        if layer_zone and layer_zone in aliases:
            return layer
        attributes = layer.attributes if isinstance(layer.attributes, dict) else {}
        attr_zone = _coerce_attr_string(
            attributes,
            ("zone_code", "zoneCode", "LU_DESC", "land_use", "landUse"),
        )
        if attr_zone and attr_zone.strip().lower() in aliases:
            return layer
    return None


def _official_source_gaps(
    jurisdiction: str,
    unresolved_fields: list[str],
) -> list[dict[str, object]]:
    if jurisdiction != "SG":
        return []
    return [
        {
            "field": field,
            "reason": "not_resolved_from_current_registry",
            "candidate_sources": SINGAPORE_RULE_SOURCE_REGISTRY.get(field, []),
        }
        for field in unresolved_fields
    ]


async def get_zoning_rules_for_zone(
    session: AsyncSession,
    zone_code: Optional[str],
    jurisdiction: str = "SG",
) -> ZoningRulesResult:
    """Query RefRule database for zoning parameters.

    Args:
        session: Database session
        zone_code: Zone code (e.g., "C", "R", "SG:commercial", "residential")
        jurisdiction: Jurisdiction code (default "SG")

    Returns:
        ZoningRulesResult with plot_ratio, height_limit, site_coverage, and source info
    """
    normalized_zone = normalize_zone_code(zone_code, jurisdiction)

    if not normalized_zone:
        logger.warning("No zone code provided for rules lookup")
        return ZoningRulesResult(
            source_reference="No zone code provided",
        )

    zoning_layer = await _get_zoning_layer_for_zone(
        session,
        normalized_zone=normalized_zone,
        raw_zone_code=zone_code,
        jurisdiction=jurisdiction,
    )
    zoning_layer_attributes = (
        zoning_layer.attributes
        if zoning_layer and isinstance(zoning_layer.attributes, dict)
        else {}
    )

    zoning_layer_plot_ratio = _coerce_attr_float(
        zoning_layer_attributes,
        ("gpr", "GPR", "plot_ratio", "plotRatio", "gross_plot_ratio", "max_far"),
    )
    zoning_layer_height_limit = _coerce_attr_float(
        zoning_layer_attributes,
        (
            "height_m",
            "heightLimitM",
            "building_height_limit_m",
            "max_building_height_m",
        ),
    )
    zoning_layer_site_coverage = _coerce_attr_float(
        zoning_layer_attributes,
        ("site_coverage_pct", "siteCoveragePct", "max_site_coverage_pct"),
    )
    zoning_layer_zone_description = _coerce_attr_string(
        zoning_layer_attributes,
        ("LU_DESC", "land_use", "landUse", "zone_description", "zoneDescription"),
    )

    # Query RefRule for zoning/building rules.
    stmt = (
        select(RefRule)
        .where(RefRule.jurisdiction == jurisdiction)
        .where(RefRule.topic.in_(("zoning", "building")))
    )

    result = await session.execute(stmt)
    all_rules = result.scalars().all()

    # Filter rules applicable to this zone
    applicable_rules = []
    for rule in all_rules:
        if rule.applicability and isinstance(rule.applicability, dict):
            rule_zone_code = rule.applicability.get("zone_code")
            if rule_zone_code and rule_zone_code.lower() == normalized_zone.lower():
                applicable_rules.append(rule)
    approved_rules = [
        rule
        for rule in applicable_rules
        if rule.review_status == "approved" and bool(rule.is_published)
    ]
    review_counts = Counter(
        (rule.review_status or "unknown") for rule in applicable_rules
    )
    published_count = sum(1 for rule in applicable_rules if bool(rule.is_published))
    traceable_count = sum(
        1
        for rule in approved_rules
        if any(
            (rule.source_id, rule.document_id, isinstance(rule.source_provenance, dict))
        )
    )
    # Extract parameter values
    plot_ratio: Optional[float] = zoning_layer_plot_ratio
    building_height_limit_m: Optional[float] = zoning_layer_height_limit
    site_coverage_pct: Optional[float] = zoning_layer_site_coverage
    setback_front_m: Optional[float] = None
    setback_rear_m: Optional[float] = None
    setback_side_m: Optional[float] = None
    step_backs: list[dict[str, float]] = []
    air_rights_note: Optional[str] = None
    resolved_by: dict[str, str] = {}

    if zoning_layer_zone_description:
        resolved_by["land_use"] = "ref_zoning_layer"
    if zoning_layer_plot_ratio is not None:
        resolved_by["plot_ratio"] = "ref_zoning_layer"
    if zoning_layer_height_limit is not None:
        resolved_by["building_height_limit_m"] = "ref_zoning_layer"
    if zoning_layer_site_coverage is not None:
        resolved_by["site_coverage_pct"] = "ref_zoning_layer"

    for rule in approved_rules:
        parameter_key = (rule.parameter_key or "").lower()
        try:
            if parameter_key == "zoning.max_far":
                plot_ratio = float(rule.value)
                resolved_by["plot_ratio"] = "ref_rule"
            elif parameter_key == "zoning.max_building_height_m":
                building_height_limit_m = float(rule.value)
                resolved_by["building_height_limit_m"] = "ref_rule"
            elif parameter_key == "zoning.site_coverage.max_percent":
                site_coverage_pct = float(rule.value)
                resolved_by["site_coverage_pct"] = "ref_rule"
            elif parameter_key == "zoning.setback.front_min_m":
                setback_front_m = float(rule.value)
                resolved_by["setbacks"] = "ref_rule"
            elif parameter_key == "zoning.setback.rear_min_m":
                setback_rear_m = float(rule.value)
                resolved_by["setbacks"] = "ref_rule"
            elif parameter_key == "zoning.setback.side_min_m":
                setback_side_m = float(rule.value)
                resolved_by["setbacks"] = "ref_rule"
            elif parameter_key.startswith("zoning.stepback."):
                applicability = (
                    rule.applicability if isinstance(rule.applicability, dict) else {}
                )
                level_value = applicability.get("level") or applicability.get("storey")
                if level_value is None:
                    level = len(step_backs) + 1
                else:
                    level = int(level_value)
                step_backs.append({"level": float(level), "depth_m": float(rule.value)})
                resolved_by["step_backs"] = "ref_rule"
            elif parameter_key.startswith("zoning.air_rights."):
                air_rights_note = str(rule.value)
                resolved_by["air_rights_note"] = "ref_rule"
        except (ValueError, TypeError) as e:
            logger.warning(
                "Failed to parse rule value",
                parameter_key=rule.parameter_key,
                value=rule.value,
                error=str(e),
            )

    if not applicable_rules and zoning_layer is None:
        logger.info(
            "No configured rule data resolved for zone",
            zone_code=normalized_zone,
            jurisdiction=jurisdiction,
            total_rules_checked=len(all_rules),
        )

    if (
        not any(
            value is not None
            for value in (
                plot_ratio,
                building_height_limit_m,
                site_coverage_pct,
                setback_front_m,
                setback_rear_m,
                setback_side_m,
                air_rights_note,
            )
        )
        and not step_backs
    ):
        coverage_state = "missing"
        confidence = "low"
    elif not approved_rules and applicable_rules:
        coverage_state = "review_pending"
        confidence = "low"
    elif set(RESOLVABLE_FIELDS).difference(resolved_by):
        coverage_state = "partial"
        confidence = "medium"
    elif traceable_count < len(approved_rules):
        coverage_state = "approved"
        confidence = "medium"
    else:
        coverage_state = "approved"
        confidence = "high"

    unresolved_fields = [
        field for field in RESOLVABLE_FIELDS if field not in resolved_by
    ]
    rule_corpus_status = {
        "zone_code": normalized_zone,
        "coverage_state": coverage_state,
        "confidence": confidence,
        "counts": {
            "applicable": len(applicable_rules),
            "approved": len(approved_rules),
            "published": published_count,
            "traceable": traceable_count,
            "needs_review": review_counts.get("needs_review", 0),
            "rejected": review_counts.get("rejected", 0),
            "zoning_layers": 1 if zoning_layer else 0,
        },
        "applied_rule_ids": [rule.id for rule in approved_rules if rule.id is not None],
        "applied_zoning_layer_id": zoning_layer.id if zoning_layer else None,
        "resolved_by": resolved_by,
        "unresolved_fields": unresolved_fields,
        "official_source_gaps": _official_source_gaps(jurisdiction, unresolved_fields),
    }

    logger.info(
        "Zoning rules retrieved from configured registry",
        zone_code=normalized_zone,
        plot_ratio=plot_ratio,
        height_limit=building_height_limit_m,
        site_coverage=site_coverage_pct,
        rules_count=len(applicable_rules),
        zoning_layer_id=zoning_layer.id if zoning_layer else None,
    )

    return ZoningRulesResult(
        plot_ratio=plot_ratio,
        building_height_limit_m=building_height_limit_m,
        site_coverage_pct=site_coverage_pct,
        setback_front_m=setback_front_m,
        setback_rear_m=setback_rear_m,
        setback_side_m=setback_side_m,
        step_backs=step_backs,
        air_rights_note=air_rights_note,
        zone_code=normalized_zone,
        zone_description=(
            zoning_layer_zone_description or _extract_zone_description(normalized_zone)
        ),
        source_reference=(
            f"{jurisdiction} Rule Registry (RefRule"
            + (" + zoning layers" if zoning_layer else "")
            + ")"
        ),
        rules_found=len(approved_rules),
        rule_corpus_status=rule_corpus_status,
    )
