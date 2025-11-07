from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

from app.api.v1 import finance as finance_api
from app.schemas.finance import FinanceJobStatusSchema, SensitivityBandInput


class _StubEntry:
    def __init__(self, period: int, outstanding_debt: str | Decimal):
        self.period = period
        self.outstanding_debt = outstanding_debt


class _StubSchedule:
    def __init__(self, entries: list[_StubEntry]):
        self.entries = entries


def test_normalise_project_id_and_project_uuid_helpers():
    project_uuid = uuid4()
    assert finance_api._normalise_project_id(str(project_uuid)) == project_uuid

    uuid_from_int = finance_api._normalise_project_id(123456)
    assert isinstance(uuid_from_int, UUID)

    with pytest.raises(HTTPException) as excinfo:
        finance_api._normalise_project_id(-1)
    assert excinfo.value.status_code == 422

    scenario = SimpleNamespace(project_id=str(project_uuid))
    assert finance_api._project_uuid_from_scenario(scenario) == project_uuid

    with pytest.raises(HTTPException) as exc_scenario:
        finance_api._project_uuid_from_scenario(SimpleNamespace(project_id=object()))
    assert exc_scenario.value.status_code == 500


def test_build_construction_interest_schedule_and_facilities():
    schedule = _StubSchedule([_StubEntry(1, "1000000"), _StubEntry(2, "1500000")])
    schema, payload = finance_api._build_construction_interest_schedule(
        schedule,
        currency="SGD",
        base_interest_rate=Decimal("0.06"),
        base_periods_per_year=12,
        capitalise_interest=True,
        facilities=[
            {
                "name": "Bridge",
                "amount": "500000",
                "interest_rate": "0.05",
                "upfront_fee_pct": "1.0",
                "exit_fee_pct": "0.5",
                "capitalise_interest": False,
            }
        ],
    )
    assert schema.currency == "SGD"
    assert schema.facilities[0].name == "Bridge"
    assert schema.total_interest == Decimal("25000.00")
    assert payload["upfront_fee_total"] == "5000.00"
    assert payload["exit_fee_total"] == "2500.00"
    assert schema.entries[0].period == "1"


def test_evaluate_sensitivity_bands_returns_metadata():
    bands = [
        SensitivityBandInput(
            parameter="rent_growth",
            low=Decimal("-5"),
            base=Decimal("0"),
            high=Decimal("10"),
            notes=["base"],
        )
    ]
    results, metadata = finance_api._evaluate_sensitivity_bands(
        bands,
        base_npv=Decimal("1000000"),
        base_irr=Decimal("0.12"),
        escalated_cost=Decimal("500000"),
        base_interest_total=Decimal("75000"),
        currency="SGD",
    )
    assert [entry.scenario for entry in results] == ["Low", "Base", "High"]
    assert metadata[0]["delta_label"].startswith("-")
    assert results[-1].notes[-1].startswith("High case applies")


def test_scenario_job_statuses_and_status_payload():
    scenario = SimpleNamespace(id=7, assumptions=None)
    default_status = finance_api._scenario_job_statuses(scenario)
    assert default_status[0].status == "completed"

    scenario_with_jobs = SimpleNamespace(
        id=8,
        assumptions={
            "async_jobs": {
                "sensitivity": [
                    {
                        "task_id": "abc123",
                        "status": "running",
                        "backend": "rq",
                        "queued_at": "2024-01-01T12:00:00",
                    }
                ]
            }
        },
        updated_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
    )
    payload = finance_api._status_payload(scenario_with_jobs)
    assert payload["pending_jobs"] is True
    assert payload["jobs"][0]["task_id"] == "abc123"


def test_record_async_job_appends_entries():
    scenario = SimpleNamespace(
        id=9,
        assumptions={"async_jobs": {"sensitivity": []}},
    )
    job_status = FinanceJobStatusSchema(
        scenario_id=9,
        task_id="new-job",
        status="queued",
        backend="inline",
        queued_at=datetime(2024, 2, 1, tzinfo=timezone.utc),
    )
    finance_api._record_async_job(scenario, job_status)
    jobs = scenario.assumptions["async_jobs"]["sensitivity"]
    assert jobs[-1]["task_id"] == "new-job"
    assert jobs[-1]["queued_at"].startswith("2024-02-01")
