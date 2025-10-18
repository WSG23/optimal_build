"""Seed a finance feasibility demo project with sample scenarios."""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Union
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, engine
from app.models.base import BaseModel
from app.models.finance import (
    FinCapitalStack,
    FinCostItem,
    FinProject,
    FinResult,
    FinScenario,
    FinSchedule,
)
from app.models.projects import Project, ProjectPhase, ProjectType
from app.models.rkp import RefCostIndex
from app.services.finance import calculator

logger = structlog.get_logger(__name__)

DEMO_PROJECT_ID = 401
DEMO_PROJECT_NAME = "Finance Demo Development"
DEMO_CURRENCY = "SGD"


DecimalLike = Union[Decimal, int, float, str]


def _normalise_project_id(value: Union[int, str, UUID]) -> UUID:
    """Coerce various project id representations into a UUID."""

    if isinstance(value, UUID):
        return value
    if isinstance(value, str):
        return UUID(value)
    if isinstance(value, int):
        if value < 0:
            raise ValueError("project_id must be non-negative")
        return UUID(int=value)
    raise TypeError(f"Unsupported project_id type: {type(value)!r}")


@dataclass
class ScenarioSeedResult:
    """Counts and aggregates produced while seeding a scenario."""

    scenario: FinScenario
    cost_items: int
    schedule_rows: int
    results: int
    total_cost: Decimal
    total_revenue: Decimal
    cumulative_cash: Decimal
    escalated_cost: Decimal
    discount_rate: Decimal


@dataclass
class FinanceDemoSummary:
    """Summary of seeded finance demo entities."""

    project_id: str
    fin_project_id: int
    scenarios: int
    cost_items: int
    schedule_rows: int
    results: int

    def as_dict(self) -> dict[str, int]:
        return {
            "project_id": self.project_id,
            "fin_project_id": self.fin_project_id,
            "scenarios": self.scenarios,
            "cost_items": self.cost_items,
            "schedule_rows": self.schedule_rows,
            "results": self.results,
        }


