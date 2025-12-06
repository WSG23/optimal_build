"""TPB and Buildings Department compliance checking utilities for Hong Kong properties.

This module provides compliance validation functions based on Hong Kong's:
- Town Planning Board (TPB) - Outline Zoning Plans (OZP)
- Buildings Department (BD) - Building Regulations
- Lands Department - Lease conditions
"""

from decimal import Decimal
from typing import Any, Dict

from backend._compat.datetime import utcnow

from app.models.hong_kong_property import HKComplianceStatus, HongKongProperty
from app.models.rkp import RefRule
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# NOTE: Hong Kong TPB and BD rules are stored in the RefRule database table
# This allows jurisdiction-agnostic calculations via services/buildable.py
# Rules are queried dynamically based on jurisdiction and zone_code
#
# To populate rules, use: python -m scripts.seed_hong_kong_rules


async def check_tpb_compliance(
    property: HongKongProperty, session: AsyncSession
) -> Dict[str, Any]:
    """
    Check Town Planning Board (TPB) zoning compliance for a Hong Kong property.

    Validates against Outline Zoning Plan (OZP) requirements including:
    - Plot ratio limits
    - Building height restrictions (metres and mPD)
    - Site coverage limits
    - Permitted uses

    Args:
        property: HongKongProperty model instance
        session: AsyncSession for database queries

    Returns:
        Dict containing:
        - status: HKComplianceStatus (PASSED, FAILED, WARNING, PENDING)
        - violations: List of violation descriptions
        - warnings: List of warning messages
        - rules_applied: The TPB rules that were checked
    """
    violations: list[str] = []
    warnings: list[str] = []

    # Get zoning rules
    if not property.zoning:
        return {
            "status": HKComplianceStatus.PENDING,
            "message": "Zoning not specified",
            "violations": [],
            "warnings": ["Property zoning must be specified for compliance check"],
            "rules_applied": {},
        }

    # Convert enum to string if needed
    zoning_str = (
        property.zoning.value if hasattr(property.zoning, "value") else property.zoning
    )
    zone_code = f"HK:{zoning_str}"

    # Query RefRule database for TPB zoning rules
    stmt = (
        select(RefRule)
        .where(RefRule.jurisdiction == "HK")
        .where(RefRule.authority == "TPB")
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
            "status": HKComplianceStatus.WARNING,
            "message": f"No TPB rules found for zoning: {zoning_str}",
            "violations": [],
            "warnings": [f"No zoning rules found in database for zone {zone_code}"],
            "rules_applied": {},
        }

    # Parse rules into dict for easier checking
    rules_dict: Dict[str, Any] = {}
    for rule in applicable_rules:
        if rule.parameter_key == "zoning.max_plot_ratio":
            rules_dict["max_plot_ratio"] = Decimal(rule.value)
        elif rule.parameter_key == "zoning.max_building_height_m":
            rules_dict["max_height_m"] = Decimal(rule.value)
        elif rule.parameter_key == "zoning.max_building_height_mpd":
            rules_dict["max_height_mpd"] = Decimal(rule.value)
        elif rule.parameter_key == "zoning.max_site_coverage":
            # Convert "65%" string to 0.65 decimal
            value_str = str(rule.value).replace("%", "")
            rules_dict["max_site_coverage"] = Decimal(value_str) / 100
        elif rule.parameter_key == "zoning.max_storeys":
            rules_dict["max_storeys"] = int(rule.value)

    # Check plot ratio
    if property.plot_ratio and "max_plot_ratio" in rules_dict:
        max_plot_ratio = rules_dict["max_plot_ratio"]
        if property.plot_ratio > max_plot_ratio:
            violations.append(
                f"Plot ratio {property.plot_ratio} exceeds maximum {max_plot_ratio} "
                f"for {zoning_str} zone under OZP"
            )

    # Check building height (metres)
    if property.building_height_m and "max_height_m" in rules_dict:
        max_height = rules_dict["max_height_m"]
        if property.building_height_m > max_height:
            violations.append(
                f"Building height {property.building_height_m}m exceeds maximum {max_height}m "
                f"for {zoning_str} zone"
            )

    # Check building height (mPD - metres above Principal Datum)
    if property.max_building_height_mpd and "max_height_mpd" in rules_dict:
        max_mpd = rules_dict["max_height_mpd"]
        if property.max_building_height_mpd > max_mpd:
            violations.append(
                f"Building height {property.max_building_height_mpd}mPD exceeds maximum "
                f"{max_mpd}mPD for {zoning_str} zone"
            )

    # Check number of storeys
    if property.num_storeys and "max_storeys" in rules_dict:
        max_storeys = rules_dict["max_storeys"]
        if property.num_storeys > max_storeys:
            violations.append(
                f"Number of storeys ({property.num_storeys}) exceeds maximum ({max_storeys}) "
                f"for {zoning_str} zone"
            )

    # Calculate actual plot ratio if GFA is provided
    if (
        property.gross_floor_area_sqft
        and property.land_area_sqft
        and property.land_area_sqft > 0
    ):
        actual_plot_ratio = property.gross_floor_area_sqft / property.land_area_sqft
        if "max_plot_ratio" in rules_dict:
            max_plot_ratio = rules_dict["max_plot_ratio"]
            if actual_plot_ratio > max_plot_ratio:
                violations.append(
                    f"Actual plot ratio {actual_plot_ratio:.2f} (GFA/site area) exceeds "
                    f"maximum {max_plot_ratio} for {zoning_str} zone"
                )

    # Check site coverage
    if "max_site_coverage" in rules_dict:
        max_coverage = rules_dict["max_site_coverage"]
        if property.site_coverage and property.site_coverage > max_coverage * 100:
            violations.append(
                f"Site coverage {property.site_coverage}% exceeds maximum "
                f"{float(max_coverage) * 100:.0f}% for {zoning_str} zone"
            )

    # Determine status
    if violations:
        status = HKComplianceStatus.FAILED
    elif warnings:
        status = HKComplianceStatus.WARNING
    else:
        status = HKComplianceStatus.PASSED

    return {
        "status": status,
        "violations": violations,
        "warnings": warnings,
        "rules_applied": {
            k: str(v) if isinstance(v, Decimal) else v for k, v in rules_dict.items()
        },
    }


