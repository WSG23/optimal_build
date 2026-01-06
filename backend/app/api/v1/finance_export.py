"""Finance export, construction loan, and sensitivity API endpoints.

This module handles:
- PATCH /scenarios/{scenario_id}/construction-loan - Update construction loan config
- POST /scenarios/{scenario_id}/sensitivity - Rerun sensitivity analysis
- GET /export - Export scenario as ZIP bundle
"""

from __future__ import annotations

import csv
import io
import json
import zipfile
from collections.abc import Iterator, Mapping, Sequence
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from time import perf_counter
from typing import Any

import backend.jobs.finance_sensitivity  # noqa: F401
from backend.jobs import JobDispatch, job_queue
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import RequestIdentity, require_reviewer
from app.core.config import settings
from app.core.database import get_session
from app.models.finance import FinResult, FinScenario
from app.schemas.finance import (
    CapitalStackSummarySchema,
    ConstructionLoanInput,
    ConstructionLoanInterestSchema,
    FinanceFeasibilityResponse,
    FinanceSensitivityOutcomeSchema,
    SensitivityBandInput,
)
from app.services.finance import calculator
from app.services.finance.argus_export import get_argus_export_service
from app.utils import metrics
from app.utils.logging import get_logger, log_event

from .finance_common import (
    ConstructionLoanUpdatePayload,
    FinanceSensitivityRunPayload,
    band_payloads_equal,
    clear_sensitivity_jobs,
    convert_drawdown_schedule,
    decimal_from_value,
    format_percentage_label,
    has_pending_sensitivity_job,
    json_safe,
    project_uuid_from_scenario,
    quantize_currency,
    rebuild_drawdown_summary,
    record_async_job,
    store_sensitivity_metadata,
)
from .finance_scenarios import (
    _ensure_project_owner,
    summarise_persisted_scenario,
)

router = APIRouter(prefix="/finance", tags=["finance"])
logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Construction Interest Schedule Builder
# ---------------------------------------------------------------------------


def build_construction_interest_schedule(
    schedule: calculator.FinancingDrawdownSchedule,
    *,
    currency: str,
    base_interest_rate: Decimal | None,
    base_periods_per_year: int | None,
    capitalise_interest: bool,
    facilities: Sequence[Mapping[str, Any]] | None = None,
) -> tuple[ConstructionLoanInterestSchema, dict[str, Any]]:
    """Build the construction loan interest schedule from a drawdown schedule."""

    rate = base_interest_rate or Decimal("0.04")
    periods = max(1, base_periods_per_year or 12)
    period_rate = rate / Decimal(periods)

    opening_balance = Decimal("0")
    entry_payloads: list[dict[str, str]] = []
    total_interest = Decimal("0")
    for entry in schedule.entries:
        closing_balance = decimal_from_value(entry.outstanding_debt)
        average_balance = (opening_balance + closing_balance) / Decimal("2")
        interest_accrued = quantize_currency(average_balance * period_rate) or Decimal(
            "0"
        )
        total_interest += interest_accrued
        entry_payloads.append(
            {
                "period": str(entry.period),
                "opening_balance": str(
                    quantize_currency(opening_balance) or opening_balance
                ),
                "closing_balance": str(
                    quantize_currency(closing_balance) or closing_balance
                ),
                "average_balance": str(
                    quantize_currency(average_balance) or average_balance
                ),
                "interest_accrued": str(interest_accrued),
            }
        )
        opening_balance = closing_balance

    facility_payloads: list[dict[str, str | bool | None]] = []
    upfront_total = Decimal("0")
    exit_total = Decimal("0")
    facility_interest_total = Decimal("0")
    for facility in facilities or []:
        amount = decimal_from_value(facility.get("amount", "0"))
        if amount is None:
            amount = Decimal("0")
        raw_rate = facility.get("interest_rate")
        facility_rate = decimal_from_value(raw_rate) if raw_rate is not None else rate
        facility_interest = quantize_currency(amount * facility_rate) or Decimal("0")
        facility_interest_total += facility_interest
        upfront_pct_raw = facility.get("upfront_fee_pct")
        upfront_pct = (
            decimal_from_value(upfront_pct_raw) if upfront_pct_raw is not None else None
        )
        upfront_fee = None
        if upfront_pct is not None:
            upfront_fee = quantize_currency(amount * (upfront_pct / Decimal("100")))
            if upfront_fee is not None:
                upfront_total += upfront_fee
        exit_pct_raw = facility.get("exit_fee_pct")
        exit_pct = (
            decimal_from_value(exit_pct_raw) if exit_pct_raw is not None else None
        )
        exit_fee = None
        if exit_pct is not None:
            exit_fee = quantize_currency(amount * (exit_pct / Decimal("100")))
            if exit_fee is not None:
                exit_total += exit_fee
        facility_payloads.append(
            {
                "name": facility.get("name", "Facility"),
                "amount": str(quantize_currency(amount) or amount),
                "interest_rate": str(facility_rate),
                "periods_per_year": facility.get("periods_per_year"),
                "capitalised": bool(facility.get("capitalise_interest", True)),
                "total_interest": str(facility_interest),
                "upfront_fee": str(upfront_fee) if upfront_fee is not None else None,
                "exit_fee": str(exit_fee) if exit_fee is not None else None,
                "reserve_months": facility.get("reserve_months"),
                "amortisation_months": facility.get("amortisation_months"),
            }
        )

    total_interest = facility_interest_total or total_interest

    schema_payload = {
        "currency": currency,
        "interest_rate": str(rate),
        "periods_per_year": periods,
        "capitalised": capitalise_interest,
        "total_interest": str(quantize_currency(total_interest) or total_interest),
        "upfront_fee_total": str(quantize_currency(upfront_total) or upfront_total),
        "exit_fee_total": str(quantize_currency(exit_total) or exit_total),
        "facilities": facility_payloads,
        "entries": entry_payloads,
    }
    schema = ConstructionLoanInterestSchema.model_validate(schema_payload)
    return schema, schema_payload


