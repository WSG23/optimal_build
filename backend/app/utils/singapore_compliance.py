"""BCA and URA compliance checking utilities for Singapore properties.

This module provides compliance validation functions based on Singapore's:
- Building and Construction Authority (BCA) requirements
- Urban Redevelopment Authority (URA) zoning regulations
"""

from collections import Counter
from decimal import Decimal
from typing import Any, Dict, Iterable

from backend._compat.datetime import utcnow
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rkp import RefRule
from app.models.singapore_property import ComplianceStatus, SingaporeProperty

# NOTE: Singapore URA and BCA rules are now stored in the RefRule database table
# This allows jurisdiction-agnostic calculations via services/buildable.py
# Rules are queried dynamically based on jurisdiction and zone_code
#
# To populate rules, use: python -m scripts.seed_singapore_rules
#
# Legacy hardcoded rules removed - use RefRule database instead


def _resolve_buildable_service_module() -> Any:
    from importlib import import_module

    module_names = ("app.services.buildable", "backend.app.services.buildable")
    modules = [import_module(name) for name in module_names]
    canonical_modules = set(module_names)
    for module in modules:
        calculate = getattr(module, "calculate_buildable", None)
        if (
            calculate is not None
            and getattr(calculate, "__module__", None) not in canonical_modules
        ):
            return module
    return modules[0]


def _rule_zone_code(rule: Any) -> str | None:
    applicability = getattr(rule, "applicability", None)
    if not isinstance(applicability, dict):
        return None
    zone = applicability.get("zone_code") or applicability.get("zone")
    if isinstance(zone, list):
        return next((str(item) for item in zone if item), None)
    if zone:
        return str(zone)
    return None


def _filter_rules_for_zone(rules: Iterable[Any], zone_code: str) -> list[Any]:
    return [rule for rule in rules if _rule_zone_code(rule) == zone_code]


def _approved_published_rules(rules: Iterable[Any]) -> list[Any]:
    return [
        rule
        for rule in rules
        if getattr(rule, "review_status", None) == "approved"
        and bool(getattr(rule, "is_published", False))
    ]


def _serialise_rule_evidence(rule: Any) -> dict[str, Any]:
    provenance = getattr(rule, "source_provenance", None)
    if isinstance(provenance, dict):
        source_provenance = dict(provenance)
    else:
        source_provenance = {}

    if getattr(rule, "review_status", None) == "approved":
        source_provenance.setdefault("document_id", getattr(rule, "document_id", None))
        source_provenance.setdefault("clause_id", None)
        source_provenance.setdefault("pages", [])

    return {
        "rule_id": getattr(rule, "id", None),
        "source_id": getattr(rule, "source_id", None),
        "document_id": getattr(rule, "document_id", None),
        "authority": getattr(rule, "authority", None),
        "topic": getattr(rule, "topic", None),
        "parameter_key": getattr(rule, "parameter_key", None),
        "operator": getattr(rule, "operator", None),
        "value": getattr(rule, "value", None),
        "unit": getattr(rule, "unit", None),
        "clause_ref": getattr(rule, "clause_ref", None),
        "review_status": getattr(rule, "review_status", None),
        "is_published": bool(getattr(rule, "is_published", False)),
        "applicability": getattr(rule, "applicability", None) or {},
        "notes": getattr(rule, "notes", None),
        "review_notes": getattr(rule, "review_notes", None),
        "source_provenance": source_provenance,
    }


