"""Resource consent and Building consent compliance utilities for New Zealand properties.

This module provides compliance validation functions based on New Zealand's:
- Resource Management Act 1991 (RMA) - Planning and environmental controls
- Building Act 2004 - Building regulations and code compliance
- Auckland Unitary Plan / District Plans - Zoning rules
"""

from decimal import Decimal
from typing import Any, Dict

from backend._compat.datetime import utcnow

from app.models.new_zealand_property import NZComplianceStatus, NewZealandProperty
from app.models.rkp import RefRule
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# NOTE: New Zealand RMA and Building Act rules are stored in the RefRule database table
# This allows jurisdiction-agnostic calculations via services/buildable.py
# Rules are queried dynamically based on jurisdiction and zone_code
#
# To populate rules, use: python -m scripts.seed_new_zealand_rules


async def check_district_plan_compliance(
    property: NewZealandProperty, session: AsyncSession
) -> Dict[str, Any]:
    """
    Check District Plan / Unitary Plan zoning compliance for a NZ property.

    Validates against Auckland Unitary Plan or relevant District Plan including:
    - Height limits and height in relation to boundary (HIRB)
    - Site coverage
    - Impervious surface limits
    - Setback requirements
    - Density controls

    Args:
        property: NewZealandProperty model instance
        session: AsyncSession for database queries

    Returns:
        Dict containing:
        - status: NZComplianceStatus (PASSED, FAILED, WARNING, PENDING)
        - violations: List of violation descriptions
        - warnings: List of warning messages
        - activity_status: Consent type required (Permitted, Controlled, etc.)
        - rules_applied: The district plan rules that were checked
    """
    violations: list[str] = []
    warnings: list[str] = []
    activity_status = "Permitted"  # Default - may be upgraded based on infringements

    # Get zoning rules
    if not property.zoning:
        return {
            "status": NZComplianceStatus.PENDING,
            "message": "Zoning not specified",
            "violations": [],
            "warnings": ["Property zoning must be specified for compliance check"],
            "activity_status": "Unknown",
            "rules_applied": {},
        }

    # Convert enum to string if needed
    zoning_str = (
        property.zoning.value if hasattr(property.zoning, "value") else property.zoning
    )
    zone_code = f"NZ:{zoning_str}"

    # Query RefRule database for District Plan zoning rules
    stmt = (
        select(RefRule)
        .where(RefRule.jurisdiction == "NZ")
        .where(RefRule.authority == "Council")
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
            "status": NZComplianceStatus.WARNING,
            "message": f"No District Plan rules found for zoning: {zoning_str}",
            "violations": [],
            "warnings": [f"No zoning rules found in database for zone {zone_code}"],
            "activity_status": "Unknown",
            "rules_applied": {},
        }

    # Parse rules into dict for easier checking
    rules_dict: Dict[str, Any] = {}
    for rule in applicable_rules:
        if rule.parameter_key == "zoning.max_building_height_m":
            rules_dict["max_height_m"] = Decimal(rule.value)
        elif rule.parameter_key == "zoning.max_site_coverage":
            value_str = str(rule.value).replace("%", "")
            rules_dict["max_site_coverage"] = Decimal(value_str)
        elif rule.parameter_key == "zoning.max_impervious_surface":
            value_str = str(rule.value).replace("%", "")
            rules_dict["max_impervious_surface"] = Decimal(value_str)
        elif rule.parameter_key == "zoning.min_setback_front_m":
            rules_dict["min_setback_front"] = Decimal(rule.value)
        elif rule.parameter_key == "zoning.min_setback_side_m":
            rules_dict["min_setback_side"] = Decimal(rule.value)
        elif rule.parameter_key == "zoning.min_setback_rear_m":
            rules_dict["min_setback_rear"] = Decimal(rule.value)
        elif rule.parameter_key == "zoning.hirb_angle":
            rules_dict["hirb_angle"] = Decimal(rule.value)
        elif rule.parameter_key == "zoning.min_lot_size_sqm":
            rules_dict["min_lot_size"] = Decimal(rule.value)

    # Check building height
    if property.building_height_m and "max_height_m" in rules_dict:
        max_height = rules_dict["max_height_m"]
        if property.building_height_m > max_height:
            violations.append(
                f"Building height {property.building_height_m}m exceeds maximum {max_height}m "
                f"for {zoning_str} zone"
            )
            activity_status = "Restricted Discretionary"

    # Check site coverage
    if property.site_coverage_percent and "max_site_coverage" in rules_dict:
        max_coverage = rules_dict["max_site_coverage"]
        if property.site_coverage_percent > max_coverage:
            violations.append(
                f"Site coverage {property.site_coverage_percent}% exceeds maximum "
                f"{max_coverage}% for {zoning_str} zone"
            )
            activity_status = "Restricted Discretionary"

    # Check impervious surface
    if property.impervious_surface_percent and "max_impervious_surface" in rules_dict:
        max_impervious = rules_dict["max_impervious_surface"]
        if property.impervious_surface_percent > max_impervious:
            violations.append(
                f"Impervious surface {property.impervious_surface_percent}% exceeds maximum "
                f"{max_impervious}% for {zoning_str} zone"
            )
            activity_status = "Restricted Discretionary"

    # Check setbacks
    if property.setback_front_m and "min_setback_front" in rules_dict:
        min_front = rules_dict["min_setback_front"]
        if property.setback_front_m < min_front:
            violations.append(
                f"Front setback {property.setback_front_m}m is less than minimum "
                f"{min_front}m for {zoning_str} zone"
            )
            activity_status = "Restricted Discretionary"

    if property.setback_side_m and "min_setback_side" in rules_dict:
        min_side = rules_dict["min_setback_side"]
        if property.setback_side_m < min_side:
            warnings.append(
                f"Side setback {property.setback_side_m}m is less than minimum "
                f"{min_side}m - may require neighbour approval"
            )
            if activity_status == "Permitted":
                activity_status = "Controlled"

    # Check lot size
    if property.land_area_sqm and "min_lot_size" in rules_dict:
        min_lot = rules_dict["min_lot_size"]
        if property.land_area_sqm < min_lot:
            violations.append(
                f"Lot size {property.land_area_sqm}sqm is below minimum "
                f"{min_lot}sqm for {zoning_str} zone"
            )
            activity_status = "Non-Complying"

    # Determine status
    if violations:
        status = NZComplianceStatus.FAILED
    elif warnings:
        status = NZComplianceStatus.WARNING
    else:
        status = NZComplianceStatus.PASSED

    return {
        "status": status,
        "violations": violations,
        "warnings": warnings,
        "activity_status": activity_status,
        "rules_applied": {
            k: str(v) if isinstance(v, Decimal) else v for k, v in rules_dict.items()
        },
    }


