"""Toronto Zoning By-law and Ontario Building Code compliance utilities.

This module provides compliance validation functions based on Toronto's:
- City of Toronto Zoning By-law 569-2013
- City of Toronto Official Plan
- Ontario Building Code (OBC)
- Toronto Green Standard (TGS)
"""

from decimal import Decimal
from typing import Any, Dict

from backend._compat.datetime import utcnow

from app.models.toronto_property import TorontoComplianceStatus, TorontoProperty
from app.models.rkp import RefRule
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# NOTE: Toronto zoning and OBC rules are stored in the RefRule database table
# This allows jurisdiction-agnostic calculations via services/buildable.py
# Rules are queried dynamically based on jurisdiction and zone_code
#
# To populate rules, use: python -m scripts.seed_toronto_rules


async def check_zoning_compliance(
    property: TorontoProperty, session: AsyncSession
) -> Dict[str, Any]:
    """
    Check City of Toronto Zoning By-law 569-2013 compliance.

    Validates against zoning requirements including:
    - Floor Space Index (FSI) limits
    - Building height limits
    - Lot coverage limits
    - Setback requirements
    - Angular plane requirements

    Args:
        property: TorontoProperty model instance
        session: AsyncSession for database queries

    Returns:
        Dict containing:
        - status: TorontoComplianceStatus (PASSED, FAILED, WARNING, PENDING)
        - violations: List of violation descriptions
        - warnings: List of warning messages
        - iz_requirements: Inclusionary Zoning requirements if applicable
        - rules_applied: The zoning rules that were checked
    """
    violations: list[str] = []
    warnings: list[str] = []
    iz_requirements: Dict[str, Any] = {}

    if not property.zoning:
        return {
            "status": TorontoComplianceStatus.PENDING,
            "message": "Zoning not specified",
            "violations": [],
            "warnings": ["Property zoning must be specified for compliance check"],
            "iz_requirements": {},
            "rules_applied": {},
        }

    zoning_str = (
        property.zoning.value if hasattr(property.zoning, "value") else property.zoning
    )
    zone_code = f"TOR:{zoning_str}"

    # Query RefRule database for Toronto zoning rules
    stmt = (
        select(RefRule)
        .where(RefRule.jurisdiction == "TOR")
        .where(RefRule.authority == "CityPlanning")
        .where(RefRule.topic == "zoning")
        .where(RefRule.review_status == "approved")
        .where(RefRule.is_published)
    )
    result = await session.execute(stmt)
    all_rules = result.scalars().all()

    # Filter rules applicable to this zone
    applicable_rules = []
    for rule in all_rules:
        if rule.applicability and isinstance(rule.applicability, dict):
            rule_zone_code = rule.applicability.get("zone_code")
            if rule_zone_code == zone_code:
                applicable_rules.append(rule)

    if not applicable_rules:
        return {
            "status": TorontoComplianceStatus.WARNING,
            "message": f"No zoning rules found for zone: {zoning_str}",
            "violations": [],
            "warnings": [f"No zoning rules found in database for zone {zone_code}"],
            "iz_requirements": {},
            "rules_applied": {},
        }

    # Parse rules into dict for easier checking
    rules_dict: Dict[str, Any] = {}
    for rule in applicable_rules:
        if rule.parameter_key == "zoning.max_fsi":
            rules_dict["max_fsi"] = Decimal(rule.value)
        elif rule.parameter_key == "zoning.max_building_height_m":
            rules_dict["max_height_m"] = Decimal(rule.value)
        elif rule.parameter_key == "zoning.max_lot_coverage":
            value_str = str(rule.value).replace("%", "")
            rules_dict["max_lot_coverage"] = Decimal(value_str)
        elif rule.parameter_key == "zoning.min_setback_front_m":
            rules_dict["min_setback_front"] = Decimal(rule.value)
        elif rule.parameter_key == "zoning.min_setback_side_m":
            rules_dict["min_setback_side"] = Decimal(rule.value)
        elif rule.parameter_key == "zoning.min_setback_rear_m":
            rules_dict["min_setback_rear"] = Decimal(rule.value)

    # Check FSI (Floor Space Index)
    if property.floor_space_index and "max_fsi" in rules_dict:
        max_fsi = rules_dict["max_fsi"]
        if property.floor_space_index > max_fsi:
            violations.append(
                f"FSI {property.floor_space_index} exceeds maximum {max_fsi} for {zoning_str} zone"
            )

    # Check building height
    if property.building_height_m and "max_height_m" in rules_dict:
        max_height = rules_dict["max_height_m"]
        if property.building_height_m > max_height:
            violations.append(
                f"Building height {property.building_height_m}m exceeds maximum "
                f"{max_height}m for {zoning_str} zone"
            )

    # Check lot coverage
    if property.lot_coverage_percent and "max_lot_coverage" in rules_dict:
        max_coverage = rules_dict["max_lot_coverage"]
        if property.lot_coverage_percent > max_coverage:
            violations.append(
                f"Lot coverage {property.lot_coverage_percent}% exceeds maximum "
                f"{max_coverage}% for {zoning_str} zone"
            )

    # Check setbacks
    if property.setback_front_m and "min_setback_front" in rules_dict:
        min_front = rules_dict["min_setback_front"]
        if property.setback_front_m < min_front:
            violations.append(
                f"Front setback {property.setback_front_m}m is less than minimum "
                f"{min_front}m for {zoning_str} zone"
            )

    # Calculate actual FSI if GFA is provided
    if (
        property.gross_floor_area_sqm
        and property.lot_area_sqm
        and property.lot_area_sqm > 0
    ):
        actual_fsi = property.gross_floor_area_sqm / property.lot_area_sqm
        if "max_fsi" in rules_dict:
            max_fsi = rules_dict["max_fsi"]
            if actual_fsi > max_fsi:
                violations.append(
                    f"Actual FSI {actual_fsi:.2f} (GFA/lot area) exceeds "
                    f"maximum {max_fsi} for {zoning_str} zone"
                )

    # Check Inclusionary Zoning requirements
    if property.iz_area:
        iz_requirements["in_iz_area"] = True
        if property.iz_affordable_percentage:
            iz_requirements["affordable_percentage"] = float(
                property.iz_affordable_percentage
            )
            warnings.append(
                f"Inclusionary Zoning applies: {property.iz_affordable_percentage}% "
                "of units must be affordable housing"
            )
        if property.iz_affordable_units_required:
            iz_requirements["affordable_units"] = property.iz_affordable_units_required
            warnings.append(
                f"{property.iz_affordable_units_required} affordable units required"
            )

    # Determine status
    if violations:
        status = TorontoComplianceStatus.FAILED
    elif warnings:
        status = TorontoComplianceStatus.WARNING
    else:
        status = TorontoComplianceStatus.PASSED

    return {
        "status": status,
        "violations": violations,
        "warnings": warnings,
        "iz_requirements": iz_requirements,
        "rules_applied": {
            k: str(v) if isinstance(v, Decimal) else v for k, v in rules_dict.items()
        },
    }