SCENARIO_DEFINITIONS: Sequence[Mapping[str, Any]] = (
    {
        "key": "A",
        "name": "Scenario A – Base Case",
        "description": "Baseline absorption with phased sales releases.",
        "is_primary": True,
        "cost_escalation": {
            "amount": Decimal("38950000"),
            "base_period": "2024-Q1",
            "series_name": "construction_all_in",
            "jurisdiction": "SG",
            "provider": "Public",
        },
        "cash_flow": {
            "discount_rate": Decimal("0.08"),
            "cash_flows": [
                Decimal("-2500000"),
                Decimal("-4100000"),
                Decimal("-4650000"),
                Decimal("-200000"),
                Decimal("4250000"),
                Decimal("10200000"),
            ],
        },
        "dscr": {
            "net_operating_incomes": [
                Decimal("0"),
                Decimal("0"),
                Decimal("3800000"),
                Decimal("5600000"),
                Decimal("7200000"),
                Decimal("7800000"),
            ],
            "debt_services": [
                Decimal("0"),
                Decimal("0"),
                Decimal("3200000"),
                Decimal("3300000"),
                Decimal("3400000"),
                Decimal("3400000"),
            ],
            "period_labels": ["M1", "M2", "M3", "M4", "M5", "M6"],
        },
        "cost_items": (
            {
                "name": "Land acquisition",
                "category": "land",
                "cost_group": "acquisition",
                "total_cost": Decimal("12000000"),
            },
            {
                "name": "Hard construction",
                "category": "construction",
                "cost_group": "hard_costs",
                "quantity": Decimal("25000"),
                "unit_cost": Decimal("950"),
                "total_cost": Decimal("23750000"),
            },
            {
                "name": "Soft costs & fees",
                "category": "soft_costs",
                "cost_group": "consultants",
                "total_cost": Decimal("3200000"),
            },
        ),
        "schedule": (
            {
                "month_index": 1,
                "hard_cost": Decimal("2000000"),
                "soft_cost": Decimal("500000"),
                "revenue": Decimal("0"),
            },
            {
                "month_index": 2,
                "hard_cost": Decimal("3500000"),
                "soft_cost": Decimal("600000"),
                "revenue": Decimal("0"),
            },
            {
                "month_index": 3,
                "hard_cost": Decimal("4000000"),
                "soft_cost": Decimal("650000"),
                "revenue": Decimal("0"),
            },
            {
                "month_index": 4,
                "hard_cost": Decimal("3600000"),
                "soft_cost": Decimal("600000"),
                "revenue": Decimal("4000000"),
            },
            {
                "month_index": 5,
                "hard_cost": Decimal("3200000"),
                "soft_cost": Decimal("550000"),
                "revenue": Decimal("8000000"),
            },
            {
                "month_index": 6,
                "hard_cost": Decimal("1500000"),
                "soft_cost": Decimal("300000"),
                "revenue": Decimal("12000000"),
            },
        ),
        "capital_stack": (
            {
                "name": "Sponsor Equity",
                "source_type": "equity",
                "amount": Decimal("15580000"),
            },
            {
                "name": "Senior Loan",
                "source_type": "debt",
                "amount": Decimal("23370000"),
                "rate": Decimal("0.0475"),
                "tranche_order": 1,
            },
        ),
        "drawdown_schedule": (
            {
                "period": "M1",
                "equity_draw": Decimal("6000000"),
                "debt_draw": Decimal("0"),
            },
            {
                "period": "M2",
                "equity_draw": Decimal("4500000"),
                "debt_draw": Decimal("2500000"),
            },
            {
                "period": "M3",
                "equity_draw": Decimal("3000000"),
                "debt_draw": Decimal("4500000"),
            },
            {
                "period": "M4",
                "equity_draw": Decimal("1200000"),
                "debt_draw": Decimal("5000000"),
            },
            {
                "period": "M5",
                "equity_draw": Decimal("800000"),
                "debt_draw": Decimal("6500000"),
            },
            {
                "period": "M6",
                "equity_draw": Decimal("300000"),
                "debt_draw": Decimal("4870000"),
            },
        ),
    },
    {
        "key": "B",
        "name": "Scenario B – Upside Release",
        "description": "Faster sales velocity with premium unit mix.",
        "is_primary": False,
        "cost_escalation": {
            "amount": Decimal("41100000"),
            "base_period": "2024-Q1",
            "series_name": "construction_all_in",
            "jurisdiction": "SG",
            "provider": "Public",
        },
        "cash_flow": {
            "discount_rate": Decimal("0.075"),
            "cash_flows": [
                Decimal("-2750000"),
                Decimal("-4250000"),
                Decimal("-4900000"),
                Decimal("50000"),
                Decimal("5700000"),
                Decimal("11350000"),
            ],
        },
        "dscr": {
            "net_operating_incomes": [
                Decimal("0"),
                Decimal("0"),
                Decimal("4200000"),
                Decimal("6500000"),
                Decimal("8200000"),
                Decimal("9200000"),
            ],
            "debt_services": [
                Decimal("0"),
                Decimal("0"),
                Decimal("3100000"),
                Decimal("3200000"),
                Decimal("3200000"),
                Decimal("3200000"),
            ],
            "period_labels": ["M1", "M2", "M3", "M4", "M5", "M6"],
        },
        "cost_items": (
            {
                "name": "Land acquisition",
                "category": "land",
                "cost_group": "acquisition",
                "total_cost": Decimal("12000000"),
            },
            {
                "name": "Enhanced construction",
                "category": "construction",
                "cost_group": "hard_costs",
                "quantity": Decimal("25500"),
                "unit_cost": Decimal("1000"),
                "total_cost": Decimal("25500000"),
            },
            {
                "name": "Experience centre & marketing",
                "category": "soft_costs",
                "cost_group": "marketing",
                "total_cost": Decimal("3600000"),
            },
        ),
        "schedule": (
            {
                "month_index": 1,
                "hard_cost": Decimal("2200000"),
                "soft_cost": Decimal("550000"),
                "revenue": Decimal("0"),
            },
            {
                "month_index": 2,
                "hard_cost": Decimal("3600000"),
                "soft_cost": Decimal("650000"),
                "revenue": Decimal("0"),
            },
            {
                "month_index": 3,
                "hard_cost": Decimal("4200000"),
                "soft_cost": Decimal("700000"),
                "revenue": Decimal("0"),
            },
            {
                "month_index": 4,
                "hard_cost": Decimal("3800000"),
                "soft_cost": Decimal("650000"),
                "revenue": Decimal("4500000"),
            },
            {
                "month_index": 5,
                "hard_cost": Decimal("3200000"),
                "soft_cost": Decimal("600000"),
                "revenue": Decimal("9500000"),
            },
            {
                "month_index": 6,
                "hard_cost": Decimal("1800000"),
                "soft_cost": Decimal("350000"),
                "revenue": Decimal("13500000"),
            },
        ),
        "capital_stack": (
            {
                "name": "Sponsor Equity",
                "source_type": "equity",
                "amount": Decimal("16440000"),
            },
            {
                "name": "Senior Loan",
                "source_type": "debt",
                "amount": Decimal("20550000"),
                "rate": Decimal("0.0450"),
                "tranche_order": 1,
            },
            {
                "name": "Mezzanine Loan",
                "source_type": "mezzanine_debt",
                "amount": Decimal("4110000"),
                "rate": Decimal("0.0825"),
                "tranche_order": 2,
            },
        ),
        "drawdown_schedule": (
            {
                "period": "M1",
                "equity_draw": Decimal("6500000"),
                "debt_draw": Decimal("1800000"),
            },
            {
                "period": "M2",
                "equity_draw": Decimal("5000000"),
                "debt_draw": Decimal("3200000"),
            },
            {
                "period": "M3",
                "equity_draw": Decimal("3200000"),
                "debt_draw": Decimal("4900000"),
            },
            {
                "period": "M4",
                "equity_draw": Decimal("800000"),
                "debt_draw": Decimal("5300000"),
            },
            {
                "period": "M5",
                "equity_draw": Decimal("600000"),
                "debt_draw": Decimal("5400000"),
            },
            {
                "period": "M6",
                "equity_draw": Decimal("344000"),
                "debt_draw": Decimal("4060000"),
            },
        ),
    },
    {
        "key": "C",
        "name": "Scenario C – Downside Stress",
        "description": "Conservative absorption with extended sales cycle.",
        "is_primary": False,
        "cost_escalation": {
            "amount": Decimal("36800000"),
            "base_period": "2024-Q1",
            "series_name": "construction_all_in",
            "jurisdiction": "SG",
            "provider": "Public",
        },
        "cash_flow": {
            "discount_rate": Decimal("0.085"),
            "cash_flows": [
                Decimal("-2250000"),
                Decimal("-3750000"),
                Decimal("-4100000"),
                Decimal("-850000"),
                Decimal("1900000"),
                Decimal("6500000"),
            ],
        },
        "dscr": {
            "net_operating_incomes": [
                Decimal("0"),
                Decimal("0"),
                Decimal("3200000"),
                Decimal("4500000"),
                Decimal("5200000"),
                Decimal("5800000"),
            ],
            "debt_services": [
                Decimal("0"),
                Decimal("0"),
                Decimal("3100000"),
                Decimal("3200000"),
                Decimal("3250000"),
                Decimal("3250000"),
            ],
            "period_labels": ["M1", "M2", "M3", "M4", "M5", "M6"],
        },
        "cost_items": (
            {
                "name": "Land acquisition",
                "category": "land",
                "cost_group": "acquisition",
                "total_cost": Decimal("12000000"),
            },
            {
                "name": "Value-engineered construction",
                "category": "construction",
                "cost_group": "hard_costs",
                "quantity": Decimal("24000"),
                "unit_cost": Decimal("900"),
                "total_cost": Decimal("21600000"),
            },
            {
                "name": "Streamlined soft costs",
                "category": "soft_costs",
                "cost_group": "consultants",
                "total_cost": Decimal("2800000"),
            },
        ),
        "schedule": (
            {
                "month_index": 1,
                "hard_cost": Decimal("1800000"),
                "soft_cost": Decimal("450000"),
                "revenue": Decimal("0"),
            },
            {
                "month_index": 2,
                "hard_cost": Decimal("3200000"),
                "soft_cost": Decimal("550000"),
                "revenue": Decimal("0"),
            },
            {
                "month_index": 3,
                "hard_cost": Decimal("3500000"),
                "soft_cost": Decimal("600000"),
                "revenue": Decimal("0"),
            },
            {
                "month_index": 4,
                "hard_cost": Decimal("3300000"),
                "soft_cost": Decimal("550000"),
                "revenue": Decimal("3000000"),
            },
            {
                "month_index": 5,
                "hard_cost": Decimal("2600000"),
                "soft_cost": Decimal("500000"),
                "revenue": Decimal("5000000"),
            },
            {
                "month_index": 6,
                "hard_cost": Decimal("1200000"),
                "soft_cost": Decimal("300000"),
                "revenue": Decimal("8000000"),
            },
        ),
        "capital_stack": (
            {
                "name": "Sponsor Equity",
                "source_type": "equity",
                "amount": Decimal("14720000"),
            },
            {
                "name": "Senior Loan",
                "source_type": "debt",
                "amount": Decimal("18400000"),
                "rate": Decimal("0.0485"),
                "tranche_order": 1,
            },
            {
                "name": "Bridge Facility",
                "source_type": "bridge_debt",
                "amount": Decimal("3680000"),
                "rate": Decimal("0.0650"),
                "tranche_order": 2,
            },
        ),
        "drawdown_schedule": (
            {
                "period": "M1",
                "equity_draw": Decimal("5200000"),
                "debt_draw": Decimal("1500000"),
            },
            {
                "period": "M2",
                "equity_draw": Decimal("3900000"),
                "debt_draw": Decimal("3000000"),
            },
            {
                "period": "M3",
                "equity_draw": Decimal("2800000"),
                "debt_draw": Decimal("4200000"),
            },
            {
                "period": "M4",
                "equity_draw": Decimal("1400000"),
                "debt_draw": Decimal("4600000"),
            },
            {
                "period": "M5",
                "equity_draw": Decimal("900000"),
                "debt_draw": Decimal("4800000"),
            },
            {
                "period": "M6",
                "equity_draw": Decimal("520000"),
                "debt_draw": Decimal("3980000"),
            },
        ),
    },
)


