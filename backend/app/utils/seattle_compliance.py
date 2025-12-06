"""Seattle Land Use Code and Building Code compliance utilities.

This module provides compliance validation functions based on Seattle's:
- Seattle Municipal Code (SMC) Title 23 - Land Use Code
- Washington State Building Code (WSBC)
- Seattle Department of Construction and Inspections (SDCI) requirements
"""

from decimal import Decimal
from typing import Any, Dict

from backend._compat.datetime import utcnow

from app.models.seattle_property import SeattleComplianceStatus, SeattleProperty
from app.models.rkp import RefRule
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# NOTE: Seattle SMC and WSBC rules are stored in the RefRule database table
# This allows jurisdiction-agnostic calculations via services/buildable.py
# Rules are queried dynamically based on jurisdiction and zone_code
#
# To populate rules, use: python -m scripts.seed_seattle_rules


async def check_zoning_compliance(
    property: SeattleProperty, session: AsyncSession
) -> Dict[str, Any]:
    """
    Check Seattle Municipal Code (SMC) Title 23 zoning compliance.

    Validates against Seattle Land Use Code including:
    - Floor Area Ratio (FAR) limits
    - Building height limits
    - Lot coverage limits
    - Setback requirements
    - Mandatory Housing Affordability (MHA) requirements

    Args:
        property: SeattleProperty model instance
        session: AsyncSession for database queries

    Returns:
        Dict containing:
        - status: SeattleComplianceStatus (PASSED, FAILED, WARNING, PENDING)
        - violations: List of violation descriptions
        - warnings: List of warning messages
        - mha_requirements: MHA payment/performance requirements if applicable
        - rules_applied: The SMC rules that were checked
    """
    violations: list[str] = []
    warnings: list[str] = []
    mha_requirements: Dict[str, Any] = {}

    if not property.zoning:
        return {
            "status": SeattleComplianceStatus.PENDING,
            "message": "Zoning not specified",
            "violations": [],
            "warnings": ["Property zoning must be specified for compliance check"],
            "mha_requirements": {},
            "rules_applied": {},
        }

    # Convert enum to string if needed
    zoning_str = (
        property.zoning.value if hasattr(property.zoning, "value") else property.zoning
    )
    zone_code = f"SEA:{zoning_str}"

    # Query RefRule database for Seattle zoning rules
    stmt = (
        select(RefRule)
        .where(RefRule.jurisdiction == "SEA")
        .where(RefRule.authority == "SDCI")
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
            "status": SeattleComplianceStatus.WARNING,
            "message": f"No SMC rules found for zoning: {zoning_str}",
            "violations": [],
            "warnings": [f"No zoning rules found in database for zone {zone_code}"],
            "mha_requirements": {},
            "rules_applied": {},
        }

    # Parse rules into dict for easier checking
    rules_dict: Dict[str, Any] = {}
    for rule in applicable_rules:
        if rule.parameter_key == "zoning.max_far":
            rules_dict["max_far"] = Decimal(rule.value)
        elif rule.parameter_key == "zoning.max_building_height_ft":
            rules_dict["max_height_ft"] = Decimal(rule.value)
        elif rule.parameter_key == "zoning.max_lot_coverage":
            value_str = str(rule.value).replace("%", "")
            rules_dict["max_lot_coverage"] = Decimal(value_str)
        elif rule.parameter_key == "zoning.min_setback_front_ft":
            rules_dict["min_setback_front"] = Decimal(rule.value)
        elif rule.parameter_key == "zoning.min_setback_side_ft":
            rules_dict["min_setback_side"] = Decimal(rule.value)
        elif rule.parameter_key == "zoning.min_setback_rear_ft":
            rules_dict["min_setback_rear"] = Decimal(rule.value)

    # Check FAR
    if property.floor_area_ratio and "max_far" in rules_dict:
        max_far = rules_dict["max_far"]
        if property.floor_area_ratio > max_far:
            violations.append(
                f"FAR {property.floor_area_ratio} exceeds maximum {max_far} "
                f"for {zoning_str} zone"
            )

    # Check building height
    if property.building_height_ft and "max_height_ft" in rules_dict:
        max_height = rules_dict["max_height_ft"]
        if property.building_height_ft > max_height:
            violations.append(
                f"Building height {property.building_height_ft}ft exceeds maximum "
                f"{max_height}ft for {zoning_str} zone"
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
    if property.setback_front_ft and "min_setback_front" in rules_dict:
        min_front = rules_dict["min_setback_front"]
        if property.setback_front_ft < min_front:
            violations.append(
                f"Front setback {property.setback_front_ft}ft is less than minimum "
                f"{min_front}ft for {zoning_str} zone"
            )

    # Calculate actual FAR if GFA is provided
    if (
        property.gross_floor_area_sqft
        and property.lot_area_sqft
        and property.lot_area_sqft > 0
    ):
        actual_far = property.gross_floor_area_sqft / property.lot_area_sqft
        if "max_far" in rules_dict:
            max_far = rules_dict["max_far"]
            if actual_far > max_far:
                violations.append(
                    f"Actual FAR {actual_far:.2f} (GFA/lot area) exceeds "
                    f"maximum {max_far} for {zoning_str} zone"
                )

    # Check MHA requirements
    if property.mha_zone:
        mha_requirements["zone"] = property.mha_zone
        if property.mha_payment_option:
            # MHA payment rates vary by zone (simplified)
            payment_per_sqft = {
                "M": 20.75,
                "M1": 14.25,
                "M2": 5.58,
            }.get(property.mha_zone, 10.00)
            if property.gross_floor_area_sqft:
                estimated_payment = (
                    float(property.gross_floor_area_sqft) * payment_per_sqft
                )
                mha_requirements["payment_option"] = {
                    "rate_per_sqft": payment_per_sqft,
                    "estimated_total": estimated_payment,
                }
                warnings.append(
                    f"MHA payment option: estimated ${estimated_payment:,.0f} "
                    f"(${payment_per_sqft}/sqft)"
                )
        if property.mha_performance_option:
            # Performance requirement is typically 5-11% of units affordable
            performance_pct = {
                "M": 11,
                "M1": 8,
                "M2": 5,
            }.get(property.mha_zone, 7)
            mha_requirements["performance_option"] = {
                "affordable_percentage": performance_pct,
            }
            warnings.append(
                f"MHA performance option: {performance_pct}% of units must be affordable"
            )

    # Determine status
    if violations:
        status = SeattleComplianceStatus.FAILED
    elif warnings:
        status = SeattleComplianceStatus.WARNING
    else:
        status = SeattleComplianceStatus.PASSED

    return {
        "status": status,
        "violations": violations,
        "warnings": warnings,
        "mha_requirements": mha_requirements,
        "rules_applied": {
            k: str(v) if isinstance(v, Decimal) else v for k, v in rules_dict.items()
        },
    }


async def check_building_code_compliance(
    property: SeattleProperty, session: AsyncSession
) -> Dict[str, Any]:
    """
    Check Washington State Building Code (WSBC) and Seattle amendments compliance.

    Validates against building code including:
    - Seattle Energy Code requirements
    - Fire and life safety
    - Accessibility (ADA)
    - Seismic requirements

    Args:
        property: SeattleProperty model instance
        session: AsyncSession for database queries

    Returns:
        Dict containing:
        - status: SeattleComplianceStatus
        - violations: List of violation descriptions
        - warnings: List of warning messages
        - recommendations: List of recommended actions
        - requirements_applied: The building code requirements checked
    """
    violations: list[str] = []
    warnings: list[str] = []
    recommendations: list[str] = []

    if not property.zoning:
        return {
            "status": SeattleComplianceStatus.WARNING,
            "message": "Zoning not specified",
            "violations": [],
            "warnings": ["Property zoning must be specified for building code check"],
            "recommendations": [],
            "requirements_applied": {},
        }

    zoning_str = (
        property.zoning.value if hasattr(property.zoning, "value") else property.zoning
    )
    zone_code = f"SEA:{zoning_str}"

    # Query RefRule database for building code rules
    stmt = (
        select(RefRule)
        .where(RefRule.jurisdiction == "SEA")
        .where(RefRule.authority == "WSBC")
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
        if rule.parameter_key == "building.seismic_design_category":
            requirements["seismic_design_category"] = rule.value

    # Seattle Energy Code recommendations
    recommendations.append(
        "Seattle Energy Code compliance required - exceeds Washington State requirements"
    )
    recommendations.append(
        "All-electric building option available for expedited permitting"
    )

    # Check for design review requirement
    if property.design_review_required:
        warnings.append(
            f"Design review required ({property.design_review_type}). "
            "Additional time and fees apply."
        )

    # Check for environmental review
    if property.sepa_required:
        warnings.append("SEPA environmental review required before permit issuance")
        recommendations.append(
            "Consider early SEPA checklist submission to identify issues"
        )

    # Check for critical areas
    if property.critical_area:
        warnings.append(
            "Property contains or is adjacent to critical area (steep slope, wetland, etc.). "
            "Additional studies and mitigation may be required."
        )

    # Check for shoreline
    if property.shoreline_zone:
        warnings.append(
            "Property is within Shoreline Management jurisdiction. "
            "Shoreline permit may be required."
        )

    # Check for landmarks
    if property.is_landmark:
        warnings.append(
            f"Property is a designated landmark ({property.landmark_designation}). "
            "Landmarks Board approval required for alterations."
        )

    # Add general SDCI recommendations
    recommendations.append(
        "Pre-application conference with SDCI recommended for complex projects"
    )
    recommendations.append(
        "Building permit required before construction - typical review 4-12 weeks"
    )

    # Determine status
    if violations:
        status = SeattleComplianceStatus.FAILED
    elif warnings:
        status = SeattleComplianceStatus.WARNING
    else:
        status = SeattleComplianceStatus.PASSED

    return {
        "status": status,
        "violations": violations,
        "warnings": warnings,
        "recommendations": recommendations,
        "requirements_applied": requirements,
    }


async def calculate_gfa_utilization_async(
    property: SeattleProperty, session: AsyncSession | None = None
) -> Dict[str, Any]:
    """
    Calculate GFA utilization for Seattle property.

    Seattle uses:
    - Floor Area Ratio (FAR)
    - sqft as primary unit
    - MHA bonus FAR for affordable housing

    Args:
        property: SeattleProperty model instance
        session: AsyncSession for database queries (optional)

    Returns:
        Dict containing development potential metrics
    """
    from app.services.jurisdictions import get_engineering_defaults

    if not property.lot_area_sqft or not property.max_far:
        return {
            "error": "Lot area and maximum FAR required for GFA calculation",
            "max_gfa_sqft": None,
            "current_gfa_sqft": None,
            "remaining_gfa_sqft": None,
            "utilization_percentage": None,
            "potential_units": None,
            "recommendations": [
                "Specify lot area and FAR to calculate development potential"
            ],
        }

    # Get Seattle engineering defaults
    eng_defaults = get_engineering_defaults("SEA", "residential")
    efficiency_ratio = eng_defaults.get("efficiency_ratio", 0.85)

    lot_area = float(property.lot_area_sqft)
    max_far = float(property.max_far)

    # Add MHA bonus if applicable
    bonus_far = float(property.incentive_zoning_bonus or 0)
    total_far = max_far + bonus_far

    max_gfa_sqft = lot_area * total_far
    current_gfa_sqft = (
        float(property.gross_floor_area_sqft) if property.gross_floor_area_sqft else 0.0
    )
    remaining_gfa_sqft = max_gfa_sqft - current_gfa_sqft
    utilization_pct = (
        (current_gfa_sqft / max_gfa_sqft * 100) if max_gfa_sqft > 0 else 0.0
    )

    # Convert to sqm
    max_gfa_sqm = max_gfa_sqft * 0.092903

    # Net rentable area estimate
    net_rentable_sqft = max_gfa_sqft * efficiency_ratio

    # Estimate potential units
    potential_units = None
    zoning_value = (
        property.zoning.value if hasattr(property.zoning, "value") else property.zoning
    )
    multifamily_zones = [
        "LR1",
        "LR2",
        "LR3",
        "MR",
        "MR-RC",
        "HR",
        "SM",
        "SM-SLU",
        "SM-D",
    ]
    if zoning_value in multifamily_zones and remaining_gfa_sqft > 0:
        # Seattle average unit sizes vary by type
        if zoning_value == "HR":
            avg_unit_size = 750  # Highrise units smaller
        elif zoning_value.startswith("SM"):
            avg_unit_size = 800
        else:
            avg_unit_size = 900  # Lowrise/midrise
        potential_units = int(remaining_gfa_sqft / avg_unit_size)

    recommendations = []
    if remaining_gfa_sqft > 0:
        recommendations.append(
            f"Maximum GFA: {max_gfa_sqft:,.0f} sqft (FAR {total_far:.2f})"
        )
        if bonus_far > 0:
            recommendations.append(
                f"Includes {bonus_far:.2f} bonus FAR from incentive zoning"
            )
        recommendations.append(
            f"Current utilization is {utilization_pct:.1f}% of maximum allowed"
        )
        recommendations.append(
            f"Net Rentable Area estimate: {net_rentable_sqft:,.0f} sqft "
            f"({efficiency_ratio * 100:.0f}% efficiency)"
        )
        if potential_units:
            recommendations.append(
                f"Potential for approximately {potential_units} additional units"
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
            "base_far": max_far,
            "bonus_far": bonus_far,
            "total_far": total_far,
            "net_rentable_sqft": net_rentable_sqft,
            "efficiency_ratio": efficiency_ratio,
            "floor_height_ft": eng_defaults.get("floor_to_floor", 10.0),
        },
        "recommendations": recommendations,
    }


def calculate_gfa_utilization(property: SeattleProperty) -> Dict[str, Any]:
    """Synchronous wrapper for GFA utilization calculation."""
    from app.services.jurisdictions import get_engineering_defaults

    if not property.lot_area_sqft or not property.max_far:
        return {
            "error": "Lot area and maximum FAR required for GFA calculation",
            "max_gfa_sqft": None,
            "current_gfa_sqft": None,
            "remaining_gfa_sqft": None,
            "utilization_percentage": None,
            "potential_units": None,
            "recommendations": [
                "Specify lot area and FAR to calculate development potential"
            ],
        }

    eng_defaults = get_engineering_defaults("SEA", "residential")
    efficiency_ratio = eng_defaults.get("efficiency_ratio", 0.85)

    lot_area = float(property.lot_area_sqft)
    max_far = float(property.max_far)
    bonus_far = float(property.incentive_zoning_bonus or 0)
    total_far = max_far + bonus_far

    max_gfa_sqft = lot_area * total_far
    current_gfa_sqft = (
        float(property.gross_floor_area_sqft) if property.gross_floor_area_sqft else 0.0
    )
    remaining_gfa_sqft = max_gfa_sqft - current_gfa_sqft
    utilization_pct = (
        (current_gfa_sqft / max_gfa_sqft * 100) if max_gfa_sqft > 0 else 0.0
    )

    max_gfa_sqm = max_gfa_sqft * 0.092903
    net_rentable_sqft = max_gfa_sqft * efficiency_ratio

    potential_units = None
    zoning_value = (
        property.zoning.value if hasattr(property.zoning, "value") else property.zoning
    )
    multifamily_zones = [
        "LR1",
        "LR2",
        "LR3",
        "MR",
        "MR-RC",
        "HR",
        "SM",
        "SM-SLU",
        "SM-D",
    ]
    if zoning_value in multifamily_zones and remaining_gfa_sqft > 0:
        if zoning_value == "HR":
            avg_unit_size = 750
        elif zoning_value.startswith("SM"):
            avg_unit_size = 800
        else:
            avg_unit_size = 900
        potential_units = int(remaining_gfa_sqft / avg_unit_size)

    recommendations = []
    if remaining_gfa_sqft > 0:
        recommendations.append(
            f"Maximum GFA: {max_gfa_sqft:,.0f} sqft (FAR {total_far:.2f})"
        )
        if bonus_far > 0:
            recommendations.append(
                f"Includes {bonus_far:.2f} bonus FAR from incentive zoning"
            )
        recommendations.append(
            f"Current utilization is {utilization_pct:.1f}% of maximum allowed"
        )
        recommendations.append(
            f"Net Rentable Area estimate: {net_rentable_sqft:,.0f} sqft "
            f"({efficiency_ratio * 100:.0f}% efficiency)"
        )
        if potential_units:
            recommendations.append(
                f"Potential for approximately {potential_units} additional units"
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
            "base_far": max_far,
            "bonus_far": bonus_far,
            "total_far": total_far,
            "net_rentable_sqft": net_rentable_sqft,
            "efficiency_ratio": efficiency_ratio,
            "floor_height_ft": eng_defaults.get("floor_to_floor", 10.0),
        },
        "recommendations": recommendations,
    }