async def check_building_code_compliance(
    property: NewZealandProperty, session: AsyncSession
) -> Dict[str, Any]:
    """
    Check Building Code / Building Act compliance for a NZ property.

    Validates against Building Code clauses including:
    - Structure (B1/B2)
    - Fire safety (C1-C6)
    - Access (D1)
    - Moisture (E1-E3)
    - Services and facilities (G1-G15)
    - Energy efficiency (H1)

    Args:
        property: NewZealandProperty model instance
        session: AsyncSession for database queries

    Returns:
        Dict containing:
        - status: NZComplianceStatus
        - violations: List of violation descriptions
        - warnings: List of warning messages
        - recommendations: List of recommended actions
        - requirements_applied: The Building Code requirements checked
    """
    violations: list[str] = []
    warnings: list[str] = []
    recommendations: list[str] = []

    if not property.zoning:
        return {
            "status": NZComplianceStatus.WARNING,
            "message": "Zoning not specified",
            "violations": [],
            "warnings": ["Property zoning must be specified for building code check"],
            "recommendations": [],
            "requirements_applied": {},
        }

    # Convert enum to string if needed
    zoning_str = (
        property.zoning.value if hasattr(property.zoning, "value") else property.zoning
    )
    zone_code = f"NZ:{zoning_str}"

    # Query RefRule database for Building Code rules
    stmt = (
        select(RefRule)
        .where(RefRule.jurisdiction == "NZ")
        .where(RefRule.authority == "MBIE")
        .where(RefRule.topic == "building")
        .where(RefRule.review_status == "approved")
        .where(RefRule.is_published)
    )
    result = await session.execute(stmt)
    all_rules = result.scalars().all()

    # Filter rules applicable to this zone/building type
    applicable_rules = []
    for rule in all_rules:
        if rule.applicability and isinstance(rule.applicability, dict):
            rule_zone_code = rule.applicability.get("zone_code")
            if rule_zone_code == zone_code or rule_zone_code is None:
                applicable_rules.append(rule)

    requirements: Dict[str, Any] = {}
    for rule in applicable_rules:
        if rule.parameter_key == "building.h1.insulation_r_value":
            requirements["min_insulation_r"] = Decimal(rule.value)
        elif rule.parameter_key == "building.g5.water_efficiency":
            requirements["water_efficiency_required"] = rule.value == "true"

    # Add general Building Code recommendations
    recommendations.append(
        "Building Consent required from local BCA before construction"
    )
    recommendations.append(
        "Producer statements (PS1-PS4) may be required for specialist systems"
    )
    recommendations.append(
        "Code Compliance Certificate (CCC) required within 2 years of building consent"
    )

    # Check for residential sustainability
    if zoning_str.startswith("residential"):
        recommendations.append(
            "Consider Homestar certification for sustainable residential design"
        )
        recommendations.append(
            "H1 Energy Efficiency requirements apply - check insulation levels"
        )

    # Check for heritage constraints
    if property.is_heritage_listed:
        warnings.append(
            f"Property is heritage listed (Category: {property.heritage_category}). "
            "Heritage NZ approval may be required for alterations."
        )
        recommendations.append(
            "Consult Heritage New Zealand Pouhere Taonga before any works"
        )

    # Check for natural hazards
    if property.flood_hazard_zone:
        warnings.append(
            "Property is in a flood hazard zone. Additional consent requirements apply."
        )
        recommendations.append(
            "Minimum floor levels may be required above design flood level"
        )

    if property.coastal_hazard_zone:
        warnings.append(
            "Property is in a coastal hazard zone. Managed retreat provisions may apply."
        )

    # Determine status
    if violations:
        status = NZComplianceStatus.FAILED
    elif warnings:
        status = NZComplianceStatus.WARNING
    else:
        status = NZComplianceStatus.PASSED

    return {
        "status": status,
        "violations": violations,
        "warnings": warnings,
        "recommendations": recommendations,
        "requirements_applied": {
            k: str(v) if isinstance(v, Decimal) else v for k, v in requirements.items()
        },
    }