async def check_building_code_compliance(
    property: TorontoProperty, session: AsyncSession
) -> Dict[str, Any]:
    """
    Check Ontario Building Code (OBC) compliance for a Toronto property.

    Validates against building code including:
    - Fire and life safety
    - Accessibility (AODA)
    - Energy efficiency
    - Toronto Green Standard (TGS)

    Args:
        property: TorontoProperty model instance
        session: AsyncSession for database queries

    Returns:
        Dict containing:
        - status: TorontoComplianceStatus
        - violations: List of violation descriptions
        - warnings: List of warning messages
        - recommendations: List of recommended actions
        - tgs_requirements: Toronto Green Standard requirements
    """
    violations: list[str] = []
    warnings: list[str] = []
    recommendations: list[str] = []
    tgs_requirements: Dict[str, Any] = {}

    if not property.zoning:
        return {
            "status": TorontoComplianceStatus.WARNING,
            "message": "Zoning not specified",
            "violations": [],
            "warnings": ["Property zoning must be specified for building code check"],
            "recommendations": [],
            "tgs_requirements": {},
        }

    zoning_str = (
        property.zoning.value if hasattr(property.zoning, "value") else property.zoning
    )
    zone_code = f"TOR:{zoning_str}"

    # Query RefRule database for OBC rules
    stmt = (
        select(RefRule)
        .where(RefRule.jurisdiction == "TOR")
        .where(RefRule.authority == "OBC")
        .where(RefRule.topic == "building")
        .where(RefRule.review_status == "approved")
        .where(RefRule.is_published)
    )
    result = await session.execute(stmt)
    all_rules = result.scalars().all()

    applicable_rules = []
    for rule in all_rules:
        if rule.applicability and isinstance(rule.applicability, dict):
            rule_zone_code = rule.applicability.get("zone_code")
            if rule_zone_code == zone_code or rule_zone_code is None:
                applicable_rules.append(rule)

    requirements: Dict[str, Any] = {}
    for rule in applicable_rules:
        if rule.parameter_key == "building.energy.tier1_required":
            requirements["tgs_tier1_required"] = rule.value == "true"

    # Toronto Green Standard requirements
    tgs_requirements["tier1_mandatory"] = True
    tgs_requirements["tier2_incentives"] = True
    recommendations.append(
        "Toronto Green Standard Tier 1 is mandatory for new developments"
    )
    recommendations.append(
        "TGS Tier 2-4 available for development charge refunds (up to 25%)"
    )

    if property.tgs_tier:
        tgs_requirements["current_tier"] = property.tgs_tier
        if property.tgs_tier in ["Tier 2", "Tier 3", "Tier 4"]:
            recommendations.append(
                f"Property targeting {property.tgs_tier} - eligible for DC refund"
            )

    # Check for environmental requirements
    if property.environmental_assessment_required:
        if not property.phase_1_esa_complete:
            warnings.append(
                "Phase 1 Environmental Site Assessment required before building permit"
            )
        if not property.record_of_site_condition:
            warnings.append("Record of Site Condition (RSC) may be required from MECP")

    # Heritage considerations
    if property.is_heritage_designated:
        warnings.append(
            f"Property is heritage designated ({property.heritage_designation_type}). "
            "Heritage permit required before alterations."
        )
        recommendations.append(
            "Consult with City of Toronto Heritage Preservation Services"
        )

    # Add general OBC recommendations
    recommendations.append(
        "Building permit required from Toronto Building before construction"
    )
    recommendations.append(
        "AODA accessibility requirements apply to all new construction"
    )
    recommendations.append(
        "Typical permit review timeline: 15-30 business days (residential)"
    )

    # Determine status
    if violations:
        status = TorontoComplianceStatus.FAILED
    elif warnings:
        status = TorontoComplianceStatus.WARNING
    else:
        status = TorontoComplianceStatus.PASSED

    return {
        "status": status,
        "violations": violations,
        "warnings": warnings,
        "recommendations": recommendations,
        "tgs_requirements": tgs_requirements,
        "requirements_applied": requirements,
    }