# ---------------------------------------------------------------------------
# Sensitivity Analysis Helpers
# ---------------------------------------------------------------------------


def _base_finance_metrics(
    scenario: FinScenario,
) -> tuple[Decimal, Decimal | None, Decimal, Decimal | None]:
    """Extract baseline finance metrics required for sensitivity runs."""

    escalated_cost: Decimal | None = None
    base_npv: Decimal | None = None
    base_irr: Decimal | None = None
    interest_total: Decimal | None = None

    for result in scenario.results:
        if result.name == "escalated_cost" and result.value is not None:
            escalated_cost = decimal_from_value(result.value)
        elif result.name == "npv" and result.value is not None:
            base_npv = decimal_from_value(result.value)
        elif result.name == "irr" and result.value is not None:
            base_irr = decimal_from_value(result.value)
        elif result.name == "construction_loan_interest" and result.value is not None:
            interest_total = decimal_from_value(result.value)

    if escalated_cost is None or base_npv is None:
        raise HTTPException(
            status_code=409,
            detail="Scenario is missing baseline finance results for sensitivity analysis.",
        )
    return base_npv, base_irr, escalated_cost, interest_total


def _build_sensitivity_job_context(
    scenario: FinScenario,
    *,
    assumptions: Mapping[str, Any],
    escalated_cost: Decimal,
    drawdown_summary: calculator.FinancingDrawdownSchedule | None,
    loan_config: ConstructionLoanInput | None,
) -> dict[str, Any]:
    """Construct the job context payload for async sensitivity runs."""

    cash_config = assumptions.get("cash_flow") or {}
    cash_flows = cash_config.get("cash_flows") or []
    discount_rate = cash_config.get("discount_rate", "0")
    currency = (
        getattr(scenario.fin_project, "currency", None)
        or assumptions.get("currency")
        or "SGD"
    )
    drawdown_schema = (
        convert_drawdown_schedule(drawdown_summary)
        if drawdown_summary is not None
        else None
    )

    return {
        "cash_flows": [str(value) for value in cash_flows],
        "discount_rate": str(discount_rate),
        "escalated_cost": str(escalated_cost),
        "currency": currency,
        "interest_periods": (
            loan_config.periods_per_year
            if loan_config and loan_config.periods_per_year
            else 12
        ),
        "capitalise_interest": (
            loan_config.capitalise_interest if loan_config else True
        ),
        "base_interest_rate": (
            str(loan_config.interest_rate)
            if loan_config and loan_config.interest_rate is not None
            else None
        ),
        "schedule": (
            drawdown_schema.model_dump(mode="json") if drawdown_schema else None
        ),
        "facilities": (
            [
                facility.model_dump(mode="json")
                for facility in (loan_config.facilities or [])
            ]
            if loan_config and loan_config.facilities
            else []
        ),
    }


