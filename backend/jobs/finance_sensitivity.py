"""Background job for processing deferred finance sensitivity bands."""

from __future__ import annotations

import inspect
from contextlib import asynccontextmanager
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, AsyncIterator, Mapping, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.jobs import job
from app.core.database import get_session
from app.models.finance import FinResult, FinScenario
from app.services.finance import calculator


def _resolve_session_dependency():
    try:
        from app.main import app as fastapi_app  # type: ignore
    except Exception:  # pragma: no cover - fallback when app isn't available
        fastapi_app = None

    if fastapi_app is not None:
        override = fastapi_app.dependency_overrides.get(get_session)
        if override is not None:
            return override
    return get_session


@asynccontextmanager
async def _job_session() -> AsyncIterator[AsyncSession]:
    dependency = _resolve_session_dependency()
    resource = dependency()

    if inspect.isasyncgen(resource):
        generator = resource
        try:
            session = await anext(generator)  # type: ignore[arg-type]
        except StopAsyncIteration as exc:  # pragma: no cover - defensive guard
            raise RuntimeError("Session dependency did not yield a session") from exc
        try:
            yield session
        finally:
            await generator.aclose()
        return

    if inspect.isawaitable(resource):
        session = await resource
        try:
            yield session
        finally:
            close = getattr(session, "close", None)
            if callable(close):
                await close()
        return

    if isinstance(resource, AsyncSession):
        try:
            yield resource
        finally:
            await resource.close()
        return

    raise TypeError(
        "Session dependency must return an AsyncSession, coroutine, or async generator"
    )


def _json_safe(value: Any) -> Any:
    import json

    return json.loads(json.dumps(value, default=str))


def _coerce_decimal(value: object | None) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