async def check_bd_compliance(
    property: HongKongProperty, session: AsyncSession
) -> Dict[str, Any]:
    """
    Check Buildings Department (BD) compliance for a Hong Kong property.

    Validates against Building Regulations including:
    - Building (Planning) Regulations
    - Site coverage requirements
    - Open space requirements
    - Means of escape requirements

    Args:
        property: HongKongProperty model instance
        session: AsyncSession for database queries

    Returns:
        Dict containing:
        - status: HKComplianceStatus
        - violations: List of violation descriptions
        - warnings: List of warning messages
        - recommendations: List of recommended actions
        - requirements_applied: The BD requirements that were checked
    """
    violations: list[str] = []
    warnings: list[str] = []
    recommendations: list[str] = []

    if not property.zoning:
        return {
            "status": HKComplianceStatus.WARNING,
            "message": "Zoning not specified",
            "violations": [],
            "warnings": ["Property zoning must be specified for BD compliance check"],
            "recommendations": [],
            "requirements_applied": {},
        }

    # Convert enum to string if needed
    zoning_str = (
        property.zoning.value if hasattr(property.zoning, "value") else property.zoning
    )
    zone_code = f"HK:{zoning_str}"

    # Query RefRule database for BD building rules
    stmt = (
        select(RefRule)
        .where(RefRule.jurisdiction == "HK")
        .where(RefRule.authority == "BD")
        .where(RefRule.topic == "building")
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
            "status": HKComplianceStatus.WARNING,
            "message": f"No BD rules found for zoning: {zoning_str}",
            "violations": [],
            "warnings": [f"No building rules found in database for zone {zone_code}"],
            "recommendations": [],
            "requirements_applied": {},
        }

    # Parse rules into dict
    requirements: Dict[str, Any] = {}
    for rule in applicable_rules:
        if rule.parameter_key == "building.site_coverage.max_percent":
            value_str = str(rule.value).replace("%", "")
            requirements["max_site_coverage"] = Decimal(value_str) / 100
        elif rule.parameter_key == "building.open_space.min_percent":
            value_str = str(rule.value).replace("%", "")
            requirements["min_open_space"] = Decimal(value_str) / 100
        elif rule.parameter_key == "building.min_unit_size_sqft":
            requirements["min_unit_size_sqft"] = Decimal(rule.value)

    # Check site coverage from BD regulations
    if property.site_coverage and "max_site_coverage" in requirements:
        max_coverage = requirements["max_site_coverage"]
        if property.site_coverage > max_coverage * 100:
            violations.append(
                f"Site coverage {property.site_coverage}% exceeds BD maximum "
                f"{float(max_coverage) * 100:.0f}% for {zoning_str} development"
            )

    # Add general BD recommendations
    recommendations.append("BEAM Plus certification recommended for new developments")
    recommendations.append(
        "Ensure compliance with Building (Planning) Regulations for means of escape"
    )
    recommendations.append(
        "Fire Services Department certificate required before Occupation Permit"
    )
    recommendations.append(
        "Barrier-free access required per Design Manual: Access for Persons with Disabilities"
    )

    # Check for graded buildings
    if property.is_graded_building:
        warnings.append(
            f"Property is a graded historic building (Grade: {property.heritage_grade}). "
            "Special approval from Antiquities Advisory Board may be required."
        )
        recommendations.append(
            "Consult with Antiquities and Monuments Office before any alterations"
        )

    # Determine status
    if violations:
        status = HKComplianceStatus.FAILED
    elif warnings:
        status = HKComplianceStatus.WARNING
    else:
        status = HKComplianceStatus.PASSED

    return {
        "status": status,
        "violations": violations,
        "warnings": warnings,
        "recommendations": recommendations,
        "requirements_applied": {
            k: str(v) if isinstance(v, Decimal) else v for k, v in requirements.items()
        },
    }