async def calculate_gfa_utilization_async(
    property: TorontoProperty, session: AsyncSession | None = None
) -> Dict[str, Any]:
    """
    Calculate GFA utilization for Toronto property.

    Toronto uses:
    - Floor Space Index (FSI) instead of FAR
    - sqm as standard metric unit
    - Inclusionary Zoning requirements in protected areas

    Args:
        property: TorontoProperty model instance
        session: AsyncSession for database queries (optional)

    Returns:
        Dict containing development potential metrics
    """
    from app.services.jurisdictions import get_engineering_defaults

    if not property.lot_area_sqm or not property.max_fsi:
        return {
            "error": "Lot area and maximum FSI required for GFA calculation",
            "max_gfa_sqm": None,
            "current_gfa_sqm": None,
            "remaining_gfa_sqm": None,
            "utilization_percentage": None,
            "potential_units": None,
            "recommendations": [
                "Specify lot area and FSI to calculate development potential"
            ],
        }

    # Get Toronto engineering defaults
    eng_defaults = get_engineering_defaults("TOR", "residential")
    efficiency_ratio = eng_defaults.get("efficiency_ratio", 0.85)

    lot_area = float(property.lot_area_sqm)
    max_fsi = float(property.max_fsi)

    max_gfa_sqm = lot_area * max_fsi
    max_gfa_sqft = max_gfa_sqm * 10.7639  # Convert to sqft

    current_gfa_sqm = (
        float(property.gross_floor_area_sqm) if property.gross_floor_area_sqm else 0.0
    )
    remaining_gfa_sqm = max_gfa_sqm - current_gfa_sqm
    utilization_pct = (current_gfa_sqm / max_gfa_sqm * 100) if max_gfa_sqm > 0 else 0.0

    # Net leasable area estimate
    net_leasable_sqm = max_gfa_sqm * efficiency_ratio

    # Estimate potential units
    potential_units = None
    zoning_value = (
        property.zoning.value if hasattr(property.zoning, "value") else property.zoning
    )
    residential_zones = ["RD", "RS", "RT", "RM", "RA", "RAC", "CR"]
    if zoning_value in residential_zones and remaining_gfa_sqm > 0:
        # Toronto average unit sizes
        if zoning_value == "RA":
            avg_unit_size = 70  # Apartments smaller
        elif zoning_value in ["RT", "RM"]:
            avg_unit_size = 90  # Townhouse/multiplex
        else:
            avg_unit_size = 120  # Houses
        potential_units = int(remaining_gfa_sqm / avg_unit_size)

    recommendations = []
    if remaining_gfa_sqm > 0:
        recommendations.append(
            f"Maximum GFA: {max_gfa_sqm:,.0f} sqm (FSI {max_fsi:.2f})"
        )
        recommendations.append(
            f"Current utilization is {utilization_pct:.1f}% of maximum allowed"
        )
        recommendations.append(
            f"Net Leasable Area estimate: {net_leasable_sqm:,.0f} sqm "
            f"({efficiency_ratio * 100:.0f}% efficiency)"
        )
        if potential_units:
            recommendations.append(
                f"Potential for approximately {potential_units} additional units"
            )
        if property.iz_area and potential_units:
            affordable_units = int(potential_units * 0.10)  # Assume 10% IZ
            recommendations.append(
                f"Note: ~{affordable_units} units may need to be affordable (IZ area)"
            )
    else:
        recommendations.append("Maximum GFA utilization reached")

    return {
        "max_gfa_sqm": float(max_gfa_sqm),
        "max_gfa_sqft": float(max_gfa_sqft),
        "current_gfa_sqm": float(current_gfa_sqm),
        "remaining_gfa_sqm": float(remaining_gfa_sqm),
        "utilization_percentage": float(utilization_pct),
        "potential_units": potential_units,
        "buildable_metrics": {
            "fsi": max_fsi,
            "net_leasable_sqm": net_leasable_sqm,
            "efficiency_ratio": efficiency_ratio,
            "floor_height_m": eng_defaults.get("floor_to_floor", 3.0),
        },
        "recommendations": recommendations,
    }