def evaluate_sensitivity_bands(
    bands: Sequence[SensitivityBandInput],
    *,
    base_npv: Decimal,
    base_irr: Decimal | None,
    escalated_cost: Decimal,
    base_interest_total: Decimal | None,
    currency: str,
) -> tuple[list[FinanceSensitivityOutcomeSchema], list[dict[str, Any]]]:
    """Derive sensitivity scenarios for the supplied parameter bands."""

    results: list[FinanceSensitivityOutcomeSchema] = []
    metadata_entries: list[dict[str, Any]] = []
    for band in bands:
        for label, delta in (
            ("Low", band.low),
            ("Base", band.base),
            ("High", band.high),
        ):
            if delta is None:
                continue
            delta_decimal = decimal_from_value(delta)
            npv_factor = Decimal("1") + (delta_decimal / Decimal("100"))
            cost_factor = Decimal("1") + (delta_decimal / Decimal("200"))
            irr_value: Decimal | None = None
            if base_irr is not None:
                irr_value = (base_irr + (delta_decimal / Decimal("1000"))).quantize(
                    Decimal("0.0001"), rounding=ROUND_HALF_UP
                )
            npv_value = quantize_currency(base_npv * npv_factor)
            escalated_value = quantize_currency(escalated_cost * cost_factor)
            interest_value = (
                quantize_currency(base_interest_total * cost_factor)
                if base_interest_total is not None
                else None
            )
            notes = list(band.notes or [])
            notes.append(
                f"{label} case applies {delta_decimal:+g}% adjustment to "
                f"{band.parameter}"
            )
            entry = FinanceSensitivityOutcomeSchema(
                parameter=band.parameter,
                scenario=label,
                delta_label=format_percentage_label(delta_decimal),
                npv=npv_value,
                irr=irr_value,
                escalated_cost=escalated_value,
                total_interest=interest_value,
                notes=notes,
            )
            results.append(entry)
            metadata_entries.append(entry.model_dump(mode="json"))
    return results, metadata_entries


# ---------------------------------------------------------------------------
# CSV Export Helpers
# ---------------------------------------------------------------------------


def _flush_buffer(stream: io.StringIO) -> bytes | None:
    """Read and reset the buffer returning encoded CSV content."""

    data = stream.getvalue()
    stream.seek(0)
    stream.truncate(0)
    if not data:
        return None
    return data.encode("utf-8")


def _capital_stack_to_csv(summary: CapitalStackSummarySchema) -> str:
    """Serialise capital stack slices into CSV rows."""

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "Name",
            "Source",
            "Category",
            "Amount",
            "Share",
            "Rate",
            "Tranche Order",
            "Metadata",
        ]
    )
    for component in summary.slices:
        metadata_payload = ""
        if component.metadata:
            try:
                metadata_payload = json.dumps(component.metadata, sort_keys=True)
            except TypeError:
                metadata_payload = str(component.metadata)
        writer.writerow(
            [
                component.name,
                component.source_type,
                component.category,
                component.amount,
                component.share,
                component.rate or "",
                component.tranche_order or "",
                metadata_payload,
            ]
        )
    return buffer.getvalue()


