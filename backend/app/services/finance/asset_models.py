"""Asset-specific finance modelling helpers for Phase 2C."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Iterable, Sequence, Union

from app.schemas.finance import AssetFinancialSummarySchema, FinanceAssetBreakdownSchema

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


def _to_string(value: Decimal | None, places: int | None = None) -> str | None:
    if value is None:
        return None
    if places is not None:
        quant = Decimal(1).scaleb(-places)
        try:
            value = value.quantize(quant, rounding=ROUND_HALF_UP)
        except (InvalidOperation, ValueError):
            pass
    return format(value, "f")


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
    allocation_pct: Decimal | None = None
    nia_sqm: Decimal | None = None
    rent_psm_month: Decimal | None = None
    gross_rent_annual_sgd: Decimal | None = None
    vacancy_loss_sgd: Decimal | None = None
    effective_gross_income_sgd: Decimal | None = None
    operating_expenses_sgd: Decimal | None = None
    annual_opex_sgd: Decimal | None = None
    noi_annual_sgd: Decimal | None = None
    annual_noi_sgd: Decimal | None = None
    annual_revenue_sgd: Decimal | None = None
    estimated_capex_sgd: Decimal | None = None
    capex_sgd: Decimal | None = None
    payback_years: Decimal | None = None
    absorption_months: Decimal | None = None
    stabilised_yield_pct: Decimal | None = None
    risk_level: str | None = None
    risk_priority: int | None = None
    heritage_premium_pct: Decimal | None = None
    notes: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        """Backfill legacy aliases for compatibility with existing stubs."""

        if self.annual_noi_sgd is None and self.noi_annual_sgd is not None:
            object.__setattr__(self, "annual_noi_sgd", self.noi_annual_sgd)
        elif self.noi_annual_sgd is None and self.annual_noi_sgd is not None:
            object.__setattr__(self, "noi_annual_sgd", self.annual_noi_sgd)

        if self.capex_sgd is None and self.estimated_capex_sgd is not None:
            object.__setattr__(self, "capex_sgd", self.estimated_capex_sgd)
        elif self.estimated_capex_sgd is None and self.capex_sgd is not None:
            object.__setattr__(self, "estimated_capex_sgd", self.capex_sgd)

        if self.annual_opex_sgd is None and self.operating_expenses_sgd is not None:
            object.__setattr__(self, "annual_opex_sgd", self.operating_expenses_sgd)
        elif self.operating_expenses_sgd is None and self.annual_opex_sgd is not None:
            object.__setattr__(self, "operating_expenses_sgd", self.annual_opex_sgd)

        if self.annual_revenue_sgd is None and self.gross_rent_annual_sgd is not None:
            object.__setattr__(self, "annual_revenue_sgd", self.gross_rent_annual_sgd)
        elif self.gross_rent_annual_sgd is None and self.annual_revenue_sgd is not None:
            object.__setattr__(self, "gross_rent_annual_sgd", self.annual_revenue_sgd)


def build_asset_financials(
    inputs: AssetFinanceInput | Sequence[AssetFinanceInput],
) -> AssetFinanceBreakdown | tuple[AssetFinanceBreakdown, ...]:
    """Transform optimiser outputs into per-asset finance metrics."""

    if isinstance(inputs, AssetFinanceInput):
        queue: Sequence[AssetFinanceInput] = [inputs]
        is_single = True
    else:
        queue = inputs
        is_single = False

    breakdowns: list[AssetFinanceBreakdown] = []
    for item in queue:
        nia_sqm = _quantize_area(item.nia_sqm)
        rent_psm_month = _quantize_currency(item.rent_psm_month)

        gross_rent = None
        if nia_sqm is not None and rent_psm_month is not None:
            gross_rent = _quantize_currency(nia_sqm * rent_psm_month * Decimal("12"))
        if gross_rent is None and item.estimated_revenue_sgd is not None:
            estimated_revenue = _to_decimal(item.estimated_revenue_sgd)
            if estimated_revenue is not None:
                gross_rent = _quantize_currency(estimated_revenue)

        vacancy_pct = item.stabilised_vacancy_pct
        vacancy_loss = None
        effective_gross_income = gross_rent
        if vacancy_pct is not None and gross_rent is not None:
            vacancy_ratio = _to_decimal(vacancy_pct)
            if vacancy_ratio is not None:
                vacancy_loss = _quantize_currency(gross_rent * vacancy_ratio)
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
                    effective_gross_income * opex_ratio
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
        if capex is not None and noi is not None and noi != Decimal("0"):
            try:
                payback_years = (capex / noi).quantize(
                    PAYBACK_QUANT, rounding=ROUND_HALF_UP
                )
            except (InvalidOperation, ZeroDivisionError):
                payback_years = None

        stabilised_yield = None
        if noi is not None and capex is not None and capex != Decimal("0"):
            try:
                stabilised_yield = (noi / capex).quantize(
                    PERCENT_QUANT, rounding=ROUND_HALF_UP
                )
            except (InvalidOperation, ZeroDivisionError):
                stabilised_yield = None

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
                annual_opex_sgd=operating_expenses,
                noi_annual_sgd=noi,
                annual_noi_sgd=noi,
                annual_revenue_sgd=gross_rent,
                estimated_capex_sgd=capex,
                capex_sgd=capex,
                payback_years=payback_years,
                absorption_months=_quantize_duration(item.absorption_months),
                stabilised_yield_pct=stabilised_yield,
                risk_level=item.risk_level,
                risk_priority=(
                    RISK_PRIORITY.get(item.risk_level) if item.risk_level else None
                ),
                heritage_premium_pct=_quantize_percent(item.heritage_premium_pct),
                notes=item.notes,
            )
        )

    if is_single:
        return breakdowns[0]
    return tuple(breakdowns)


def summarise_asset_financials(
    breakdowns: Sequence[AssetFinanceBreakdown],
    project_name: str | None = None,
) -> AssetFinancialSummarySchema | None:
    """Aggregate per-asset metrics into Phase 2C finance summary."""

    if not breakdowns:
        return None

    total_revenue = Decimal("0")
    total_noi = Decimal("0")
    total_capex = Decimal("0")
    total_nia = Decimal("0")
    dominant: str | None = None
    for entry in breakdowns:
        if entry.annual_revenue_sgd is not None:
            total_revenue += entry.annual_revenue_sgd
        if entry.annual_noi_sgd is not None:
            total_noi += entry.annual_noi_sgd
        if entry.estimated_capex_sgd is not None:
            total_capex += entry.estimated_capex_sgd
        if entry.nia_sqm is not None:
            total_nia += entry.nia_sqm
        if entry.risk_level:
            rank = RISK_PRIORITY.get(entry.risk_level, 0)
            if dominant is None or rank >= RISK_PRIORITY.get(dominant, 0):
                dominant = entry.risk_level

    blended_yield = None
    if total_capex and total_noi:
        try:
            blended_yield = (total_noi / total_capex).quantize(
                PERCENT_QUANT, rounding=ROUND_HALF_UP
            )
        except (InvalidOperation, ZeroDivisionError):
            blended_yield = None

    return AssetFinancialSummarySchema(
        project_name=project_name,
        total_capex_sgd=_quantize_currency(total_capex) if total_capex else None,
        total_annual_revenue_sgd=(
            _quantize_currency(total_revenue) if total_revenue else None
        ),
        total_annual_noi_sgd=(_quantize_currency(total_noi) if total_noi else None),
        total_nia_sqm=_quantize_area(total_nia) if total_nia else None,
        dominant_risk_profile=dominant,
        blended_yield_pct=blended_yield,
    )


def serialise_breakdown(
    breakdowns: AssetFinanceBreakdown | Iterable[AssetFinanceBreakdown],
) -> FinanceAssetBreakdownSchema | list[FinanceAssetBreakdownSchema]:
    """Convert dataclass breakdowns into API response schemas."""

    if isinstance(breakdowns, AssetFinanceBreakdown):
        queue: Iterable[AssetFinanceBreakdown] = [breakdowns]
        is_single = True
    else:
        queue = breakdowns
        is_single = False

    payload: list[FinanceAssetBreakdownSchema] = []
    for entry in queue:
        payload.append(
            FinanceAssetBreakdownSchema(
                asset_type=entry.asset_type,
                allocation_pct=_to_string(entry.allocation_pct, 2),
                nia_sqm=_to_string(entry.nia_sqm, 2),
                rent_psm_month=_to_string(entry.rent_psm_month, 2),
                gross_rent_annual_sgd=_to_string(entry.gross_rent_annual_sgd, 2),
                annual_revenue_sgd=_to_string(entry.annual_revenue_sgd, 2),
                vacancy_loss_sgd=_to_string(entry.vacancy_loss_sgd, 2),
                effective_gross_income_sgd=_to_string(
                    entry.effective_gross_income_sgd, 2
                ),
                operating_expenses_sgd=_to_string(entry.operating_expenses_sgd, 2),
                annual_opex_sgd=_to_string(entry.annual_opex_sgd, 2),
                noi_annual_sgd=_to_string(entry.noi_annual_sgd, 2),
                annual_noi_sgd=_to_string(entry.annual_noi_sgd, 2),
                estimated_capex_sgd=_to_string(entry.estimated_capex_sgd, 2),
                capex_sgd=_to_string(entry.capex_sgd, 2),
                payback_years=_to_string(entry.payback_years, 2),
                absorption_months=_to_string(entry.absorption_months, 1),
                stabilised_yield_pct=_to_string(entry.stabilised_yield_pct, 4),
                risk_level=entry.risk_level,
                risk_priority=entry.risk_priority,
                heritage_premium_pct=_to_string(entry.heritage_premium_pct, 4),
                notes=list(entry.notes),
            )
        )

    if is_single:
        return payload[0]
    return payload


__all__ = [
    "AssetFinanceBreakdown",
    "AssetFinanceInput",
    "build_asset_financials",
    "serialise_breakdown",
    "summarise_asset_financials",
]
