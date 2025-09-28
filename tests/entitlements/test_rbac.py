"""RBAC enforcement and metrics validation for the entitlements API."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")

from app.utils import metrics
from backend.app.services.entitlements import EntitlementsService
from backend.scripts.seed_entitlements_sg import seed_entitlements
from httpx import AsyncClient

PROJECT_ID = 90301


@pytest.mark.asyncio
async def test_mutation_role_checks_and_metrics(
    async_session_factory, app_client: AsyncClient
) -> None:
    """Viewer roles should be rejected while reviewer roles succeed and emit metrics."""

    async with async_session_factory() as session:
        await seed_entitlements(session, project_id=PROJECT_ID)
        await session.commit()
        service = EntitlementsService(session)
        roadmap_page = await service.list_roadmap_items(project_id=PROJECT_ID, limit=1)
        first_item = roadmap_page.items[0]
        roadmap_item_id = first_item.id

    study_counter_before = metrics.counter_value(
        metrics.ENTITLEMENTS_STUDY_COUNTER, {"operation": "create"}
    )
    roadmap_counter_before = metrics.counter_value(
        metrics.ENTITLEMENTS_ROADMAP_COUNTER, {"operation": "update"}
    )

    study_payload = {
        "project_id": PROJECT_ID,
        "name": "Traffic Impact Review",
        "study_type": "traffic",
    }

    forbidden_study = await app_client.post(
        f"/api/v1/entitlements/{PROJECT_ID}/studies",
        headers={"X-Role": "viewer"},
        json=study_payload,
    )
    assert forbidden_study.status_code == 403
    assert metrics.counter_value(
        metrics.ENTITLEMENTS_STUDY_COUNTER, {"operation": "create"}
    ) == pytest.approx(study_counter_before)

    permitted_study = await app_client.post(
        f"/api/v1/entitlements/{PROJECT_ID}/studies",
        headers={"X-Role": "reviewer"},
        json=study_payload,
    )
    assert permitted_study.status_code == 201
    created_study = permitted_study.json()
    assert created_study["name"] == study_payload["name"]
    assert metrics.counter_value(
        metrics.ENTITLEMENTS_STUDY_COUNTER, {"operation": "create"}
    ) == pytest.approx(study_counter_before + 1.0)

    update_payload = {"status": "in_progress"}

    forbidden_update = await app_client.put(
        f"/api/v1/entitlements/{PROJECT_ID}/roadmap/{roadmap_item_id}",
        headers={"X-Role": "viewer"},
        json=update_payload,
    )
    assert forbidden_update.status_code == 403
    assert metrics.counter_value(
        metrics.ENTITLEMENTS_ROADMAP_COUNTER, {"operation": "update"}
    ) == pytest.approx(roadmap_counter_before)

    permitted_update = await app_client.put(
        f"/api/v1/entitlements/{PROJECT_ID}/roadmap/{roadmap_item_id}",
        headers={"X-Role": "reviewer"},
        json=update_payload,
    )
    assert permitted_update.status_code == 200
    assert permitted_update.json()["status"] == "in_progress"
    assert metrics.counter_value(
        metrics.ENTITLEMENTS_ROADMAP_COUNTER, {"operation": "update"}
    ) == pytest.approx(roadmap_counter_before + 1.0)

    metrics_response = await app_client.get("/health/metrics")
    assert metrics_response.status_code == 200
    metrics_body = metrics_response.text
    assert 'entitlements_study_requests_total{operation="create"}' in metrics_body
    assert 'entitlements_roadmap_requests_total{operation="update"}' in metrics_body


@pytest.mark.asyncio
async def test_roadmap_creation_requires_reviewer_and_records_metrics(
    async_session_factory, app_client: AsyncClient
) -> None:
    """Viewer POSTs should be rejected while reviewer POSTs succeed and emit metrics."""

    metrics.reset_metrics()

    async with async_session_factory() as session:
        await seed_entitlements(session, project_id=PROJECT_ID)
        await session.commit()
        service = EntitlementsService(session)
        roadmap_page = await service.list_roadmap_items(project_id=PROJECT_ID, limit=1)
        approval_type_id = roadmap_page.items[0].approval_type_id
        next_sequence = roadmap_page.total + 1

    counter_labels = {"operation": "create"}
    request_labels = {"endpoint": "entitlements_roadmap_create"}
    counter_before = metrics.counter_value(
        metrics.ENTITLEMENTS_ROADMAP_COUNTER, counter_labels
    )
    request_before = metrics.counter_value(metrics.REQUEST_COUNTER, request_labels)

    payload = {
        "project_id": PROJECT_ID,
        "approval_type_id": approval_type_id,
        "sequence_order": next_sequence,
        "metadata": {"created_by": "pytest"},
    }

    viewer_response = await app_client.post(
        f"/api/v1/entitlements/{PROJECT_ID}/roadmap",
        headers={"X-Role": "viewer"},
        json=payload,
    )
    assert viewer_response.status_code == 403
    assert metrics.counter_value(
        metrics.ENTITLEMENTS_ROADMAP_COUNTER, counter_labels
    ) == pytest.approx(counter_before)
    assert metrics.counter_value(
        metrics.REQUEST_COUNTER, request_labels
    ) == pytest.approx(request_before)

    reviewer_response = await app_client.post(
        f"/api/v1/entitlements/{PROJECT_ID}/roadmap",
        headers={"X-Role": "reviewer"},
        json=payload,
    )
    assert reviewer_response.status_code == 201
    created_item = reviewer_response.json()
    assert created_item["project_id"] == PROJECT_ID
    assert created_item["sequence_order"] == next_sequence
    assert created_item["approval_type_id"] == approval_type_id
    assert metrics.counter_value(
        metrics.ENTITLEMENTS_ROADMAP_COUNTER, counter_labels
    ) == pytest.approx(counter_before + 1.0)
    assert metrics.counter_value(
        metrics.REQUEST_COUNTER, request_labels
    ) == pytest.approx(request_before + 1.0)