def calculate_gfa_utilization(property: TorontoProperty) -> Dict[str, Any]:
    """Synchronous wrapper for GFA utilization calculation."""
    from app.services.jurisdictions import get_engineering_defaults

    if not property.lot_area_sqm or not property.max_fsi:
        return {
            "error": "Lot area and maximum FSI required for GFA calculation",
            "max_gfa_sqm": None,
            "current_gfa_sqm": None,
            "remaining_gfa_sqm": None,
            "utilization_percentage": None,
            "potential_units": None,
            "recommendations": [
                "Specify lot area and FSI to calculate development potential"
            ],
        }

    eng_defaults = get_engineering_defaults("TOR", "residential")
    efficiency_ratio = eng_defaults.get("efficiency_ratio", 0.85)

    lot_area = float(property.lot_area_sqm)
    max_fsi = float(property.max_fsi)

    max_gfa_sqm = lot_area * max_fsi
    max_gfa_sqft = max_gfa_sqm * 10.7639

    current_gfa_sqm = (
        float(property.gross_floor_area_sqm) if property.gross_floor_area_sqm else 0.0
    )
    remaining_gfa_sqm = max_gfa_sqm - current_gfa_sqm
    utilization_pct = (current_gfa_sqm / max_gfa_sqm * 100) if max_gfa_sqm > 0 else 0.0

    net_leasable_sqm = max_gfa_sqm * efficiency_ratio

    potential_units = None
    zoning_value = (
        property.zoning.value if hasattr(property.zoning, "value") else property.zoning
    )
    residential_zones = ["RD", "RS", "RT", "RM", "RA", "RAC", "CR"]
    if zoning_value in residential_zones and remaining_gfa_sqm > 0:
        if zoning_value == "RA":
            avg_unit_size = 70
        elif zoning_value in ["RT", "RM"]:
            avg_unit_size = 90
        else:
            avg_unit_size = 120
        potential_units = int(remaining_gfa_sqm / avg_unit_size)

    recommendations = []
    if remaining_gfa_sqm > 0:
        recommendations.append(
            f"Maximum GFA: {max_gfa_sqm:,.0f} sqm (FSI {max_fsi:.2f})"
        )
        recommendations.append(
            f"Current utilization is {utilization_pct:.1f}% of maximum allowed"
        )
        recommendations.append(
            f"Net Leasable Area estimate: {net_leasable_sqm:,.0f} sqm "
            f"({efficiency_ratio * 100:.0f}% efficiency)"
        )
        if potential_units:
            recommendations.append(
                f"Potential for approximately {potential_units} additional units"
            )
    else:
        recommendations.append("Maximum GFA utilization reached")

    return {
        "max_gfa_sqm": float(max_gfa_sqm),
        "max_gfa_sqft": float(max_gfa_sqft),
        "current_gfa_sqm": float(current_gfa_sqm),
        "remaining_gfa_sqm": float(remaining_gfa_sqm),
        "utilization_percentage": float(utilization_pct),
        "potential_units": potential_units,
        "buildable_metrics": {
            "fsi": max_fsi,
            "net_leasable_sqm": net_leasable_sqm,
            "efficiency_ratio": efficiency_ratio,
            "floor_height_m": eng_defaults.get("floor_to_floor", 3.0),
        },
        "recommendations": recommendations,
    }