async def check_infrastructure_compliance(
    property: NewZealandProperty, session: AsyncSession
) -> Dict[str, Any]:
    """
    Check infrastructure and development contributions requirements.

    Validates:
    - Three waters connections (water, wastewater, stormwater)
    - Development contributions payable
    - Infrastructure capacity

    Args:
        property: NewZealandProperty model instance
        session: AsyncSession for database queries

    Returns:
        Dict containing infrastructure compliance status
    """
    violations: list[str] = []
    warnings: list[str] = []
    recommendations: list[str] = []

    # Check three waters
    if not property.has_reticulated_water:
        warnings.append(
            "No reticulated water supply. Private bore or rainwater tank required."
        )
        recommendations.append(
            "Water supply consent may be required from regional council"
        )

    if not property.has_reticulated_wastewater:
        warnings.append(
            "No reticulated wastewater. On-site wastewater system required."
        )
        recommendations.append(
            "On-site wastewater discharge consent required from regional council"
        )

    if not property.has_stormwater_connection:
        warnings.append(
            "No stormwater connection. On-site stormwater management required."
        )
        recommendations.append(
            "Stormwater management plan required for building consent"
        )

    # Development contributions
    if property.infrastructure_growth_charge:
        recommendations.append(
            f"Development contributions of ${property.infrastructure_growth_charge:,.0f} "
            "payable to council"
        )
    else:
        recommendations.append(
            "Development contributions may be payable - confirm with council"
        )

    # Determine status
    if violations:
        status = NZComplianceStatus.FAILED
    elif warnings:
        status = NZComplianceStatus.WARNING
    else:
        status = NZComplianceStatus.PASSED

    return {
        "status": status,
        "violations": violations,
        "warnings": warnings,
        "recommendations": recommendations,
    }


