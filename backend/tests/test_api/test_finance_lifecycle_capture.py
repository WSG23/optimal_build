from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.analytics_capture import EntityLifecycleEvent, StatusTransition
from app.models.finance import FinProject, FinScenario
from app.models.projects import Project, ProjectPhase, ProjectType


@pytest.mark.asyncio
async def test_delete_finance_scenario_soft_deletes_and_records_lifecycle(
    app_client: AsyncClient,
    async_session_factory,
) -> None:
    project_id = uuid4()
    async with async_session_factory() as session:
        session.add(
            Project(
                id=project_id,
                project_name="Lifecycle Capture",
                project_code="LIFECYCLE-CAPTURE",
                project_type=ProjectType.NEW_DEVELOPMENT,
                current_phase=ProjectPhase.FEASIBILITY,
            )
        )
        fin_project = FinProject(project_id=project_id, name="Lifecycle Finance")
        session.add(fin_project)
        await session.flush()
        scenario = FinScenario(
            project_id=project_id,
            fin_project_id=fin_project.id,
            name="Delete Me",
            assumptions={"source": "test"},
        )
        session.add(scenario)
        await session.commit()
        scenario_id = scenario.id

    response = await app_client.delete(
        f"/api/v1/finance/scenarios/{scenario_id}",
        headers={"X-Role": "admin", "X-Request-ID": "finance-delete-test"},
    )
    assert response.status_code == 204, response.text

    async with async_session_factory() as session:
        persisted = await session.get(FinScenario, scenario_id)
        lifecycle = (
            (
                await session.execute(
                    select(EntityLifecycleEvent).where(
                        EntityLifecycleEvent.entity_type == "fin_scenario",
                        EntityLifecycleEvent.entity_id == str(scenario_id),
                        EntityLifecycleEvent.action == "soft_delete",
                    )
                )
            )
            .scalars()
            .first()
        )
        transition = (
            (
                await session.execute(
                    select(StatusTransition).where(
                        StatusTransition.entity_type == "fin_scenario",
                        StatusTransition.entity_id == str(scenario_id),
                        StatusTransition.to_status == "deleted",
                    )
                )
            )
            .scalars()
            .first()
        )

    assert persisted is not None
    assert persisted.deleted_at is not None
    assert lifecycle is not None
    assert lifecycle.tombstone_payload["name"] == "Delete Me"
    assert transition is not None
