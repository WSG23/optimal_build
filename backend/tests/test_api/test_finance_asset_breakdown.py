"""Phase 2C finance API tests for asset-specific modelling and privacy."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")

from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from app.models.projects import Project, ProjectPhase, ProjectType

from app.core.config import settings
from backend.jobs import JobDispatch, job_queue


def _build_asset_mix():
    return [
        {
            "asset_type": "office",
            "allocation_pct": "55.0",
            "nia_sqm": "1000",
            "rent_psm_month": "10",
            "stabilised_vacancy_pct": "5",
            "opex_pct_of_rent": "20",
            "estimated_revenue_sgd": "91200",
            "estimated_capex_sgd": "500000",
            "absorption_months": "6",
            "risk_level": "balanced",
            "notes": ["Office baseline with healthy demand."],
        },
        {
            "asset_type": "retail",
            "allocation_pct": "25.0",
            "nia_sqm": "500",
            "rent_psm_month": "8",
            "stabilised_vacancy_pct": "10",
            "opex_pct_of_rent": "25",
            "estimated_revenue_sgd": "32400",
            "estimated_capex_sgd": "150000",
            "absorption_months": "9",
            "risk_level": "moderate",
            "notes": ["Retail uplift assumes curated tenant mix."],
        },
    ]


@pytest.mark.asyncio
async def test_finance_asset_mix_breakdown_and_privacy(
    app_client: AsyncClient,
    async_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    owner_email = "demo-owner@example.com"
    project_uuid = uuid4()
    async with async_session_factory() as session:
        project = Project(
            id=project_uuid,
            project_name="Test Project",
            project_code="FINANCE-TST",
            project_type=ProjectType.NEW_DEVELOPMENT,
            current_phase=ProjectPhase.CONCEPT,
            owner_email=owner_email,
        )
        session.add(project)
        await session.commit()

    payload = {
        "project_id": str(project_uuid),
        "project_name": "Test Project",
        "scenario": {
            "name": "Phase 2C Base Case",
            "description": "Includes asset mix payload",
            "currency": "SGD",
            "is_primary": True,
            "cost_escalation": {
                "amount": "650000",
                "base_period": "2024-Q1",
                "series_name": "construction_cost_index",
                "jurisdiction": "SG",
            },
            "cash_flow": {
                "discount_rate": "0.085",
                "cash_flows": ["-650000", "150000", "180000", "200000"],
            },
            "drawdown_schedule": [
                {"period": "Q1", "equity_draw": "200000", "debt_draw": "0"},
                {"period": "Q2", "equity_draw": "100000", "debt_draw": "150000"},
                {"period": "Q3", "equity_draw": "0", "debt_draw": "200000"},
            ],
            "construction_loan": {
                "interest_rate": "0.05",
                "periods_per_year": 12,
                "capitalise_interest": True,
                "facilities": [
                    {
                        "name": "Senior Loan",
                        "amount": "250000",
                        "interest_rate": "0.045",
                        "periods_per_year": 12,
                        "capitalise_interest": True,
                    },
                    {
                        "name": "Mezz Loan",
                        "amount": "150000",
                        "interest_rate": "0.08",
                        "periods_per_year": 12,
                        "capitalise_interest": False,
                        "upfront_fee_pct": "1.0",
                    },
                ],
            },
            "sensitivity_bands": [
                {
                    "parameter": "Rent",
                    "low": "-8",
                    "base": "0",
                    "high": "6",
                },
                {
                    "parameter": "Construction Cost",
                    "low": "10",
                    "base": "0",
                    "high": "-5",
                },
                {
                    "parameter": "Interest Rate (delta %)",
                    "low": "1.50",
                    "base": "0",
                    "high": "-0.75",
                },
            ],
            "asset_mix": _build_asset_mix(),
        },
    }

    response = await app_client.post(
        "/api/v1/finance/feasibility",
        json=payload,
        headers={"X-Role": "reviewer", "X-User-Email": owner_email},
    )
    assert response.status_code == 200
    body = response.json()

    assert body["asset_mix_summary"] is not None
    assert (
        body["asset_mix_summary"]["total_estimated_revenue_sgd"] == "123600.00"
    ), body["asset_mix_summary"]
    assert body["asset_mix_summary"]["dominant_risk_profile"] == "moderate"
    assert len(body["asset_breakdowns"]) == 2
    office_breakdown = body["asset_breakdowns"][0]
    assert office_breakdown["asset_type"] == "office"
    assert office_breakdown["noi_annual_sgd"] == "91200.00"
    assert office_breakdown["estimated_capex_sgd"] == "500000.00"
    interest = body["construction_loan_interest"]
    assert interest is not None
    assert interest["entries"], "Expected construction loan interest entries"
    assert interest["entries"][0]["period"] == "Q1"
    assert interest["facilities"], "Multi-facility breakdown expected"
    facility_names = {item["name"] for item in interest["facilities"]}
    assert {"Senior Loan", "Mezz Loan"} <= facility_names
    mezz_facility = next(
        item for item in interest["facilities"] if item["name"] == "Mezz Loan"
    )
    assert mezz_facility["capitalised"] is False
    assert mezz_facility["upfront_fee"] == "1500.00"
    assert interest["upfront_fee_total"] == "1500.00"
    loan_config = body["construction_loan"]
    assert loan_config is not None
    assert loan_config["interest_rate"] == "0.0500"
    assert loan_config["facilities"], "Expected facilities in loan config"
    assert loan_config["facilities"][0]["name"] == "Senior Loan"
    sensitivity = body["sensitivity_results"]
    assert sensitivity, "Sensitivity results should be returned"
    assert sensitivity[0]["parameter"] == "Rent"

    fin_project_id = body["fin_project_id"]
    list_response = await app_client.get(
        f"/api/v1/finance/scenarios?fin_project_id={fin_project_id}",
        headers={"X-Role": "reviewer"},
    )
    assert list_response.status_code == 200
    scenarios = list_response.json()
    assert len(scenarios) >= 1
    persisted = scenarios[-1]
    assert persisted["asset_mix_summary"]["total_estimated_revenue_sgd"] == "123600.00"
    assert len(persisted["asset_breakdowns"]) == 2
    assert any(result["name"] == "asset_financials" for result in persisted["results"])
    assert persisted[
        "sensitivity_results"
    ], "Persisted scenario should include sensitivity results"
    assert persisted[
        "construction_loan_interest"
    ], "Persisted scenario should include construction loan interest"
    assert persisted["construction_loan"] is not None

    export_response = await app_client.get(
        f"/api/v1/finance/export?scenario_id={body['scenario_id']}",
        headers={"X-Role": "reviewer"},
    )
    assert export_response.status_code == 200
    export_text = export_response.text
    assert "Construction Loan Facilities" in export_text
    assert "Sensitivity Analysis Outcomes" in export_text
    assert "Rent" in export_text

    viewer_response = await app_client.get(
        f"/api/v1/finance/scenarios?fin_project_id={fin_project_id}",
        headers={"X-Role": "viewer"},
    )
    assert viewer_response.status_code == 403


@pytest.mark.asyncio
async def test_update_finance_construction_loan(
    app_client: AsyncClient,
) -> None:
    base_payload = {
        "project_id": 401,
        "project_name": "Loan Update",
        "scenario": {
            "name": "Original Loan",
            "currency": "SGD",
            "is_primary": True,
            "cost_escalation": {
                "amount": "250000",
                "base_period": "2024-Q1",
                "series_name": "construction_cost_index",
                "jurisdiction": "SG",
            },
            "cash_flow": {
                "discount_rate": "0.085",
                "cash_flows": ["-250000", "80000", "90000", "95000"],
            },
            "drawdown_schedule": [
                {"period": "Q1", "equity_draw": "100000", "debt_draw": "0"},
                {"period": "Q2", "equity_draw": "50000", "debt_draw": "75000"},
            ],
            "construction_loan": {
                "interest_rate": "0.05",
                "periods_per_year": 12,
                "capitalise_interest": True,
            },
            "asset_mix": _build_asset_mix(),
        },
    }

    create_response = await app_client.post(
        "/api/v1/finance/feasibility",
        json=base_payload,
        headers={"X-Role": "reviewer"},
    )
    assert create_response.status_code == 200
    scenario_id = create_response.json()["scenario_id"]

    update_payload = {
        "construction_loan": {
            "interest_rate": "0.0625",
            "periods_per_year": 12,
            "capitalise_interest": False,
            "facilities": [
                {
                    "name": "Tranche A",
                    "amount": "150000",
                    "interest_rate": "0.055",
                    "periods_per_year": 12,
                    "capitalise_interest": True,
                    "upfront_fee_pct": "1.0",
                },
                {
                    "name": "Tranche B",
                    "amount": "50000",
                    "interest_rate": "0.075",
                    "periods_per_year": 12,
                    "capitalise_interest": False,
                    "exit_fee_pct": "2.0",
                },
            ],
        }
    }

    patch_response = await app_client.patch(
        f"/api/v1/finance/scenarios/{scenario_id}/construction-loan",
        json=update_payload,
        headers={"X-Role": "reviewer"},
    )
    assert patch_response.status_code == 200
    body = patch_response.json()
    loan_config = body["construction_loan"]
    assert loan_config is not None
    assert loan_config["interest_rate"] == "0.0625"
    assert len(loan_config["facilities"]) == 2
    tranche_b = next(
        item for item in loan_config["facilities"] if item["name"] == "Tranche B"
    )
    assert tranche_b["exit_fee_pct"] == "2.00"


@pytest.mark.asyncio
async def test_finance_sensitivity_overflow_enqueues_job(
    app_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "FINANCE_SENSITIVITY_MAX_SYNC_BANDS", 1)

    captured: dict[str, Any] = {}

    async def fake_enqueue(job_name, scenario_id, *, bands, context, queue=None):
        captured["job_name"] = job_name
        captured["scenario_id"] = scenario_id
        captured["bands"] = bands
        captured["context"] = context
        return JobDispatch(
            backend="celery",
            job_name=job_name,
            queue=queue,
            status="queued",
            task_id="job-123",
        )

    monkeypatch.setattr(job_queue._backend, "name", "celery", raising=False)
    monkeypatch.setattr(job_queue, "enqueue", fake_enqueue, raising=False)

    payload = {
        "project_id": 401,
        "project_name": "Sensitivity Overflow",
        "scenario": {
            "name": "Overflow Scenario",
            "currency": "SGD",
            "is_primary": False,
            "cost_escalation": {
                "amount": "350000",
                "base_period": "2024-Q1",
                "series_name": "construction_cost_index",
                "jurisdiction": "SG",
            },
            "cash_flow": {
                "discount_rate": "0.08",
                "cash_flows": ["-350000", "90000", "95000", "110000"],
            },
            "drawdown_schedule": [
                {"period": "M0", "equity_draw": "50000", "debt_draw": "0"},
                {"period": "M1", "equity_draw": "0", "debt_draw": "125000"},
            ],
            "construction_loan": {
                "interest_rate": "0.045",
                "periods_per_year": 12,
                "capitalise_interest": True,
            },
            "sensitivity_bands": [
                {"parameter": "Rent", "low": "-5", "base": "0", "high": "6"},
                {
                    "parameter": "Construction Cost",
                    "low": "10",
                    "base": "0",
                    "high": "-5",
                },
            ],
            "asset_mix": _build_asset_mix(),
        },
    }

    response = await app_client.post(
        "/api/v1/finance/feasibility",
        json=payload,
        headers={"X-Role": "reviewer"},
    )
    assert response.status_code == 200
    body = response.json()
    assert captured["job_name"] == "finance.sensitivity"
    assert isinstance(captured["bands"], list)
    # metadata should note async processing
    sensitivity_result = next(
        result for result in body["results"] if result["name"] == "sensitivity_analysis"
    )
    bands_meta = sensitivity_result["metadata"]["bands"]
    assert any(entry.get("parameter") == "__async__" for entry in bands_meta)

    jobs_response = await app_client.get(
        f"/api/v1/finance/jobs?scenario_id={body['scenario_id']}",
        headers={"X-Role": "reviewer"},
    )
    assert jobs_response.status_code == 200
    jobs = jobs_response.json()
    assert jobs, "Expected job status entries"
    job_entry = jobs[0]
    assert job_entry["status"] in {"queued", "completed"}
    assert job_entry["scenario_id"] == body["scenario_id"]

    status_response = await app_client.get(
        f"/api/v1/finance/scenarios/{body['scenario_id']}/status",
        headers={"X-Role": "reviewer"},
    )
    assert status_response.status_code == 200
    status_body = status_response.json()
    assert status_body["pending_jobs"]


@pytest.mark.asyncio
async def test_finance_jobs_completed_when_no_async_entries(
    app_client: AsyncClient,
) -> None:
    payload = {
        "project_id": 402,
        "project_name": "No Async Jobs",
        "scenario": {
            "name": "No Jobs Scenario",
            "currency": "SGD",
            "is_primary": False,
            "cost_escalation": {
                "amount": "150000",
                "base_period": "2024-Q1",
                "series_name": "construction_cost_index",
                "jurisdiction": "SG",
            },
            "cash_flow": {"discount_rate": "0.085", "cash_flows": ["-150000", "50000"]},
            "drawdown_schedule": [
                {"period": "Q1", "equity_draw": "75000", "debt_draw": "0"},
                {"period": "Q2", "equity_draw": "0", "debt_draw": "75000"},
            ],
            "construction_loan": {
                "interest_rate": "0.045",
                "periods_per_year": 12,
                "capitalise_interest": True,
            },
            "asset_mix": _build_asset_mix(),
        },
    }

    response = await app_client.post(
        "/api/v1/finance/feasibility",
        json=payload,
        headers={"X-Role": "reviewer"},
    )
    assert response.status_code == 200
    scenario_id = response.json()["scenario_id"]

    jobs_response = await app_client.get(
        f"/api/v1/finance/jobs?scenario_id={scenario_id}",
        headers={"X-Role": "reviewer"},
    )
    assert jobs_response.status_code == 200
    jobs = jobs_response.json()
    assert jobs == [
        {
            "scenario_id": scenario_id,
            "task_id": None,
            "status": "completed",
            "backend": None,
            "queued_at": None,
        }
    ]


@pytest.mark.asyncio
async def test_finance_sensitivity_job_execution(
    app_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from backend.jobs.finance_sensitivity import process_finance_sensitivity_job

    original_limit = settings.FINANCE_SENSITIVITY_MAX_SYNC_BANDS
    monkeypatch.setattr(settings, "FINANCE_SENSITIVITY_MAX_SYNC_BANDS", 1)

    captured: dict[str, Any] = {}

    async def fake_enqueue(job_name, scenario_id, *, bands, context, queue=None):
        captured["job_name"] = job_name
        captured["scenario_id"] = scenario_id
        captured["bands"] = bands
        captured["context"] = context
        return JobDispatch(
            backend="inline",
            job_name=job_name,
            queue=queue,
            status="queued",
            task_id="test-task-456",
        )

    monkeypatch.setattr(job_queue._backend, "name", "celery", raising=False)
    monkeypatch.setattr(job_queue, "enqueue", fake_enqueue, raising=False)

    payload = {
        "project_id": 501,
        "project_name": "Async Job Scenario",
        "scenario": {
            "name": "Async Overflow",
            "currency": "SGD",
            "is_primary": False,
            "cost_escalation": {
                "amount": "450000",
                "base_period": "2024-Q1",
                "series_name": "construction_cost_index",
                "jurisdiction": "SG",
            },
            "cash_flow": {
                "discount_rate": "0.08",
                "cash_flows": ["-450000", "120000", "140000", "160000"],
            },
            "drawdown_schedule": [
                {"period": "M0", "equity_draw": "150000", "debt_draw": "0"},
                {"period": "M1", "equity_draw": "0", "debt_draw": "150000"},
                {"period": "M2", "equity_draw": "0", "debt_draw": "150000"},
            ],
            "construction_loan": {
                "interest_rate": "0.048",
                "periods_per_year": 12,
                "capitalise_interest": True,
            },
            "sensitivity_bands": [
                {"parameter": "Rent", "low": "-5", "base": "0", "high": "6"},
                {
                    "parameter": "Construction Cost",
                    "low": "10",
                    "base": "0",
                    "high": "-5",
                },
            ],
            "asset_mix": _build_asset_mix(),
        },
    }

    response = await app_client.post(
        "/api/v1/finance/feasibility",
        json=payload,
        headers={"X-Role": "reviewer"},
    )
    assert response.status_code == 200
    scenario_id = response.json()["scenario_id"]
    assert captured["scenario_id"] == scenario_id

    # Add task_id to context so the job can find and remove the correct async_jobs entry
    job_context = dict(captured["context"])
    job_context["task_id"] = "test-task-456"

    job_result = await process_finance_sensitivity_job(
        captured["scenario_id"],
        bands=captured["bands"],
        context=job_context,
    )
    assert job_result["status"] == "completed"

    jobs_response = await app_client.get(
        f"/api/v1/finance/jobs?scenario_id={scenario_id}",
        headers={"X-Role": "reviewer"},
    )
    assert jobs_response.status_code == 200
    jobs = jobs_response.json()
    assert jobs == [
        {
            "scenario_id": scenario_id,
            "task_id": None,
            "status": "completed",
            "backend": None,
            "queued_at": None,
        }
    ]

    scenario_response = await app_client.get(
        f"/api/v1/finance/scenarios?fin_project_id={response.json()['fin_project_id']}",
        headers={"X-Role": "reviewer"},
    )
    assert scenario_response.status_code == 200
    latest = scenario_response.json()[-1]
    assert any(
        entry.get("parameter") != "__async__" for entry in latest["sensitivity_results"]
    )

    monkeypatch.setattr(settings, "FINANCE_SENSITIVITY_MAX_SYNC_BANDS", original_limit)


@pytest.mark.asyncio
async def test_finance_status_stream_returns_updates(
    app_client: AsyncClient,
) -> None:
    payload = {
        "project_id": 503,
        "project_name": "Stream Scenario",
        "scenario": {
            "name": "Stream Status",
            "currency": "SGD",
            "is_primary": False,
            "cost_escalation": {
                "amount": "180000",
                "base_period": "2024-Q1",
                "series_name": "construction_cost_index",
                "jurisdiction": "SG",
            },
            "cash_flow": {"discount_rate": "0.08", "cash_flows": ["-180000", "90000"]},
            "drawdown_schedule": [
                {"period": "M0", "equity_draw": "90000", "debt_draw": "0"},
                {"period": "M1", "equity_draw": "0", "debt_draw": "90000"},
            ],
            "construction_loan": {
                "interest_rate": "0.045",
                "periods_per_year": 12,
                "capitalise_interest": True,
            },
            "asset_mix": _build_asset_mix(),
        },
    }

    response = await app_client.post(
        "/api/v1/finance/feasibility",
        json=payload,
        headers={"X-Role": "reviewer"},
    )
    assert response.status_code == 200
    scenario_id = response.json()["scenario_id"]

    async with app_client.stream(
        "GET",
        f"/api/v1/finance/scenarios/{scenario_id}/status-stream",
        headers={"X-Role": "reviewer"},
    ) as stream:
        chunks = []
        async for chunk in stream.aiter_bytes():
            chunks.append(chunk)
        body = b"".join(chunks)
    assert b"data:" in body


@pytest.mark.asyncio
async def test_finance_scenarios_require_project_owner(
    app_client: AsyncClient,
    async_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    project_uuid = uuid4()
    owner_email = "owner@example.com"
    async with async_session_factory() as session:
        project = Project(
            id=project_uuid,
            project_name="Private Finance Project",
            project_code="PRIVATE-001",
            project_type=ProjectType.NEW_DEVELOPMENT,
            current_phase=ProjectPhase.CONCEPT,
            owner_email=owner_email,
        )
        session.add(project)
        await session.commit()

    payload = {
        "project_id": str(project_uuid),
        "project_name": "Owner Scenario",
        "scenario": {
            "name": "Owner Scenario",
            "currency": "SGD",
            "is_primary": True,
            "cost_escalation": {
                "amount": "120000",
                "base_period": "2024-Q1",
                "series_name": "construction_cost_index",
                "jurisdiction": "SG",
            },
            "cash_flow": {"discount_rate": "0.08", "cash_flows": ["-120000", "90000"]},
            "drawdown_schedule": [
                {"period": "M0", "equity_draw": "60000", "debt_draw": "0"},
                {"period": "M1", "equity_draw": "0", "debt_draw": "60000"},
            ],
            "construction_loan": {
                "interest_rate": "0.045",
                "periods_per_year": 12,
                "capitalise_interest": True,
            },
            "asset_mix": _build_asset_mix(),
        },
    }

    owner_headers = {"X-Role": "reviewer", "X-User-Email": owner_email}
    response = await app_client.post(
        "/api/v1/finance/feasibility",
        json=payload,
        headers=owner_headers,
    )
    assert response.status_code == 200
    fin_project_id = response.json()["fin_project_id"]

    owner_list = await app_client.get(
        f"/api/v1/finance/scenarios?fin_project_id={fin_project_id}",
        headers=owner_headers,
    )
    assert owner_list.status_code == 200

    viewer_headers = {"X-Role": "viewer", "X-User-Email": "viewer@example.com"}
    viewer_response = await app_client.get(
        f"/api/v1/finance/scenarios?fin_project_id={fin_project_id}",
        headers=viewer_headers,
    )
    assert viewer_response.status_code == 403