def _to_decimal(value: DecimalLike, *, places: int = 2) -> Decimal:
    """Normalise *value* to a :class:`Decimal` rounded to ``places`` decimal places."""

    decimal_value = value if isinstance(value, Decimal) else Decimal(str(value))
    if places is None:
        return decimal_value
    quantiser = Decimal("1") if places == 0 else Decimal(f"1.{'0' * places}")
    return decimal_value.quantize(quantiser, rounding=ROUND_HALF_UP)


def _serialise_cashflows(values: Iterable[Decimal]) -> list[str]:
    return [str(_to_decimal(value)) for value in values]


async def ensure_schema() -> None:
    """Create database tables if they do not yet exist."""

    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)


async def _load_indices(
    session: AsyncSession,
    *,
    series_name: str,
    jurisdiction: str,
    provider: str | None,
) -> list[RefCostIndex]:
    stmt = select(RefCostIndex).where(
        RefCostIndex.series_name == series_name,
        RefCostIndex.jurisdiction == jurisdiction,
    )
    if provider:
        stmt = stmt.where(RefCostIndex.provider == provider)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def _seed_scenario(
    session: AsyncSession,
    *,
    fin_project: FinProject,
    definition: Mapping[str, Any],
) -> ScenarioSeedResult:
    key = str(definition.get("key", ""))
    assumptions: dict[str, Any] = {
        "key": key,
        "name": definition["name"],
        "description": definition.get("description"),
        "currency": fin_project.currency,
        "is_primary": bool(definition.get("is_primary", False)),
    }

    cost_config = definition["cost_escalation"]
    cash_config = definition["cash_flow"]
    dscr_config = definition.get("dscr")
    capital_stack_config = definition.get("capital_stack")
    drawdown_config = definition.get("drawdown_schedule")

    assumptions["cost_escalation"] = {
        "amount": str(_to_decimal(cost_config["amount"])),
        "base_period": cost_config["base_period"],
        "series_name": cost_config["series_name"],
        "jurisdiction": cost_config["jurisdiction"],
        "provider": cost_config.get("provider"),
    }
    assumptions["cash_flow"] = {
        "discount_rate": str(_to_decimal(cash_config["discount_rate"], places=4)),
        "cash_flows": _serialise_cashflows(cash_config["cash_flows"]),
    }
    if dscr_config:
        assumptions["dscr"] = {
            "net_operating_incomes": _serialise_cashflows(
                dscr_config["net_operating_incomes"]
            ),
            "debt_services": _serialise_cashflows(dscr_config["debt_services"]),
            "period_labels": list(dscr_config.get("period_labels") or []),
        }
    if capital_stack_config:
        capital_stack_assumptions: list[dict[str, Any]] = []
        for item in capital_stack_config:
            capital_stack_assumptions.append(
                {
                    "name": item["name"],
                    "source_type": item["source_type"],
                    "amount": str(_to_decimal(item["amount"])),
                    "rate": (
                        str(_to_decimal(item["rate"], places=4))
                        if item.get("rate") is not None
                        else None
                    ),
                    "tranche_order": item.get("tranche_order"),
                }
            )
        assumptions["capital_stack"] = capital_stack_assumptions
    if drawdown_config:
        drawdown_assumptions: list[dict[str, Any]] = []
        for entry in drawdown_config:
            drawdown_assumptions.append(
                {
                    "period": entry["period"],
                    "equity_draw": str(_to_decimal(entry.get("equity_draw", 0))),
                    "debt_draw": str(_to_decimal(entry.get("debt_draw", 0))),
                }
            )
        assumptions["drawdown_schedule"] = drawdown_assumptions

    scenario = FinScenario(
        project_id=fin_project.project_id,
        fin_project_id=fin_project.id,
        name=definition["name"],
        description=definition.get("description"),
        assumptions=assumptions,
        is_primary=bool(definition.get("is_primary", False)),
    )
    session.add(scenario)
    await session.flush()

    total_cost = Decimal("0")
    cost_items: list[FinCostItem] = []
    for item in definition.get("cost_items", []):
        quantity = item.get("quantity")
        unit_cost = item.get("unit_cost")
        total = _to_decimal(item["total_cost"])
        total_cost += total
        cost_items.append(
            FinCostItem(
                project_id=fin_project.project_id,
                scenario_id=scenario.id,
                name=item["name"],
                category=item.get("category"),
                cost_group=item.get("cost_group"),
                quantity=_to_decimal(quantity) if quantity is not None else None,
                unit_cost=_to_decimal(unit_cost) if unit_cost is not None else None,
                total_cost=total,
                metadata={"seed": "finance_demo", "scenario_key": key},
            )
        )
    session.add_all(cost_items)

    cumulative = Decimal("0")
    total_revenue = Decimal("0")
    schedule_rows: list[FinSchedule] = []
    for entry in definition.get("schedule", []):
        hard = _to_decimal(entry.get("hard_cost", 0))
        soft = _to_decimal(entry.get("soft_cost", 0))
        revenue = _to_decimal(entry.get("revenue", 0))
        total_revenue += revenue
        cash_flow = revenue - hard - soft
        cumulative += cash_flow
        schedule_rows.append(
            FinSchedule(
                project_id=fin_project.project_id,
                scenario_id=scenario.id,
                month_index=int(entry.get("month_index", 0)),
                hard_cost=hard,
                soft_cost=soft,
                revenue=revenue,
                cash_flow=cash_flow,
                cumulative_cash_flow=cumulative,
                metadata={"seed": "finance_demo", "scenario_key": key},
            )
        )
    session.add_all(schedule_rows)

    indices = await _load_indices(
        session,
        series_name=cost_config["series_name"],
        jurisdiction=cost_config["jurisdiction"],
        provider=cost_config.get("provider"),
    )

    escalated_cost = calculator.escalate_amount(
        cost_config["amount"],
        base_period=cost_config["base_period"],
        indices=indices,
        series_name=cost_config["series_name"],
        jurisdiction=cost_config["jurisdiction"],
        provider=cost_config.get("provider"),
    )

    discount_rate = cash_config["discount_rate"]
    cash_flows = tuple(Decimal(str(value)) for value in cash_config["cash_flows"])
    npv_value = calculator.npv(discount_rate, cash_flows)
    npv_rounded = _to_decimal(npv_value)

    irr_value: Decimal | None = None
    irr_metadata: dict[str, Any] = {
        "cash_flows": _serialise_cashflows(cash_flows),
        "discount_rate": str(_to_decimal(discount_rate, places=4)),
    }
    try:
        irr_raw = calculator.irr(cash_flows)
        irr_value = irr_raw.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    except ValueError:
        irr_metadata["warning"] = (
            "IRR could not be computed because the cash flows lack a sign change"
        )

    dscr_entries: list[calculator.DscrEntry] = []
    dscr_metadata: dict[str, Any] = {}
    if dscr_config:
        timeline = calculator.dscr_timeline(
            dscr_config["net_operating_incomes"],
            dscr_config["debt_services"],
            period_labels=dscr_config.get("period_labels"),
            currency=fin_project.currency,
        )
        dscr_entries = timeline
        dscr_metadata = {
            "entries": [
                {
                    "period": str(entry.period),
                    "noi": str(_to_decimal(entry.noi)),
                    "debt_service": str(_to_decimal(entry.debt_service)),
                    "dscr": str(entry.dscr) if entry.dscr is not None else None,
                    "currency": entry.currency,
                }
                for entry in timeline
            ]
        }

    capital_stack_metadata: dict[str, Any] | None = None
    capital_stack_total: Decimal | None = None
    if capital_stack_config:
        capital_stack_inputs: list[dict[str, Any]] = []
        for item in capital_stack_config:
            capital_stack_inputs.append(
                {
                    "name": item["name"],
                    "source_type": item["source_type"],
                    "amount": _to_decimal(item["amount"]),
                    "rate": (
                        _to_decimal(item["rate"], places=4)
                        if item.get("rate") is not None
                        else None
                    ),
                    "tranche_order": item.get("tranche_order"),
                }
            )
        stack_summary = calculator.capital_stack_summary(
            capital_stack_inputs,
            currency=fin_project.currency,
            total_development_cost=escalated_cost,
        )
        capital_stack_rows: list[FinCapitalStack] = []
        slices_payload: list[dict[str, Any]] = []
        for idx, component in enumerate(stack_summary.slices):
            metadata = {
                "seed": "finance_demo",
                "scenario_key": key,
                "category": component.category,
            }
            tranche_order = (
                component.tranche_order if component.tranche_order is not None else idx
            )
            capital_stack_rows.append(
                FinCapitalStack(
                    project_id=fin_project.project_id,
                    scenario_id=scenario.id,
                    name=component.name,
                    source_type=component.source_type,
                    tranche_order=tranche_order,
                    amount=component.amount,
                    rate=component.rate,
                    equity_share=component.share,
                    metadata=metadata,
                )
            )
            slices_payload.append(
                {
                    "name": component.name,
                    "source_type": component.source_type,
                    "category": component.category,
                    "amount": str(component.amount),
                    "share": str(component.share),
                    "rate": str(component.rate) if component.rate is not None else None,
                    "tranche_order": component.tranche_order,
                }
            )
        if capital_stack_rows:
            session.add_all(capital_stack_rows)
        capital_stack_total = stack_summary.total
        capital_stack_metadata = {
            "currency": stack_summary.currency,
            "totals": {
                "total": str(stack_summary.total),
                "equity": str(stack_summary.equity_total),
                "debt": str(stack_summary.debt_total),
                "other": str(stack_summary.other_total),
            },
            "ratios": {
                "equity": (
                    str(stack_summary.equity_ratio)
                    if stack_summary.equity_ratio is not None
                    else None
                ),
                "debt": (
                    str(stack_summary.debt_ratio)
                    if stack_summary.debt_ratio is not None
                    else None
                ),
                "other": (
                    str(stack_summary.other_ratio)
                    if stack_summary.other_ratio is not None
                    else None
                ),
                "loan_to_cost": (
                    str(stack_summary.loan_to_cost)
                    if stack_summary.loan_to_cost is not None
                    else None
                ),
                "weighted_average_debt_rate": (
                    str(stack_summary.weighted_average_debt_rate)
                    if stack_summary.weighted_average_debt_rate is not None
                    else None
                ),
            },
            "slices": slices_payload,
        }

    drawdown_metadata: dict[str, Any] | None = None
    if drawdown_config:
        drawdown_inputs: list[dict[str, Any]] = []
        for entry in drawdown_config:
            drawdown_inputs.append(
                {
                    "period": entry["period"],
                    "equity_draw": _to_decimal(entry.get("equity_draw", 0)),
                    "debt_draw": _to_decimal(entry.get("debt_draw", 0)),
                }
            )
        drawdown_summary = calculator.drawdown_schedule(
            drawdown_inputs,
            currency=fin_project.currency,
        )
        drawdown_metadata = {
            "currency": drawdown_summary.currency,
            "totals": {
                "equity": str(drawdown_summary.total_equity),
                "debt": str(drawdown_summary.total_debt),
                "peak_debt_balance": str(drawdown_summary.peak_debt_balance),
                "final_debt_balance": str(drawdown_summary.final_debt_balance),
            },
            "entries": [
                {
                    "period": entry.period,
                    "equity_draw": str(entry.equity_draw),
                    "debt_draw": str(entry.debt_draw),
                    "total_draw": str(entry.total_draw),
                    "cumulative_equity": str(entry.cumulative_equity),
                    "cumulative_debt": str(entry.cumulative_debt),
                    "outstanding_debt": str(entry.outstanding_debt),
                }
                for entry in drawdown_summary.entries
            ],
        }

    results: list[FinResult] = [
        FinResult(
            project_id=fin_project.project_id,
            scenario_id=scenario.id,
            name="escalated_cost",
            value=escalated_cost,
            unit=fin_project.currency,
            metadata={
                "base_amount": str(_to_decimal(cost_config["amount"])),
                "base_period": cost_config["base_period"],
                "series_name": cost_config["series_name"],
                "jurisdiction": cost_config["jurisdiction"],
                "provider": cost_config.get("provider"),
                "indices_used": len(indices),
            },
        ),
        FinResult(
            project_id=fin_project.project_id,
            scenario_id=scenario.id,
            name="npv",
            value=npv_rounded,
            unit=fin_project.currency,
            metadata={
                "discount_rate": str(_to_decimal(discount_rate, places=4)),
                "cash_flows": _serialise_cashflows(cash_flows),
            },
        ),
        FinResult(
            project_id=fin_project.project_id,
            scenario_id=scenario.id,
            name="irr",
            value=irr_value,
            unit="ratio",
            metadata=irr_metadata,
        ),
    ]

    if dscr_entries:
        results.append(
            FinResult(
                project_id=fin_project.project_id,
                scenario_id=scenario.id,
                name="dscr_timeline",
                value=None,
                unit=None,
                metadata=dscr_metadata,
            )
        )

    if capital_stack_metadata and capital_stack_total is not None:
        results.append(
            FinResult(
                project_id=fin_project.project_id,
                scenario_id=scenario.id,
                name="capital_stack",
                value=capital_stack_total,
                unit=fin_project.currency,
                metadata=capital_stack_metadata,
            )
        )

    if drawdown_metadata:
        results.append(
            FinResult(
                project_id=fin_project.project_id,
                scenario_id=scenario.id,
                name="drawdown_schedule",
                value=None,
                unit=None,
                metadata=drawdown_metadata,
            )
        )

    session.add_all(results)

    return ScenarioSeedResult(
        scenario=scenario,
        cost_items=len(cost_items),
        schedule_rows=len(schedule_rows),
        results=len(results),
        total_cost=total_cost,
        total_revenue=total_revenue,
        cumulative_cash=cumulative,
        escalated_cost=escalated_cost,
        discount_rate=Decimal(str(discount_rate)),
    )


