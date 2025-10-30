"""Asset-specific finance modelling helpers for Phase 2C."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Iterable, Sequence, Union

from app.schemas.finance import (
    AssetFinancialSummarySchema,
    FinanceAssetBreakdownSchema,
)

NumberLike = Union[Decimal, int, float, str]

CURRENCY_QUANT = Decimal("0.01")
PERCENT_QUANT = Decimal("0.0001")
AREA_QUANT = Decimal("0.01")
MONTHS_QUANT = Decimal("0.1")
PAYBACK_QUANT = Decimal("0.01")

RISK_PRIORITY = {"low": 1, "balanced": 2, "moderate": 3, "elevated": 4}


def _to_decimal(value: NumberLike | None) -> Decimal | None:
    """Convert supported numeric inputs into :class:`Decimal`."""

    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    try:
        if isinstance(value, (int, str)):
            return Decimal(value)
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _quantize_currency(value: Decimal | None) -> Decimal | None:
    if value is None:
        return None
    return value.quantize(CURRENCY_QUANT, rounding=ROUND_HALF_UP)


def _quantize_percent(value: Decimal | None) -> Decimal | None:
    if value is None:
        return None
    return value.quantize(PERCENT_QUANT, rounding=ROUND_HALF_UP)


def _quantize_area(value: Decimal | None) -> Decimal | None:
    if value is None:
        return None
    return value.quantize(AREA_QUANT, rounding=ROUND_HALF_UP)


def _quantize_duration(value: Decimal | None) -> Decimal | None:
    if value is None:
        return None
    return value.quantize(MONTHS_QUANT, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class AssetFinanceInput:
    """Asset optimisation payload used for finance modelling."""

    asset_type: str
    allocation_pct: Decimal | None = None
    nia_sqm: Decimal | None = None
    rent_psm_month: Decimal | None = None
    stabilised_vacancy_pct: Decimal | None = None
    opex_pct_of_rent: Decimal | None = None
    estimated_revenue_sgd: Decimal | None = None
    estimated_capex_sgd: Decimal | None = None
    absorption_months: Decimal | None = None
    risk_level: str | None = None
    heritage_premium_pct: Decimal | None = None
    notes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class AssetFinanceBreakdown:
    """Calculated finance metrics for a single asset allocation."""

    asset_type: str
    allocation_pct: Decimal | None
    nia_sqm: Decimal | None
    rent_psm_month: Decimal | None
    gross_rent_annual_sgd: Decimal | None
    vacancy_loss_sgd: Decimal | None
    effective_gross_income_sgd: Decimal | None
    operating_expenses_sgd: Decimal | None
    noi_annual_sgd: Decimal | None
    estimated_capex_sgd: Decimal | None
    payback_years: Decimal | None
    absorption_months: Decimal | None
    risk_level: str | None
    heritage_premium_pct: Decimal | None
    notes: tuple[str, ...] = field(default_factory=tuple)


def build_asset_financials(
    inputs: Sequence[AssetFinanceInput],
) -> tuple[AssetFinanceBreakdown, ...]:
    """Transform optimiser outputs into per-asset finance metrics."""

    breakdowns: list[AssetFinanceBreakdown] = []
    for item in inputs:
        nia_sqm = _quantize_area(item.nia_sqm)
        rent_psm_month = _quantize_currency(item.rent_psm_month)

        gross_rent = None
        if nia_sqm is not None and rent_psm_month is not None:
            gross_rent = _quantize_currency(nia_sqm * rent_psm_month * Decimal("12"))

        vacancy_pct = item.stabilised_vacancy_pct
        vacancy_loss = None
        effective_gross_income = gross_rent
        if vacancy_pct is not None and gross_rent is not None:
            vacancy_ratio = _to_decimal(vacancy_pct)
            if vacancy_ratio is not None:
                vacancy_loss = _quantize_currency(
                    gross_rent * (vacancy_ratio / Decimal("100"))
                )
                if vacancy_loss is not None:
                    effective_gross_income = _quantize_currency(
                        gross_rent - vacancy_loss
                    )

        opex_pct = item.opex_pct_of_rent
        operating_expenses = None
        if opex_pct is not None and effective_gross_income is not None:
            opex_ratio = _to_decimal(opex_pct)
            if opex_ratio is not None:
                operating_expenses = _quantize_currency(
                    effective_gross_income * (opex_ratio / Decimal("100"))
                )

        noi = None
        if effective_gross_income is not None:
            base_noi = effective_gross_income - (operating_expenses or Decimal("0"))
            noi = _quantize_currency(base_noi)

        if noi is None and item.estimated_revenue_sgd is not None:
            estimated_noi = _to_decimal(item.estimated_revenue_sgd)
            noi = _quantize_currency(estimated_noi)

        capex = _quantize_currency(item.estimated_capex_sgd)
        payback_years = None
        if capex is not None and noi not in (None, Decimal("0")):
            try:
                payback_years = (capex / noi).quantize(
                    PAYBACK_QUANT, rounding=ROUND_HALF_UP
                )
            except (InvalidOperation, ZeroDivisionError):
                payback_years = None

        breakdowns.append(
            AssetFinanceBreakdown(
                asset_type=item.asset_type,
                allocation_pct=_quantize_percent(item.allocation_pct),
                nia_sqm=nia_sqm,
                rent_psm_month=rent_psm_month,
                gross_rent_annual_sgd=gross_rent,
                vacancy_loss_sgd=vacancy_loss,
                effective_gross_income_sgd=effective_gross_income,
                operating_expenses_sgd=operating_expenses,
                noi_annual_sgd=noi,
                estimated_capex_sgd=capex,
                payback_years=payback_years,
                absorption_months=_quantize_duration(item.absorption_months),
                risk_level=item.risk_level,
                heritage_premium_pct=_quantize_percent(item.heritage_premium_pct),
                notes=item.notes,
            )
        )

    return tuple(breakdowns)


def summarise_asset_financials(
    breakdowns: Sequence[AssetFinanceBreakdown],
) -> AssetFinancialSummarySchema | None:
    """Aggregate per-asset metrics into Phase 2C finance summary."""

    if not breakdowns:
        return None

    total_revenue = Decimal("0")
    total_capex = Decimal("0")
    dominant: str | None = None
    for entry in breakdowns:
        if entry.noi_annual_sgd is not None:
            total_revenue += entry.noi_annual_sgd
        if entry.estimated_capex_sgd is not None:
            total_capex += entry.estimated_capex_sgd
        if entry.risk_level:
            rank = RISK_PRIORITY.get(entry.risk_level, 0)
            if dominant is None or rank >= RISK_PRIORITY.get(dominant, 0):
                dominant = entry.risk_level

    summary = AssetFinancialSummarySchema(
        total_estimated_revenue_sgd=(
            _quantize_currency(total_revenue) if total_revenue > 0 else None
        ),
        total_estimated_capex_sgd=(
            _quantize_currency(total_capex) if total_capex > 0 else None
        ),
        dominant_risk_profile=dominant,
        notes=[],
    )

    if summary.dominant_risk_profile:
        summary.notes.append(f"Dominant risk profile: {summary.dominant_risk_profile}.")
    if summary.total_estimated_revenue_sgd:
        summary.notes.append("Revenue aggregates annual NOI across asset allocations.")
    if summary.total_estimated_capex_sgd:
        summary.notes.append("Capex includes programme-specific fit-out costs.")

    return summary


def serialise_breakdown(
    breakdowns: Iterable[AssetFinanceBreakdown],
) -> list[FinanceAssetBreakdownSchema]:
    """Convert dataclass breakdowns into API response schemas."""

    payload: list[FinanceAssetBreakdownSchema] = []
    for entry in breakdowns:
        payload.append(
            FinanceAssetBreakdownSchema(
                asset_type=entry.asset_type,
                allocation_pct=entry.allocation_pct,
                nia_sqm=entry.nia_sqm,
                rent_psm_month=entry.rent_psm_month,
                gross_rent_annual_sgd=entry.gross_rent_annual_sgd,
                vacancy_loss_sgd=entry.vacancy_loss_sgd,
                effective_gross_income_sgd=entry.effective_gross_income_sgd,
                operating_expenses_sgd=entry.operating_expenses_sgd,
                noi_annual_sgd=entry.noi_annual_sgd,
                estimated_capex_sgd=entry.estimated_capex_sgd,
                payback_years=entry.payback_years,
                absorption_months=entry.absorption_months,
                risk_level=entry.risk_level,
                heritage_premium_pct=entry.heritage_premium_pct,
                notes=list(entry.notes),
            )
        )
    return payload


__all__ = [
    "AssetFinanceBreakdown",
    "AssetFinanceInput",
    "build_asset_financials",
    "serialise_breakdown",
    "summarise_asset_financials",
]