def _rule_corpus_status(
    *,
    authority: str,
    topic: str,
    zone_code: str,
    applicable_rules: list[Any],
    approved_rules: list[Any],
) -> dict[str, Any]:
    review_counts = Counter(
        str(getattr(rule, "review_status", "unknown")) for rule in applicable_rules
    )
    published_count = sum(
        1 for rule in applicable_rules if bool(getattr(rule, "is_published", False))
    )
    traceable_count = sum(
        1
        for rule in approved_rules
        if any(
            (
                getattr(rule, "source_id", None),
                getattr(rule, "document_id", None),
                isinstance(getattr(rule, "source_provenance", None), dict),
            )
        )
    )

    if not applicable_rules:
        coverage_state = "missing"
        confidence = "low"
    elif not approved_rules:
        coverage_state = "review_pending"
        confidence = "low"
    elif len(approved_rules) < len(applicable_rules):
        coverage_state = "partial"
        confidence = "medium"
    elif traceable_count < len(approved_rules):
        coverage_state = "approved"
        confidence = "medium"
    else:
        coverage_state = "approved"
        confidence = "high"

    return {
        "authority": authority,
        "topic": topic,
        "zone_code": zone_code,
        "coverage_state": coverage_state,
        "confidence": confidence,
        "counts": {
            "applicable": len(applicable_rules),
            "approved": len(approved_rules),
            "published": published_count,
            "traceable": traceable_count,
            "needs_review": review_counts.get("needs_review", 0),
            "rejected": review_counts.get("rejected", 0),
        },
        "applied_rule_ids": [
            getattr(rule, "id", None)
            for rule in approved_rules
            if getattr(rule, "id", None) is not None
        ],
    }


async def check_ura_compliance(
    property: SingaporeProperty, session: AsyncSession
) -> Dict[str, Any]:
    """
    Check URA zoning compliance for a Singapore property using RefRule database.

    Args:
        property: SingaporeProperty model instance
        session: AsyncSession for database queries

    Returns:
        Dict containing:
        - status: ComplianceStatus (PASSED, FAILED, WARNING, PENDING)
        - violations: List of violation descriptions
        - warnings: List of warning messages
        - rules_applied: The URA rules that were checked
    """
    violations: list[str] = []
    warnings: list[str] = []

    # Get zoning rules
    if not property.zoning:
        return {
            "status": ComplianceStatus.PENDING,
            "message": "Zoning not specified",
            "violations": [],
            "warnings": ["Property zoning must be specified for compliance check"],
            "rules_applied": {},
            "rule_evidence": [],
            "rule_corpus_status": {
                "authority": "URA",
                "topic": "zoning",
                "zone_code": None,
                "coverage_state": "missing",
                "confidence": "low",
                "counts": {
                    "applicable": 0,
                    "approved": 0,
                    "published": 0,
                    "traceable": 0,
                    "needs_review": 0,
                    "rejected": 0,
                },
                "applied_rule_ids": [],
            },
        }

    # Convert enum to string if needed
    zoning_str = (
        property.zoning.value if hasattr(property.zoning, "value") else property.zoning
    )
    zone_code = f"SG:{zoning_str}"

    # Query RefRule database for URA zoning rules
    stmt = (
        select(RefRule)
        .where(RefRule.jurisdiction == "SG")
        .where(RefRule.authority == "URA")
        .where(RefRule.topic == "zoning")
    )
    result = await session.execute(stmt)
    all_rules = result.scalars().all()

    # Filter rules applicable to this zone
    applicable_rules = _filter_rules_for_zone(all_rules, zone_code)
    approved_rules = _approved_published_rules(applicable_rules)
    rule_corpus_status = _rule_corpus_status(
        authority="URA",
        topic="zoning",
        zone_code=zone_code,
        applicable_rules=applicable_rules,
        approved_rules=approved_rules,
    )

    if not applicable_rules:
        return {
            "status": ComplianceStatus.WARNING,
            "message": f"No URA rules found for zoning: {zoning_str}",
            "violations": [],
            "warnings": [f"No zoning rules found in database for zone {zone_code}"],
            "rules_applied": {},
            "rule_evidence": [],
            "rule_corpus_status": rule_corpus_status,
        }

    if not approved_rules:
        return {
            "status": ComplianceStatus.WARNING,
            "message": f"URA rules for zoning {zoning_str} exist but are not approved",
            "violations": [],
            "warnings": [
                f"URA rules exist for zone {zone_code}, but none are both approved and published"
            ],
            "rules_applied": {},
            "rule_evidence": [],
            "rule_corpus_status": rule_corpus_status,
        }

    # Parse rules into dict for easier checking
    rules_dict = {}
    for rule in approved_rules:
        if rule.parameter_key == "zoning.max_far":
            rules_dict["max_plot_ratio"] = Decimal(rule.value)
        elif rule.parameter_key == "zoning.max_building_height_m":
            rules_dict["max_height_m"] = Decimal(rule.value)

    # Check plot ratio
    if property.gross_plot_ratio and "max_plot_ratio" in rules_dict:
        max_plot_ratio = rules_dict["max_plot_ratio"]
        if property.gross_plot_ratio > max_plot_ratio:
            violations.append(
                f"Plot ratio {property.gross_plot_ratio} exceeds maximum {max_plot_ratio} "
                f"for {zoning_str} zone"
            )

    # Check building height
    if property.building_height_m and "max_height_m" in rules_dict:
        max_height = rules_dict["max_height_m"]
        if property.building_height_m > max_height:
            violations.append(
                f"Building height {property.building_height_m}m exceeds maximum {max_height}m "
                f"for {zoning_str} zone"
            )

    # Calculate actual plot ratio if GFA is provided
    if (
        property.gross_floor_area_sqm
        and property.land_area_sqm
        and property.land_area_sqm > 0
    ):
        actual_plot_ratio = property.gross_floor_area_sqm / property.land_area_sqm
        if "max_plot_ratio" in rules_dict:
            max_plot_ratio = rules_dict["max_plot_ratio"]
            if actual_plot_ratio > max_plot_ratio:
                violations.append(
                    f"Actual plot ratio {actual_plot_ratio:.2f} (GFA/land area) exceeds "
                    f"maximum {max_plot_ratio} for {property.zoning} zone"
                )

    # Determine status
    if violations:
        status = ComplianceStatus.FAILED
    elif warnings:
        status = ComplianceStatus.WARNING
    else:
        status = ComplianceStatus.PASSED

    return {
        "status": status,
        "violations": violations,
        "warnings": warnings,
        "rules_applied": {
            k: str(v) if isinstance(v, Decimal) else v for k, v in rules_dict.items()
        },
        "rule_evidence": [_serialise_rule_evidence(rule) for rule in approved_rules],
        "rule_corpus_status": rule_corpus_status,
    }