@job(name="finance.sensitivity", queue="finance")
async def process_finance_sensitivity_job(
    scenario_id: int,
    *,
    bands: Sequence[Mapping[str, Any]],
    context: Mapping[str, Any],
    session: AsyncSession | None = None,
) -> dict[str, Any]:
    from app.api.v1.finance import (
        _build_construction_interest_schedule,
        _evaluate_sensitivity_bands,
        _decimal_from_value,
    )
    from app.schemas.finance import (
        FinanceSensitivityOutcomeSchema,
        SensitivityBandInput,
    )

    # Use provided session (tests) or create new session (production)
    if session is not None:
        # Test mode: use provided session, don't commit (test controls transaction)
        use_external_session = True
        session_ctx = None
    else:
        # Production mode: create own session and commit
        use_external_session = False
        session_ctx = _job_session()

    async def _run_job(sess: AsyncSession) -> dict[str, Any]:
        stmt = (
            select(FinScenario)
            .where(FinScenario.id == scenario_id)
            .options(
                selectinload(FinScenario.results),
                selectinload(FinScenario.fin_project),
            )
        )
        scenario = (await sess.execute(stmt)).scalars().first()
        if scenario is None:
            return {"status": "missing", "scenario_id": scenario_id}

        try:
            band_inputs = [SensitivityBandInput.model_validate(band) for band in bands]
        except Exception as exc:  # pragma: no cover - defensive guard
            return {
                "status": "invalid_bands",
                "scenario_id": scenario_id,
                "error": str(exc),
            }
        if not band_inputs:
            return {"status": "noop", "scenario_id": scenario_id}

        task_id = context.get("task_id")
        queued_at = context.get("queued_at")

        cash_flows = [Decimal(str(value)) for value in context.get("cash_flows", [])]
        discount_rate = Decimal(str(context.get("discount_rate", "0")))
        escalated_cost = Decimal(str(context.get("escalated_cost", "0")))
        currency = str(
            context.get("currency") or getattr(scenario.fin_project, "currency", "SGD")
        )
        interest_periods = int(context.get("interest_periods", 12))
        capitalise_interest = bool(context.get("capitalise_interest", True))
        base_interest_rate = _coerce_decimal(context.get("base_interest_rate"))

        schedule_summary = None
        schedule_payload = context.get("schedule")
        if isinstance(schedule_payload, Mapping):
            entries = schedule_payload.get("entries") or []
            drawdown_inputs = []
            for entry in entries:
                if not isinstance(entry, Mapping):
                    continue
                drawdown_inputs.append(
                    {
                        "period": str(entry.get("period", "")),
                        "equity_draw": _decimal_from_value(
                            entry.get("equity_draw", "0")
                        ),
                        "debt_draw": _decimal_from_value(entry.get("debt_draw", "0")),
                    }
                )
            if drawdown_inputs:
                schedule_summary = calculator.drawdown_schedule(
                    drawdown_inputs,
                    currency=str(schedule_payload.get("currency", currency)),
                )

        facility_payloads = context.get("facilities")
        if isinstance(facility_payloads, Sequence):
            facility_inputs = [
                dict(item) if isinstance(item, Mapping) else dict(item)  # type: ignore[arg-type]
                for item in facility_payloads
            ]
        else:
            facility_inputs = []

        base_interest_schedule = None
        if schedule_summary is not None:
            base_interest_schedule, _ = _build_construction_interest_schedule(
                schedule_summary,
                currency=schedule_summary.currency,
                base_interest_rate=base_interest_rate,
                base_periods_per_year=interest_periods,
                capitalise_interest=capitalise_interest,
                facilities=facility_inputs,
            )

        base_npv = calculator.npv(discount_rate, cash_flows)
        base_irr = None
        try:
            base_irr = calculator.irr(cash_flows).quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )
        except ValueError:
            base_irr = None
        interest_total = (
            _decimal_from_value(base_interest_schedule.total_interest)
            if (
                base_interest_schedule
                and base_interest_schedule.total_interest is not None
            )
            else None
        )

        sensitivity_results, sensitivity_metadata = _evaluate_sensitivity_bands(
            band_inputs,
            base_npv=base_npv,
            base_irr=base_irr,
            escalated_cost=escalated_cost,
            base_interest_total=interest_total,
            currency=currency,
        )

        existing_result: FinResult | None = None
        for candidate in scenario.results:
            if candidate.name == "sensitivity_analysis":
                existing_result = candidate
                break
        if existing_result is None:
            existing_result = FinResult(
                project_id=scenario.project_id,
                scenario=scenario,
                name="sensitivity_analysis",
                value=None,
                unit=None,
                metadata={},
            )
            sess.add(existing_result)

        metadata_payload = existing_result.metadata
        if not isinstance(metadata_payload, dict):
            metadata_payload = {}
        bands_meta = metadata_payload.get("bands")
        if not isinstance(bands_meta, list):
            bands_meta = []

        cleaned_bands: list[dict[str, Any]] = []
        for entry in bands_meta:
            if not isinstance(entry, dict):
                continue
            parameter = entry.get("parameter")
            if parameter == "__async__":
                continue
            if parameter == "__truncated__":
                updated = dict(entry)
                updated["status"] = "processed_async"
                updated.pop("skipped_count", None)
                cleaned_bands.append(updated)
                continue
            cleaned_bands.append(entry)

        cleaned_bands.extend(sensitivity_metadata)
        metadata_payload["bands"] = cleaned_bands
        existing_result.metadata = _json_safe(metadata_payload)

        # Mark metadata as modified for SQLAlchemy to detect the change
        from sqlalchemy.orm.attributes import flag_modified

        flag_modified(existing_result, "metadata_json")

        assumptions = dict(scenario.assumptions or {})
        async_jobs = assumptions.get("async_jobs")
        if isinstance(async_jobs, dict):
            sensitivity_entries = async_jobs.get("sensitivity")
            if isinstance(sensitivity_entries, list):
                pruned_entries: list[dict[str, Any]] = []
                for entry in sensitivity_entries:
                    if not isinstance(entry, dict):
                        continue
                    if task_id and entry.get("task_id") == task_id:
                        continue
                    if queued_at and entry.get("queued_at") == queued_at:
                        continue
                    pruned_entries.append(entry)
                if pruned_entries:
                    async_jobs["sensitivity"] = pruned_entries
                else:
                    async_jobs.pop("sensitivity", None)
            if not async_jobs.get("sensitivity"):
                async_jobs.pop("sensitivity", None)
            if async_jobs:
                assumptions["async_jobs"] = async_jobs
            else:
                assumptions.pop("async_jobs", None)
            scenario.assumptions = assumptions

        # In test mode (external session), flush instead of commit so changes are visible
        # within the test transaction. In production, commit to persist changes.
        if use_external_session:
            await sess.flush()
        else:
            await sess.commit()

        return {
            "status": "completed",
            "scenario_id": scenario_id,
            "bands": [
                (
                    band.model_dump(mode="json")
                    if isinstance(band, FinanceSensitivityOutcomeSchema)
                    else band
                )
                for band in sensitivity_results
            ],
            "metadata": cleaned_bands,
        }

    # Execute job with appropriate session
    if use_external_session:
        # Test mode: use provided session
        return await _run_job(session)  # type: ignore[arg-type]
    else:
        # Production mode: create and manage own session
        if session_ctx is None:  # pragma: no cover - defensive guard
            raise RuntimeError("Session dependency did not return a context manager")
        async with session_ctx as managed_session:  # type: ignore[union-attr]
            return await _run_job(managed_session)


__all__ = ["process_finance_sensitivity_job"]
