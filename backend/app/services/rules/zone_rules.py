"""Zone rules query service for Site Acquisition.

Queries the RefRule database table for zoning parameters (plot ratio, height limits,
site coverage) using the same data source as CAD Upload and compliance checking.

This replaces the hardcoded mock values in URAIntegrationService.get_zoning_info().
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rkp import RefRule

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


@dataclass
class ZoningRulesResult:
    """Result of zoning rules query."""

    plot_ratio: Optional[float] = None
    building_height_limit_m: Optional[float] = None
    site_coverage_pct: Optional[float] = None
    zone_code: Optional[str] = None
    zone_description: Optional[str] = None
    source_reference: str = "RefRule Database"
    rules_found: int = 0

    @property
    def has_data(self) -> bool:
        """Check if any zoning data was found."""
        return self.plot_ratio is not None or self.building_height_limit_m is not None


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

    # Query RefRule for zoning rules
    stmt = (
        select(RefRule)
        .where(RefRule.jurisdiction == jurisdiction)
        .where(RefRule.topic == "zoning")
        .where(RefRule.review_status == "approved")
        .where(RefRule.is_published.is_(True))
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

    if not applicable_rules:
        logger.info(
            "No zoning rules found for zone",
            zone_code=normalized_zone,
            jurisdiction=jurisdiction,
            total_rules_checked=len(all_rules),
        )
        return ZoningRulesResult(
            zone_code=normalized_zone,
            zone_description=_extract_zone_description(normalized_zone),
            source_reference=f"No RefRule data for {normalized_zone}",
            rules_found=0,
        )

    # Extract parameter values
    plot_ratio: Optional[float] = None
    building_height_limit_m: Optional[float] = None
    site_coverage_pct: Optional[float] = None

    for rule in applicable_rules:
        try:
            if rule.parameter_key == "zoning.max_far":
                plot_ratio = float(rule.value)
            elif rule.parameter_key == "zoning.max_building_height_m":
                building_height_limit_m = float(rule.value)
            elif rule.parameter_key == "zoning.site_coverage.max_percent":
                site_coverage_pct = float(rule.value)
        except (ValueError, TypeError) as e:
            logger.warning(
                "Failed to parse rule value",
                parameter_key=rule.parameter_key,
                value=rule.value,
                error=str(e),
            )

    logger.info(
        "Zoning rules retrieved from RefRule database",
        zone_code=normalized_zone,
        plot_ratio=plot_ratio,
        height_limit=building_height_limit_m,
        site_coverage=site_coverage_pct,
        rules_count=len(applicable_rules),
    )

    return ZoningRulesResult(
        plot_ratio=plot_ratio,
        building_height_limit_m=building_height_limit_m,
        site_coverage_pct=site_coverage_pct,
        zone_code=normalized_zone,
        zone_description=_extract_zone_description(normalized_zone),
        source_reference=f"URA Zoning Rules ({jurisdiction} RefRule Database)",
        rules_found=len(applicable_rules),
    )