def _iter_results_csv(scenario: FinScenario, *, currency: str) -> Iterator[bytes]:
    """Yield CSV rows describing a scenario and its persisted results."""

    def _stringify(value: object) -> str:
        return "" if value is None else str(value)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Metric", "Value", "Unit"])
    chunk = _flush_buffer(buffer)
    if chunk:
        yield chunk

    ordered_results = sorted(
        scenario.results, key=lambda item: getattr(item, "id", 0) or 0
    )
    for result in ordered_results:
        value_repr = _stringify(result.value)
        unit_repr = result.unit or ""
        writer.writerow([result.name, value_repr, unit_repr])
        chunk = _flush_buffer(buffer)
        if chunk:
            yield chunk

        metadata: dict[str, Any] | None = (
            result.metadata if isinstance(result.metadata, dict) else None
        )
        if result.name == "dscr_timeline" and metadata:
            timeline = metadata.get("entries")
            if timeline:
                writer.writerow([])
                chunk = _flush_buffer(buffer)
                if chunk:
                    yield chunk
                writer.writerow(["Period", "NOI", "Debt Service", "DSCR", "Currency"])
                chunk = _flush_buffer(buffer)
                if chunk:
                    yield chunk
                for entry in timeline:
                    writer.writerow(
                        [
                            entry.get("period", ""),
                            entry.get("noi", ""),
                            entry.get("debt_service", ""),
                            entry.get("dscr", ""),
                            entry.get("currency", currency),
                        ]
                    )
                    chunk = _flush_buffer(buffer)
                    if chunk:
                        yield chunk

        if result.name == "capital_stack" and metadata:
            section_currency = metadata.get("currency") or unit_repr or currency
            writer.writerow([])
            chunk = _flush_buffer(buffer)
            if chunk:
                yield chunk
            writer.writerow(["Capital Stack Summary"])
            chunk = _flush_buffer(buffer)
            if chunk:
                yield chunk

            totals = metadata.get("totals")
            if isinstance(totals, dict):
                total_rows = (
                    ("Total Financing", totals.get("total"), section_currency),
                    ("Equity Financing", totals.get("equity"), section_currency),
                    ("Debt Financing", totals.get("debt"), section_currency),
                    ("Other Financing", totals.get("other"), section_currency),
                )
                for label, raw_value, unit in total_rows:
                    if raw_value is None:
                        continue
                    writer.writerow([label, _stringify(raw_value), unit])
                    chunk = _flush_buffer(buffer)
                    if chunk:
                        yield chunk

            ratios = metadata.get("ratios")
            if isinstance(ratios, dict):
                ratio_rows = (
                    ("Equity Ratio", ratios.get("equity")),
                    ("Debt Ratio", ratios.get("debt")),
                    ("Other Ratio", ratios.get("other")),
                    ("Loan To Cost", ratios.get("loan_to_cost")),
                    (
                        "Weighted Average Debt Rate",
                        ratios.get("weighted_average_debt_rate"),
                    ),
                )
                for label, raw_value in ratio_rows:
                    if raw_value is None:
                        continue
                    writer.writerow([label, _stringify(raw_value), "ratio"])
                    chunk = _flush_buffer(buffer)
                    if chunk:
                        yield chunk

            slices = metadata.get("slices")
            if isinstance(slices, list) and slices:
                writer.writerow([])
                chunk = _flush_buffer(buffer)
                if chunk:
                    yield chunk
                writer.writerow(["Capital Stack Slices"])
                chunk = _flush_buffer(buffer)
                if chunk:
                    yield chunk
                writer.writerow(
                    [
                        "Name",
                        "Source Type",
                        "Category",
                        "Amount",
                        "Share",
                        "Rate",
                        "Tranche Order",
                    ]
                )
                chunk = _flush_buffer(buffer)
                if chunk:
                    yield chunk
                for component in slices:
                    writer.writerow(
                        [
                            component.get("name", ""),
                            component.get("source_type", ""),
                            component.get("category", ""),
                            _stringify(component.get("amount")),
                            _stringify(component.get("share")),
                            _stringify(component.get("rate")),
                            _stringify(component.get("tranche_order")),
                        ]
                    )
                    chunk = _flush_buffer(buffer)
                    if chunk:
                        yield chunk

        if result.name == "drawdown_schedule" and metadata:
            schedule_currency = metadata.get("currency") or unit_repr or currency
            writer.writerow([])
            chunk = _flush_buffer(buffer)
            if chunk:
                yield chunk
            writer.writerow(["Drawdown Schedule Summary"])
            chunk = _flush_buffer(buffer)
            if chunk:
                yield chunk

            totals = metadata.get("totals")
            if isinstance(totals, dict):
                total_rows = (
                    ("Total Equity Draw", totals.get("equity"), schedule_currency),
                    ("Total Debt Draw", totals.get("debt"), schedule_currency),
                    (
                        "Peak Debt Balance",
                        totals.get("peak_debt_balance"),
                        schedule_currency,
                    ),
                    (
                        "Final Debt Balance",
                        totals.get("final_debt_balance"),
                        schedule_currency,
                    ),
                )
                for label, raw_value, unit in total_rows:
                    if raw_value is None:
                        continue
                    writer.writerow([label, _stringify(raw_value), unit])
                    chunk = _flush_buffer(buffer)
                    if chunk:
                        yield chunk

            entries = metadata.get("entries")
            if isinstance(entries, list) and entries:
                writer.writerow([])
                chunk = _flush_buffer(buffer)
                if chunk:
                    yield chunk
                writer.writerow(
                    [
                        "Period",
                        "Equity Draw",
                        "Debt Draw",
                        "Total Draw",
                        "Cumulative Equity",
                        "Cumulative Debt",
                        "Outstanding Debt",
                        "Currency",
                    ]
                )
                chunk = _flush_buffer(buffer)
                if chunk:
                    yield chunk
                for entry in entries:
                    writer.writerow(
                        [
                            entry.get("period", ""),
                            _stringify(entry.get("equity_draw")),
                            _stringify(entry.get("debt_draw")),
                            _stringify(entry.get("total_draw")),
                            _stringify(entry.get("cumulative_equity")),
                            _stringify(entry.get("cumulative_debt")),
                            _stringify(entry.get("outstanding_debt")),
                            schedule_currency,
                        ]
                    )
                    chunk = _flush_buffer(buffer)
                    if chunk:
                        yield chunk

        if result.name == "asset_financials" and metadata:
            writer.writerow([])
            chunk = _flush_buffer(buffer)
            if chunk:
                yield chunk
            writer.writerow(["Asset Financial Summary"])
            chunk = _flush_buffer(buffer)
            if chunk:
                yield chunk
            summary_meta = metadata.get("summary")
            if isinstance(summary_meta, dict):
                summary_rows = (
                    (
                        "Total Estimated Revenue",
                        summary_meta.get("total_estimated_revenue_sgd"),
                        currency,
                    ),
                    (
                        "Total Estimated Capex",
                        summary_meta.get("total_estimated_capex_sgd"),
                        currency,
                    ),
                    (
                        "Dominant Risk Profile",
                        summary_meta.get("dominant_risk_profile"),
                        "",
                    ),
                )
                for label, value, unit in summary_rows:
                    if value is None:
                        continue
                    writer.writerow([label, _stringify(value), unit])
                    chunk = _flush_buffer(buffer)
                    if chunk:
                        yield chunk
                notes = summary_meta.get("notes")
                if isinstance(notes, list) and notes:
                    writer.writerow(["Notes"])
                    chunk = _flush_buffer(buffer)
                    if chunk:
                        yield chunk
                    for note in notes:
                        writer.writerow([_stringify(note)])
                        chunk = _flush_buffer(buffer)
                        if chunk:
                            yield chunk

            breakdowns_meta = metadata.get("breakdowns")
            if isinstance(breakdowns_meta, list) and breakdowns_meta:
                writer.writerow([])
                chunk = _flush_buffer(buffer)
                if chunk:
                    yield chunk
                writer.writerow(
                    [
                        "Asset Type",
                        "Allocation %",
                        "NOI (Annual)",
                        "Capex",
                        "Payback (years)",
                        "Absorption (months)",
                        "Risk Level",
                    ]
                )
                chunk = _flush_buffer(buffer)
                if chunk:
                    yield chunk
                for entry in breakdowns_meta:
                    if not isinstance(entry, dict):
                        continue
                    writer.writerow(
                        [
                            entry.get("asset_type", ""),
                            _stringify(entry.get("allocation_pct")),
                            _stringify(entry.get("noi_annual_sgd")),
                            _stringify(entry.get("estimated_capex_sgd")),
                            _stringify(entry.get("payback_years")),
                            _stringify(entry.get("absorption_months")),
                            entry.get("risk_level", ""),
                        ]
                    )
                    chunk = _flush_buffer(buffer)
                    if chunk:
                        yield chunk

        if result.name == "construction_loan_interest" and metadata:
            writer.writerow([])
            chunk = _flush_buffer(buffer)
            if chunk:
                yield chunk
            writer.writerow(["Construction Loan Summary"])
            chunk = _flush_buffer(buffer)
            if chunk:
                yield chunk
            summary_rows = (
                ("Base Interest Rate", metadata.get("interest_rate"), "ratio"),
                ("Total Interest", metadata.get("total_interest"), currency),
                ("Upfront Fees", metadata.get("upfront_fee_total"), currency),
                ("Exit Fees", metadata.get("exit_fee_total"), currency),
            )
            for label, value, unit in summary_rows:
                if value in (None, ""):
                    continue
                writer.writerow([label, value, unit])
                chunk = _flush_buffer(buffer)
                if chunk:
                    yield chunk

            facilities = metadata.get("facilities")
            if isinstance(facilities, list) and facilities:
                writer.writerow([])
                chunk = _flush_buffer(buffer)
                if chunk:
                    yield chunk
                writer.writerow(["Construction Loan Facilities"])
                chunk = _flush_buffer(buffer)
                if chunk:
                    yield chunk
                writer.writerow(
                    [
                        "Name",
                        "Amount",
                        "Interest Rate",
                        "Capitalised",
                        "Upfront Fee",
                        "Exit Fee",
                    ]
                )
                chunk = _flush_buffer(buffer)
                if chunk:
                    yield chunk
                for facility in facilities:
                    if not isinstance(facility, dict):
                        continue
                    writer.writerow(
                        [
                            facility.get("name", ""),
                            facility.get("amount", ""),
                            facility.get("interest_rate", ""),
                            "Y" if facility.get("capitalised") else "N",
                            facility.get("upfront_fee", ""),
                            facility.get("exit_fee", ""),
                        ]
                    )
                    chunk = _flush_buffer(buffer)
                    if chunk:
                        yield chunk

        if result.name == "sensitivity_analysis" and metadata:
            bands = metadata.get("bands")
            if isinstance(bands, list) and bands:
                writer.writerow([])
                chunk = _flush_buffer(buffer)
                if chunk:
                    yield chunk
                writer.writerow(["Sensitivity Analysis Outcomes"])
                chunk = _flush_buffer(buffer)
                if chunk:
                    yield chunk
                writer.writerow(
                    [
                        "Parameter",
                        "Scenario",
                        "Delta",
                        "NPV",
                        "IRR",
                        "Escalated Cost",
                        "Total Interest",
                        "Notes",
                    ]
                )
                chunk = _flush_buffer(buffer)
                if chunk:
                    yield chunk
                for entry in bands:
                    if not isinstance(entry, dict):
                        continue
                    if entry.get("parameter") == "__async__":
                        continue
                    notes_value = entry.get("notes")
                    if isinstance(notes_value, list):
                        notes_text = "; ".join(
                            str(item) for item in notes_value if item not in (None, "")
                        )
                    else:
                        notes_text = (
                            "" if notes_value in (None, "", []) else str(notes_value)
                        )
                    writer.writerow(
                        [
                            entry.get("parameter", ""),
                            entry.get("scenario", ""),
                            entry.get("delta_label") or entry.get("deltaLabel") or "",
                            entry.get("npv", ""),
                            entry.get("irr", ""),
                            entry.get("escalated_cost", ""),
                            entry.get("total_interest", ""),
                            notes_text,
                        ]
                    )
                    chunk = _flush_buffer(buffer)
                    if chunk:
                        yield chunk

    escalated = next(
        (item for item in ordered_results if item.name == "escalated_cost"), None
    )
    cost_meta = None
    if escalated is not None and isinstance(escalated.metadata, dict):
        cost_meta = escalated.metadata.get("cost_index")

    if cost_meta:
        writer.writerow([])
        chunk = _flush_buffer(buffer)
        if chunk:
            yield chunk
        writer.writerow(["Cost Index Provenance"])
        chunk = _flush_buffer(buffer)
        if chunk:
            yield chunk
        for key, value in cost_meta.items():
            if isinstance(value, dict):
                writer.writerow([key])
                chunk = _flush_buffer(buffer)
                if chunk:
                    yield chunk
                for sub_key, sub_value in value.items():
                    writer.writerow([f"  {sub_key}", sub_value])
                    chunk = _flush_buffer(buffer)
                    if chunk:
                        yield chunk
            else:
                writer.writerow([key, value])
                chunk = _flush_buffer(buffer)
                if chunk:
                    yield chunk

    chunk = _flush_buffer(buffer)
    if chunk:
        yield chunk


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.patch(
    "/scenarios/{scenario_id}/construction-loan",
    response_model=FinanceFeasibilityResponse,
)
async def update_construction_loan(
    scenario_id: int,
    payload: ConstructionLoanUpdatePayload,
    session: AsyncSession = Depends(get_session),
    identity: RequestIdentity = Depends(require_reviewer),
) -> FinanceFeasibilityResponse:
    """Update a persisted scenario's construction loan configuration."""

    stmt = (
        select(FinScenario)
        .where(FinScenario.id == scenario_id)
        .options(
            selectinload(FinScenario.fin_project),
            selectinload(FinScenario.capital_stack),
            selectinload(FinScenario.results),
            selectinload(FinScenario.asset_breakdowns),
        )
    )
    scenario = (await session.execute(stmt)).scalars().first()
    if scenario is None:
        raise HTTPException(status_code=404, detail="Finance scenario not found")
    await _ensure_project_owner(session, project_uuid_from_scenario(scenario), identity)

    if payload.construction_loan is None:
        raise HTTPException(status_code=400, detail="construction_loan is required")

    assumptions = dict(scenario.assumptions or {})
    assumptions["construction_loan"] = payload.construction_loan.model_dump(mode="json")
    scenario.assumptions = assumptions

    drawdown_data = assumptions.get("drawdown_schedule")
    schedule_summary = None
    if isinstance(drawdown_data, list) and drawdown_data:
        schedule_inputs = []
        for entry in drawdown_data:
            if not isinstance(entry, Mapping):
                continue
            schedule_inputs.append(
                {
                    "period": entry.get("period", ""),
                    "equity_draw": decimal_from_value(entry.get("equity_draw", "0")),
                    "debt_draw": decimal_from_value(entry.get("debt_draw", "0")),
                }
            )
        if schedule_inputs:
            schedule_summary = calculator.drawdown_schedule(
                schedule_inputs,
                currency=assumptions.get("currency")
                or getattr(scenario.fin_project, "currency", "SGD"),
            )

    construction_interest_schema = None
    construction_interest_metadata = None
    if schedule_summary is not None:
        facility_payloads = (
            [
                facility.model_dump(mode="json")
                for facility in payload.construction_loan.facilities
            ]
            if payload.construction_loan.facilities
            else None
        )
        (
            construction_interest_schema,
            construction_interest_metadata,
        ) = build_construction_interest_schedule(
            schedule_summary,
            currency=schedule_summary.currency,
            base_interest_rate=payload.construction_loan.interest_rate,
            base_periods_per_year=payload.construction_loan.periods_per_year,
            capitalise_interest=payload.construction_loan.capitalise_interest,
            facilities=facility_payloads,
        )

    if construction_interest_schema and construction_interest_metadata:
        interest_value = decimal_from_value(
            construction_interest_schema.total_interest
            if construction_interest_schema.total_interest is not None
            else "0"
        )
        existing_result = None
        for stored in scenario.results:
            if stored.name == "construction_loan_interest":
                existing_result = stored
                break
        if existing_result is None:
            existing_result = FinResult(
                project_id=str(project_uuid_from_scenario(scenario)),
                scenario=scenario,
                name="construction_loan_interest",
                value=interest_value,
                unit=schedule_summary.currency,
                metadata=json_safe(construction_interest_metadata),
            )
            session.add(existing_result)
        else:
            existing_result.value = interest_value
            existing_result.unit = schedule_summary.currency
            existing_result.metadata = json_safe(construction_interest_metadata)

    await session.commit()
    scenario = (await session.execute(stmt)).scalars().first()
    if scenario is None:
        raise HTTPException(status_code=404, detail="Finance scenario not found")
    return await summarise_persisted_scenario(scenario, session=session)


