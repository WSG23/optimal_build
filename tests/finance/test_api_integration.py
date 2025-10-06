"""Integration tests for the finance API endpoints."""

from __future__ import annotations

import csv
import io
import uuid
from collections.abc import Iterable
from decimal import ROUND_HALF_UP, Decimal

import pytest

pytest.importorskip("fastapi")
pydantic = pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")

_PYDANTIC_VERSION = getattr(pydantic, "__version__", "2")
try:
    _PYDANTIC_MAJOR = int(_PYDANTIC_VERSION.split(".", 1)[0])
except ValueError:
    _PYDANTIC_MAJOR = 2
if _PYDANTIC_MAJOR < 2:
    pytest.skip("Finance API tests require Pydantic v2", allow_module_level=True)


from backend.app.models.projects import Project, ProjectPhase, ProjectType
from backend.app.models.rkp import RefCostIndex
from backend.app.schemas.finance import DscrInputs
from backend.app.services.finance import calculator
from backend.scripts.seed_finance_demo import seed_finance_demo
from httpx import AsyncClient

REVIEWER_HEADERS = {"X-Role": "reviewer"}
VIEWER_HEADERS = {"X-Role": "viewer"}


def _wrap_model_validator(func):
    def _wrapper(*args, **kwargs):
        if args:
            instance = args[-1]
        else:
            instance = kwargs.get("values") or kwargs.get("self")
        return func(instance)

    return _wrapper


if getattr(DscrInputs, "__model_validators__", None):
    DscrInputs.__model_validators__ = [
        _wrap_model_validator(validator)
        for validator in DscrInputs.__model_validators__
    ]
    original_validator = DscrInputs.__dict__["_validate_lengths"].__func__
    DscrInputs._validate_lengths = classmethod(
        _wrap_model_validator(original_validator)
    )


async def _seed_cost_indices(session, entries: Iterable[RefCostIndex]) -> None:
    """Persist the supplied cost index records."""

    session.add_all(list(entries))
    await session.commit()


async def _ensure_project(session, *, project_id: uuid.UUID, name: str) -> None:
    """Insert a minimal project row to satisfy foreign key constraints."""

    existing = await session.get(Project, project_id)
    if existing is not None:
        return
    project = Project(
        id=project_id,
        project_name=name,
        project_code=f"QA-{project_id.hex[:8]}",
        project_type=ProjectType.NEW_DEVELOPMENT,
        current_phase=ProjectPhase.FEASIBILITY,
        owner_email="qa@example.com",
        description="Finance integration test project",
    )
    session.add(project)
    await session.commit()


def _expected_dscr_entries() -> list[calculator.DscrEntry]:
    """Return the DSCR entries used for assertions."""

    return calculator.dscr_timeline(
        [Decimal("0"), Decimal("1200"), Decimal("-300")],
        [Decimal("0"), Decimal("1000"), Decimal("800")],
        period_labels=["M0", "M1", "M2"],
        currency="SGD",
    )


def _serialise_dscr_entries(
    entries: Iterable[calculator.DscrEntry],
) -> list[dict[str, object]]:
    """Convert calculator entries into the API's serialised representation."""

    serialised: list[dict[str, object]] = []
    for entry in entries:
        dscr_value = entry.dscr
        if dscr_value is None:
            dscr_repr = None
        elif dscr_value.is_infinite():
            dscr_repr = str(dscr_value)
        else:
            dscr_repr = str(
                dscr_value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
            )
        serialised.append(
            {
                "period": str(entry.period),
                "noi": str(entry.noi),
                "debt_service": str(entry.debt_service),
                "dscr": dscr_repr,
                "currency": entry.currency,
            }
        )
    return serialised


