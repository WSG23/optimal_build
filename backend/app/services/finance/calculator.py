"""Deterministic financial calculators built on :class:`~decimal.Decimal`."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation, localcontext
from typing import Iterable, List, Optional, Sequence, Tuple, Union

from app.models.rkp import RefCostIndex

NumberLike = Union[Decimal, int, float, str]
CURRENCY_QUANTIZER = Decimal("0.01")
DSCR_QUANTIZER = Decimal("0.0001")
DEFAULT_PRECISION = 28


@dataclass(frozen=True)
class DscrEntry:
    """Single period DSCR breakdown."""

    period: Union[int, str]
    noi: Decimal
    debt_service: Decimal
    dscr: Optional[Decimal]
    currency: str


@dataclass(frozen=True)
class PriceSensitivityResult:
    """Immutable representation of a 2D price sensitivity analysis."""

    currency: str
    price_deltas: Tuple[Decimal, ...]
    volume_deltas: Tuple[Decimal, ...]
    prices: Tuple[Decimal, ...]
    grid: Tuple[Tuple[Decimal, ...], ...]


def _to_decimal(value: NumberLike) -> Decimal:
    """Convert *value* into a :class:`Decimal` using string casting for stability."""

    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, str)):
        return Decimal(value)
    return Decimal(str(value))


def _quantize_currency(value: Decimal) -> Decimal:
    """Quantise a monetary value to cents using half-up rounding."""

    return value.quantize(CURRENCY_QUANTIZER, rounding=ROUND_HALF_UP)


def _normalise_cash_flows(cash_flows: Sequence[NumberLike]) -> Tuple[Decimal, ...]:
    """Normalise an iterable of cash flows into a tuple of :class:`Decimal`."""

    return tuple(_to_decimal(cash) for cash in cash_flows)


def npv(
    rate: NumberLike,
    cash_flows: Sequence[NumberLike],
    *,
    precision: int = DEFAULT_PRECISION,
) -> Decimal:
    """Compute the net present value of ``cash_flows`` discounted by ``rate``.

    Parameters
    ----------
    rate:
        Periodic discount rate expressed as a decimal fraction (``0.05`` for 5%).
    cash_flows:
        Ordered sequence of cash flows where index ``0`` represents the present period.
    precision:
        Decimal precision to use for the calculation.
    """

    cash_values = _normalise_cash_flows(cash_flows)
    discount_rate = _to_decimal(rate)
    one = Decimal("1")
    npv_total = Decimal("0")
    with localcontext() as ctx:
        ctx.prec = precision
        for period, cash in enumerate(cash_values):
            discount_factor = (one + discount_rate) ** period
            if discount_factor == 0:
                raise ZeroDivisionError(
                    "Discount factor evaluated to zero; rate cannot be -1 for positive periods."
                )
            npv_total += cash / discount_factor
    return npv_total


def _npv_derivative(
    rate: Decimal, cash_flows: Sequence[Decimal], precision: int
) -> Decimal:
    """Derivative of NPV with respect to ``rate`` for Newton iterations."""

    one = Decimal("1")
    derivative = Decimal("0")
    with localcontext() as ctx:
        ctx.prec = precision
        for period, cash in enumerate(cash_flows):
            if period == 0:
                continue
            denominator = (one + rate) ** (period + 1)
            if denominator == 0:
                raise ZeroDivisionError(
                    "Encountered zero denominator while differentiating NPV."
                )
            derivative -= (period * cash) / denominator
    return derivative


def _has_sign_change(values: Sequence[Decimal]) -> bool:
    """Return ``True`` if ``values`` contain both positive and negative amounts."""

    has_positive = any(value > 0 for value in values)
    has_negative = any(value < 0 for value in values)
    return has_positive and has_negative


def irr(
    cash_flows: Sequence[NumberLike],
    *,
    guess: NumberLike = Decimal("0.1"),
    precision: int = DEFAULT_PRECISION,
    tolerance: NumberLike = Decimal("1e-7"),
    max_iterations: int = 64,
    lower_bound: NumberLike = Decimal("-0.999999"),
    upper_bound: NumberLike = Decimal("10"),
) -> Decimal:
    """Compute the internal rate of return using Newton's method with a fallback."""

    flows = _normalise_cash_flows(cash_flows)
    if not flows:
        raise ValueError("IRR requires at least one cash flow.")
    if not _has_sign_change(flows):
        raise ValueError("IRR requires cash flows with at least one sign change.")

    with localcontext() as ctx:
        ctx.prec = precision
        rate = _to_decimal(guess)
        tolerance_value = _to_decimal(tolerance)
        lower = _to_decimal(lower_bound)
        upper = _to_decimal(upper_bound)

        for _ in range(max_iterations):
            value = npv(rate, flows, precision=ctx.prec)
            if abs(value) <= tolerance_value:
                return rate
            derivative = _npv_derivative(rate, flows, ctx.prec)
            if derivative == 0:
                break
            step = value / derivative
            rate -= step
            if abs(step) <= tolerance_value:
                return rate
            if rate <= lower or rate >= upper:
                break

        # Fallback to a bisection search within the provided bounds.
        lower_value = npv(lower, flows, precision=ctx.prec)
        upper_value = npv(upper, flows, precision=ctx.prec)

        if lower_value == 0:
            return lower
        if upper_value == 0:
            return upper
        if lower_value * upper_value > 0:
            raise ValueError("Failed to bracket a root for the IRR calculation.")

        for _ in range(max_iterations):
            midpoint = (lower + upper) / 2
            midpoint_value = npv(midpoint, flows, precision=ctx.prec)
            if abs(midpoint_value) <= tolerance_value:
                return midpoint
            if lower_value * midpoint_value < 0:
                upper = midpoint
                upper_value = midpoint_value
            else:
                lower = midpoint
                lower_value = midpoint_value
        return midpoint