async def check_bca_compliance(
    property: SingaporeProperty, session: AsyncSession
) -> Dict[str, Any]:
    """
    Check BCA building compliance for a Singapore property using RefRule database.

    Args:
        property: SingaporeProperty model instance
        session: AsyncSession for database queries

    Returns:
        Dict containing:
        - status: ComplianceStatus
        - violations: List of violation descriptions
        - warnings: List of warning messages
        - recommendations: List of recommended actions
        - requirements_applied: The BCA requirements that were checked
    """
    violations: list[str] = []
    warnings: list[str] = []
    recommendations: list[str] = []

    if not property.zoning:
        return {
            "status": ComplianceStatus.WARNING,
            "message": "Zoning not specified",
            "violations": [],
            "warnings": ["Property zoning must be specified for BCA compliance check"],
            "recommendations": [],
            "requirements_applied": {},
            "rule_evidence": [],
            "rule_corpus_status": {
                "authority": "BCA",
                "topic": "building",
                "zone_code": None,
                "coverage_state": "missing",
                "confidence": "low",
                "counts": {
                    "applicable": 0,
                    "approved": 0,
                    "published": 0,
                    "traceable": 0,
                    "needs_review": 0,
                    "rejected": 0,
                },
                "applied_rule_ids": [],
            },
        }

    # Convert enum to string if needed
    zoning_str = (
        property.zoning.value if hasattr(property.zoning, "value") else property.zoning
    )
    zone_code = f"SG:{zoning_str}"

    # Query RefRule database for BCA building rules
    stmt = (
        select(RefRule)
        .where(RefRule.jurisdiction == "SG")
        .where(RefRule.authority == "BCA")
        .where(RefRule.topic == "building")
    )
    result = await session.execute(stmt)
    all_rules = result.scalars().all()

    # Filter rules applicable to this zone
    applicable_rules = _filter_rules_for_zone(all_rules, zone_code)
    approved_rules = _approved_published_rules(applicable_rules)
    rule_corpus_status = _rule_corpus_status(
        authority="BCA",
        topic="building",
        zone_code=zone_code,
        applicable_rules=applicable_rules,
        approved_rules=approved_rules,
    )

    if not applicable_rules:
        return {
            "status": ComplianceStatus.WARNING,
            "message": f"No BCA rules found for zoning: {zoning_str}",
            "violations": [],
            "warnings": [f"No building rules found in database for zone {zone_code}"],
            "recommendations": [],
            "requirements_applied": {},
            "rule_evidence": [],
            "rule_corpus_status": rule_corpus_status,
        }

    if not approved_rules:
        return {
            "status": ComplianceStatus.WARNING,
            "message": f"BCA rules for zoning {zoning_str} exist but are not approved",
            "violations": [],
            "warnings": [
                f"BCA rules exist for zone {zone_code}, but none are both approved and published"
            ],
            "recommendations": [],
            "requirements_applied": {},
            "rule_evidence": [],
            "rule_corpus_status": rule_corpus_status,
        }

    # Parse rules into dict
    requirements = {}
    for rule in approved_rules:
        if rule.parameter_key == "zoning.site_coverage.max_percent":
            # Convert "40%" string to 0.40 decimal
            value_str = rule.value.replace("%", "")
            requirements["max_site_coverage"] = Decimal(value_str) / 100

    # Check site coverage
    if (
        property.gross_floor_area_sqm
        and property.land_area_sqm
        and property.num_storeys
    ):
        # Estimate building footprint (assuming uniform floor plates)
        footprint = property.gross_floor_area_sqm / property.num_storeys
        site_coverage = footprint / property.land_area_sqm
        max_coverage = requirements.get("max_site_coverage", Decimal("1.0"))

        if site_coverage > max_coverage:
            violations.append(
                f"Site coverage {site_coverage:.1%} exceeds maximum {max_coverage:.0%} "
                f"for {zoning_str} development"
            )

    # Add general BCA recommendations
    recommendations.append(
        "BCA Green Mark certification may be required for this development type"
    )
    recommendations.append(
        "Ensure compliance with BCA Accessibility Code (barrier-free access)"
    )
    recommendations.append(
        "SCDF Fire Safety Certificate required before obtaining Temporary Occupation Permit"
    )

    # Check residential-specific requirements (disabled for now - needs more property data)
    if False:
        # Check average unit size
        if property.num_storeys and property.gross_floor_area_sqm:
            # Calculate residential GFA (assume 80% of total for mixed use)
            residential_gfa = property.gross_floor_area_sqm
            if property.zoning == "mixed_use":
                residential_gfa = property.gross_floor_area_sqm * Decimal("0.8")

            # Estimate number of units if not provided
            estimated_units = (
                property.num_storeys * 8
            )  # Rough estimate: 8 units per floor

            if residential_gfa and estimated_units:
                avg_unit_size = residential_gfa / estimated_units
                min_size = requirements.get("min_unit_size_sqm", Decimal("35"))

                if avg_unit_size < min_size:
                    violations.append(
                        f"Average unit size {avg_unit_size:.1f}sqm below minimum {min_size}sqm "
                        f"for residential development"
                    )

        # Check parking requirements
        if property.num_storeys:
            estimated_units = property.num_storeys * 8
            min_parking_ratio = requirements.get("min_parking_ratio", Decimal("1.0"))
            required_parking = int(estimated_units * min_parking_ratio)

            # Note: We don't have parking data in model yet, so this is informational
            recommendations.append(
                f"Ensure at least {required_parking} parking lots are provided "
                f"({min_parking_ratio} lot per unit)"
            )

    # Determine status
    if violations:
        status = ComplianceStatus.FAILED
    elif warnings:
        status = ComplianceStatus.WARNING
    else:
        status = ComplianceStatus.PASSED

    return {
        "status": status,
        "violations": violations,
        "warnings": warnings,
        "recommendations": recommendations,
        "requirements_applied": {
            k: str(v) if isinstance(v, Decimal) else v for k, v in requirements.items()
        },
        "rule_evidence": [_serialise_rule_evidence(rule) for rule in approved_rules],
        "rule_corpus_status": rule_corpus_status,
    }


