"""Standalone developer deal calculator endpoint."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from math import ceil
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend._compat.datetime import utcnow
from app.api.deps import require_viewer
from app.core.database import get_session
from app.schemas.buildable import BuildableDefaults
from app.schemas.deal_calculator import (
    DealCalculatorCoordinates,
    DealCalculatorFinanceSummary,
    DealCalculatorRequest,
    DealCalculatorResponse,
    DealCalculatorSiteSummary,
)
from app.schemas.feasibility import BuildEnvelopeSnapshot, FeasibilityAssessmentRequest, NewFeasibilityProjectInput
from app.services.agents.ura_integration import URAIntegrationService
from app.services.buildable import BuildableService, BuildableInput
from app.services.finance import (
    AssetFinanceInput,
    build_asset_financials,
    calculate_comprehensive_metrics,
    irr,
    npv,
    serialise_breakdown,
    summarise_asset_financials,
)
from app.services.feasibility import generate_feasibility_rules, run_feasibility_assessment
from app.services.geocoding import Address, GeocodingService

router = APIRouter(prefix="/developers/deal-calculator", tags=["developers"])
geocoding_service = GeocodingService()
ura_service = URAIntegrationService()

_MONEY = Decimal("0.01")
_RATIO = Decimal("0.0001")


def _to_decimal(value: object | None) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _quantize_money(value: Decimal | None) -> Decimal | None:
    if value is None:
        return None
    return value.quantize(_MONEY, rounding=ROUND_HALF_UP)


def _quantize_ratio(value: Decimal | None) -> Decimal | None:
    if value is None:
        return None
    return value.quantize(_RATIO, rounding=ROUND_HALF_UP)


def _fraction_from_pct(value: float) -> Decimal:
    return Decimal(str(value)) / Decimal("100")


def _infer_land_use(
    requested_land_use: str | None,
    zone_description: str | None,
    existing_use: str | None,
    zone_code: str | None,
) -> str:
    if requested_land_use and requested_land_use.strip():
        return requested_land_use.strip().lower().replace(" ", "_")

    candidates = [
        (zone_description or "").lower(),
        (existing_use or "").lower(),
        (zone_code or "").lower(),
    ]
    if any("residential" in item or item.startswith("r") for item in candidates):
        return "residential"
    if any("industrial" in item or "business" in item or item.startswith("b") for item in candidates):
        return "industrial"
    if any("mixed" in item or item.startswith("mu") for item in candidates):
        return "mixed_use"
    return "commercial"


def _build_source_reference(zone_source: dict[str, Any], ura_source_provider: str | None) -> str | None:
    source_parts: list[str] = []
    parcel_source = zone_source.get("parcel_source")
    note = zone_source.get("note")
    jurisdiction = zone_source.get("jurisdiction")
    if parcel_source:
        source_parts.append(str(parcel_source))
    if jurisdiction:
        source_parts.append(str(jurisdiction))
    if ura_source_provider:
        source_parts.append(ura_source_provider)
    if note:
        source_parts.append(str(note))
    if not source_parts:
        return None
    return " | ".join(source_parts)


def _build_finance_inputs(asset_optimizations: list[Any]) -> list[AssetFinanceInput]:
    return [
        AssetFinanceInput(
            asset_type=entry.asset_type,
            allocation_pct=_to_decimal(entry.allocation_pct),
            nia_sqm=_to_decimal(entry.nia_sqm),
            rent_psm_month=_to_decimal(entry.rent_psm_month),
            stabilised_vacancy_pct=_to_decimal(entry.stabilised_vacancy_pct),
            opex_pct_of_rent=_to_decimal(entry.opex_pct_of_rent),
            estimated_revenue_sgd=_to_decimal(entry.estimated_revenue_sgd),
            estimated_capex_sgd=_to_decimal(entry.estimated_capex_sgd),
            absorption_months=_to_decimal(entry.absorption_months),
            risk_level=entry.risk_level,
            heritage_premium_pct=_to_decimal(entry.heritage_premium_pct),
            notes=tuple(entry.notes),
        )
        for entry in asset_optimizations
    ]


def _average_absorption_years(asset_optimizations: list[Any]) -> int:
    months = [
        float(entry.absorption_months)
        for entry in asset_optimizations
        if entry.absorption_months is not None
    ]
    if not months:
        return 1
    return max(1, ceil((sum(months) / len(months)) / 12))


def _build_finance_summary(
    *,
    asset_optimizations: list[Any],
    financing: Any,
) -> tuple[DealCalculatorFinanceSummary, list[Any], Any | None]:
    finance_inputs = _build_finance_inputs(asset_optimizations)
    breakdowns_raw = build_asset_financials(finance_inputs)
    breakdowns = list(breakdowns_raw if isinstance(breakdowns_raw, tuple) else (breakdowns_raw,))
    asset_mix_summary = summarise_asset_financials(breakdowns, project_name="Quick Screen")

    total_capex = asset_mix_summary.total_capex_sgd if asset_mix_summary else None
    annual_revenue = asset_mix_summary.total_annual_revenue_sgd if asset_mix_summary else None
    annual_noi = asset_mix_summary.total_annual_noi_sgd if asset_mix_summary else None

    equity_fraction = _fraction_from_pct(financing.equity_pct)
    debt_fraction = _fraction_from_pct(financing.debt_pct)
    interest_fraction = _fraction_from_pct(financing.annual_interest_rate_pct)
    discount_fraction = _fraction_from_pct(financing.discount_rate_pct)
    exit_cap_fraction = _fraction_from_pct(financing.exit_cap_rate_pct)
    sale_cost_fraction = _fraction_from_pct(financing.sale_cost_pct)

    equity_required = (
        _quantize_money(total_capex * equity_fraction) if total_capex is not None else None
    )
    debt_amount = (
        _quantize_money(total_capex * debt_fraction) if total_capex is not None else None
    )
    annual_debt_service = (
        _quantize_money(debt_amount * interest_fraction) if debt_amount is not None else None
    )
    operating_expenses = None
    if annual_revenue is not None and annual_noi is not None:
        operating_expenses = annual_revenue - annual_noi

    metrics = None
    if total_capex is not None and annual_revenue is not None and annual_noi is not None:
        metrics = calculate_comprehensive_metrics(
            property_value=total_capex,
            gross_rental_income=annual_revenue,
            operating_expenses=operating_expenses or Decimal("0"),
            loan_amount=debt_amount,
            annual_debt_service=annual_debt_service,
            initial_cash_investment=equity_required,
            vacancy_rate=Decimal("0"),
            currency="SGD",
        )

    estimated_exit_value = None
    if annual_noi is not None and exit_cap_fraction > 0:
        estimated_exit_value = _quantize_money(annual_noi / exit_cap_fraction)

    annual_equity_cash = None
    if annual_noi is not None:
        annual_equity_cash = annual_noi - (annual_debt_service or Decimal("0"))

    net_exit = None
    if estimated_exit_value is not None:
        sale_costs = estimated_exit_value * sale_cost_fraction
        net_exit = estimated_exit_value - sale_costs - (debt_amount or Decimal("0"))

    cash_flows: list[Decimal] = []
    if equity_required is not None:
        lease_up_years = _average_absorption_years(asset_optimizations)
        cash_flows.append(-equity_required)
        for year in range(1, max(financing.hold_years, 1) + 1):
            flow = Decimal("0")
            if year >= lease_up_years and annual_equity_cash is not None:
                flow += annual_equity_cash
            if year == financing.hold_years and net_exit is not None:
                flow += net_exit
            cash_flows.append(flow)

    npv_value = None
    irr_value = None
    moic_value = None
    raw_moic = None
    if cash_flows:
        npv_value = _quantize_money(npv(discount_fraction, cash_flows))
        invested = abs(cash_flows[0]) if cash_flows[0] < 0 else Decimal("0")
        distributions = sum((flow for flow in cash_flows[1:] if flow > 0), Decimal("0"))
        if invested > 0 and distributions > 0:
            raw_moic = distributions / invested
            moic_value = _quantize_ratio(raw_moic)
        try:
            irr_value = _quantize_ratio(irr(cash_flows))
        except ValueError:
            irr_value = None
            if raw_moic is not None and financing.hold_years > 0:
                fallback_irr = Decimal(
                    str(pow(float(raw_moic), 1 / financing.hold_years) - 1)
                )
                irr_value = _quantize_ratio(fallback_irr)

    notes = [
        "Standalone quick screen. Validate planning, construction, and financing assumptions before investment committee use.",
        "Finance outputs are derived from the suggested asset mix and a simplified construction-to-stabilisation hold model.",
    ]

    if metrics and metrics.dscr is not None:
        notes.append(
            f"DSCR computed against annual interest-only debt service using {financing.annual_interest_rate_pct:.1f}% cost of debt."
        )

    summary = DealCalculatorFinanceSummary(
        total_capex_sgd=total_capex,
        total_annual_revenue_sgd=annual_revenue,
        total_annual_noi_sgd=annual_noi,
        blended_yield_pct=asset_mix_summary.blended_yield_pct if asset_mix_summary else None,
        equity_required_sgd=equity_required,
        debt_amount_sgd=debt_amount,
        annual_debt_service_sgd=annual_debt_service,
        cap_rate_pct=metrics.cap_rate if metrics else None,
        dscr=metrics.dscr if metrics else None,
        npv_sgd=npv_value,
        irr=irr_value,
        moic=moic_value,
        estimated_exit_value_sgd=estimated_exit_value,
        notes=notes,
    )
    return summary, breakdowns, asset_mix_summary


@router.post("/evaluate", response_model=DealCalculatorResponse)
async def evaluate_deal(
    payload: DealCalculatorRequest,
    session: AsyncSession = Depends(get_session),
    _: object = Depends(require_viewer),
) -> DealCalculatorResponse:
    """Evaluate a standalone SG development deal from an address or manual assumptions."""

    geocoding_source = geocoding_service.get_google_geocoding_metadata()
    amenities_source = geocoding_service.get_onemap_amenities_metadata()
    ura_source = ura_service.source_metadata()

    if payload.address:
        geocoded = await geocoding_service.geocode_details(payload.address)
        if geocoded is None:
            raise HTTPException(status_code=404, detail="Unable to resolve address")
        latitude, longitude, formatted_address = geocoded
        address = Address(full_address=formatted_address or payload.address)
        coordinates = DealCalculatorCoordinates(latitude=latitude, longitude=longitude)
        ura_zoning = await ura_service.get_zoning_info(address.full_address)
        property_info = await ura_service.get_property_info(address.full_address)
        existing_use = payload.existing_use or await ura_service.get_existing_use(address.full_address)
        input_mode = "address"
    else:
        formatted_address = "Manual parameters"
        address = Address(full_address=formatted_address)
        coordinates = None
        ura_zoning = None
        property_info = None
        existing_use = payload.existing_use
        input_mode = "manual"

    zone_code = payload.zone_code or (ura_zoning.zone_code if ura_zoning else None)
    zone_description = ura_zoning.zone_description if ura_zoning else None
    land_use = _infer_land_use(payload.land_use, zone_description, existing_use, zone_code)

    site_area_sqm = (
        payload.site_area_sqm
        or (property_info.site_area_sqm if property_info else None)
        or 1000.0
    )
    allowable_plot_ratio = (
        payload.allowable_plot_ratio
        or (ura_zoning.plot_ratio if ura_zoning and ura_zoning.plot_ratio else None)
        or 3.5
    )
    current_gfa_sqm = (
        payload.current_gfa_sqm
        if payload.current_gfa_sqm is not None
        else (property_info.gfa_approved if property_info else None)
    )
    existing_use = existing_use or land_use.replace("_", " ").title()

    buildable_service = BuildableService(session)
    buildable_calc = await buildable_service.calculate_parameters(
        BuildableInput(
            land_area=site_area_sqm,
            zone_code=zone_code,
            plot_ratio=allowable_plot_ratio,
            site_coverage=(ura_zoning.site_coverage / 100.0) if ura_zoning and ura_zoning.site_coverage else None,
            floor_height_m=4.0,
            efficiency_ratio=0.82,
        )
    )

    source_reference = _build_source_reference(
        buildable_calc.zone_source.model_dump(mode="json"),
        ura_source.provider if ura_source else None,
    )
    additional_potential = None
    if current_gfa_sqm is not None:
        additional_potential = max(buildable_calc.metrics.gfa_cap_m2 - current_gfa_sqm, 0)

    build_envelope = BuildEnvelopeSnapshot(
        zone_code=zone_code,
        zone_description=zone_description,
        site_area_sqm=site_area_sqm,
        allowable_plot_ratio=allowable_plot_ratio,
        max_buildable_gfa_sqm=buildable_calc.metrics.gfa_cap_m2,
        current_gfa_sqm=current_gfa_sqm,
        additional_potential_gfa_sqm=additional_potential,
        assumptions=[
            f"Buildable screen calculated from {site_area_sqm:,.0f} sqm site area at plot ratio {allowable_plot_ratio:g}.",
            f"Rule corpus coverage: {buildable_calc.rule_corpus_status.coverage_state} ({buildable_calc.rule_corpus_status.confidence} confidence).",
        ],
        source_reference=source_reference,
        rule_corpus_status=buildable_calc.rule_corpus_status,
    )

    project = NewFeasibilityProjectInput(
        name=payload.project_name or "Quick Screen",
        site_address=address.full_address,
        site_area_sqm=site_area_sqm,
        land_use=land_use,
        target_gross_floor_area_sqm=payload.target_gross_floor_area_sqm,
        building_height_meters=payload.building_height_meters,
        build_envelope=build_envelope,
    )
    rules_response = generate_feasibility_rules(project)
    assessment = run_feasibility_assessment(
        FeasibilityAssessmentRequest(
            project=project,
            selected_rule_ids=rules_response.recommended_rule_ids,
        )
    )
    finance_summary, breakdowns, asset_mix_summary = _build_finance_summary(
        asset_optimizations=assessment.asset_optimizations,
        financing=payload.financing,
    )

    if geocoding_source and geocoding_source.state != "live":
        finance_summary.notes.append(
            f"Geocoding source is {geocoding_source.state.value}; verify the resolved address before relying on site-specific outputs."
        )
    if ura_source and ura_source.state != "live":
        finance_summary.notes.append(
            f"URA source is {ura_source.state.value}; zoning and property metadata may be mocked or unavailable."
        )

    return DealCalculatorResponse(
        generated_at=utcnow(),
        site=DealCalculatorSiteSummary(
            input_mode=input_mode,
            formatted_address=address.full_address,
            coordinates=coordinates,
            jurisdiction_code="SG",
            land_use=land_use,
            existing_use=existing_use,
            zone_code=zone_code,
            zone_description=zone_description,
            geocoding_source=geocoding_source,
            amenities_source=amenities_source,
            ura_source=ura_source,
        ),
        build_envelope=build_envelope,
        rule_corpus_status=buildable_calc.rule_corpus_status,
        recommended_rule_ids=rules_response.recommended_rule_ids,
        feasibility_summary=assessment.summary,
        feasibility_rules=assessment.rules,
        recommendations=assessment.recommendations,
        asset_optimizations=assessment.asset_optimizations,
        asset_mix_summary=asset_mix_summary,
        asset_breakdowns=serialise_breakdown(breakdowns),
        finance_summary=finance_summary,
    )


__all__ = ["router", "evaluate_deal", "geocoding_service", "ura_service"]