async def calculate_gfa_utilization_async(
    property: NewZealandProperty, session: AsyncSession | None = None
) -> Dict[str, Any]:
    """
    Calculate GFA utilization for New Zealand property.

    New Zealand uses:
    - Site coverage percentage (not plot ratio typically)
    - Height limits in metres
    - sqm as primary unit

    Args:
        property: NewZealandProperty model instance
        session: AsyncSession for database queries (optional)

    Returns:
        Dict containing:
        - max_gfa_sqm: Maximum allowable GFA estimate
        - current_gfa_sqm: Current GFA
        - remaining_gfa_sqm: Remaining development potential
        - utilization_percentage: Current utilization %
        - potential_units: Estimated additional units possible
        - recommendations: List of optimization suggestions
    """
    from app.services.jurisdictions import get_engineering_defaults

    if not property.land_area_sqm:
        return {
            "error": "Land area required for GFA calculation",
            "max_gfa_sqm": None,
            "current_gfa_sqm": None,
            "remaining_gfa_sqm": None,
            "utilization_percentage": None,
            "potential_units": None,
            "recommendations": ["Specify land area to calculate development potential"],
        }

    # Get NZ engineering defaults
    eng_defaults = get_engineering_defaults("NZ", "residential")
    efficiency_ratio = eng_defaults.get("efficiency_ratio", 0.85)
    floor_height = eng_defaults.get("floor_to_floor", 2.7)

    # Calculate max GFA based on site coverage and height
    max_site_coverage = float(property.max_site_coverage_percent or 45) / 100
    max_height = float(property.maximum_building_height_m or 11)
    land_area = float(property.land_area_sqm)

    # Max floors based on height
    max_floors = int(max_height / floor_height)

    # Max building footprint
    max_footprint = land_area * max_site_coverage

    # Max GFA (floors x footprint)
    max_gfa_sqm = max_footprint * max_floors

    current_gfa_sqm = (
        float(property.gross_floor_area_sqm) if property.gross_floor_area_sqm else 0.0
    )
    remaining_gfa_sqm = max_gfa_sqm - current_gfa_sqm
    utilization_pct = (current_gfa_sqm / max_gfa_sqm * 100) if max_gfa_sqm > 0 else 0.0

    # Net floor area estimate
    net_floor_area = max_gfa_sqm * efficiency_ratio

    # Estimate potential units (residential only)
    potential_units = None
    zoning_value = (
        property.zoning.value if hasattr(property.zoning, "value") else property.zoning
    )
    residential_zones = [
        "residential_large_lot",
        "residential_single_house",
        "residential_mixed_housing_suburban",
        "residential_mixed_housing_urban",
        "residential_terrace_housing_apartment",
    ]
    if zoning_value in residential_zones and remaining_gfa_sqm > 0:
        # NZ average unit sizes vary by zone
        if zoning_value == "residential_terrace_housing_apartment":
            avg_unit_size = 65  # Smaller apartments
        elif zoning_value == "residential_mixed_housing_urban":
            avg_unit_size = 80
        else:
            avg_unit_size = 120  # Houses
        potential_units = int(remaining_gfa_sqm / avg_unit_size)

    recommendations = []
    if remaining_gfa_sqm > 0:
        recommendations.append(f"Estimated maximum GFA: {max_gfa_sqm:,.0f} sqm")
        recommendations.append(
            f"Current utilization is {utilization_pct:.1f}% of estimated maximum"
        )
        recommendations.append(
            f"Net Floor Area estimate: {net_floor_area:,.0f} sqm "
            f"({efficiency_ratio * 100:.0f}% efficiency)"
        )
        if potential_units:
            recommendations.append(
                f"Potential for approximately {potential_units} additional dwellings"
            )
    else:
        recommendations.append("Estimated maximum GFA utilization reached")

    return {
        "max_gfa_sqm": float(max_gfa_sqm),
        "current_gfa_sqm": float(current_gfa_sqm),
        "remaining_gfa_sqm": float(remaining_gfa_sqm),
        "utilization_percentage": float(utilization_pct),
        "potential_units": potential_units,
        "buildable_metrics": {
            "max_footprint_sqm": max_footprint,
            "max_floors": max_floors,
            "net_floor_area_sqm": net_floor_area,
            "efficiency_ratio": efficiency_ratio,
            "floor_height_m": floor_height,
        },
        "recommendations": recommendations,
    }