@pytest.mark.asyncio
async def test_finance_feasibility_and_export_endpoints(
    async_session_factory, app_client: AsyncClient
) -> None:
    """Seeding demo data should enable both finance endpoints end-to-end."""

    project_uuid = uuid.uuid4()
    project_id_str = str(project_uuid)
    async with async_session_factory() as session:
        await _ensure_project(
            session,
            project_id=project_uuid,
            name="Finance Demo QA",
        )
        await _seed_cost_indices(
            session,
            [
                RefCostIndex(
                    jurisdiction="SG",
                    series_name="construction_all_in",
                    category="composite",
                    period="2024-Q1",
                    value=Decimal("100"),
                    unit="index",
                    source="test",
                    provider="IntegrationTest",
                ),
                RefCostIndex(
                    jurisdiction="SG",
                    series_name="construction_all_in",
                    category="composite",
                    period="2024-Q4",
                    value=Decimal("120"),
                    unit="index",
                    source="test",
                    provider="IntegrationTest",
                ),
            ],
        )
        summary = await seed_finance_demo(
            session,
            project_id=project_uuid,
            project_name="Finance Demo QA",
            currency="SGD",
            reset_existing=True,
        )

    scenario_payload = {
        "project_id": project_id_str,
        "project_name": "Finance QA Scenario",
        "fin_project_id": summary.fin_project_id,
        "scenario": {
            "name": "QA Scenario",
            "description": "Scenario used by integration test",
            "currency": "SGD",
            "is_primary": False,
            "cost_escalation": {
                "amount": "1000.00",
                "base_period": "2024-Q1",
                "series_name": "construction_all_in",
                "jurisdiction": "SG",
                "provider": "IntegrationTest",
            },
            "cash_flow": {
                "discount_rate": "0.08",
                "cash_flows": ["-1000", "-500", "1500", "700"],
            },
            "dscr": {
                "net_operating_incomes": ["0", "1200", "-300"],
                "debt_services": ["0", "1000", "800"],
                "period_labels": ["M0", "M1", "M2"],
            },
            "capital_stack": [
                {
                    "name": "Sponsor Equity",
                    "source_type": "equity",
                    "amount": "400",
                },
                {
                    "name": "Senior Loan",
                    "source_type": "debt",
                    "amount": "800",
                    "rate": "0.065",
                    "tranche_order": 1,
                },
            ],
            "drawdown_schedule": [
                {"period": "M0", "equity_draw": "150", "debt_draw": "0"},
                {"period": "M1", "equity_draw": "250", "debt_draw": "300"},
                {"period": "M2", "equity_draw": "0", "debt_draw": "500"},
            ],
        },
    }

    response = await app_client.post(
        "/api/v1/finance/feasibility",
        json=scenario_payload,
        headers=REVIEWER_HEADERS,
    )
    assert response.status_code == 200
    body = response.json()

    expected_npv = calculator.npv(
        Decimal("0.08"),
        [Decimal("-1000"), Decimal("-500"), Decimal("1500"), Decimal("700")],
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    expected_irr = calculator.irr(
        [Decimal("-1000"), Decimal("-500"), Decimal("1500"), Decimal("700")]
    ).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    expected_dscr_entries = _expected_dscr_entries()

    assert body["project_id"] == project_id_str
    assert body["fin_project_id"] == summary.fin_project_id

    escalated_cost = Decimal(body["escalated_cost"])
    assert escalated_cost == Decimal("1200.00")

    cost_index = body["cost_index"]
    assert cost_index["base_period"] == "2024-Q1"
    assert cost_index["latest_period"] == "2024-Q4"
    assert Decimal(cost_index["scalar"]) == Decimal("1.2000")

    results_by_name = {result["name"]: result for result in body["results"]}
    assert {
        "escalated_cost",
        "npv",
        "irr",
        "capital_stack",
        "drawdown_schedule",
    }.issubset(results_by_name.keys())

    escalated_result = results_by_name["escalated_cost"]
    assert Decimal(escalated_result["value"]) == Decimal("1200.00")
    assert escalated_result["unit"] == "SGD"

    npv_result = results_by_name["npv"]
    assert Decimal(npv_result["value"]) == expected_npv
    assert npv_result["unit"] == "SGD"

    irr_result = results_by_name["irr"]
    assert Decimal(irr_result["value"]) == expected_irr
    assert irr_result["unit"] == "ratio"

    capital_stack_result = results_by_name["capital_stack"]
    assert Decimal(capital_stack_result["value"]) == Decimal("1200.00")
    capital_meta = capital_stack_result["metadata"]
    assert capital_meta["totals"]["equity"] == "400.00"
    assert capital_meta["ratios"]["debt"] == "0.6667"
    assert len(capital_meta["slices"]) == 2

    drawdown_result = results_by_name["drawdown_schedule"]
    assert drawdown_result["value"] is None
    drawdown_meta = drawdown_result["metadata"]
    assert drawdown_meta["totals"]["debt"] == "800.00"
    assert drawdown_meta["entries"][1]["period"] == "M1"
    assert drawdown_meta["entries"][1]["outstanding_debt"] == "300.00"

    actual_dscr_entries = body["dscr_timeline"]
    serialised_expected = _serialise_dscr_entries(expected_dscr_entries)
    assert len(actual_dscr_entries) == len(serialised_expected)
    for actual, expected in zip(actual_dscr_entries, serialised_expected, strict=False):
        assert actual["period"] == expected["period"]
        assert Decimal(actual["noi"]) == Decimal(expected["noi"])
        assert Decimal(actual["debt_service"]) == Decimal(expected["debt_service"])
        assert actual["currency"] == expected["currency"]
        assert actual["dscr"] == expected["dscr"]

    capital_stack_summary = body["capital_stack"]
    assert capital_stack_summary is not None
    assert Decimal(capital_stack_summary["total"]) == Decimal("1200.00")
    assert Decimal(capital_stack_summary["equity_total"]) == Decimal("400.00")
    assert Decimal(capital_stack_summary["debt_total"]) == Decimal("800.00")
    assert capital_stack_summary["slices"][0]["category"] == "equity"
    assert Decimal(capital_stack_summary["slices"][1]["share"]) == Decimal("0.6667")

    drawdown_schedule = body["drawdown_schedule"]
    assert drawdown_schedule is not None
    assert Decimal(drawdown_schedule["total_debt"]) == Decimal("800.00")
    assert drawdown_schedule["entries"][1]["period"] == "M1"
    assert Decimal(drawdown_schedule["entries"][1]["outstanding_debt"]) == Decimal(
        "300.00"
    )

    scenario_id = body["scenario_id"]

    export_response = await app_client.get(
        "/api/v1/finance/export",
        params={"scenario_id": scenario_id},
        headers=VIEWER_HEADERS,
    )
    assert export_response.status_code == 200
    assert export_response.headers["content-type"].startswith("text/csv")

    csv_content = export_response.read().decode("utf-8")
    reader = csv.reader(io.StringIO(csv_content))
    rows = [row for row in reader if row]
    assert rows[0] == ["Metric", "Value", "Unit"]

    exported_metrics = {
        row[0]: row
        for row in rows
        if row and row[0] in {"escalated_cost", "npv", "irr"}
    }
    assert "npv" in exported_metrics
    assert Decimal(exported_metrics["npv"][1]) == expected_npv

    timeline_header_index = next(
        index
        for index, row in enumerate(rows)
        if row == ["Period", "NOI", "Debt Service", "DSCR", "Currency"]
    )
    exported_timeline = rows[
        timeline_header_index + 1 : timeline_header_index + 1 + len(serialised_expected)
    ]
    for exported_row, expected in zip(
        exported_timeline, serialised_expected, strict=False
    ):
        period, noi, debt_service, dscr_value, currency = exported_row
        assert period == expected["period"]
        assert Decimal(noi) == Decimal(expected["noi"])
        assert Decimal(debt_service) == Decimal(expected["debt_service"])
        assert currency == expected["currency"]
        if expected["dscr"] is None:
            assert dscr_value == ""
        else:
            assert dscr_value == expected["dscr"]


@pytest.mark.asyncio
async def test_finance_feasibility_requires_reviewer_role(
    app_client: AsyncClient,
) -> None:
    payload = {
        "project_id": 123,
        "project_name": "RBAC Test",
        "fin_project_id": None,
        "scenario": {
            "name": "Role Validation",
            "description": "",
            "currency": "SGD",
            "is_primary": False,
            "cost_escalation": {
                "amount": "1000.00",
                "base_period": "2024-Q1",
                "series_name": "construction_all_in",
                "jurisdiction": "SG",
            },
            "cash_flow": {
                "discount_rate": "0.08",
                "cash_flows": ["-1000", "500"],
            },
        },
    }

    missing_header = await app_client.post(
        "/api/v1/finance/feasibility",
        headers={"X-Role": "viewer"},
        json=payload,
    )
    assert missing_header.status_code == 403

    viewer_header = await app_client.post(
        "/api/v1/finance/feasibility",
        json=payload,
        headers=VIEWER_HEADERS,
    )
    assert viewer_header.status_code == 403

    export_forbidden = await app_client.get(
        "/api/v1/finance/export",
        params={"scenario_id": 1},
        headers={"X-Role": "guest"},
    )
    assert export_forbidden.status_code == 403