@router.post(
    "/scenarios/{scenario_id}/sensitivity",
    response_model=FinanceFeasibilityResponse,
)
async def rerun_finance_sensitivity(
    scenario_id: int,
    payload: FinanceSensitivityRunPayload,
    session: AsyncSession = Depends(get_session),
    identity: RequestIdentity = Depends(require_reviewer),
) -> FinanceFeasibilityResponse:
    """Recompute or enqueue sensitivity analysis for an existing scenario."""

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

    try:
        base_npv, base_irr, escalated_cost, base_interest_total = _base_finance_metrics(
            scenario
        )
    except HTTPException:
        raise

    currency = (
        getattr(scenario.fin_project, "currency", None)
        or (scenario.assumptions or {}).get("currency")
        or "SGD"
    )

    assumptions = dict(scenario.assumptions or {})
    existing_band_payloads = (
        assumptions.get("sensitivity_bands")
        if isinstance(assumptions.get("sensitivity_bands"), list)
        else None
    )
    new_band_payloads = [
        band.model_dump(mode="json") for band in payload.sensitivity_bands
    ]
    if band_payloads_equal(
        existing_band_payloads, new_band_payloads
    ) and not has_pending_sensitivity_job(scenario):
        await session.commit()
        scenario = (await session.execute(base_stmt)).scalars().first()
        assert scenario is not None
        return await summarise_persisted_scenario(scenario, session=session)
    assumptions["sensitivity_bands"] = new_band_payloads
    scenario.assumptions = assumptions

    drawdown_summary = rebuild_drawdown_summary(assumptions, currency=currency)
    raw_loan = assumptions.get("construction_loan")
    loan_config: ConstructionLoanInput | None = None
    if isinstance(raw_loan, Mapping):
        try:
            loan_config = ConstructionLoanInput.model_validate(raw_loan)
        except Exception:  # pragma: no cover - tolerate legacy payloads
            loan_config = None

    sync_threshold = max(1, settings.FINANCE_SENSITIVITY_MAX_SYNC_BANDS)
    if len(payload.sensitivity_bands) <= sync_threshold:
        (
            sensitivity_results,
            sensitivity_metadata,
        ) = evaluate_sensitivity_bands(
            payload.sensitivity_bands,
            base_npv=base_npv,
            base_irr=base_irr,
            escalated_cost=escalated_cost,
            base_interest_total=base_interest_total,
            currency=currency,
        )
        store_sensitivity_metadata(session, scenario, sensitivity_metadata or [])
        clear_sensitivity_jobs(scenario)
        await session.commit()
    else:
        if has_pending_sensitivity_job(scenario):
            await session.commit()
            scenario = (await session.execute(base_stmt)).scalars().first()
            assert scenario is not None
            return await summarise_persisted_scenario(scenario, session=session)
        job_context = _build_sensitivity_job_context(
            scenario,
            assumptions=assumptions,
            escalated_cost=escalated_cost,
            drawdown_summary=drawdown_summary,
            loan_config=loan_config,
        )
        dispatch: JobDispatch = await job_queue.enqueue(
            "finance.sensitivity",
            scenario.id,
            bands=[band.model_dump(mode="json") for band in payload.sensitivity_bands],
            context=job_context,
            queue="finance",
        )
        queued_at = datetime.now(timezone.utc)
        from app.schemas.finance import FinanceJobStatusSchema

        job_status = FinanceJobStatusSchema(
            scenario_id=scenario.id,
            task_id=dispatch.task_id,
            status=dispatch.status,
            backend=dispatch.backend,
            queued_at=queued_at,
        )
        record_async_job(scenario, job_status)
        store_sensitivity_metadata(
            session,
            scenario,
            [
                {
                    "parameter": "__async__",
                    "status": dispatch.status,
                    "task_id": dispatch.task_id,
                    "queue": dispatch.queue,
                }
            ],
        )
        await session.commit()

    scenario = (await session.execute(base_stmt)).scalars().first()
    if scenario is None:
        raise HTTPException(status_code=404, detail="Finance scenario not found")
    return await summarise_persisted_scenario(scenario, session=session)