def dscr_timeline(
    net_operating_incomes: Sequence[NumberLike],
    debt_services: Sequence[NumberLike],
    *,
    period_labels: Optional[Sequence[Union[int, str]]] = None,
    currency: str = "SGD",
    precision: int = DEFAULT_PRECISION,
) -> List[DscrEntry]:
    """Generate a DSCR timeline ensuring monetary values are rounded to cents."""

    incomes = _normalise_cash_flows(net_operating_incomes)
    services = _normalise_cash_flows(debt_services)
    if len(incomes) != len(services):
        raise ValueError(
            "net_operating_incomes and debt_services must be of equal length."
        )
    if period_labels and len(period_labels) != len(incomes):
        raise ValueError("period_labels must match the length of the cash flow series.")

    entries: List[DscrEntry] = []
    with localcontext() as ctx:
        ctx.prec = precision
        for idx, (noi, debt) in enumerate(zip(incomes, services)):
            period = period_labels[idx] if period_labels else idx
            quantized_noi = _quantize_currency(noi)
            quantized_debt = _quantize_currency(debt)
            if debt == 0:
                dscr_value: Optional[Decimal]
                if noi > 0:
                    dscr_value = Decimal("Infinity")
                elif noi < 0:
                    dscr_value = Decimal("-Infinity")
                else:
                    dscr_value = None
            else:
                dscr_value = (noi / debt).quantize(
                    DSCR_QUANTIZER, rounding=ROUND_HALF_UP
                )
            entries.append(
                DscrEntry(
                    period=period,
                    noi=quantized_noi,
                    debt_service=quantized_debt,
                    dscr=dscr_value,
                    currency=currency,
                )
            )
    return entries


def price_sensitivity_grid(
    base_price: NumberLike,
    base_volume: NumberLike,
    price_deltas: Sequence[NumberLike],
    volume_deltas: Sequence[NumberLike],
    *,
    currency: str = "SGD",
    precision: int = DEFAULT_PRECISION,
) -> PriceSensitivityResult:
    """Build a price sensitivity revenue grid quantised to cents."""

    price_adjustments = tuple(_to_decimal(delta) for delta in price_deltas)
    volume_adjustments = tuple(_to_decimal(delta) for delta in volume_deltas)
    price = _to_decimal(base_price)
    volume = _to_decimal(base_volume)

    price_points: List[Decimal] = []
    grid_rows: List[Tuple[Decimal, ...]] = []

    with localcontext() as ctx:
        ctx.prec = precision
        for price_delta in price_adjustments:
            adjusted_price = _quantize_currency(price * (Decimal("1") + price_delta))
            price_points.append(adjusted_price)
            row: List[Decimal] = []
            for volume_delta in volume_adjustments:
                adjusted_volume = volume * (Decimal("1") + volume_delta)
                revenue = _quantize_currency(adjusted_price * adjusted_volume)
                row.append(revenue)
            grid_rows.append(tuple(row))

    return PriceSensitivityResult(
        currency=currency,
        price_deltas=price_adjustments,
        volume_deltas=volume_adjustments,
        prices=tuple(price_points),
        grid=tuple(grid_rows),
    )


def escalate_amount(
    amount: NumberLike,
    *,
    base_period: str,
    indices: Iterable[RefCostIndex],
    series_name: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    provider: Optional[str] = None,
    precision: int = DEFAULT_PRECISION,
) -> Decimal:
    """Escalate ``amount`` by comparing base and latest cost indices."""

    base_value = _to_decimal(amount)
    indices_list = list(indices)
    latest = RefCostIndex.latest(
        indices_list,
        jurisdiction=jurisdiction,
        provider=provider,
        series_name=series_name,
    )
    if latest is None:
        return _quantize_currency(base_value)

    base_index = None
    for index in indices_list:
        if base_period and index.period == base_period:
            if series_name and index.series_name != series_name:
                continue
            if jurisdiction and index.jurisdiction != jurisdiction:
                continue
            if provider and index.provider != provider:
                continue
            base_index = index
            break

    if base_index is None:
        return _quantize_currency(base_value)

    try:
        with localcontext() as ctx:
            ctx.prec = precision
            latest_value = _to_decimal(latest.value)
            base_value_index = _to_decimal(base_index.value)
            if base_value_index == 0:
                raise ZeroDivisionError(
                    "Base index value cannot be zero for escalation."
                )
            scalar = latest_value / base_value_index
            return _quantize_currency(base_value * scalar)
    except (InvalidOperation, ZeroDivisionError):
        return _quantize_currency(base_value)


__all__ = [
    "DscrEntry",
    "PriceSensitivityResult",
    "dscr_timeline",
    "escalate_amount",
    "irr",
    "npv",
    "price_sensitivity_grid",
]
