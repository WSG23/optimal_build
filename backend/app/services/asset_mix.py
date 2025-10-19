"""Asset mix and optimisation helpers for developer feasibility."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass(frozen=True, slots=True)
class AssetOptimizationPlan:
    """Represents an allocation recommendation for a specific asset type."""

    asset_type: str
    allocation_pct: float
    nia_efficiency: float | None = None
    target_floor_height_m: float | None = None
    parking_ratio_per_1000sqm: float | None = None
    heritage_notes: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    allocated_gfa_sqm: float | None = None
    rent_psm_month: float | None = None
    fitout_cost_psm: float | None = None
    absorption_months: int | None = None
    risk_level: str | None = None
    estimated_revenue_sgd: float | None = None
    estimated_capex_sgd: float | None = None


_ASSET_PROFILES: dict[str, list[AssetOptimizationPlan]] = {
    "commercial": [
        AssetOptimizationPlan(
            asset_type="office",
            allocation_pct=60.0,
            nia_efficiency=0.82,
            target_floor_height_m=4.2,
            parking_ratio_per_1000sqm=1.2,
            rent_psm_month=14.5,
            fitout_cost_psm=2800,
            absorption_months=12,
            risk_level="moderate",
            notes=[
                "Target Grade A office floor plates around 1,800 sqm with 82% efficiency.",
            ],
        ),
        AssetOptimizationPlan(
            asset_type="retail",
            allocation_pct=25.0,
            nia_efficiency=0.68,
            target_floor_height_m=5.0,
            parking_ratio_per_1000sqm=3.5,
            rent_psm_month=18.0,
            fitout_cost_psm=3200,
            absorption_months=10,
            risk_level="balanced",
            notes=[
                "Dedicate podium levels to retail/F&B to activate frontage and drive rents.",
            ],
        ),
        AssetOptimizationPlan(
            asset_type="amenities",
            allocation_pct=15.0,
            nia_efficiency=0.55,
            target_floor_height_m=4.5,
            rent_psm_month=0.0,
            fitout_cost_psm=1500,
            absorption_months=6,
            risk_level="low",
            notes=[
                "Stack shared amenities and mechanical floors above podium for tenant experience.",
            ],
        ),
    ],
    "residential": [
        AssetOptimizationPlan(
            asset_type="residential",
            allocation_pct=70.0,
            nia_efficiency=0.78,
            target_floor_height_m=3.3,
            parking_ratio_per_1000sqm=0.8,
            rent_psm_month=12.0,
            fitout_cost_psm=2200,
            absorption_months=14,
            risk_level="moderate",
            notes=[
                "Blend 2- and 3-bedroom units to maintain average 85 sqm efficiencies."
            ],
        ),
        AssetOptimizationPlan(
            asset_type="serviced_apartments",
            allocation_pct=20.0,
            nia_efficiency=0.72,
            target_floor_height_m=3.1,
            parking_ratio_per_1000sqm=0.5,
            rent_psm_month=15.0,
            fitout_cost_psm=2600,
            absorption_months=12,
            risk_level="balanced",
            notes=[
                "Serviced offerings support recurring income and project underwriting."
            ],
        ),
        AssetOptimizationPlan(
            asset_type="amenities",
            allocation_pct=10.0,
            nia_efficiency=0.5,
            target_floor_height_m=4.0,
            rent_psm_month=0.0,
            fitout_cost_psm=1400,
            absorption_months=6,
            risk_level="low",
            notes=[
                "Allocate podium for wellness, childcare, and community facilities."
            ],
        ),
    ],
    "industrial": [
        AssetOptimizationPlan(
            asset_type="high-spec logistics",
            allocation_pct=50.0,
            nia_efficiency=0.75,
            target_floor_height_m=10.0,
            parking_ratio_per_1000sqm=1.1,
            rent_psm_month=9.5,
            fitout_cost_psm=2100,
            absorption_months=16,
            risk_level="balanced",
            notes=[
                "Design clear heights >9m with dual ramp access for logistics operators."
            ],
        ),
        AssetOptimizationPlan(
            asset_type="production",
            allocation_pct=30.0,
            nia_efficiency=0.7,
            target_floor_height_m=8.0,
            parking_ratio_per_1000sqm=0.9,
            rent_psm_month=8.0,
            fitout_cost_psm=2300,
            absorption_months=18,
            risk_level="elevated",
            notes=[
                "Provision 12kN/m² loading and flexible M&E trunks for advanced manufacturing."
            ],
        ),
        AssetOptimizationPlan(
            asset_type="support services",
            allocation_pct=20.0,
            nia_efficiency=0.6,
            target_floor_height_m=4.5,
            rent_psm_month=7.0,
            fitout_cost_psm=1600,
            absorption_months=9,
            risk_level="moderate",
            notes=[
                "Stack corporate offices and amenities for on-site workforce support."
            ],
        ),
    ],
    "mixed_use": [
        AssetOptimizationPlan(
            asset_type="retail",
            allocation_pct=25.0,
            nia_efficiency=0.65,
            target_floor_height_m=5.0,
            parking_ratio_per_1000sqm=3.0,
            rent_psm_month=17.5,
            fitout_cost_psm=3100,
            absorption_months=11,
            risk_level="balanced",
            notes=[
                "Activate levels 1-3 with F&B and lifestyle retail to anchor placemaking."
            ],
        ),
        AssetOptimizationPlan(
            asset_type="office",
            allocation_pct=40.0,
            nia_efficiency=0.8,
            target_floor_height_m=4.2,
            parking_ratio_per_1000sqm=1.1,
            rent_psm_month=14.0,
            fitout_cost_psm=2700,
            absorption_months=12,
            risk_level="moderate",
            notes=[
                "Mid-rise office floors provide steady NOI and complement retail traffic."
            ],
        ),
        AssetOptimizationPlan(
            asset_type="hospitality",
            allocation_pct=20.0,
            nia_efficiency=0.7,
            target_floor_height_m=3.6,
            parking_ratio_per_1000sqm=0.6,
            rent_psm_month=16.0,
            fitout_cost_psm=2400,
            absorption_months=15,
            risk_level="elevated",
            notes=[
                "Upper floors suited for hospitality or serviced suites to extend stay mix."
            ],
        ),
        AssetOptimizationPlan(
            asset_type="amenities",
            allocation_pct=15.0,
            nia_efficiency=0.5,
            target_floor_height_m=4.0,
            rent_psm_month=0.0,
            fitout_cost_psm=1500,
            absorption_months=6,
            risk_level="low",
            notes=[
                "Allocate sky terraces and shared facilities to differentiate mixed-use stack."
            ],
            heritage_notes=[
                "Ensure façade conservation requirements are met across all uses."
            ],
        ),
    ],
}


def _normalise_land_use(value: str) -> str:
    lowered = value.lower()
    if any(keyword in lowered for keyword in ("residential", "apartment", "condo")):
        return "residential"
    if any(
        keyword in lowered for keyword in ("industrial", "logistics", "manufacturing")
    ):
        return "industrial"
    if any(keyword in lowered for keyword in ("mixed", "integrated")):
        return "mixed_use"
    return "commercial"


def build_asset_mix(
    land_use: str,
    *,
    achievable_gfa_sqm: float | None = None,
    additional_gfa: float | None = None,
    heritage: bool = False,
) -> list[AssetOptimizationPlan]:
    """Return the recommended asset allocation for the provided land use."""

    profile_key = _normalise_land_use(land_use)
    base_profile = _ASSET_PROFILES.get(profile_key) or _ASSET_PROFILES["mixed_use"]
    plans: list[AssetOptimizationPlan] = []
    for plan in base_profile:
        cloned = AssetOptimizationPlan(
            asset_type=plan.asset_type,
            allocation_pct=plan.allocation_pct,
            nia_efficiency=plan.nia_efficiency,
            target_floor_height_m=plan.target_floor_height_m,
            parking_ratio_per_1000sqm=plan.parking_ratio_per_1000sqm,
            heritage_notes=list(plan.heritage_notes),
            notes=list(plan.notes),
            rent_psm_month=plan.rent_psm_month,
            fitout_cost_psm=plan.fitout_cost_psm,
            absorption_months=plan.absorption_months,
            risk_level=plan.risk_level,
        )
        plans.append(cloned)

    if additional_gfa is not None:
        if additional_gfa > 0:
            plans[0].notes.append(
                f"Allocate uplift (~{additional_gfa:,.0f} sqm) to {plans[0].asset_type} floors to maximise value."
            )
        else:
            plans[-1].notes.append(
                "No additional GFA headroom — focus on efficiency and refurbishment scope."
            )

    total_allocation = sum(plan.allocation_pct for plan in plans)
    if total_allocation != 100.0 and total_allocation > 0:
        scale = 100.0 / total_allocation
        for index, plan in enumerate(plans):
            plans[index] = AssetOptimizationPlan(
                asset_type=plan.asset_type,
                allocation_pct=round(plan.allocation_pct * scale, 1),
                nia_efficiency=plan.nia_efficiency,
                target_floor_height_m=plan.target_floor_height_m,
                parking_ratio_per_1000sqm=plan.parking_ratio_per_1000sqm,
                heritage_notes=list(plan.heritage_notes),
                notes=list(plan.notes),
                rent_psm_month=plan.rent_psm_month,
                fitout_cost_psm=plan.fitout_cost_psm,
                absorption_months=plan.absorption_months,
                risk_level=plan.risk_level,
            )

    if achievable_gfa_sqm is not None:
        for index, plan in enumerate(plans):
            allocated = achievable_gfa_sqm * (plan.allocation_pct / 100.0)
            estimated_revenue = None
            estimated_capex = None
            if (
                allocated is not None
                and plan.rent_psm_month
                and plan.rent_psm_month > 0
                and plan.nia_efficiency
            ):
                effective_area = allocated * plan.nia_efficiency
                estimated_revenue = plan.rent_psm_month * 12 * effective_area
            if allocated is not None and plan.fitout_cost_psm:
                estimated_capex = plan.fitout_cost_psm * allocated
            plans[index] = AssetOptimizationPlan(
                asset_type=plan.asset_type,
                allocation_pct=plan.allocation_pct,
                nia_efficiency=plan.nia_efficiency,
                target_floor_height_m=plan.target_floor_height_m,
                parking_ratio_per_1000sqm=plan.parking_ratio_per_1000sqm,
                heritage_notes=list(plan.heritage_notes),
                notes=list(plan.notes),
                allocated_gfa_sqm=allocated,
                rent_psm_month=plan.rent_psm_month,
                fitout_cost_psm=plan.fitout_cost_psm,
                absorption_months=plan.absorption_months,
                risk_level=plan.risk_level,
                estimated_revenue_sgd=estimated_revenue,
                estimated_capex_sgd=estimated_capex,
            )
    if heritage:
        for index, plan in enumerate(plans):
            if plan.heritage_notes:
                augmented_notes = list(plan.notes) + plan.heritage_notes
                plans[index] = AssetOptimizationPlan(
                    asset_type=plan.asset_type,
                    allocation_pct=plan.allocation_pct,
                    nia_efficiency=plan.nia_efficiency,
                    target_floor_height_m=plan.target_floor_height_m,
                    parking_ratio_per_1000sqm=plan.parking_ratio_per_1000sqm,
                    heritage_notes=list(plan.heritage_notes),
                    notes=augmented_notes,
                    allocated_gfa_sqm=plan.allocated_gfa_sqm,
                    rent_psm_month=plan.rent_psm_month,
                    fitout_cost_psm=plan.fitout_cost_psm,
                    absorption_months=plan.absorption_months,
                    risk_level=plan.risk_level,
                    estimated_revenue_sgd=plan.estimated_revenue_sgd,
                    estimated_capex_sgd=plan.estimated_capex_sgd,
                )

    return plans


def format_asset_mix_summary(
    plans: Iterable[AssetOptimizationPlan],
    achievable_gfa_sqm: int,
) -> list[str]:
    """Return human-readable recommendations for asset optimisation."""

    recommendations: list[str] = []
    mix_summary = ", ".join(
        f"{plan.asset_type.replace('_', ' ').capitalize()} {plan.allocation_pct:.0f}%"
        for plan in plans
    )
    recommendations.append(
        f"Programme allocation: {mix_summary} based on achievable {achievable_gfa_sqm:,} sqm GFA."
    )
    for plan in plans:
        recommendations.extend(plan.notes)
        if plan.heritage_notes:
            recommendations.extend(plan.heritage_notes)
        if plan.allocated_gfa_sqm is not None:
            recommendations.append(
                f"{plan.asset_type.replace('_', ' ').capitalize()} allocation ≈ {plan.allocated_gfa_sqm:,.0f} sqm GFA."
            )
        if plan.estimated_revenue_sgd is not None and plan.estimated_revenue_sgd > 0:
            recommendations.append(
                f"Projected annual revenue for {plan.asset_type} ≈ ${plan.estimated_revenue_sgd:,.0f}."
            )
        if plan.estimated_capex_sgd is not None and plan.estimated_capex_sgd > 0:
            recommendations.append(
                f"Indicative fit-out CAPEX for {plan.asset_type} ≈ ${plan.estimated_capex_sgd:,.0f}."
            )
        if plan.risk_level:
            absorption = (
                f"absorption ≈ {plan.absorption_months} months"
                if plan.absorption_months
                else "absorption timeline pending"
            )
            recommendations.append(
                f"{plan.asset_type.replace('_', ' ').capitalize()} risk profile: {plan.risk_level.title()} ({absorption})."
            )
    return recommendations


__all__ = ["AssetOptimizationPlan", "build_asset_mix", "format_asset_mix_summary"]