@router.get("/export")
async def export_finance_scenario(
    scenario_id: int = Query(...),
    session: AsyncSession = Depends(get_session),
    identity: RequestIdentity = Depends(require_reviewer),
) -> StreamingResponse:
    """Stream a ZIP bundle with CSV/JSON finance scenario artefacts."""

    metrics.REQUEST_COUNTER.labels(endpoint="finance_export").inc()
    metrics.FINANCE_EXPORT_TOTAL.inc()
    start_time = perf_counter()
    response: StreamingResponse | None = None
    try:
        if scenario_id < 1:
            raise HTTPException(status_code=400, detail="scenario_id must be positive")
        stmt = (
            select(FinScenario)
            .where(FinScenario.id == scenario_id)
            .options(
                selectinload(FinScenario.results),
                selectinload(FinScenario.fin_project),
                selectinload(FinScenario.capital_stack),
                selectinload(FinScenario.asset_breakdowns),
            )
            .limit(1)
        )
        result = await session.execute(stmt)
        scenario = result.scalar_one_or_none()
        if scenario is None:
            raise HTTPException(status_code=404, detail="Finance scenario not found")
        await _ensure_project_owner(
            session, project_uuid_from_scenario(scenario), identity
        )

        assumptions = scenario.assumptions or {}
        currency = assumptions.get("currency") or getattr(
            scenario.fin_project, "currency", "USD"
        )

        summary = await summarise_persisted_scenario(scenario, session=session)
        summary_payload = summary.model_dump(mode="json")

        csv_buffer = io.BytesIO()
        for chunk in _iter_results_csv(scenario, currency=str(currency)):
            csv_buffer.write(chunk)
        csv_bytes = csv_buffer.getvalue()

        archive_buffer = io.BytesIO()
        with zipfile.ZipFile(archive_buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("scenario.csv", csv_bytes)
            archive.writestr(
                "scenario.json",
                json.dumps(summary_payload, indent=2, sort_keys=True),
            )
            if summary.capital_stack is not None:
                archive.writestr(
                    "capital_stack.csv", _capital_stack_to_csv(summary.capital_stack)
                )
                capital_stack_payload = summary_payload.get("capital_stack")
                if capital_stack_payload:
                    archive.writestr(
                        "capital_stack.json",
                        json.dumps(capital_stack_payload, indent=2, sort_keys=True),
                    )
            if summary.sensitivity_results:
                archive.writestr(
                    "sensitivity.json",
                    json.dumps(summary.sensitivity_results, indent=2, default=str),
                )

        archive_buffer.seek(0)
        archive_bytes = archive_buffer.getvalue()
        filename = f"finance_scenario_{scenario.id}.zip"
        response = StreamingResponse(
            iter([archive_bytes]),
            media_type="application/zip",
        )
        response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'

        log_event(logger, "finance_feasibility_export", scenario_id=scenario.id)
    finally:
        duration_ms = (perf_counter() - start_time) * 1000
        metrics.FINANCE_EXPORT_DURATION_MS.observe(duration_ms)

    assert response is not None
    return response


@router.get("/export/argus")
async def export_argus_scenario(
    scenario_id: int = Query(...),
    session: AsyncSession = Depends(get_session),
    identity: RequestIdentity = Depends(require_reviewer),
) -> StreamingResponse:
    """Stream a ZIP bundle with ARGUS Enterprise compatible CSVs."""

    if scenario_id < 1:
        raise HTTPException(status_code=400, detail="scenario_id must be positive")

    stmt = (
        select(FinScenario)
        .where(FinScenario.id == scenario_id)
        .options(
            selectinload(FinScenario.results),
            selectinload(FinScenario.fin_project),
        )
        .limit(1)
    )
    result = await session.execute(stmt)
    scenario = result.scalar_one_or_none()

    if scenario is None:
        raise HTTPException(status_code=404, detail="Finance scenario not found")

    await _ensure_project_owner(session, project_uuid_from_scenario(scenario), identity)

    # In a real impl, we would fetch/calculate property info relative to the scenario
    # For now, we stub or partially populate from scenario
    property_data = {
        "id": f"PROP-{scenario.id}",
        "name": scenario.name,
        "gfa_sqft": 0,  # Should fetch from project
        "year_built": datetime.utcnow().year,
    }

    service = get_argus_export_service()
    bundle = service.build_bundle_from_scenario(scenario.assumptions, property_data)
    zip_bytes = service.generate_export_zip(bundle)

    filename = f"ARGUS_Export_{scenario.id}.zip"
    response = StreamingResponse(
        iter([zip_bytes]),
        media_type="application/zip",
    )
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


__all__ = ["router"]