async def seed_finance_demo(
    session: AsyncSession,
    *,
    project_id: Union[int, str, UUID] = DEMO_PROJECT_ID,
    project_name: str = DEMO_PROJECT_NAME,
    currency: str = DEMO_CURRENCY,
    reset_existing: bool = True,
) -> FinanceDemoSummary:
    """Seed a finance demo project with scenarios and sample metrics."""

    project_uuid = _normalise_project_id(project_id)

    project = await session.get(Project, project_uuid)
    if project is None:
        project = Project(
            id=project_uuid,
            project_name=project_name,
            project_code=f"FINANCE-DEMO-{project_uuid.hex[:8].upper()}",
            project_type=ProjectType.NEW_DEVELOPMENT,
            current_phase=ProjectPhase.FEASIBILITY,
            description="Demo project generated by seed_finance_demo",
        )
        session.add(project)
        await session.flush()
    else:
        # Keep demo metadata up to date for repeatable seeding runs.
        project.project_name = project_name
        if not project.description:
            project.description = "Demo project generated by seed_finance_demo"

    if reset_existing:
        existing = await session.execute(
            select(FinProject).where(FinProject.project_id == project_uuid)
        )
        for project in existing.scalars():
            metadata = project.metadata or {}
            if metadata.get("seed") == "finance_demo":
                await session.delete(project)
        await session.flush()

    fin_project = FinProject(
        project_id=project_uuid,
        name=project_name,
        currency=currency,
        metadata={
            "seed": "finance_demo",
            "description": "Demo finance workspace generated by seed_finance_demo",
        },
    )
    session.add(fin_project)
    await session.flush()

    scenario_results: list[ScenarioSeedResult] = []
    for definition in SCENARIO_DEFINITIONS:
        result = await _seed_scenario(
            session, fin_project=fin_project, definition=definition
        )
        scenario_results.append(result)

    primary = next(
        (item for item in scenario_results if item.scenario.is_primary), None
    )
    if primary is None and scenario_results:
        primary = scenario_results[0]

    if primary:
        fin_project.discount_rate = primary.discount_rate
        fin_project.total_development_cost = primary.total_cost
        fin_project.total_gross_profit = primary.cumulative_cash

        fin_project.metadata = {
            **(fin_project.metadata or {}),
            "scenarios": {
                str(definition.get("key", result.scenario.id)): result.scenario.id
                for definition, result in zip(
                    SCENARIO_DEFINITIONS, scenario_results, strict=False
                )
            },
        }

    await session.commit()

    return FinanceDemoSummary(
        project_id=str(fin_project.project_id),
        fin_project_id=fin_project.id,
        scenarios=len(scenario_results),
        cost_items=sum(item.cost_items for item in scenario_results),
        schedule_rows=sum(item.schedule_rows for item in scenario_results),
        results=sum(item.results for item in scenario_results),
    )