async def calculate_gfa_utilization_async(
    property: SingaporeProperty, session: Any = None
) -> Dict[str, Any]:
    """
    Calculate GFA utilization using the production buildable service.

    This integrates with services/buildable.py which accounts for:
    - Floor-to-floor height (4.0m default)
    - Efficiency ratio (82% - accounts for walls, MEP, structure, circulation)
    - Site coverage constraints
    - Height limits

    Args:
        property: SingaporeProperty model instance
        session: AsyncSession for database queries (optional for Singapore MVP)

    Returns:
        Dict containing:
        - max_gfa_sqm: Maximum allowable GFA (from buildable service)
        - current_gfa_sqm: Current GFA
        - remaining_gfa_sqm: Remaining development potential
        - utilization_percentage: Current utilization %
        - potential_units: Estimated additional units possible
        - buildable_metrics: Detailed metrics from buildable service
        - recommendations: List of optimization suggestions
    """
    from app.schemas.buildable import BuildableDefaults

    buildable_service = _resolve_buildable_service_module()
    ResolvedZone = buildable_service.ResolvedZone
    calculate_buildable = buildable_service.calculate_buildable

    if not property.land_area_sqm or not property.gross_plot_ratio:
        return {
            "error": "Land area and plot ratio required for GFA calculation",
            "max_gfa_sqm": None,
            "current_gfa_sqm": None,
            "remaining_gfa_sqm": None,
            "utilization_percentage": None,
            "potential_units": None,
            "recommendations": [
                "Specify land area and plot ratio to calculate development potential"
            ],
        }

    # Create buildable defaults using property data
    defaults = BuildableDefaults(
        plotRatio=float(property.gross_plot_ratio),
        siteAreaM2=float(property.land_area_sqm),
        siteCoverage=0.45,  # Default, will be overridden by zoning rules
        floorHeightM=4.0,  # Default floor-to-floor from config
        efficiencyFactor=0.82,  # 82% efficiency (18% loss for walls, MEP, structure, circulation)
    )

    # Create resolved zone (simplified for Singapore MVP - no PostGIS integration yet)
    resolved = ResolvedZone(
        zone_code=(
            property.zoning.value
            if hasattr(property.zoning, "value")
            else property.zoning
        ),
        parcel=None,
        zone_layers=[],
        input_kind="property",
        geometry_properties=None,
    )

    # Calculate buildable metrics using production service
    if session:
        buildable_calc = await calculate_buildable(
            session=session,
            resolved=resolved,
            defaults=defaults,
            typ_floor_to_floor_m=4.0,
            efficiency_ratio=0.82,
        )
        max_gfa = buildable_calc.metrics.gfa_cap_m2
        nsa_est = buildable_calc.metrics.nsa_est_m2
        floors_max = buildable_calc.metrics.floors_max
        footprint = buildable_calc.metrics.footprint_m2
    else:
        # Fallback: Simple calculation without database
        max_gfa = float(property.land_area_sqm * property.gross_plot_ratio)
        nsa_est = int(max_gfa * 0.82)  # 82% efficiency
        floors_max = property.num_storeys or 0
        footprint = int(float(property.land_area_sqm) * 0.45)  # 45% site coverage

    current_gfa = (
        float(property.gross_floor_area_sqm) if property.gross_floor_area_sqm else 0.0
    )
    remaining_gfa = max_gfa - current_gfa
    utilization_pct = (current_gfa / max_gfa * 100) if max_gfa > 0 else 0.0

    # Estimate potential units (residential only)
    potential_units = None
    zoning_value = (
        property.zoning.value if hasattr(property.zoning, "value") else property.zoning
    )
    if zoning_value in ["residential", "mixed_use"] and remaining_gfa > 0:
        avg_unit_size = 70  # Assume 70sqm average
        potential_units = int(remaining_gfa / avg_unit_size)

    recommendations = []
    if remaining_gfa > 0:
        recommendations.append(f"You can build up to {remaining_gfa:.0f} sqm more GFA")
        recommendations.append(
            f"Current utilization is {utilization_pct:.1f}% of maximum allowed"
        )
        recommendations.append(
            f"Net Saleable Area (NSA) estimate: {nsa_est:,} sqm (82% efficiency)"
        )
        if potential_units:
            recommendations.append(
                f"Potential for approximately {potential_units} additional residential units"
            )
    else:
        recommendations.append("Maximum GFA utilization reached")

    return {
        "max_gfa_sqm": float(max_gfa),
        "current_gfa_sqm": float(current_gfa),
        "remaining_gfa_sqm": float(remaining_gfa),
        "utilization_percentage": float(utilization_pct),
        "potential_units": potential_units,
        "buildable_metrics": {
            "nsa_estimate_sqm": nsa_est,
            "floors_max": floors_max,
            "footprint_sqm": footprint,
            "efficiency_ratio": 0.82,
        },
        "recommendations": recommendations,
    }