async def run_full_compliance_check(
    property: TorontoProperty, session: AsyncSession
) -> Dict[str, Any]:
    """
    Run complete zoning and building code compliance checks on a Toronto property.

    Args:
        property: TorontoProperty model instance
        session: AsyncSession for database queries

    Returns:
        Dict containing complete compliance report
    """
    zoning_check = await check_zoning_compliance(property, session)
    building_check = await check_building_code_compliance(property, session)
    gfa_calc = calculate_gfa_utilization(property)

    all_violations = zoning_check.get("violations", []) + building_check.get(
        "violations", []
    )
    all_warnings = zoning_check.get("warnings", []) + building_check.get("warnings", [])
    all_recommendations = building_check.get("recommendations", []) + gfa_calc.get(
        "recommendations", []
    )

    if all_violations:
        overall_status = TorontoComplianceStatus.FAILED
    elif all_warnings:
        overall_status = TorontoComplianceStatus.WARNING
    else:
        overall_status = TorontoComplianceStatus.PASSED

    compliance_notes = []
    if zoning_check.get("violations"):
        compliance_notes.extend([f"Zoning: {v}" for v in zoning_check["violations"]])
    if building_check.get("violations"):
        compliance_notes.extend([f"OBC: {v}" for v in building_check["violations"]])
    if all_warnings:
        compliance_notes.extend([f"Warning: {w}" for w in all_warnings])

    return {
        "overall_status": overall_status,
        "zoning_status": zoning_check["status"],
        "building_status": building_check["status"],
        "iz_requirements": zoning_check.get("iz_requirements", {}),
        "tgs_requirements": building_check.get("tgs_requirements", {}),
        "violations": all_violations,
        "warnings": all_warnings,
        "recommendations": all_recommendations,
        "compliance_notes": "\n".join(compliance_notes) if compliance_notes else None,
        "compliance_data": {
            "zoning_check": zoning_check,
            "building_check": building_check,
            "gfa_calculation": gfa_calc,
            "checked_at": utcnow().isoformat(),
        },
    }


async def update_property_compliance(
    property: TorontoProperty, session: AsyncSession
) -> TorontoProperty:
    """
    Run compliance checks and update the property model fields.

    Args:
        property: TorontoProperty model instance
        session: AsyncSession for database queries

    Returns:
        Updated property instance (not yet committed to database)
    """
    compliance_result = await run_full_compliance_check(property, session)

    zoning_status = compliance_result["zoning_status"]
    building_status = compliance_result["building_status"]
    property.zoning_compliance_status = (
        zoning_status.value if hasattr(zoning_status, "value") else zoning_status
    )
    property.building_code_compliance_status = (
        building_status.value if hasattr(building_status, "value") else building_status
    )
    property.compliance_notes = compliance_result["compliance_notes"]
    property.compliance_data = compliance_result["compliance_data"]
    property.compliance_last_checked = utcnow()

    # Update GFA utilization metrics
    gfa_calc = compliance_result["compliance_data"]["gfa_calculation"]
    if gfa_calc.get("max_gfa_sqm"):
        from decimal import Decimal

        property.max_developable_gfa_sqm = Decimal(str(gfa_calc["max_gfa_sqm"]))
        property.max_developable_gfa_sqft = Decimal(str(gfa_calc["max_gfa_sqft"]))
        property.gfa_utilization_percentage = Decimal(
            str(gfa_calc["utilization_percentage"])
        )
        property.potential_additional_units = gfa_calc.get("potential_units")

    return property


__all__ = [
    "check_zoning_compliance",
    "check_building_code_compliance",
    "calculate_gfa_utilization",
    "calculate_gfa_utilization_async",
    "run_full_compliance_check",
    "update_property_compliance",
]
