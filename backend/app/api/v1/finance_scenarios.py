"""Finance scenario CRUD API endpoints.

This module handles:
- POST /feasibility - Execute full finance pipeline for a scenario
- GET /scenarios - List persisted finance scenarios
- PATCH /scenarios/{id} - Update scenario metadata
- DELETE /scenarios/{scenario_id} - Delete a scenario
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import ROUND_HALF_UP, Decimal
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import RequestIdentity, require_reviewer, require_viewer
from app.core.database import get_session
from app.models.finance import (
    FinProject,
    FinResult,
    FinScenario,
)
from app.models.projects import Project
from app.models.rkp import RefCostIndex
from app.schemas.finance import (
    AssetFinancialSummarySchema,
    ConstructionLoanInput,
    ConstructionLoanInterestSchema,
    CostIndexProvenance,
    DscrEntrySchema,
    FinanceAssetBreakdownSchema,
    FinanceFeasibilityResponse,
    FinanceResultSchema,
    FinanceSensitivityOutcomeSchema,
    SensitivityBandInput,
)
from app.services.finance import (
    calculator,
)
from app.utils.logging import get_logger, log_event

from .finance_common import (
    FinanceScenarioUpdatePayload,
    build_cost_index_snapshot,
    build_facility_metadata_map,
    compute_scalar,
    convert_capital_stack_summary,
    convert_drawdown_schedule,
    convert_dscr_entry,
    decimal_from_value,
    json_safe,
    merge_facility_metadata,
    normalise_facility_key,
    normalise_project_id,
    project_uuid_from_scenario,
    scenario_job_statuses,
    serialise_asset_breakdown_model,
)

router = APIRouter(prefix="/finance", tags=["finance"])
logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Project Owner Verification
# ---------------------------------------------------------------------------


async def _ensure_project_owner(
    session: AsyncSession,
    project_uuid: UUID,
    identity: RequestIdentity,
) -> None:
    """Verify that the caller owns the referenced project (admin bypass)."""

    from .finance_common import raise_finance_privacy_error

    if identity.role == "admin":
        return

    stmt = select(Project.owner_id, Project.owner_email).where(
        Project.id == project_uuid
    )
    result = await session.execute(stmt)
    row = result.first()
    if row is None:
        raise_finance_privacy_error(
            project_uuid=project_uuid,
            identity=identity,
            reason="project_missing",
            detail="Finance data restricted to project owner.",
        )

    owner_id, owner_email = row
    if owner_id is None and owner_email is None:
        raise_finance_privacy_error(
            project_uuid=project_uuid,
            identity=identity,
            reason="owner_metadata_missing",
            detail="Finance data restricted to project owner.",
        )

    if not identity.user_id and not identity.email:
        raise_finance_privacy_error(
            project_uuid=project_uuid,
            identity=identity,
            reason="identity_metadata_missing",
            detail=(
                "Finance data restricted to project owner; "
                "supply X-User-Id or X-User-Email headers."
            ),
        )

    matches = False
    if identity.user_id and owner_id is not None:
        matches |= str(owner_id) == identity.user_id
    if identity.email and owner_email:
        matches |= owner_email.lower() == identity.email.lower()

    if not matches:
        raise_finance_privacy_error(
            project_uuid=project_uuid,
            identity=identity,
            reason="ownership_mismatch",
            detail="Finance data restricted to project owner.",
        )


# ---------------------------------------------------------------------------
# Cost Index Loading
# ---------------------------------------------------------------------------


async def _load_cost_indices(
    session: AsyncSession,
    *,
    series_name: str,
    jurisdiction: str,
    provider: str | None,
) -> list[RefCostIndex]:
    """Load cost indices for escalation calculations."""

    stmt = select(RefCostIndex).where(
        RefCostIndex.series_name == series_name,
        RefCostIndex.jurisdiction == jurisdiction,
    )
    if provider:
        stmt = stmt.where(RefCostIndex.provider == provider)
    result = await session.execute(stmt)
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Scenario Summarisation (FinanceScenarioMapper equivalent)
# ---------------------------------------------------------------------------


async def summarise_persisted_scenario(
    scenario: FinScenario,
    *,
    session: AsyncSession,
) -> FinanceFeasibilityResponse:
    """Transform a persisted scenario into a complete API response.

    This function is the core mapper that reconstructs the full finance
    feasibility response from stored scenario data, results, and assumptions.
    """

    assumptions: dict[str, Any] = dict(scenario.assumptions or {})
    sensitivity_results: list[FinanceSensitivityOutcomeSchema] = []
    construction_loan_config: ConstructionLoanInput | None = None
    raw_construction = assumptions.get("construction_loan")
    if isinstance(raw_construction, Mapping):
        try:
            construction_loan_config = ConstructionLoanInput.model_validate(
                raw_construction
            )
        except Exception:  # pragma: no cover - defensive for legacy records
            construction_loan_config = None
    fin_project = scenario.fin_project
    sensitivity_jobs = scenario_job_statuses(scenario)
    if fin_project is None:
        raise HTTPException(
            status_code=500, detail="Finance project missing for scenario"
        )

    sensitivity_band_inputs: list[SensitivityBandInput] = []
    raw_bands = assumptions.get("sensitivity_bands")
    if isinstance(raw_bands, list):
        for entry in raw_bands:
            if not isinstance(entry, Mapping):
                continue
            try:
                sensitivity_band_inputs.append(
                    SensitivityBandInput.model_validate(entry)
                )
            except Exception:  # pragma: no cover - tolerate invalid legacy rows
                continue

    cost_config = assumptions.get("cost_escalation") or {}
    cash_config = assumptions.get("cash_flow") or {}
    dscr_config = assumptions.get("dscr")
    capital_stack_config = assumptions.get("capital_stack")
    drawdown_config = assumptions.get("drawdown_schedule")

    try:
        amount_value = decimal_from_value(cost_config["amount"])
    except (
        KeyError
    ) as exc:  # pragma: no cover - seeded data always includes cost config
        raise HTTPException(
            status_code=500, detail="Scenario missing cost escalation data"
        ) from exc

    indices = await _load_cost_indices(
        session,
        series_name=cost_config.get("series_name", ""),
        jurisdiction=cost_config.get("jurisdiction", ""),
        provider=cost_config.get("provider"),
    )

    escalated_cost = calculator.escalate_amount(
        amount_value,
        base_period=cost_config.get("base_period", ""),
        indices=indices,
        series_name=cost_config.get("series_name"),
        jurisdiction=cost_config.get("jurisdiction"),
        provider=cost_config.get("provider"),
    )

    latest_index = RefCostIndex.latest(
        indices,
        jurisdiction=cost_config.get("jurisdiction"),
        provider=cost_config.get("provider"),
        series_name=cost_config.get("series_name"),
    )
    base_index: RefCostIndex | None = None
    for index in indices:
        if str(index.period) != cost_config.get("base_period"):
            continue
        if index.series_name != cost_config.get("series_name"):
            continue
        if index.jurisdiction != cost_config.get("jurisdiction"):
            continue
        if cost_config.get("provider") and index.provider != cost_config.get(
            "provider"
        ):
            continue
        base_index = index
        break

    cost_provenance = CostIndexProvenance(
        series_name=cost_config.get("series_name", ""),
        jurisdiction=cost_config.get("jurisdiction", ""),
        provider=cost_config.get("provider"),
        base_period=cost_config.get("base_period", ""),
        latest_period=str(latest_index.period) if latest_index else None,
        scalar=compute_scalar(
            build_cost_index_snapshot(base_index),
            build_cost_index_snapshot(latest_index),
        ),
        base_index=build_cost_index_snapshot(base_index),
        latest_index=build_cost_index_snapshot(latest_index),
    )

    discount_rate = cash_config.get("discount_rate", "0")
    cash_flows = cash_config.get("cash_flows") or []
    npv_value = calculator.npv(discount_rate, cash_flows)
    npv_rounded = npv_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    irr_value: Decimal | None = None
    irr_metadata = {
        "cash_flows": [str(value) for value in cash_flows],
        "discount_rate": str(discount_rate),
    }
    try:
        irr_raw = calculator.irr(cash_flows)
        irr_value = irr_raw.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    except ValueError:
        irr_metadata["warning"] = (
            "IRR could not be computed for the provided cash flows"
        )

    dscr_entries: list[DscrEntrySchema] = []
    if dscr_config:
        timeline = calculator.dscr_timeline(
            dscr_config.get("net_operating_incomes", []),
            dscr_config.get("debt_services", []),
            period_labels=dscr_config.get("period_labels"),
            currency=fin_project.currency,
        )
        dscr_entries = [convert_dscr_entry(entry) for entry in timeline]

    facility_metadata_map = build_facility_metadata_map(construction_loan_config)

    capital_stack_inputs: list[Mapping[str, Any]] = []
    if scenario.capital_stack:
        ordered = sorted(
            scenario.capital_stack,
            key=lambda item: (
                item.tranche_order if item.tranche_order is not None else item.id
            ),
        )
        for entry in ordered:
            facility_key = normalise_facility_key(entry.name)
            facility_meta = facility_metadata_map.get(facility_key)
            metadata = merge_facility_metadata(entry.metadata, facility_meta)
            capital_stack_inputs.append(
                {
                    "name": entry.name,
                    "source_type": entry.source_type or "other",
                    "amount": entry.amount or Decimal("0"),
                    "rate": entry.rate,
                    "tranche_order": entry.tranche_order,
                    "metadata": metadata,
                }
            )
    elif isinstance(capital_stack_config, list):
        for item in capital_stack_config:
            slice_payload = item.model_dump(mode="json")
            facility_key = normalise_facility_key(slice_payload.get("name"))
            facility_meta = facility_metadata_map.get(facility_key)
            metadata = merge_facility_metadata(
                slice_payload.get("metadata"), facility_meta
            )
            capital_stack_inputs.append(
                {
                    "name": slice_payload.get("name", ""),
                    "source_type": slice_payload.get("source_type", "other"),
                    "amount": decimal_from_value(slice_payload.get("amount", "0")),
                    "rate": (
                        decimal_from_value(slice_payload.get("rate"))
                        if slice_payload.get("rate") is not None
                        else None
                    ),
                    "tranche_order": slice_payload.get("tranche_order"),
                    "metadata": metadata,
                }
            )

    capital_stack_summary = None
    if capital_stack_inputs:
        capital_stack_summary = calculator.capital_stack_summary(
            capital_stack_inputs,
            currency=fin_project.currency,
            total_development_cost=escalated_cost,
        )

    drawdown_summary = None
    if isinstance(drawdown_config, list) and drawdown_config:
        schedule_inputs = []
        for entry in drawdown_config:
            schedule_inputs.append(
                {
                    "period": entry.get("period", ""),
                    "equity_draw": decimal_from_value(entry.get("equity_draw", "0")),
                    "debt_draw": decimal_from_value(entry.get("debt_draw", "0")),
                }
            )
        drawdown_summary = calculator.drawdown_schedule(
            schedule_inputs,
            currency=fin_project.currency,
        )

    dscr_metadata = {}
    if dscr_entries:
        dscr_metadata = {
            "entries": [
                json_safe(entry.model_dump(mode="json")) for entry in dscr_entries
            ],
        }

    capital_metadata = None
    if capital_stack_summary:
        capital_metadata = {
            "currency": capital_stack_summary.currency,
            "totals": {
                "total": str(capital_stack_summary.total),
                "equity": str(capital_stack_summary.equity_total),
                "debt": str(capital_stack_summary.debt_total),
                "other": str(capital_stack_summary.other_total),
            },
            "ratios": {
                "equity": (
                    str(capital_stack_summary.equity_ratio)
                    if capital_stack_summary.equity_ratio is not None
                    else None
                ),
                "debt": (
                    str(capital_stack_summary.debt_ratio)
                    if capital_stack_summary.debt_ratio is not None
                    else None
                ),
                "other": (
                    str(capital_stack_summary.other_ratio)
                    if capital_stack_summary.other_ratio is not None
                    else None
                ),
                "loan_to_cost": (
                    str(capital_stack_summary.loan_to_cost)
                    if capital_stack_summary.loan_to_cost is not None
                    else None
                ),
                "weighted_average_debt_rate": (
                    str(capital_stack_summary.weighted_average_debt_rate)
                    if capital_stack_summary.weighted_average_debt_rate is not None
                    else None
                ),
            },
            "slices": [
                {
                    "name": component.name,
                    "source_type": component.source_type,
                    "category": component.category,
                    "amount": str(component.amount),
                    "share": str(component.share),
                    "rate": str(component.rate) if component.rate is not None else None,
                    "tranche_order": component.tranche_order,
                }
                for component in capital_stack_summary.slices
            ],
        }

    drawdown_metadata = None
    if drawdown_summary:
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

    asset_mix_summary_schema: AssetFinancialSummarySchema | None = None
    asset_breakdown_schemas: list[FinanceAssetBreakdownSchema] = []
    if getattr(scenario, "asset_breakdowns", None):
        asset_breakdown_schemas = [
            serialise_asset_breakdown_model(record)
            for record in sorted(
                scenario.asset_breakdowns,
                key=lambda item: getattr(item, "id", 0) or 0,
            )
        ]
    construction_interest_schema: ConstructionLoanInterestSchema | None = None
    construction_interest_metadata: dict[str, Any] | None = None
    construction_interest_value: Decimal | None = None
    ordered_results = sorted(
        scenario.results, key=lambda item: getattr(item, "id", 0) or 0
    )
    asset_processed = False
    sensitivity_metadata_rows: list[dict[str, Any]] | None = None
    analytics_overview_result: FinResult | None = None
    for stored in ordered_results:
        metadata: dict[str, Any] | None = (  # type: ignore[assignment,has-type]
            stored.metadata if isinstance(stored.metadata, dict) else None
        )
        if stored.name == "asset_financials" and metadata and not asset_processed:
            summary_meta = metadata.get("summary")
            if summary_meta:
                try:
                    asset_mix_summary_schema = (
                        AssetFinancialSummarySchema.model_validate(summary_meta)
                    )
                except Exception:  # pragma: no cover - defensive for historical data
                    asset_mix_summary_schema = None
            breakdown_meta = metadata.get("breakdowns")
            if isinstance(breakdown_meta, list) and not asset_breakdown_schemas:
                converted: list[FinanceAssetBreakdownSchema] = []
                for entry in breakdown_meta:
                    if not isinstance(entry, dict):
                        continue
                    try:
                        converted.append(
                            FinanceAssetBreakdownSchema.model_validate(entry)
                        )
                    except Exception:  # pragma: no cover - defensive
                        continue
                asset_breakdown_schemas = converted
            asset_processed = True
            continue

        if stored.name == "sensitivity_analysis" and metadata:
            bands_meta = metadata.get("bands")
            if isinstance(bands_meta, list):
                parsed_entries: list[FinanceSensitivityOutcomeSchema] = []
                cleaned_metadata: list[dict[str, Any]] = []
                for entry in bands_meta:
                    if not isinstance(entry, dict):
                        continue
                    cleaned_metadata.append(entry)
                    if entry.get("parameter") == "__async__":
                        continue
                    try:
                        parsed_entries.append(
                            FinanceSensitivityOutcomeSchema.model_validate(entry)
                        )
                    except Exception:  # pragma: no cover - tolerate legacy rows
                        continue
                if parsed_entries:
                    sensitivity_results = parsed_entries
                if cleaned_metadata:
                    sensitivity_metadata_rows = cleaned_metadata
            continue

        if stored.name == "construction_loan_interest" and metadata:
            try:
                construction_interest_schema = (
                    ConstructionLoanInterestSchema.model_validate(metadata)
                )
                construction_interest_metadata = metadata
                construction_interest_value = stored.value
            except Exception:  # pragma: no cover - defensive for historical data
                construction_interest_schema = None

        if stored.name == "analytics_overview":
            analytics_overview_result = stored
            continue

    results: list[FinanceResultSchema] = [
        FinanceResultSchema(
            name="escalated_cost",
            value=escalated_cost,
            unit=fin_project.currency,
            metadata={
                "base_amount": str(amount_value),
                "base_period": cost_config.get("base_period"),
                "cost_index": json_safe(cost_provenance.model_dump(mode="json")),
            },
        ),
        FinanceResultSchema(
            name="npv",
            value=npv_rounded,
            unit=fin_project.currency,
            metadata={
                "discount_rate": str(discount_rate),
                "cash_flows": [str(value) for value in cash_flows],
            },
        ),
        FinanceResultSchema(
            name="irr",
            value=irr_value,
            unit="ratio",
            metadata=irr_metadata,
        ),
    ]

    if dscr_entries:
        results.append(
            FinanceResultSchema(
                name="dscr_timeline",
                value=None,
                metadata=dscr_metadata,
            )
        )

    if capital_metadata and capital_stack_summary:
        results.append(
            FinanceResultSchema(
                name="capital_stack",
                value=capital_stack_summary.total,
                unit=fin_project.currency,
                metadata=capital_metadata,
            )
        )

    if drawdown_metadata:
        results.append(
            FinanceResultSchema(
                name="drawdown_schedule",
                value=None,
                metadata=drawdown_metadata,
            )
        )

    if asset_mix_summary_schema or asset_breakdown_schemas:
        results.append(
            FinanceResultSchema(
                name="asset_financials",
                value=None,
                metadata={
                    "summary": (
                        asset_mix_summary_schema.model_dump(mode="json")
                        if asset_mix_summary_schema
                        else None
                    ),
                    "breakdowns": [
                        breakdown.model_dump(mode="json")
                        for breakdown in asset_breakdown_schemas
                    ],
                },
            )
        )

    if construction_interest_schema and construction_interest_metadata:
        results.append(
            FinanceResultSchema(
                name="construction_loan_interest",
                value=construction_interest_value,
                unit=fin_project.currency,
                metadata=construction_interest_metadata,
            )
        )
    if sensitivity_metadata_rows:
        results.append(
            FinanceResultSchema(
                name="sensitivity_analysis",
                value=None,
                unit=None,
                metadata={"bands": sensitivity_metadata_rows},
            )
        )

    if analytics_overview_result:
        results.append(
            FinanceResultSchema(
                name="analytics_overview",
                value=analytics_overview_result.value,
                unit=analytics_overview_result.unit,
                metadata=(
                    analytics_overview_result.metadata
                    if isinstance(analytics_overview_result.metadata, dict)
                    else {}
                ),
            )
        )

    drawdown_schema = None
    if drawdown_summary:
        drawdown_schema = convert_drawdown_schedule(drawdown_summary)

    return FinanceFeasibilityResponse(
        scenario_id=scenario.id,
        project_id=str(scenario.project_id),
        fin_project_id=scenario.fin_project_id,
        scenario_name=scenario.name,
        currency=fin_project.currency,
        escalated_cost=escalated_cost,
        cost_index=cost_provenance,
        results=results,
        dscr_timeline=dscr_entries,
        capital_stack=(
            convert_capital_stack_summary(capital_stack_summary)
            if capital_stack_summary
            else None
        ),
        drawdown_schedule=drawdown_schema,
        asset_mix_summary=asset_mix_summary_schema,
        asset_breakdowns=asset_breakdown_schemas,
        construction_loan_interest=construction_interest_schema,
        construction_loan=construction_loan_config,
        sensitivity_results=sensitivity_results,
        sensitivity_jobs=sensitivity_jobs,
        sensitivity_bands=sensitivity_band_inputs,
        is_primary=bool(scenario.is_primary),
        is_private=bool(getattr(scenario, "is_private", False)),
        updated_at=scenario.updated_at,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/scenarios", response_model=list[FinanceFeasibilityResponse])
async def list_finance_scenarios(
    project_id: str | int | UUID | None = Query(None),
    fin_project_id: int | None = Query(None),
    session: AsyncSession = Depends(get_session),
    identity: RequestIdentity = Depends(require_viewer),
) -> list[FinanceFeasibilityResponse]:
    """Return previously persisted finance scenarios for the requested project."""

    if project_id is None and fin_project_id is None:
        raise HTTPException(
            status_code=400,
            detail="project_id or fin_project_id must be provided",
        )

    stmt = (
        select(FinScenario)
        .options(
            selectinload(FinScenario.fin_project),
            selectinload(FinScenario.capital_stack),
            selectinload(FinScenario.results),
            selectinload(FinScenario.asset_breakdowns),
        )
        .order_by(FinScenario.id)
    )
    checked_projects: set[UUID] = set()

    if fin_project_id is not None:
        fin_project = await session.get(FinProject, fin_project_id)
        if fin_project is None:
            raise HTTPException(status_code=404, detail="Finance project not found")
        fin_project_uuid = normalise_project_id(fin_project.project_id)
        await _ensure_project_owner(session, fin_project_uuid, identity)
        checked_projects.add(fin_project_uuid)
        stmt = stmt.where(FinScenario.fin_project_id == fin_project_id)

    if project_id is not None:
        try:
            if isinstance(project_id, str):
                stripped = project_id.strip()
                if stripped.isdigit():
                    normalised = normalise_project_id(int(stripped))
                else:
                    normalised = normalise_project_id(stripped)
            else:
                normalised = normalise_project_id(project_id)
        except HTTPException as exc:
            raise exc
        except Exception as exc:  # pragma: no cover - defensive for unexpected types
            raise HTTPException(
                status_code=422, detail="project_id must be a valid UUID"
            ) from exc

        await _ensure_project_owner(session, normalised, identity)
        checked_projects.add(normalised)
        stmt = stmt.where(FinScenario.project_id == str(normalised))

    result = await session.execute(stmt)
    scenarios = list(result.scalars().all())

    summaries: list[FinanceFeasibilityResponse] = []
    for scenario in scenarios:
        scenario_project_uuid = project_uuid_from_scenario(scenario)
        if scenario_project_uuid not in checked_projects:
            await _ensure_project_owner(session, scenario_project_uuid, identity)
            checked_projects.add(scenario_project_uuid)
        summaries.append(await summarise_persisted_scenario(scenario, session=session))

    return summaries


@router.patch(
    "/scenarios/{scenario_id}",
    response_model=FinanceFeasibilityResponse,
)
async def update_finance_scenario(
    scenario_id: int,
    payload: FinanceScenarioUpdatePayload,
    session: AsyncSession = Depends(get_session),
    identity: RequestIdentity = Depends(require_reviewer),
) -> FinanceFeasibilityResponse:
    """Update mutable fields on a persisted finance scenario."""

    base_stmt = (
        select(FinScenario)
        .where(FinScenario.id == scenario_id)
        .options(
            selectinload(FinScenario.fin_project),
            selectinload(FinScenario.capital_stack),
            selectinload(FinScenario.results),
            selectinload(FinScenario.asset_breakdowns),
        )
    )
    scenario = (await session.execute(base_stmt)).scalars().first()
    if scenario is None:
        raise HTTPException(status_code=404, detail="Finance scenario not found")

    scenario_project_uuid = project_uuid_from_scenario(scenario)
    await _ensure_project_owner(session, scenario_project_uuid, identity)

    updated = False
    if payload.scenario_name is not None:
        name = payload.scenario_name.strip()
        if name and name != scenario.name:
            scenario.name = name
            updated = True
    if payload.description is not None and payload.description != scenario.description:
        scenario.description = payload.description
        updated = True
    if payload.is_primary is not None and payload.is_primary != scenario.is_primary:
        scenario.is_primary = payload.is_primary
        updated = True
        if payload.is_primary:
            await session.execute(
                update(FinScenario)
                .where(
                    FinScenario.fin_project_id == scenario.fin_project_id,
                    FinScenario.id != scenario.id,
                )
                .values(is_primary=False)
            )

    if updated:
        await session.commit()
        scenario = (await session.execute(base_stmt)).scalars().first()
        if scenario is None:
            raise HTTPException(status_code=404, detail="Finance scenario not found")
    return await summarise_persisted_scenario(scenario, session=session)


@router.delete("/scenarios/{scenario_id}", status_code=204)
async def delete_finance_scenario(
    scenario_id: int,
    session: AsyncSession = Depends(get_session),
    identity: RequestIdentity = Depends(require_reviewer),
) -> Response:
    """Delete a persisted finance scenario and associated modelling data."""

    stmt = (
        select(FinScenario)
        .where(FinScenario.id == scenario_id)
        .options(selectinload(FinScenario.fin_project))
    )
    scenario = (await session.execute(stmt)).scalars().first()
    if scenario is None:
        raise HTTPException(status_code=404, detail="Finance scenario not found")

    scenario_project_uuid = project_uuid_from_scenario(scenario)
    await _ensure_project_owner(session, scenario_project_uuid, identity)
    await session.delete(scenario)
    await session.commit()

    log_event(
        logger,
        "finance_feasibility_deleted",
        scenario_id=scenario_id,
        project_id=str(scenario_project_uuid),
    )
    return Response(status_code=204)


# Export for use by other finance modules
__all__ = [
    "router",
    "summarise_persisted_scenario",
    "_ensure_project_owner",
    "_load_cost_indices",
]
