"""Smoke test for finance API endpoints and Prometheus metrics."""

from __future__ import annotations

from collections.abc import Iterable
from decimal import ROUND_HALF_UP, Decimal
import uuid

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")

from app.utils import metrics
from backend.app.models.rkp import RefCostIndex
from backend.app.schemas.finance import DscrInputs
from backend.app.models.projects import Project, ProjectPhase, ProjectType
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
    session.add_all(list(entries))
    await session.commit()


async def _ensure_project(session, *, project_id: uuid.UUID, name: str) -> None:
    existing = await session.get(Project, project_id)
    if existing is not None:
        return
    project = Project(
        id=project_id,
        project_name=name,
        project_code=f"SMOKE-{project_id.hex[:8]}",
        project_type=ProjectType.NEW_DEVELOPMENT,
        current_phase=ProjectPhase.FEASIBILITY,
        owner_email="smoke@example.com",
        description="Finance smoke test project",
    )
    session.add(project)
    await session.commit()


def _expected_dscr_entries() -> list[calculator.DscrEntry]:
    return calculator.dscr_timeline(
        [Decimal("0"), Decimal("1200"), Decimal("-300")],
        [Decimal("0"), Decimal("1000"), Decimal("800")],
        period_labels=["M0", "M1", "M2"],
        currency="SGD",
    )


def _serialise_dscr_entries(
    entries: Iterable[calculator.DscrEntry],
) -> list[dict[str, object]]:
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


def _parse_metric_samples(metrics_text: str) -> dict[str, list[float]]:
    samples: dict[str, list[float]] = {}
    for line in metrics_text.splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split(" ", 1)
        if len(parts) != 2:
            continue
        name, raw_value = parts
        try:
            value = float(raw_value.strip())
        except ValueError:
            continue
        samples.setdefault(name, []).append(value)
    return samples


@pytest.mark.asyncio
async def test_finance_feasibility_and_export_metrics(
    async_session_factory, app_client: AsyncClient
) -> None:
    metrics.reset_metrics()

    project_uuid = uuid.uuid4()
    project_id_str = str(project_uuid)
    async with async_session_factory() as session:
        await _ensure_project(
            session,
            project_id=project_uuid,
            name="Finance Smoke Project",
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
                    provider="SmokeTest",
                ),
                RefCostIndex(
                    jurisdiction="SG",
                    series_name="construction_all_in",
                    category="composite",
                    period="2024-Q4",
                    value=Decimal("120"),
                    unit="index",
                    source="test",
                    provider="SmokeTest",
                ),
            ],
        )
        summary = await seed_finance_demo(
            session,
            project_id=project_uuid,
            project_name="Finance Smoke Project",
            currency="SGD",
            reset_existing=True,
        )

    scenario_payload = {
        "project_id": project_id_str,
        "project_name": "Finance Smoke Scenario",
        "fin_project_id": summary.fin_project_id,
        "scenario": {
            "name": "Smoke Scenario",
            "description": "Scenario used by finance smoke test",
            "currency": "SGD",
            "is_primary": False,
            "cost_escalation": {
                "amount": "1000.00",
                "base_period": "2024-Q1",
                "series_name": "construction_all_in",
                "jurisdiction": "SG",
                "provider": "SmokeTest",
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
        },
    }

    expected_npv = calculator.npv(
        Decimal("0.08"),
        [Decimal("-1000"), Decimal("-500"), Decimal("1500"), Decimal("700")],
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    expected_irr = calculator.irr(
        [Decimal("-1000"), Decimal("-500"), Decimal("1500"), Decimal("700")]
    ).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    expected_dscr_entries = _expected_dscr_entries()
    serialised_expected = _serialise_dscr_entries(expected_dscr_entries)

    baseline_feasibility = metrics.counter_value(metrics.FINANCE_FEASIBILITY_TOTAL, {})
    baseline_export = metrics.counter_value(metrics.FINANCE_EXPORT_TOTAL, {})

    response = await app_client.post(
        "/api/v1/finance/feasibility",
        json=scenario_payload,
        headers=REVIEWER_HEADERS,
    )
    assert response.status_code == 200
    body = response.json()

    assert body["project_id"] == project_id_str
    assert body["fin_project_id"] == summary.fin_project_id

    results_by_name = {result["name"]: result for result in body["results"]}
    assert Decimal(results_by_name["escalated_cost"]["value"]) == Decimal("1200.00")
    assert results_by_name["escalated_cost"]["unit"] == "SGD"
    assert Decimal(results_by_name["npv"]["value"]) == expected_npv
    assert results_by_name["npv"]["unit"] == "SGD"
    assert Decimal(results_by_name["irr"]["value"]) == expected_irr
    assert results_by_name["irr"]["unit"] == "ratio"

    actual_dscr_entries = body["dscr_timeline"]
    assert len(actual_dscr_entries) == len(serialised_expected)
    for actual, expected in zip(actual_dscr_entries, serialised_expected):
        assert actual["period"] == expected["period"]
        assert Decimal(actual["noi"]) == Decimal(expected["noi"])
        assert Decimal(actual["debt_service"]) == Decimal(expected["debt_service"])
        assert actual["currency"] == expected["currency"]
        if expected["dscr"] is None:
            assert actual["dscr"] in (None, "")
        else:
            assert actual["dscr"] == expected["dscr"]

    feasibility_total = metrics.counter_value(metrics.FINANCE_FEASIBILITY_TOTAL, {})
    assert feasibility_total == pytest.approx(baseline_feasibility + 1.0)

    metrics_response = await app_client.get("/health/metrics")
    assert metrics_response.status_code == 200
    metrics_text = metrics_response.text
    metric_samples = _parse_metric_samples(metrics_text)
    assert metric_samples["finance_feasibility_total"][0] == pytest.approx(
        feasibility_total
    )
    assert metric_samples["finance_feasibility_duration_ms_count"][0] >= 1.0

    scenario_id = body["scenario_id"]
    export_response = await app_client.get(
        "/api/v1/finance/export",
        params={"scenario_id": scenario_id},
        headers=VIEWER_HEADERS,
    )
    assert export_response.status_code == 200
    assert export_response.headers["content-type"].startswith("text/csv")

    csv_content = export_response.text
    assert csv_content.splitlines()[0].startswith("Metric,Value,Unit")

    export_total = metrics.counter_value(metrics.FINANCE_EXPORT_TOTAL, {})
    assert export_total == pytest.approx(baseline_export + 1.0)

    latest_metrics = metrics.render_latest_metrics().decode()
    latest_samples = _parse_metric_samples(latest_metrics)
    assert latest_samples["finance_export_total"][0] == pytest.approx(export_total)
    assert latest_samples["finance_export_duration_ms_count"][0] >= 1.0