def calculate_gfa_utilization(property: SingaporeProperty) -> Dict[str, Any]:
    """
    Synchronous wrapper for GFA utilization calculation.

    This is used by the MVP sync API. For async code, use calculate_gfa_utilization_async().
    """
    # Simple calculation without buildable service (for sync compatibility)
    if not property.land_area_sqm or not property.gross_plot_ratio:
        return {
            "error": "Land area and plot ratio required for GFA calculation",
            "max_gfa_sqm": None,
            "current_gfa_sqm": None,
            "remaining_gfa_sqm": None,
            "utilization_percentage": None,
            "potential_units": None,
            "recommendations": [
                "Specify land area and plot ratio to calculate development potential"
            ],
        }

    # Calculate with buildable service defaults (4.0m floor height, 82% efficiency)
    max_gfa = float(property.land_area_sqm * property.gross_plot_ratio)
    current_gfa = (
        float(property.gross_floor_area_sqm) if property.gross_floor_area_sqm else 0.0
    )
    remaining_gfa = max_gfa - current_gfa
    utilization_pct = (current_gfa / max_gfa * 100) if max_gfa > 0 else 0.0

    # Apply 82% efficiency factor for NSA estimate
    nsa_est = int(max_gfa * 0.82)

    # Estimate potential units (residential only)
    potential_units = None
    zoning_value = (
        property.zoning.value if hasattr(property.zoning, "value") else property.zoning
    )
    if zoning_value in ["residential", "mixed_use"] and remaining_gfa > 0:
        avg_unit_size = 70  # Assume 70sqm average
        potential_units = int(remaining_gfa / avg_unit_size)

    recommendations = []
    if remaining_gfa > 0:
        recommendations.append(f"You can build up to {remaining_gfa:.0f} sqm more GFA")
        recommendations.append(
            f"Current utilization is {utilization_pct:.1f}% of maximum allowed"
        )
        recommendations.append(
            f"Net Saleable Area (NSA) estimate: {nsa_est:,} sqm (82% efficiency)"
        )
        if potential_units:
            recommendations.append(
                f"Potential for approximately {potential_units} additional residential units"
            )
    else:
        recommendations.append("Maximum GFA utilization reached")

    return {
        "max_gfa_sqm": float(max_gfa),
        "current_gfa_sqm": float(current_gfa),
        "remaining_gfa_sqm": float(remaining_gfa),
        "utilization_percentage": float(utilization_pct),
        "potential_units": potential_units,
        "buildable_metrics": {
            "nsa_estimate_sqm": nsa_est,
            "efficiency_ratio": 0.82,
            "floor_height_m": 4.0,
        },
        "recommendations": recommendations,
    }


