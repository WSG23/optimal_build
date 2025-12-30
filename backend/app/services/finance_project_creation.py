"""Create finance projects/scenarios from developer GPS captures."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequestIdentity
from app.models.finance import FinCapitalStack, FinProject, FinScenario
from app.models.projects import Project, ProjectPhase, ProjectType
from app.models.property import Property
from app.schemas.finance import (
    CapitalStackSliceInput,
    CashflowInputs,
    CostEscalationInput,
    FinanceScenarioInput,
    SensitivityBandInput,
)
from app.services.jurisdictions import get_jurisdiction_config


@dataclass(frozen=True, slots=True)
class FinanceProjectCreationResult:
    project_id: UUID
    fin_project_id: int
    scenario_id: int
    project_name: str


def _coerce_decimal(value: float | int | str | Decimal | None) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _quantize_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _build_capital_stack_inputs(
    total_cost: Decimal,
    *,
    equity_pct: Decimal,
    debt_pct: Decimal,
    preferred_pct: Decimal,
) -> list[CapitalStackSliceInput]:
    total = _quantize_money(total_cost)
    equity_amount = _quantize_money(total * equity_pct / Decimal("100"))
    debt_amount = _quantize_money(total * debt_pct / Decimal("100"))
    preferred_amount = _quantize_money(total - equity_amount - debt_amount)

    return [
        CapitalStackSliceInput(
            name="Equity",
            source_type="equity",
            amount=max(Decimal("0"), equity_amount),
            tranche_order=0,
        ),
        CapitalStackSliceInput(
            name="Senior Debt",
            source_type="debt",
            amount=max(Decimal("0"), debt_amount),
            tranche_order=1,
        ),
        CapitalStackSliceInput(
            name="Preferred",
            source_type="preferred",
            amount=max(Decimal("0"), preferred_amount),
            tranche_order=2,
        ),
    ]


async def create_finance_project_from_capture(
    *,
    session: AsyncSession,
    identity: RequestIdentity,
    property_id: UUID,
    project_name: str | None = None,
    scenario_name: str | None = None,
    total_estimated_capex_sgd: float | None = None,
    total_estimated_revenue_sgd: float | None = None,
) -> FinanceProjectCreationResult:
    """Create Project → FinProject → FinScenario for a GPS-captured Property.

    Notes:
    - Finance scenario listing requires `cost_escalation` and `cash_flow` to be present
      in `FinScenario.assumptions`, even if values are placeholder estimates.
    - The capital stack shares are derived from the (Phase 2B) blueprint defaults:
      35% equity / 60% debt / 5% preferred.
    """

    property_record = await session.get(Property, property_id)
    if property_record is None:
        raise ValueError("property_not_found")

    cleaned_project_name = (project_name or property_record.name or "").strip()
    if not cleaned_project_name:
        cleaned_project_name = "GPS Capture Project"
    cleaned_scenario_name = (scenario_name or "Base Case").strip() or "Base Case"

    jurisdiction_code = (property_record.jurisdiction_code or "SG").strip().upper()
    jurisdiction = get_jurisdiction_config(jurisdiction_code)
    currency = jurisdiction.currency_code

    owner_email = (identity.email or "").strip() or None
    owner_id: UUID | None = None
    if identity.user_id:
        try:
            owner_id = UUID(identity.user_id)
        except ValueError:
            owner_id = None
    if owner_email is None and owner_id is None:
        raise ValueError("identity_required")

    project: Project | None = None
    if property_record.project_id is not None:
        project = await session.get(Project, property_record.project_id)

    if project is None:
        # Generate a unique code (required by Project model).
        project_code = f"gps_{property_id.hex}"
        project = Project(
            project_name=cleaned_project_name,
            project_code=project_code,
            project_type=ProjectType.NEW_DEVELOPMENT,
            current_phase=ProjectPhase.CONCEPT,
            owner_id=owner_id,
            owner_email=owner_email,
            start_date=date.today(),
        )
        session.add(project)
        await session.flush()

        property_record.project_id = project.id

    if owner_email and not property_record.owner_email:
        property_record.owner_email = owner_email

    # Re-use an existing finance project if present for the project.
    fin_project: FinProject | None = None
    result = await session.execute(
        select(FinProject)
        .where(FinProject.project_id == project.id)
        .order_by(FinProject.id)
        .limit(1)
    )
    fin_project = result.scalar_one_or_none()
    if fin_project is None:
        fin_project = FinProject(
            project_id=project.id,
            name=cleaned_project_name,
            currency=currency,
            discount_rate=Decimal("0.085"),
            metadata={
                "source": "developer_gps_capture",
                "property_id": str(property_id),
            },
        )
        session.add(fin_project)
        await session.flush()

    capex = _coerce_decimal(total_estimated_capex_sgd)
    revenue = _coerce_decimal(total_estimated_revenue_sgd)
    total_cost = _quantize_money(capex if capex and capex > 0 else Decimal("1000000"))
    if revenue is None or revenue <= 0:
        revenue = _quantize_money(total_cost * Decimal("1.10"))
    else:
        revenue = _quantize_money(revenue)

    # Phase 2B blueprint defaults (base case).
    equity_pct = Decimal("35")
    debt_pct = Decimal("60")
    preferred_pct = Decimal("5")

    capital_stack = _build_capital_stack_inputs(
        total_cost,
        equity_pct=equity_pct,
        debt_pct=debt_pct,
        preferred_pct=preferred_pct,
    )

    scenario_input = FinanceScenarioInput(
        name=cleaned_scenario_name,
        description="Auto-generated from GPS capture",
        currency=currency,
        is_primary=True,
        jurisdiction_code=jurisdiction.code,
        cost_escalation=CostEscalationInput(
            amount=total_cost,
            base_period="2024-Q1",
            series_name="construction_all_in",
            jurisdiction=jurisdiction.code,
        ),
        cash_flow=CashflowInputs(
            discount_rate=Decimal("0.085"),
            cash_flows=[-total_cost, revenue],
        ),
        capital_stack=capital_stack,
        sensitivity_bands=[
            SensitivityBandInput(
                parameter="Rent",
                low=Decimal("-8"),
                base=Decimal("0"),
                high=Decimal("6"),
            ),
            SensitivityBandInput(
                parameter="Construction Cost",
                low=Decimal("10"),
                base=Decimal("0"),
                high=Decimal("-5"),
            ),
            SensitivityBandInput(
                parameter="Interest Rate (delta %)",
                low=Decimal("1.50"),
                base=Decimal("0"),
                high=Decimal("-0.75"),
            ),
        ],
    )

    scenario = FinScenario(
        project_id=project.id,
        fin_project_id=fin_project.id,
        name=scenario_input.name,
        description=scenario_input.description,
        assumptions=scenario_input.model_dump(mode="json"),
        is_primary=True,
        jurisdiction_code=jurisdiction.code,
        ltv_limit_pct=Decimal("60"),
    )
    session.add(scenario)
    await session.flush()

    stack_rows: list[FinCapitalStack] = []
    for slice_input in capital_stack:
        share = None
        try:
            share = (slice_input.amount / total_cost) if total_cost > 0 else None
        except Exception:
            share = None
        stack_rows.append(
            FinCapitalStack(
                project_id=project.id,
                scenario_id=scenario.id,
                name=slice_input.name,
                source_type=slice_input.source_type,
                tranche_order=slice_input.tranche_order,
                amount=slice_input.amount,
                rate=slice_input.rate,
                equity_share=share,
                metadata_json={
                    "share": str(share) if share is not None else None,
                },
            )
        )
    session.add_all(stack_rows)

    await session.commit()

    return FinanceProjectCreationResult(
        project_id=project.id,
        fin_project_id=fin_project.id,
        scenario_id=scenario.id,
        project_name=project.project_name,
    )