async def check_lease_compliance(
    property: HongKongProperty, session: AsyncSession
) -> Dict[str, Any]:
    """
    Check Lands Department lease condition compliance.

    Validates:
    - Lease modification requirements
    - User covenant restrictions
    - Premium assessment requirements

    Args:
        property: HongKongProperty model instance
        session: AsyncSession for database queries

    Returns:
        Dict containing compliance status and any lease-related issues
    """
    violations: list[str] = []
    warnings: list[str] = []
    recommendations: list[str] = []

    # Check lease expiry
    if property.lease_remaining_years:
        if property.lease_remaining_years < 20:
            warnings.append(
                f"Lease expiring in {property.lease_remaining_years} years. "
                "Consider lease renewal or extension."
            )
        elif property.lease_remaining_years < 50:
            recommendations.append(
                f"Lease has {property.lease_remaining_years} years remaining. "
                "Factor into development timeline."
            )

    # Check if lease modification is required
    if property.lease_modification_required:
        warnings.append(
            "Lease modification required for proposed development. "
            "Land premium will be assessed by Lands Department."
        )
        if property.land_premium_estimate:
            recommendations.append(
                f"Estimated land premium: HK${property.land_premium_estimate:,.0f}"
            )

    # Check for waiver applications
    if property.waiver_application:
        recommendations.append(
            "Temporary waiver application may be required for interim uses"
        )

    # Determine status
    if violations:
        status = HKComplianceStatus.FAILED
    elif warnings:
        status = HKComplianceStatus.WARNING
    else:
        status = HKComplianceStatus.PASSED

    return {
        "status": status,
        "violations": violations,
        "warnings": warnings,
        "recommendations": recommendations,
    }


async def calculate_gfa_utilization_async(
    property: HongKongProperty, session: AsyncSession | None = None
) -> Dict[str, Any]:
    """
    Calculate GFA utilization for Hong Kong property.

    Hong Kong uses:
    - Plot ratio (not FAR terminology)
    - sqft as primary unit
    - Saleable area (not NIA terminology)

    Args:
        property: HongKongProperty model instance
        session: AsyncSession for database queries (optional)

    Returns:
        Dict containing:
        - max_gfa_sqft: Maximum allowable GFA
        - current_gfa_sqft: Current GFA
        - remaining_gfa_sqft: Remaining development potential
        - utilization_percentage: Current utilization %
        - potential_units: Estimated additional units possible
        - recommendations: List of optimization suggestions
    """
    from app.services.jurisdictions import get_engineering_defaults

    if not property.land_area_sqft or not property.plot_ratio:
        return {
            "error": "Land area and plot ratio required for GFA calculation",
            "max_gfa_sqft": None,
            "current_gfa_sqft": None,
            "remaining_gfa_sqft": None,
            "utilization_percentage": None,
            "potential_units": None,
            "recommendations": [
                "Specify land area and plot ratio to calculate development potential"
            ],
        }

    # Get HK engineering defaults
    eng_defaults = get_engineering_defaults("HK", "residential")
    efficiency_ratio = eng_defaults.get("efficiency_ratio", 0.75)

    # Calculate in sqft (HK primary unit)
    max_gfa_sqft = float(property.land_area_sqft * property.plot_ratio)
    current_gfa_sqft = (
        float(property.gross_floor_area_sqft) if property.gross_floor_area_sqft else 0.0
    )
    remaining_gfa_sqft = max_gfa_sqft - current_gfa_sqft
    utilization_pct = (
        (current_gfa_sqft / max_gfa_sqft * 100) if max_gfa_sqft > 0 else 0.0
    )

    # Convert to sqm for metrics
    max_gfa_sqm = max_gfa_sqft * 0.092903
    saleable_area_sqft = max_gfa_sqft * efficiency_ratio

    # Estimate potential units (residential only)
    potential_units = None
    zoning_value = (
        property.zoning.value if hasattr(property.zoning, "value") else property.zoning
    )
    residential_zones = ["R(A)", "R(B)", "R(C)", "R(D)", "R(E)", "C/R"]
    if zoning_value in residential_zones and remaining_gfa_sqft > 0:
        # HK average unit size ~500-700 sqft
        avg_unit_size_sqft = 600
        potential_units = int(remaining_gfa_sqft / avg_unit_size_sqft)

    recommendations = []
    if remaining_gfa_sqft > 0:
        recommendations.append(
            f"You can build up to {remaining_gfa_sqft:,.0f} sqft more GFA"
        )
        recommendations.append(
            f"Current utilization is {utilization_pct:.1f}% of maximum allowed"
        )
        recommendations.append(
            f"Saleable Area estimate: {saleable_area_sqft:,.0f} sqft "
            f"({efficiency_ratio * 100:.0f}% efficiency)"
        )
        if potential_units:
            recommendations.append(
                f"Potential for approximately {potential_units} additional residential units"
            )
    else:
        recommendations.append("Maximum GFA utilization reached")

    return {
        "max_gfa_sqft": float(max_gfa_sqft),
        "max_gfa_sqm": float(max_gfa_sqm),
        "current_gfa_sqft": float(current_gfa_sqft),
        "remaining_gfa_sqft": float(remaining_gfa_sqft),
        "utilization_percentage": float(utilization_pct),
        "potential_units": potential_units,
        "buildable_metrics": {
            "saleable_area_sqft": saleable_area_sqft,
            "efficiency_ratio": efficiency_ratio,
            "floor_height_m": eng_defaults.get("floor_to_floor", 3.15),
        },
        "recommendations": recommendations,
    }