def calculate_gfa_utilization(property: NewZealandProperty) -> Dict[str, Any]:
    """
    Synchronous wrapper for GFA utilization calculation.
    """
    from app.services.jurisdictions import get_engineering_defaults

    if not property.land_area_sqm:
        return {
            "error": "Land area required for GFA calculation",
            "max_gfa_sqm": None,
            "current_gfa_sqm": None,
            "remaining_gfa_sqm": None,
            "utilization_percentage": None,
            "potential_units": None,
            "recommendations": ["Specify land area to calculate development potential"],
        }

    eng_defaults = get_engineering_defaults("NZ", "residential")
    efficiency_ratio = eng_defaults.get("efficiency_ratio", 0.85)
    floor_height = eng_defaults.get("floor_to_floor", 2.7)

    max_site_coverage = float(property.max_site_coverage_percent or 45) / 100
    max_height = float(property.maximum_building_height_m or 11)
    land_area = float(property.land_area_sqm)

    max_floors = int(max_height / floor_height)
    max_footprint = land_area * max_site_coverage
    max_gfa_sqm = max_footprint * max_floors

    current_gfa_sqm = (
        float(property.gross_floor_area_sqm) if property.gross_floor_area_sqm else 0.0
    )
    remaining_gfa_sqm = max_gfa_sqm - current_gfa_sqm
    utilization_pct = (current_gfa_sqm / max_gfa_sqm * 100) if max_gfa_sqm > 0 else 0.0

    net_floor_area = max_gfa_sqm * efficiency_ratio

    potential_units = None
    zoning_value = (
        property.zoning.value if hasattr(property.zoning, "value") else property.zoning
    )
    residential_zones = [
        "residential_large_lot",
        "residential_single_house",
        "residential_mixed_housing_suburban",
        "residential_mixed_housing_urban",
        "residential_terrace_housing_apartment",
    ]
    if zoning_value in residential_zones and remaining_gfa_sqm > 0:
        if zoning_value == "residential_terrace_housing_apartment":
            avg_unit_size = 65
        elif zoning_value == "residential_mixed_housing_urban":
            avg_unit_size = 80
        else:
            avg_unit_size = 120
        potential_units = int(remaining_gfa_sqm / avg_unit_size)

    recommendations = []
    if remaining_gfa_sqm > 0:
        recommendations.append(f"Estimated maximum GFA: {max_gfa_sqm:,.0f} sqm")
        recommendations.append(
            f"Current utilization is {utilization_pct:.1f}% of estimated maximum"
        )
        recommendations.append(
            f"Net Floor Area estimate: {net_floor_area:,.0f} sqm "
            f"({efficiency_ratio * 100:.0f}% efficiency)"
        )
        if potential_units:
            recommendations.append(
                f"Potential for approximately {potential_units} additional dwellings"
            )
    else:
        recommendations.append("Estimated maximum GFA utilization reached")

    return {
        "max_gfa_sqm": float(max_gfa_sqm),
        "current_gfa_sqm": float(current_gfa_sqm),
        "remaining_gfa_sqm": float(remaining_gfa_sqm),
        "utilization_percentage": float(utilization_pct),
        "potential_units": potential_units,
        "buildable_metrics": {
            "max_footprint_sqm": max_footprint,
            "max_floors": max_floors,
            "net_floor_area_sqm": net_floor_area,
            "efficiency_ratio": efficiency_ratio,
            "floor_height_m": floor_height,
        },
        "recommendations": recommendations,
    }