async def run_full_compliance_check(
    property: SingaporeProperty, session: AsyncSession
) -> Dict[str, Any]:
    """
    Run complete BCA and URA compliance checks on a property using RefRule database.
    Updates the property's compliance fields.

    Args:
        property: SingaporeProperty model instance
        session: AsyncSession for database queries

    Returns:
        Dict containing complete compliance report with URA and BCA results
    """
    ura_check = await check_ura_compliance(property, session)
    bca_check = await check_bca_compliance(property, session)
    gfa_calc = calculate_gfa_utilization(property)

    # Compile all violations and recommendations
    all_violations = ura_check.get("violations", []) + bca_check.get("violations", [])
    all_warnings = ura_check.get("warnings", []) + bca_check.get("warnings", [])
    all_recommendations = bca_check.get("recommendations", []) + gfa_calc.get(
        "recommendations", []
    )

    # Determine overall compliance status
    if all_violations:
        overall_status = ComplianceStatus.FAILED
    elif all_warnings:
        overall_status = ComplianceStatus.WARNING
    else:
        overall_status = ComplianceStatus.PASSED

    # Create compliance notes summary
    compliance_notes = []
    if ura_check.get("violations"):
        compliance_notes.extend([f"URA: {v}" for v in ura_check["violations"]])
    if bca_check.get("violations"):
        compliance_notes.extend([f"BCA: {v}" for v in bca_check["violations"]])
    if all_warnings:
        compliance_notes.extend([f"Warning: {w}" for w in all_warnings])

    return {
        "overall_status": overall_status,
        "bca_status": bca_check["status"],
        "ura_status": ura_check["status"],
        "violations": all_violations,
        "warnings": all_warnings,
        "recommendations": all_recommendations,
        "compliance_notes": "\n".join(compliance_notes) if compliance_notes else None,
        "compliance_data": {
            "ura_check": ura_check,
            "bca_check": bca_check,
            "gfa_calculation": gfa_calc,
            "rule_corpus_status": {
                "ura": ura_check.get("rule_corpus_status", {}),
                "bca": bca_check.get("rule_corpus_status", {}),
            },
            "applied_rule_evidence": {
                "ura": ura_check.get("rule_evidence", []),
                "bca": bca_check.get("rule_evidence", []),
            },
            "checked_at": utcnow().isoformat(),
        },
    }


