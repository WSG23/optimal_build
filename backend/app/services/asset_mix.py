"""Asset mix and optimisation helpers for developer feasibility."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass(frozen=True, slots=True)
class AssetOptimizationPlan:
    """Represents an allocation recommendation for a specific asset type."""

    asset_type: str
    allocation_pct: float
    stabilised_vacancy_pct: float | None = None
    opex_pct_of_rent: float | None = None
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
    heritage_premium_pct: float | None = None


_ASSET_PROFILES: dict[str, list[AssetOptimizationPlan]] = {
    "commercial": [
        AssetOptimizationPlan(
            asset_type="office",
            allocation_pct=60.0,
            stabilised_vacancy_pct=6.0,
            opex_pct_of_rent=18.0,
            nia_efficiency=0.82,
            target_floor_height_m=4.2,
            parking_ratio_per_1000sqm=0.8,
            rent_psm_month=128.0,
            fitout_cost_psm=1500.0,
            absorption_months=12,
            risk_level="moderate",
            heritage_premium_pct=5.0,
            notes=[
                "Grade A office baseline aligns with Phase 2B template (CBD core rent ≈ $12 psf/month).",
            ],
        ),
        AssetOptimizationPlan(
            asset_type="retail",
            allocation_pct=25.0,
            stabilised_vacancy_pct=4.0,
            opex_pct_of_rent=22.0,
            nia_efficiency=0.75,
            target_floor_height_m=5.0,
            parking_ratio_per_1000sqm=2.5,
            rent_psm_month=360.0,
            fitout_cost_psm=2200.0,
            absorption_months=9,
            risk_level="balanced",
            heritage_premium_pct=8.0,
            notes=[
                "Prime retail podium benchmark (Orchard/Marina) with void allowances baked into efficiency.",
            ],
        ),
        AssetOptimizationPlan(
            asset_type="amenities",
            allocation_pct=15.0,
            stabilised_vacancy_pct=12.0,
            opex_pct_of_rent=30.0,
            nia_efficiency=0.85,
            target_floor_height_m=4.5,
            parking_ratio_per_1000sqm=1.2,
            rent_psm_month=25.0,
            fitout_cost_psm=900.0,
            absorption_months=16,
            risk_level="low",
            heritage_premium_pct=10.0,
            notes=[
                "Community amenities baseline covering childcare, healthcare, and shared services.",
            ],
        ),
    ],
    "residential": [
        AssetOptimizationPlan(
            asset_type="residential",
            allocation_pct=70.0,
            stabilised_vacancy_pct=7.0,
            opex_pct_of_rent=25.0,
            nia_efficiency=0.78,
            target_floor_height_m=3.2,
            parking_ratio_per_1000sqm=1.0,
            rent_psm_month=65.0,
            fitout_cost_psm=1100.0,
            absorption_months=18,
            risk_level="moderate",
            heritage_premium_pct=5.0,
            notes=[
                "CCR condominium launch benchmark with blended unit mix and 18-month absorption.",
            ],
        ),
        AssetOptimizationPlan(
            asset_type="serviced_apartments",
            allocation_pct=20.0,
            stabilised_vacancy_pct=10.0,
            opex_pct_of_rent=35.0,
            nia_efficiency=0.74,
            target_floor_height_m=3.4,
            parking_ratio_per_1000sqm=0.6,
            rent_psm_month=110.0,
            fitout_cost_psm=1400.0,
            absorption_months=12,
            risk_level="balanced",
            heritage_premium_pct=7.0,
            notes=[
                "Serviced apartment stack assumes ADR ≈ $310 with 72% occupancy.",
            ],
        ),
        AssetOptimizationPlan(
            asset_type="amenities",
            allocation_pct=10.0,
            stabilised_vacancy_pct=12.0,
            opex_pct_of_rent=30.0,
            nia_efficiency=0.85,
            target_floor_height_m=3.5,
            parking_ratio_per_1000sqm=1.2,
            rent_psm_month=25.0,
            fitout_cost_psm=900.0,
            absorption_months=16,
            risk_level="low",
            heritage_premium_pct=10.0,
            notes=[
                "Residential podium amenities include wellness, childcare, and co-working lounges.",
            ],
        ),
    ],
    "industrial": [
        AssetOptimizationPlan(
            asset_type="high-spec logistics",
            allocation_pct=50.0,
            stabilised_vacancy_pct=6.0,
            opex_pct_of_rent=15.0,
            nia_efficiency=0.88,
            target_floor_height_m=12.0,
            parking_ratio_per_1000sqm=1.3,
            rent_psm_month=26.0,
            fitout_cost_psm=850.0,
            absorption_months=8,
            risk_level="balanced",
            notes=[
                "High-spec logistics profile with 12m clear heights and ramp access for e-commerce operators.",
            ],
        ),
        AssetOptimizationPlan(
            asset_type="production",
            allocation_pct=30.0,
            stabilised_vacancy_pct=9.0,
            opex_pct_of_rent=18.0,
            nia_efficiency=0.86,
            target_floor_height_m=8.0,
            parking_ratio_per_1000sqm=1.8,
            rent_psm_month=19.0,
            fitout_cost_psm=950.0,
            absorption_months=10,
            risk_level="elevated",
            notes=[
                "Advanced manufacturing allowance with 12kN/m² loading and flexible M&E trunks.",
            ],
        ),
        AssetOptimizationPlan(
            asset_type="support services",
            allocation_pct=20.0,
            stabilised_vacancy_pct=12.0,
            opex_pct_of_rent=30.0,
            nia_efficiency=0.85,
            target_floor_height_m=3.5,
            parking_ratio_per_1000sqm=1.2,
            rent_psm_month=25.0,
            fitout_cost_psm=900.0,
            absorption_months=16,
            risk_level="moderate",
            heritage_premium_pct=10.0,
            notes=[
                "On-site workforce support (canteen, offices, clinics) using community amenity baseline.",
            ],
        ),
    ],
    "mixed_use": [
        AssetOptimizationPlan(
            asset_type="retail",
            allocation_pct=25.0,
            stabilised_vacancy_pct=5.0,
            opex_pct_of_rent=22.0,
            nia_efficiency=0.72,
            target_floor_height_m=4.8,
            parking_ratio_per_1000sqm=2.0,
            rent_psm_month=320.0,
            fitout_cost_psm=2100.0,
            absorption_months=12,
            risk_level="balanced",
            heritage_premium_pct=8.0,
            notes=[
                "Integrated development podium retail anchored by F&B and lifestyle clusters.",
            ],
        ),
        AssetOptimizationPlan(
            asset_type="office",
            allocation_pct=40.0,
            stabilised_vacancy_pct=6.0,
            opex_pct_of_rent=19.0,
            nia_efficiency=0.80,
            target_floor_height_m=4.1,
            parking_ratio_per_1000sqm=1.0,
            rent_psm_month=118.0,
            fitout_cost_psm=1400.0,
            absorption_months=12,
            risk_level="moderate",
            heritage_premium_pct=6.0,
            notes=[
                "Fringe CBD office stack complementing podium activation and providing steady NOI.",
            ],
        ),
        AssetOptimizationPlan(
            asset_type="hospitality",
            allocation_pct=20.0,
            stabilised_vacancy_pct=28.0,
            opex_pct_of_rent=43.0,
            nia_efficiency=0.60,
            target_floor_height_m=4.2,
            parking_ratio_per_1000sqm=0.8,
            rent_psm_month=190.0,
            fitout_cost_psm=3600.0,
            absorption_months=15,
            risk_level="elevated",
            heritage_premium_pct=15.0,
            notes=[
                "Hospitality stack assumes blended serviced hotel RevPAR with extended-stay offering.",
            ],
        ),
        AssetOptimizationPlan(
            asset_type="amenities",
            allocation_pct=15.0,
            stabilised_vacancy_pct=12.0,
            opex_pct_of_rent=30.0,
            nia_efficiency=0.85,
            target_floor_height_m=3.5,
            parking_ratio_per_1000sqm=1.2,
            rent_psm_month=25.0,
            fitout_cost_psm=900.0,
            absorption_months=16,
            risk_level="low",
            heritage_premium_pct=10.0,
            notes=[
                "Sky terraces and shared facilities to differentiate the mixed-use stack.",
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
            stabilised_vacancy_pct=plan.stabilised_vacancy_pct,
            opex_pct_of_rent=plan.opex_pct_of_rent,
            nia_efficiency=plan.nia_efficiency,
            target_floor_height_m=plan.target_floor_height_m,
            parking_ratio_per_1000sqm=plan.parking_ratio_per_1000sqm,
            heritage_notes=list(plan.heritage_notes),
            notes=list(plan.notes),
            rent_psm_month=plan.rent_psm_month,
            fitout_cost_psm=plan.fitout_cost_psm,
            absorption_months=plan.absorption_months,
            risk_level=plan.risk_level,
            heritage_premium_pct=plan.heritage_premium_pct,
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
                stabilised_vacancy_pct=plan.stabilised_vacancy_pct,
                opex_pct_of_rent=plan.opex_pct_of_rent,
                nia_efficiency=plan.nia_efficiency,
                target_floor_height_m=plan.target_floor_height_m,
                parking_ratio_per_1000sqm=plan.parking_ratio_per_1000sqm,
                heritage_notes=list(plan.heritage_notes),
                notes=list(plan.notes),
                rent_psm_month=plan.rent_psm_month,
                fitout_cost_psm=plan.fitout_cost_psm,
                absorption_months=plan.absorption_months,
                risk_level=plan.risk_level,
                heritage_premium_pct=plan.heritage_premium_pct,
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
                gross_revenue = plan.rent_psm_month * 12 * effective_area
                vacancy_multiplier = 1.0 - (plan.stabilised_vacancy_pct or 0.0) / 100.0
                opex_multiplier = 1.0 - (plan.opex_pct_of_rent or 0.0) / 100.0
                estimated_revenue = (
                    gross_revenue
                    * max(vacancy_multiplier, 0.0)
                    * max(opex_multiplier, 0.0)
                )
            if allocated is not None and plan.fitout_cost_psm:
                heritage_multiplier = 1.0
                if heritage and plan.heritage_premium_pct:
                    heritage_multiplier += plan.heritage_premium_pct / 100.0
                estimated_capex = plan.fitout_cost_psm * heritage_multiplier * allocated
            plans[index] = AssetOptimizationPlan(
                asset_type=plan.asset_type,
                allocation_pct=plan.allocation_pct,
                stabilised_vacancy_pct=plan.stabilised_vacancy_pct,
                opex_pct_of_rent=plan.opex_pct_of_rent,
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
                heritage_premium_pct=plan.heritage_premium_pct,
            )
    if heritage:
        for index, plan in enumerate(plans):
            if plan.heritage_notes:
                augmented_notes = list(plan.notes) + plan.heritage_notes
                if plan.heritage_premium_pct:
                    augmented_notes.append(
                        f"Heritage premium applied (+{plan.heritage_premium_pct:.0f}% fit-out uplift)."
                    )
                plans[index] = AssetOptimizationPlan(
                    asset_type=plan.asset_type,
                    allocation_pct=plan.allocation_pct,
                    stabilised_vacancy_pct=plan.stabilised_vacancy_pct,
                    opex_pct_of_rent=plan.opex_pct_of_rent,
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
                    heritage_premium_pct=plan.heritage_premium_pct,
                )

    return plans


def _format_asset_label(value: str) -> str:
    cleaned = value.replace("_", " ").strip()
    if not cleaned:
        return value
    return cleaned.title() if cleaned.lower() == cleaned else cleaned


def format_asset_mix_summary(
    plans: Iterable[AssetOptimizationPlan],
    achievable_gfa_sqm: int,
) -> list[str]:
    """Return human-readable recommendations for asset optimisation."""

    recommendations: list[str] = []
    mix_summary = ", ".join(
        f"{_format_asset_label(plan.asset_type)} {plan.allocation_pct:.0f}%"
        for plan in plans
    )
    recommendations.append(
        f"Programme allocation: {mix_summary} based on achievable {achievable_gfa_sqm:,} sqm GFA."
    )
    for plan in plans:
        label = _format_asset_label(plan.asset_type)
        recommendations.extend(plan.notes)
        if plan.heritage_notes:
            recommendations.extend(plan.heritage_notes)
        if plan.allocated_gfa_sqm is not None:
            recommendations.append(
                f"{label} allocation ≈ {plan.allocated_gfa_sqm:,.0f} sqm GFA."
            )
        if plan.estimated_revenue_sgd is not None and plan.estimated_revenue_sgd > 0:
            recommendations.append(
                f"Projected annual NOI for {label} ≈ ${plan.estimated_revenue_sgd:,.0f}."
            )
        if plan.estimated_capex_sgd is not None and plan.estimated_capex_sgd > 0:
            recommendations.append(
                f"Indicative fit-out CAPEX for {label} ≈ ${plan.estimated_capex_sgd:,.0f}."
            )
        if plan.stabilised_vacancy_pct is not None or plan.opex_pct_of_rent is not None:
            vacancy = (
                f"{plan.stabilised_vacancy_pct:.0f}% vacancy"
                if plan.stabilised_vacancy_pct is not None
                else "vacancy n/a"
            )
            opex = (
                f"{plan.opex_pct_of_rent:.0f}% OPEX"
                if plan.opex_pct_of_rent is not None
                else "OPEX n/a"
            )
            recommendations.append(f"{label} stabilised profile: {vacancy}, {opex}.")
        if plan.risk_level:
            absorption = (
                f"absorption ≈ {plan.absorption_months} months"
                if plan.absorption_months
                else "absorption timeline pending"
            )
            recommendations.append(
                f"{label} risk profile: {plan.risk_level.title()} ({absorption})."
            )
    return recommendations


__all__ = ["AssetOptimizationPlan", "build_asset_mix", "format_asset_mix_summary"]
