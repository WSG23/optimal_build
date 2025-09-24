"""Tests ensuring finance projects cannot be reassigned across projects."""

from __future__ import annotations

from decimal import Decimal

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")

from httpx import AsyncClient

from app.models.finance import FinProject


@pytest.mark.asyncio
async def test_finance_feasibility_rejects_foreign_fin_project(
    app_client: AsyncClient, async_session_factory
) -> None:
    async with async_session_factory() as setup_session:
        local_project = FinProject(
            project_id=101,
            name="Local Project",
            currency="USD",
            discount_rate=Decimal("0.05"),
            metadata={},
        )
        foreign_project = FinProject(
            project_id=202,
            name="Foreign Project",
            currency="EUR",
            discount_rate=Decimal("0.07"),
            metadata={},
        )
        setup_session.add_all([local_project, foreign_project])
        await setup_session.flush()
        foreign_project_id = foreign_project.id
        await setup_session.commit()

    payload = {
        "project_id": 101,
        "project_name": "Local Project",
        "fin_project_id": foreign_project_id,
        "scenario": {
            "name": "Mismatch Scenario",
            "description": "Attempt to reuse a foreign finance workspace",
            "currency": "SGD",
            "is_primary": False,
            "cost_escalation": {
                "amount": "1000000",
                "base_period": "2024-Q1",
                "series_name": "construction_cost",
                "jurisdiction": "SG",
            },
            "cash_flow": {
                "discount_rate": "0.08",
                "cash_flows": ["-1000000", "350000", "400000", "450000"],
            },
        },
    }

    response = await app_client.post("/api/v1/finance/feasibility", json=payload)
    assert response.status_code in (403, 404)

    async with async_session_factory() as verify_session:
        persisted = await verify_session.get(FinProject, foreign_project_id)
        assert persisted is not None
        assert persisted.currency == "EUR"
        assert persisted.discount_rate == Decimal("0.07")
