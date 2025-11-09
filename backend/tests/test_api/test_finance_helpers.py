from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

from app.api.deps import RequestIdentity
from app.api.v1 import finance as finance_api
from app.schemas.finance import SensitivityBandInput
from app.services.finance import calculator


class _StubSession:
    def __init__(self, row):
        self._row = row

    async def execute(self, _stmt):
        return SimpleNamespace(first=lambda: self._row)


def _identity(role="viewer", user_id=None, email=None):
    return RequestIdentity(role=role, user_id=user_id, email=email)


def test_normalise_project_id_accepts_str_and_int():
    project_uuid = uuid4()
    assert finance_api._normalise_project_id(str(project_uuid)) == project_uuid
    assert finance_api._normalise_project_id(project_uuid.int) == UUID(
        int=project_uuid.int
    )

    with pytest.raises(HTTPException):
        finance_api._normalise_project_id("not-a-uuid")


@pytest.mark.asyncio
async def test_ensure_project_owner_honours_admin(monkeypatch):
    identity = _identity(role="admin")
    session = _StubSession(None)
    await finance_api._ensure_project_owner(session, uuid4(), identity)

    owner_id = uuid4()
    identity = _identity(role="viewer", user_id=str(owner_id))
    session = _StubSession((owner_id, None))
    await finance_api._ensure_project_owner(session, uuid4(), identity)

    identity = _identity(role="viewer", user_id=str(uuid4()))
    session = _StubSession((owner_id, "owner@example.com"))
    with pytest.raises(HTTPException) as exc:
        await finance_api._ensure_project_owner(session, uuid4(), identity)
    assert exc.value.status_code == 403


def test_build_construction_interest_schedule_calculates_interest():
    entry = calculator.FinancingDrawdownEntry(
        period="M1",
        equity_draw=Decimal("0"),
        debt_draw=Decimal("1000000"),
        total_draw=Decimal("1000000"),
        cumulative_equity=Decimal("0"),
        cumulative_debt=Decimal("1000000"),
        outstanding_debt=Decimal("1000000"),
    )
    schedule = calculator.FinancingDrawdownSchedule(
        currency="SGD",
        entries=(entry,),
        total_equity=Decimal("0"),
        total_debt=Decimal("1000000"),
        peak_debt_balance=Decimal("1000000"),
        final_debt_balance=Decimal("1000000"),
    )

    loan_schema, metadata = finance_api._build_construction_interest_schedule(
        schedule,
        currency="SGD",
        base_interest_rate=Decimal("0.06"),
        base_periods_per_year=12,
        capitalise_interest=True,
        facilities=[
            {"amount": "1000000", "interest_rate": "0.05", "upfront_fee_pct": "1"}
        ],
    )

    assert loan_schema.total_interest > Decimal("0")
    assert metadata["entries"][0]["interest_accrued"] != "0"


def test_decimal_conversion_and_json_helpers():
    assert finance_api._decimal_from_value("1.23") == Decimal("1.23")
    assert finance_api._json_safe({"value": Decimal("1.5")}) == {"value": "1.5"}
    assert finance_api._format_percentage_label(Decimal("0.123")) == "+0.12%"


def test_evaluate_sensitivity_bands_generates_scenarios():
    band = SensitivityBandInput(parameter="Cost", low=-5, base=0, high=10, notes=[])
    results, metadata = finance_api._evaluate_sensitivity_bands(
        [band],
        base_npv=Decimal("1000000"),
        base_irr=Decimal("0.08"),
        escalated_cost=Decimal("500000"),
        base_interest_total=Decimal("120000"),
        currency="SGD",
    )
    assert {entry.scenario for entry in results} == {"Low", "Base", "High"}
    assert metadata[0]["parameter"] == "Cost"


def test_default_job_status_and_parse_datetime():
    job = finance_api._default_job_status(42)
    assert job.scenario_id == 42
    dt = datetime.utcnow()
    assert finance_api._parse_datetime_value(dt) == dt
    assert finance_api._parse_datetime_value(dt.isoformat()) == dt
    assert finance_api._parse_datetime_value("invalid") is None


def test_scenario_job_statuses_and_record_job():
    scenario = SimpleNamespace(id=1, assumptions={"async_jobs": {"sensitivity": []}})
    jobs = finance_api._scenario_job_statuses(scenario)
    assert jobs[0].status == "completed"

    new_job = finance_api._default_job_status(1).model_copy(update={"status": "queued"})
    finance_api._record_async_job(scenario, new_job)
    recorded_jobs = finance_api._scenario_job_statuses(scenario)
    assert recorded_jobs[-1].status == "queued"

    payload = finance_api._status_payload(
        SimpleNamespace(id=1, assumptions=scenario.assumptions, updated_at="now")
    )
    assert payload["pending_jobs"] is True


def test_compute_scalar_and_convert_dscr_entry():
    base = finance_api.CostIndexSnapshot(
        period="2020",
        value=Decimal("2.0"),
        unit="index",
        source="Base",
        provider="Gov",
        methodology="test",
    )
    latest = base.model_copy(update={"value": Decimal("2.2")})
    assert finance_api._compute_scalar(base, latest) == Decimal("1.1000")

    dscr_entry = calculator.DscrEntry(
        period="Y1",
        noi=Decimal("100000"),
        debt_service=Decimal("50000"),
        dscr=Decimal("2"),
        currency="SGD",
    )
    schema = finance_api._convert_dscr_entry(dscr_entry)
    assert schema.dscr == "2.0000"