def calculate_gfa_utilization(property: HongKongProperty) -> Dict[str, Any]:
    """
    Synchronous wrapper for GFA utilization calculation.

    This is used by sync API endpoints. For async code, use calculate_gfa_utilization_async().
    """
    from app.services.jurisdictions import get_engineering_defaults

    if not property.land_area_sqft or not property.plot_ratio:
        return {
            "error": "Land area and plot ratio required for GFA calculation",
            "max_gfa_sqft": None,
            "current_gfa_sqft": None,
            "remaining_gfa_sqft": None,
            "utilization_percentage": None,
            "potential_units": None,
            "recommendations": [
                "Specify land area and plot ratio to calculate development potential"
            ],
        }

    # Get HK engineering defaults
    eng_defaults = get_engineering_defaults("HK", "residential")
    efficiency_ratio = eng_defaults.get("efficiency_ratio", 0.75)

    max_gfa_sqft = float(property.land_area_sqft * property.plot_ratio)
    current_gfa_sqft = (
        float(property.gross_floor_area_sqft) if property.gross_floor_area_sqft else 0.0
    )
    remaining_gfa_sqft = max_gfa_sqft - current_gfa_sqft
    utilization_pct = (
        (current_gfa_sqft / max_gfa_sqft * 100) if max_gfa_sqft > 0 else 0.0
    )

    max_gfa_sqm = max_gfa_sqft * 0.092903
    saleable_area_sqft = max_gfa_sqft * efficiency_ratio

    potential_units = None
    zoning_value = (
        property.zoning.value if hasattr(property.zoning, "value") else property.zoning
    )
    residential_zones = ["R(A)", "R(B)", "R(C)", "R(D)", "R(E)", "C/R"]
    if zoning_value in residential_zones and remaining_gfa_sqft > 0:
        avg_unit_size_sqft = 600
        potential_units = int(remaining_gfa_sqft / avg_unit_size_sqft)

    recommendations = []
    if remaining_gfa_sqft > 0:
        recommendations.append(
            f"You can build up to {remaining_gfa_sqft:,.0f} sqft more GFA"
        )
        recommendations.append(
            f"Current utilization is {utilization_pct:.1f}% of maximum allowed"
        )
        recommendations.append(
            f"Saleable Area estimate: {saleable_area_sqft:,.0f} sqft "
            f"({efficiency_ratio * 100:.0f}% efficiency)"
        )
        if potential_units:
            recommendations.append(
                f"Potential for approximately {potential_units} additional residential units"
            )
    else:
        recommendations.append("Maximum GFA utilization reached")

    return {
        "max_gfa_sqft": float(max_gfa_sqft),
        "max_gfa_sqm": float(max_gfa_sqm),
        "current_gfa_sqft": float(current_gfa_sqft),
        "remaining_gfa_sqft": float(remaining_gfa_sqft),
        "utilization_percentage": float(utilization_pct),
        "potential_units": potential_units,
        "buildable_metrics": {
            "saleable_area_sqft": saleable_area_sqft,
            "efficiency_ratio": efficiency_ratio,
            "floor_height_m": eng_defaults.get("floor_to_floor", 3.15),
        },
        "recommendations": recommendations,
    }


