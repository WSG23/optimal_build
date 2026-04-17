from __future__ import annotations

import io
from uuid import uuid4

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")

from app.api.v1 import finance_workbook as finance_workbook_api
from app.api.v1 import finance_feasibility as finance_feasibility_api
from app.models.projects import Project, ProjectPhase, ProjectType
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from unittest.mock import AsyncMock


def _build_asset_mix() -> list[dict[str, object]]:
    return [
        {
            "asset_type": "office",
            "allocation_pct": "60",
            "nia_sqm": "1200",
            "rent_psm_month": "11",
            "stabilised_vacancy_pct": "5",
            "opex_pct_of_rent": "18",
            "estimated_revenue_sgd": "150000",
            "estimated_capex_sgd": "750000",
            "absorption_months": "8",
            "risk_level": "balanced",
            "notes": ["Office anchor"],
        },
        {
            "asset_type": "retail",
            "allocation_pct": "40",
            "nia_sqm": "600",
            "rent_psm_month": "9",
            "stabilised_vacancy_pct": "8",
            "opex_pct_of_rent": "22",
            "estimated_revenue_sgd": "95000",
            "estimated_capex_sgd": "320000",
            "absorption_months": "10",
            "risk_level": "moderate",
            "notes": ["Retail support"],
        },
    ]


def _build_payload(project_id: str) -> dict[str, object]:
    return {
        "project_id": project_id,
        "project_name": "Workbook Test Project",
        "scenario": {
            "name": "Workbook Base Case",
            "description": "Workbook exchange test",
            "currency": "SGD",
            "is_primary": True,
            "jurisdictionCode": "SG",
            "cost_escalation": {
                "amount": "900000",
                "base_period": "2024-Q1",
                "series_name": "construction_cost_index",
                "jurisdiction": "SG",
            },
            "cash_flow": {
                "discount_rate": "0.085",
                "cash_flows": ["-900000", "180000", "240000", "360000", "420000"],
            },
            "dscr": {
                "net_operating_incomes": ["120000", "135000", "145000"],
                "debt_services": ["100000", "102000", "104000"],
                "period_labels": ["Year 1", "Year 2", "Year 3"],
            },
            "capital_stack": [
                {
                    "name": "Sponsor Equity",
                    "source_type": "equity",
                    "amount": "360000",
                    "tranche_order": 1,
                },
                {
                    "name": "Senior Loan",
                    "source_type": "debt",
                    "amount": "540000",
                    "rate": "0.045",
                    "tranche_order": 2,
                },
            ],
            "drawdown_schedule": [
                {"period": "M1", "equity_draw": "150000", "debt_draw": "0"},
                {"period": "M2", "equity_draw": "90000", "debt_draw": "180000"},
                {"period": "M3", "equity_draw": "120000", "debt_draw": "200000"},
                {"period": "M4", "equity_draw": "0", "debt_draw": "160000"},
            ],
            "construction_loan": {
                "interest_rate": "0.05",
                "periods_per_year": 12,
                "capitalise_interest": True,
                "facilities": [
                    {
                        "name": "Senior Loan",
                        "amount": "540000",
                        "interest_rate": "0.045",
                        "periods_per_year": 12,
                        "capitalise_interest": True,
                        "upfront_fee_pct": "1.25",
                    }
                ],
            },
            "sensitivity_bands": [
                {"parameter": "Rent", "low": "-8", "base": "0", "high": "6"},
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


@pytest.mark.asyncio
async def test_export_preview_and_import_finance_workbook_round_trip(
    app_client: AsyncClient,
    async_session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owner_email = "workbook-owner@example.com"
    project_uuid = uuid4()
    headers = {"X-Role": "reviewer", "X-User-Email": owner_email}
    append_event_mock = AsyncMock()
    monkeypatch.setattr(finance_workbook_api, "append_event", append_event_mock)
    monkeypatch.setattr(finance_feasibility_api, "append_event", append_event_mock)

    async with async_session_factory() as session:
        session.add(
            Project(
                id=project_uuid,
                project_name="Workbook Test Project",
                project_code="FIN-WB",
                project_type=ProjectType.NEW_DEVELOPMENT,
                current_phase=ProjectPhase.CONCEPT,
                owner_email=owner_email,
            )
        )
        await session.commit()

    create_response = await app_client.post(
        "/api/v1/finance/feasibility",
        json=_build_payload(str(project_uuid)),
        headers=headers,
    )
    assert create_response.status_code == 200, create_response.text
    scenario = create_response.json()

    export_response = await app_client.get(
        f"/api/v1/finance/export/workbook?scenario_id={scenario['scenario_id']}",
        headers=headers,
    )
    assert export_response.status_code == 200, export_response.text
    assert (
        export_response.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    workbook_bytes = export_response.content
    assert workbook_bytes.startswith(b"PK")

    preview_response = await app_client.post(
        "/api/v1/finance/import/workbook/preview",
        files={
            "file": (
                "finance_scenario.xlsx",
                io.BytesIO(workbook_bytes),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        data={"project_id": str(project_uuid)},
    )
    assert preview_response.status_code == 200, preview_response.text
    preview_body = preview_response.json()
    assert preview_body["is_valid"] is True
    assert preview_body["scenario_name"] == "Workbook Base Case"
    assert preview_body["asset_count"] == 2
    assert any(
        sheet["recognised_as"] == "asset_mix"
        for sheet in preview_body["detected_sheets"]
    )

    import_response = await app_client.post(
        "/api/v1/finance/import/workbook",
        headers=headers,
        files={
            "file": (
                "finance_scenario.xlsx",
                io.BytesIO(workbook_bytes),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        data={"project_id": str(project_uuid), "project_name": "Workbook Test Project"},
    )
    assert import_response.status_code == 200, import_response.text
    imported = import_response.json()
    assert imported["scenario_name"] == "Workbook Base Case"
    assert len(imported["asset_breakdowns"]) == 2
    assert imported["construction_loan"] is not None
    assert imported["sensitivity_bands"]
    assert append_event_mock.await_count == 4
    event_types = [
        call.kwargs["event_type"] for call in append_event_mock.await_args_list
    ]
    assert event_types == [
        "finance_scenario_created",
        "export_generated",
        "finance_scenario_created",
        "workbook_imported",
    ]
    assert append_event_mock.await_args_list[0].kwargs["context"]["origin"] == "manual"
    assert (
        append_event_mock.await_args_list[2].kwargs["context"]["origin"] == "workbook"
    )