async def run_full_compliance_check(
    property: SeattleProperty, session: AsyncSession
) -> Dict[str, Any]:
    """
    Run complete SMC and building code compliance checks on a Seattle property.

    Args:
        property: SeattleProperty model instance
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
        overall_status = SeattleComplianceStatus.FAILED
    elif all_warnings:
        overall_status = SeattleComplianceStatus.WARNING
    else:
        overall_status = SeattleComplianceStatus.PASSED

    compliance_notes = []
    if zoning_check.get("violations"):
        compliance_notes.extend([f"SMC: {v}" for v in zoning_check["violations"]])
    if building_check.get("violations"):
        compliance_notes.extend([f"WSBC: {v}" for v in building_check["violations"]])
    if all_warnings:
        compliance_notes.extend([f"Warning: {w}" for w in all_warnings])

    return {
        "overall_status": overall_status,
        "zoning_status": zoning_check["status"],
        "building_status": building_check["status"],
        "mha_requirements": zoning_check.get("mha_requirements", {}),
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
    property: SeattleProperty, session: AsyncSession
) -> SeattleProperty:
    """
    Run compliance checks and update the property model fields.

    Args:
        property: SeattleProperty model instance
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

    # Update MHA payment if applicable
    mha_req = compliance_result.get("mha_requirements", {})
    if mha_req.get("payment_option"):
        from decimal import Decimal

        property.mha_payment_amount = Decimal(
            str(mha_req["payment_option"]["estimated_total"])
        )

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
    "check_zoning_compliance",
    "check_building_code_compliance",
    "calculate_gfa_utilization",
    "calculate_gfa_utilization_async",
    "run_full_compliance_check",
    "update_property_compliance",
]