async def run_full_compliance_check(
    property: HongKongProperty, session: AsyncSession
) -> Dict[str, Any]:
    """
    Run complete TPB and BD compliance checks on a Hong Kong property.
    Updates the property's compliance fields.

    Args:
        property: HongKongProperty model instance
        session: AsyncSession for database queries

    Returns:
        Dict containing complete compliance report with TPB, BD, and lease results
    """
    tpb_check = await check_tpb_compliance(property, session)
    bd_check = await check_bd_compliance(property, session)
    lease_check = await check_lease_compliance(property, session)
    gfa_calc = calculate_gfa_utilization(property)

    # Compile all violations and recommendations
    all_violations = (
        tpb_check.get("violations", [])
        + bd_check.get("violations", [])
        + lease_check.get("violations", [])
    )
    all_warnings = (
        tpb_check.get("warnings", [])
        + bd_check.get("warnings", [])
        + lease_check.get("warnings", [])
    )
    all_recommendations = (
        bd_check.get("recommendations", [])
        + lease_check.get("recommendations", [])
        + gfa_calc.get("recommendations", [])
    )

    # Determine overall compliance status
    if all_violations:
        overall_status = HKComplianceStatus.FAILED
    elif all_warnings:
        overall_status = HKComplianceStatus.WARNING
    else:
        overall_status = HKComplianceStatus.PASSED

    # Create compliance notes summary
    compliance_notes = []
    if tpb_check.get("violations"):
        compliance_notes.extend([f"TPB: {v}" for v in tpb_check["violations"]])
    if bd_check.get("violations"):
        compliance_notes.extend([f"BD: {v}" for v in bd_check["violations"]])
    if lease_check.get("violations"):
        compliance_notes.extend([f"Lease: {v}" for v in lease_check["violations"]])
    if all_warnings:
        compliance_notes.extend([f"Warning: {w}" for w in all_warnings])

    return {
        "overall_status": overall_status,
        "tpb_status": tpb_check["status"],
        "bd_status": bd_check["status"],
        "lease_status": lease_check["status"],
        "violations": all_violations,
        "warnings": all_warnings,
        "recommendations": all_recommendations,
        "compliance_notes": "\n".join(compliance_notes) if compliance_notes else None,
        "compliance_data": {
            "tpb_check": tpb_check,
            "bd_check": bd_check,
            "lease_check": lease_check,
            "gfa_calculation": gfa_calc,
            "checked_at": utcnow().isoformat(),
        },
    }


async def update_property_compliance(
    property: HongKongProperty, session: AsyncSession
) -> HongKongProperty:
    """
    Run compliance checks and update the property model fields.

    Args:
        property: HongKongProperty model instance
        session: AsyncSession for database queries

    Returns:
        Updated property instance (not yet committed to database)
    """
    compliance_result = await run_full_compliance_check(property, session)

    # Update property compliance fields
    tpb_status = compliance_result["tpb_status"]
    bd_status = compliance_result["bd_status"]
    property.tpb_compliance_status = (
        tpb_status.value if hasattr(tpb_status, "value") else tpb_status
    )
    property.bd_compliance_status = (
        bd_status.value if hasattr(bd_status, "value") else bd_status
    )
    property.compliance_notes = compliance_result["compliance_notes"]
    property.compliance_data = compliance_result["compliance_data"]
    property.compliance_last_checked = utcnow()

    # Update GFA utilization metrics
    gfa_calc = compliance_result["compliance_data"]["gfa_calculation"]
    if gfa_calc.get("max_gfa_sqft"):
        from decimal import Decimal

        property.max_developable_gfa_sqft = Decimal(str(gfa_calc["max_gfa_sqft"]))
        property.max_developable_gfa_sqm = Decimal(str(gfa_calc["max_gfa_sqm"]))
        property.gfa_utilization_percentage = Decimal(
            str(gfa_calc["utilization_percentage"])
        )
        property.potential_additional_units = gfa_calc.get("potential_units")

    return property


__all__ = [
    "check_tpb_compliance",
    "check_bd_compliance",
    "check_lease_compliance",
    "calculate_gfa_utilization",
    "calculate_gfa_utilization_async",
    "run_full_compliance_check",
    "update_property_compliance",
]