async def run_full_compliance_check(
    property: NewZealandProperty, session: AsyncSession
) -> Dict[str, Any]:
    """
    Run complete RMA and Building Act compliance checks on a NZ property.

    Args:
        property: NewZealandProperty model instance
        session: AsyncSession for database queries

    Returns:
        Dict containing complete compliance report
    """
    district_plan_check = await check_district_plan_compliance(property, session)
    building_code_check = await check_building_code_compliance(property, session)
    infrastructure_check = await check_infrastructure_compliance(property, session)
    gfa_calc = calculate_gfa_utilization(property)

    # Compile all violations and recommendations
    all_violations = (
        district_plan_check.get("violations", [])
        + building_code_check.get("violations", [])
        + infrastructure_check.get("violations", [])
    )
    all_warnings = (
        district_plan_check.get("warnings", [])
        + building_code_check.get("warnings", [])
        + infrastructure_check.get("warnings", [])
    )
    all_recommendations = (
        building_code_check.get("recommendations", [])
        + infrastructure_check.get("recommendations", [])
        + gfa_calc.get("recommendations", [])
    )

    # Determine overall compliance status
    if all_violations:
        overall_status = NZComplianceStatus.FAILED
    elif all_warnings:
        overall_status = NZComplianceStatus.WARNING
    else:
        overall_status = NZComplianceStatus.PASSED

    # Create compliance notes summary
    compliance_notes = []
    if district_plan_check.get("violations"):
        compliance_notes.extend(
            [f"District Plan: {v}" for v in district_plan_check["violations"]]
        )
    if building_code_check.get("violations"):
        compliance_notes.extend(
            [f"Building Code: {v}" for v in building_code_check["violations"]]
        )
    if all_warnings:
        compliance_notes.extend([f"Warning: {w}" for w in all_warnings])

    return {
        "overall_status": overall_status,
        "resource_consent_status": district_plan_check["status"],
        "building_consent_status": building_code_check["status"],
        "infrastructure_status": infrastructure_check["status"],
        "activity_status": district_plan_check.get("activity_status", "Unknown"),
        "violations": all_violations,
        "warnings": all_warnings,
        "recommendations": all_recommendations,
        "compliance_notes": "\n".join(compliance_notes) if compliance_notes else None,
        "compliance_data": {
            "district_plan_check": district_plan_check,
            "building_code_check": building_code_check,
            "infrastructure_check": infrastructure_check,
            "gfa_calculation": gfa_calc,
            "checked_at": utcnow().isoformat(),
        },
    }


async def update_property_compliance(
    property: NewZealandProperty, session: AsyncSession
) -> NewZealandProperty:
    """
    Run compliance checks and update the property model fields.

    Args:
        property: NewZealandProperty model instance
        session: AsyncSession for database queries

    Returns:
        Updated property instance (not yet committed to database)
    """
    compliance_result = await run_full_compliance_check(property, session)

    # Update property compliance fields
    rc_status = compliance_result["resource_consent_status"]
    bc_status = compliance_result["building_consent_status"]
    property.resource_consent_compliance_status = (
        rc_status.value if hasattr(rc_status, "value") else rc_status
    )
    property.building_consent_compliance_status = (
        bc_status.value if hasattr(bc_status, "value") else bc_status
    )
    property.compliance_notes = compliance_result["compliance_notes"]
    property.compliance_data = compliance_result["compliance_data"]
    property.compliance_last_checked = utcnow()

    # Determine resource consent type required
    property.resource_consent_type = compliance_result.get("activity_status", "Unknown")
    property.resource_consent_required = (
        compliance_result.get("activity_status", "Permitted") != "Permitted"
    )

    # Update GFA utilization metrics
    gfa_calc = compliance_result["compliance_data"]["gfa_calculation"]
    if gfa_calc.get("max_gfa_sqm"):
        from decimal import Decimal

        property.max_developable_gfa_sqm = Decimal(str(gfa_calc["max_gfa_sqm"]))
        property.gfa_utilization_percentage = Decimal(
            str(gfa_calc["utilization_percentage"])
        )
        property.potential_additional_units = gfa_calc.get("potential_units")

    return property


__all__ = [
    "check_district_plan_compliance",
    "check_building_code_compliance",
    "check_infrastructure_compliance",
    "calculate_gfa_utilization",
    "calculate_gfa_utilization_async",
    "run_full_compliance_check",
    "update_property_compliance",
]