async def update_property_compliance(
    property: SingaporeProperty, session: AsyncSession
) -> SingaporeProperty:
    """
    Run compliance checks and update the property model fields.

    Args:
        property: SingaporeProperty model instance
        session: AsyncSession for database queries

    Returns:
        Updated property instance (not yet committed to database)
    """
    compliance_result = await run_full_compliance_check(property, session)

    # Update property compliance fields (convert enum to value for SQLAlchemy)
    bca_status = compliance_result["bca_status"]
    ura_status = compliance_result["ura_status"]
    property.bca_compliance_status = (
        bca_status.value if hasattr(bca_status, "value") else bca_status
    )
    property.ura_compliance_status = (
        ura_status.value if hasattr(ura_status, "value") else ura_status
    )
    property.compliance_notes = compliance_result["compliance_notes"]
    property.compliance_data = compliance_result["compliance_data"]
    property.compliance_last_checked = utcnow()

    # Update GFA utilization metrics
    gfa_calc = compliance_result["compliance_data"]["gfa_calculation"]
    if gfa_calc.get("max_gfa_sqm"):
        property.max_developable_gfa_sqm = Decimal(str(gfa_calc["max_gfa_sqm"]))
        property.gfa_utilization_percentage = Decimal(
            str(gfa_calc["utilization_percentage"])
        )
        property.potential_additional_units = gfa_calc.get("potential_units")

    return property
