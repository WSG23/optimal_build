"""Asset mix and optimisation helpers for developer feasibility."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from importlib import resources
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


_PROFILE_CONFIG = {
    "commercial": {
        "primary": "office",
        "secondary": "retail",
        "tertiary": None,
        "amenities": "amenities",
    },
    "mixed_use": {
        "primary": "office",
        "secondary": "retail",
        "tertiary": "hospitality",
        "amenities": "amenities",
    },
}


def _load_curve_config() -> dict[str, object]:
    default: dict[str, object] = {
        "expansion": {
            "primary": 6.0,
            "primary_high": 9.0,
            "secondary": 2.0,
            "secondary_high": 3.0,
            "tertiary": 1.0,
            "tertiary_high": 2.0,
        },
        "reposition": {"primary": -5.0, "secondary": -2.5, "tertiary": -1.5},
        "vacancy": {"high": 0.15, "low": 0.05},
        "rent_soft_threshold_psm": 100.0,
        "transit_min_mrt": 1.0,
        "plot_ratio_headroom": {"significant": 0.35, "limited": 0.1},
        "absorption": {
            "vacancy_high": 3,
            "vacancy_low": -1,
            "heritage_high": 6,
            "heritage_medium": 3,
            "expansion": 4,
        },
    }

    try:
        text = (
            resources.files("app.data")
            .joinpath("asset_mix_curves.json")
            .read_text(encoding="utf-8")
        )
        data = json.loads(text)
        default.update(data)
    except FileNotFoundError:
        pass
    except OSError:
        pass
    except json.JSONDecodeError:
        pass

    return default


_CURVE_CONFIG = _load_curve_config()


def _maybe_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _maybe_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _load_asset_profiles() -> dict[str, list[AssetOptimizationPlan]]:
    try:
        profile_text = (
            resources.files("app.data")
            .joinpath("asset_mix_profiles.json")
            .read_text(encoding="utf-8")
        )
    except FileNotFoundError as exc:  # pragma: no cover - defensive
        raise RuntimeError("Missing asset mix configuration file") from exc
    except OSError as exc:  # pragma: no cover - defensive
        raise RuntimeError("Unable to load asset mix configuration") from exc

    try:
        raw_profiles: dict[str, list[dict[str, object]]] = json.loads(profile_text)
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        raise RuntimeError("Invalid asset mix configuration JSON") from exc

    profiles: dict[str, list[AssetOptimizationPlan]] = {}
    for profile_key, entries in raw_profiles.items():
        plans: list[AssetOptimizationPlan] = []
        for entry in entries:
            plan = AssetOptimizationPlan(
                asset_type=str(entry["asset_type"]),
                allocation_pct=float(entry["allocation_pct"]),
                stabilised_vacancy_pct=_maybe_float(
                    entry.get("stabilised_vacancy_pct")
                ),
                opex_pct_of_rent=_maybe_float(entry.get("opex_pct_of_rent")),
                nia_efficiency=_maybe_float(entry.get("nia_efficiency")),
                target_floor_height_m=_maybe_float(entry.get("target_floor_height_m")),
                parking_ratio_per_1000sqm=_maybe_float(
                    entry.get("parking_ratio_per_1000sqm")
                ),
                heritage_notes=list(entry.get("heritage_notes") or []),
                notes=list(entry.get("notes") or []),
                rent_psm_month=_maybe_float(entry.get("rent_psm_month")),
                fitout_cost_psm=_maybe_float(entry.get("fitout_cost_psm")),
                absorption_months=_maybe_int(entry.get("absorption_months")),
                risk_level=(
                    str(entry.get("risk_level")) if entry.get("risk_level") else None
                ),
                heritage_premium_pct=_maybe_float(entry.get("heritage_premium_pct")),
            )
            plans.append(plan)
        profiles[profile_key] = plans
    return profiles


_ASSET_PROFILES = _load_asset_profiles()


def _calc_additional_ratio(
    achievable_gfa: float | None, additional_gfa: float | None
) -> float | None:
    if achievable_gfa is None or achievable_gfa <= 0 or additional_gfa is None:
        return None
    ratio = additional_gfa / achievable_gfa
    if ratio > 1.5:
        return 1.5
    if ratio < -0.5:
        return -0.5
    return ratio


def _intensity_state(additional_ratio: float | None) -> str:
    if additional_ratio is None:
        return "steady"
    if additional_ratio >= 0.35:
        return "expansion_high"
    if additional_ratio >= 0.2:
        return "expansion"
    if additional_ratio <= 0.05:
        return "reposition"
    return "steady"


def _update_allocation(
    plan_lookup: dict[str, AssetOptimizationPlan], asset_type: str | None, delta: float
) -> None:
    if not asset_type or not delta:
        return
    plan = plan_lookup.get(asset_type)
    if plan is None:
        return
    plan_lookup[asset_type] = replace(plan, allocation_pct=plan.allocation_pct + delta)


def _append_plan_note(
    plan_lookup: dict[str, AssetOptimizationPlan], asset_type: str | None, note: str
) -> None:
    if not asset_type or not note:
        return
    plan = plan_lookup.get(asset_type)
    if plan is None:
        return
    notes = list(plan.notes)
    if note not in notes:
        notes.append(note)
        plan_lookup[asset_type] = replace(plan, notes=notes)


def _set_plan_risk(
    plan_lookup: dict[str, AssetOptimizationPlan],
    asset_type: str | None,
    risk_level: str,
    absorption_delta: int = 0,
    note: str | None = None,
) -> None:
    if not asset_type:
        return
    plan = plan_lookup.get(asset_type)
    if plan is None:
        return
    absorption_months = plan.absorption_months
    if absorption_delta:
        base = absorption_months if absorption_months is not None else 12
        absorption_months = max(1, base + absorption_delta)
    updated = replace(plan, risk_level=risk_level, absorption_months=absorption_months)
    if note:
        notes = list(updated.notes)
        if note not in notes:
            notes.append(note)
            updated = replace(updated, notes=notes)
    plan_lookup[asset_type] = updated


def _apply_existing_use_bias(
    plan_lookup: dict[str, AssetOptimizationPlan],
    profile_key: str,
    existing_use: str | None,
) -> None:
    if not existing_use:
        return
    use_lower = existing_use.lower()
    config = _PROFILE_CONFIG.get(profile_key)
    if not config:
        return

    if any(token in use_lower for token in ("retail", "mall", "shopping")):
        _update_allocation(plan_lookup, config.get("secondary"), 3.0)
        _update_allocation(plan_lookup, config.get("primary"), -3.0)
        _append_plan_note(
            plan_lookup,
            config.get("secondary"),
            "Existing tenancy mix leans retail-heavy; maintaining activation at podium.",
        )
    if any(token in use_lower for token in ("hotel", "hospitality")):
        tertiary = config.get("tertiary") or config.get("secondary")
        _update_allocation(plan_lookup, tertiary, 3.0)
        _update_allocation(plan_lookup, config.get("primary"), -3.0)
        _append_plan_note(
            plan_lookup,
            tertiary,
            "Legacy hospitality operations retained as part of repositioning.",
        )
    if "office" in use_lower and profile_key == "mixed_use":
        _update_allocation(plan_lookup, config.get("primary"), 2.0)
        _update_allocation(plan_lookup, config.get("secondary"), -2.0)


def _rebalance_plans(plans: list[AssetOptimizationPlan]) -> list[AssetOptimizationPlan]:
    total = sum(plan.allocation_pct for plan in plans)
    if total <= 0:
        return plans
    if abs(total - 100.0) <= 0.01:
        return plans
    scale = 100.0 / total
    rebalanced: list[AssetOptimizationPlan] = []
    for plan in plans:
        rebalanced.append(
            replace(
                plan,
                allocation_pct=round(plan.allocation_pct * scale, 1),
            )
        )
    correction = 100.0 - sum(plan.allocation_pct for plan in rebalanced)
    if rebalanced:
        last = rebalanced[-1]
        rebalanced[-1] = replace(
            last, allocation_pct=round(last.allocation_pct + correction, 1)
        )
    return rebalanced


def _apply_plot_ratio_context(
    plan_lookup: dict[str, AssetOptimizationPlan],
    profile_key: str,
    *,
    site_area_sqm: float | None,
    current_gfa_sqm: float | None,
    achievable_gfa_sqm: float | None,
) -> None:
    if not site_area_sqm or site_area_sqm <= 0 or current_gfa_sqm is None:
        return
    actual_ratio = current_gfa_sqm / site_area_sqm
    target_gfa = (
        achievable_gfa_sqm if achievable_gfa_sqm is not None else current_gfa_sqm
    )
    achievable_ratio = target_gfa / site_area_sqm
    headroom = achievable_ratio - actual_ratio

    config = _PROFILE_CONFIG.get(profile_key) or {}
    primary = config.get("primary")
    if primary:
        thresholds = _CURVE_CONFIG.get("plot_ratio_headroom", {})
        limited = float(thresholds.get("limited", 0.1))
        significant = float(thresholds.get("significant", 0.35))
        note = f"Existing plot ratio {actual_ratio:.2f}; headroom {headroom:.2f} to target envelope."
        _append_plan_note(plan_lookup, primary, note)
        if headroom < limited:
            _set_plan_risk(
                plan_lookup,
                primary,
                "balanced",
                absorption_delta=_CURVE_CONFIG.get("absorption", {}).get(
                    "vacancy_low", -1
                ),
                note="Limited plot ratio headroom — focus on efficiency gains.",
            )
        elif headroom > significant:
            _append_plan_note(
                plan_lookup,
                primary,
                "Significant plot ratio headroom supports vertical expansion.",
            )


def _apply_market_adjustments(
    plan_lookup: dict[str, AssetOptimizationPlan],
    profile_key: str,
    quick_metrics: dict[str, float | str] | None,
) -> None:
    if not quick_metrics:
        return
    config = _PROFILE_CONFIG.get(profile_key) or {}
    primary = config.get("primary")
    amenities = config.get("amenities")
    secondary = config.get("secondary")

    vacancy_thresholds = _CURVE_CONFIG.get("vacancy", {})
    vacancy_high = float(vacancy_thresholds.get("high", 0.15))
    vacancy_low = float(vacancy_thresholds.get("low", 0.05))
    vacancy_value = quick_metrics.get("existing_vacancy_rate")
    if isinstance(vacancy_value, (int, float)):
        vacancy = float(vacancy_value)
        if vacancy > 1:
            vacancy /= 100
        if vacancy >= vacancy_high:
            _update_allocation(plan_lookup, primary, -4.0)
            _update_allocation(plan_lookup, amenities, 4.0)
            _set_plan_risk(
                plan_lookup,
                primary,
                "moderate",
                absorption_delta=_CURVE_CONFIG.get("absorption", {}).get(
                    "vacancy_high", 3
                ),
                note="Elevated vacancy in existing asset—prioritise amenity improvements.",
            )
            _append_plan_note(
                plan_lookup,
                amenities,
                "Allocate additional floor area to amenities to lift utilisation.",
            )
        elif vacancy <= vacancy_low:
            _append_plan_note(
                plan_lookup,
                primary,
                "Strong occupancy tailwind — maintain prime positioning.",
            )

    avg_rent = quick_metrics.get("existing_average_rent_psm")
    if isinstance(avg_rent, (int, float)):
        rent_value = float(avg_rent)
        rent_threshold = float(_CURVE_CONFIG.get("rent_soft_threshold_psm", 100.0))
        if rent_value < rent_threshold and secondary:
            _update_allocation(plan_lookup, primary, -2.0)
            _update_allocation(plan_lookup, secondary, 2.0)
            _append_plan_note(
                plan_lookup,
                secondary,
                "Rebalance mix toward higher-yield components given soft existing rents.",
            )

    mrt_count = quick_metrics.get("underused_mrt_count")
    min_mrt = float(_CURVE_CONFIG.get("transit_min_mrt", 1.0))
    if isinstance(mrt_count, (int, float)) and mrt_count < min_mrt and amenities:
        _append_plan_note(
            plan_lookup,
            amenities,
            "Limited transit access — budget for last-mile solutions within amenity stack.",
        )


def _apply_intensity_adjustments(
    plans: list[AssetOptimizationPlan],
    profile_key: str,
    achievable_gfa_sqm: float | None,
    additional_gfa: float | None,
    existing_use: str | None,
    *,
    site_area_sqm: float | None,
    current_gfa_sqm: float | None,
    quick_metrics: dict[str, float | str] | None,
) -> list[AssetOptimizationPlan]:
    config = _PROFILE_CONFIG.get(profile_key)
    if not config:
        return plans

    ratio = _calc_additional_ratio(achievable_gfa_sqm, additional_gfa)
    state = _intensity_state(ratio)

    plan_lookup: dict[str, AssetOptimizationPlan] = {
        plan.asset_type: plan for plan in plans
    }
    order = [plan.asset_type for plan in plans]

    expansion_cfg = _CURVE_CONFIG.get("expansion", {})
    reposition_cfg = _CURVE_CONFIG.get("reposition", {})

    if state in {"expansion", "expansion_high"}:
        primary_delta = (
            expansion_cfg.get("primary", 6.0)
            if state == "expansion"
            else expansion_cfg.get("primary_high", 9.0)
        )
        secondary_delta = (
            expansion_cfg.get("secondary", 2.0) if config.get("secondary") else 0.0
        )
        if state == "expansion_high" and config.get("secondary"):
            secondary_delta = expansion_cfg.get("secondary_high", secondary_delta)
        tertiary_delta = 0.0
        if config.get("tertiary"):
            tertiary_delta = expansion_cfg.get("tertiary", 1.0)
            if state == "expansion_high":
                tertiary_delta = expansion_cfg.get("tertiary_high", tertiary_delta)
        amenities_delta = -(primary_delta + secondary_delta + tertiary_delta)

        _update_allocation(plan_lookup, config.get("primary"), primary_delta)
        _update_allocation(plan_lookup, config.get("secondary"), secondary_delta)
        if tertiary_delta:
            _update_allocation(plan_lookup, config.get("tertiary"), tertiary_delta)
        _update_allocation(plan_lookup, config.get("amenities"), amenities_delta)

        note = "Elevated density to absorb additional GFA uplift."
        for asset in filter(
            None,
            [
                config.get("primary"),
                config.get("secondary"),
                config.get("tertiary"),
            ],
        ):
            _set_plan_risk(
                plan_lookup,
                asset,
                "elevated",
                _CURVE_CONFIG.get("absorption", {}).get("expansion", 4),
                note,
            )

    elif state == "reposition":
        primary_delta = reposition_cfg.get("primary", -5.0)
        secondary_delta = (
            reposition_cfg.get("secondary", -2.5) if config.get("secondary") else 0.0
        )
        tertiary_delta = (
            reposition_cfg.get("tertiary", -1.5) if config.get("tertiary") else 0.0
        )
        amenities_delta = -(primary_delta + secondary_delta + tertiary_delta)

        _update_allocation(plan_lookup, config.get("primary"), primary_delta)
        _update_allocation(plan_lookup, config.get("secondary"), secondary_delta)
        if tertiary_delta:
            _update_allocation(plan_lookup, config.get("tertiary"), tertiary_delta)
        _update_allocation(plan_lookup, config.get("amenities"), amenities_delta)

        note = (
            "Heritage and existing conditions favour adaptive reuse over densification."
        )
        for asset in filter(
            None,
            [
                config.get("primary"),
                config.get("secondary"),
                config.get("tertiary"),
            ],
        ):
            _set_plan_risk(
                plan_lookup,
                asset,
                "balanced",
                -2,
                note,
            )

    _apply_existing_use_bias(plan_lookup, profile_key, existing_use)

    for asset_type, plan in list(plan_lookup.items()):
        if plan.allocation_pct < 0.0:
            plan_lookup[asset_type] = replace(plan, allocation_pct=0.0)

    _apply_market_adjustments(plan_lookup, profile_key, quick_metrics)
    _apply_plot_ratio_context(
        plan_lookup,
        profile_key,
        site_area_sqm=site_area_sqm,
        current_gfa_sqm=current_gfa_sqm,
        achievable_gfa_sqm=achievable_gfa_sqm,
    )

    plans = [plan_lookup[asset] for asset in order if asset in plan_lookup]
    return _rebalance_plans(plans)


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
    heritage_risk: str | None = None,
    existing_use: str | None = None,
    site_area_sqm: float | None = None,
    current_gfa_sqm: float | None = None,
    quick_metrics: dict[str, float | str] | None = None,
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

    plans = _apply_intensity_adjustments(
        plans,
        profile_key,
        achievable_gfa_sqm,
        additional_gfa,
        existing_use,
        site_area_sqm=site_area_sqm,
        current_gfa_sqm=current_gfa_sqm,
        quick_metrics=quick_metrics,
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

    if heritage_risk:
        severity_map = {"high": "elevated", "medium": "moderate", "low": "balanced"}
        risk_level = severity_map.get(heritage_risk.lower())
        if risk_level:
            note = (
                "Heritage overlay requires specialist conservation strategy."
                if heritage_risk.lower() == "high"
                else "Heritage compliance buffers applied to programme mix."
            )
            for index, plan in enumerate(plans):
                updated = replace(plan, risk_level=risk_level)
                absorption_months = updated.absorption_months
                if heritage_risk.lower() == "high":
                    base_absorption = (
                        absorption_months if absorption_months is not None else 12
                    )
                    heritage_adj = _CURVE_CONFIG.get("absorption", {}).get(
                        "heritage_high", 6
                    )
                    absorption_months = max(1, base_absorption + heritage_adj)
                elif heritage_risk.lower() == "medium":
                    base_absorption = (
                        absorption_months if absorption_months is not None else 12
                    )
                    heritage_adj = _CURVE_CONFIG.get("absorption", {}).get(
                        "heritage_medium", 3
                    )
                    absorption_months = max(1, base_absorption + heritage_adj)
                updated = replace(updated, absorption_months=absorption_months)
                notes = list(updated.notes)
                if note not in notes:
                    notes.append(note)
                    updated = replace(updated, notes=notes)
                plans[index] = updated

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