async def _cli_main(args: argparse.Namespace) -> FinanceDemoSummary:
    await ensure_schema()
    async with AsyncSessionLocal() as session:
        summary = await seed_finance_demo(
            session,
            project_id=args.project_id,
            project_name=args.project_name,
            currency=args.currency,
            reset_existing=not args.keep_existing,
        )
    return summary


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Seed finance demo scenarios and metrics."
    )
    parser.add_argument(
        "--project-id",
        type=int,
        default=DEMO_PROJECT_ID,
        help="Project identifier used for finance demo records.",
    )
    parser.add_argument(
        "--project-name",
        default=DEMO_PROJECT_NAME,
        help="Display name for the finance project.",
    )
    parser.add_argument(
        "--currency",
        default=DEMO_CURRENCY,
        help="ISO currency code applied to monetary fields.",
    )
    parser.add_argument(
        "--keep-existing",
        action="store_true",
        help="Skip deleting previously seeded finance demo data for the project.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> FinanceDemoSummary:
    """Entry point for CLI execution."""

    parser = _build_parser()
    args = parser.parse_args(argv)
    summary = asyncio.run(_cli_main(args))
    logger.info(
        "seed_finance_demo.summary",
        project_id=summary.project_id,
        fin_project_id=summary.fin_project_id,
        scenarios=summary.scenarios,
        cost_items=summary.cost_items,
        schedule_rows=summary.schedule_rows,
        results=summary.results,
    )
    return summary


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()


__all__ = [
    "FinanceDemoSummary",
    "ScenarioSeedResult",
    "ensure_schema",
    "main",
    "seed_finance_demo",
]
