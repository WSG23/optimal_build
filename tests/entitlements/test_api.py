"""Integration tests for the entitlements API."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")

from httpx import AsyncClient

from app.utils import metrics
from backend.scripts.seed_entitlements_sg import seed_entitlements


PROJECT_ID = 90301


@pytest.mark.asyncio
async def test_entitlements_workflow(
    async_session_factory, app_client: AsyncClient
) -> None:
    """Seeding and API interactions should manage entitlements end-to-end."""

    async with async_session_factory() as session:
        summary = await seed_entitlements(
            session, project_id=PROJECT_ID, reset_existing=True
        )
        await session.commit()

    assert summary.roadmap_items > 0

    base_path_response = await app_client.post(
        "/api/v1/entitlements",
        headers={"X-Role": "admin"},
        json={},
    )
    assert base_path_response.status_code == 400
    assert "project" in base_path_response.json()["detail"].lower()

    roadmap_response = await app_client.get(
        f"/api/v1/entitlements/{PROJECT_ID}/roadmap"
    )
    assert roadmap_response.status_code == 200
    roadmap_body = roadmap_response.json()
    assert roadmap_body["total"] == summary.roadmap_items
    first_item_id = roadmap_body["items"][0]["id"]

    paged_response = await app_client.get(
        f"/api/v1/entitlements/{PROJECT_ID}/roadmap?limit=1&offset=1"
    )
    assert paged_response.status_code == 200
    assert len(paged_response.json()["items"]) <= 1

    study_payload = {
        "project_id": PROJECT_ID,
        "name": "Traffic Impact Study",
        "study_type": "traffic",
        "status": "draft",
        "consultant": "Acme Transport",
        "due_date": "2024-11-01",
        "attachments": [
            {"label": "Report", "url": "https://example.com/traffic-study.pdf"}
        ],
    }
    forbidden_response = await app_client.post(
        f"/api/v1/entitlements/{PROJECT_ID}/studies",
        headers={"X-Role": "viewer"},
        json=study_payload,
    )
    assert forbidden_response.status_code == 403

    create_study = await app_client.post(
        f"/api/v1/entitlements/{PROJECT_ID}/studies",
        headers={"X-Role": "admin"},
        json=study_payload,
    )
    assert create_study.status_code == 201
    study_body = create_study.json()
    study_id = study_body["id"]
    assert study_body["name"] == study_payload["name"]
    assert study_body["attachments"][0]["url"].startswith("https://example.com")

    update_roadmap = await app_client.put(
        f"/api/v1/entitlements/{PROJECT_ID}/roadmap/{first_item_id}",
        headers={"X-Role": "admin"},
        json={
            "status": "in_progress",
            "target_submission_date": "2024-11-15",
        },
    )
    assert update_roadmap.status_code == 200
    assert update_roadmap.json()["status"] == "in_progress"
    assert update_roadmap.json()["target_submission_date"] == "2024-11-15"

    clear_submission = await app_client.put(
        f"/api/v1/entitlements/{PROJECT_ID}/roadmap/{first_item_id}",
        headers={"X-Role": "admin"},
        json={"target_submission_date": None},
    )
    assert clear_submission.status_code == 200
    assert clear_submission.json()["target_submission_date"] is None

    stakeholder_payload = {
        "project_id": PROJECT_ID,
        "name": "Urban Redevelopment Authority",
        "organisation": "URA",
        "engagement_type": "agency",
        "status": "active",
        "contact_email": "planner@example.gov",
        "notes": "Monthly coordination meeting established.",
    }
    stakeholder_response = await app_client.post(
        f"/api/v1/entitlements/{PROJECT_ID}/stakeholders",
        headers={"X-Role": "admin"},
        json=stakeholder_payload,
    )
    assert stakeholder_response.status_code == 201
    stakeholder_body = stakeholder_response.json()
    engagement_id = stakeholder_body["id"]

    legal_payload = {
        "project_id": PROJECT_ID,
        "name": "Development Agreement",
        "instrument_type": "agreement",
        "status": "draft",
        "reference_code": "DA-2024-01",
        "attachments": [
            {
                "label": "Agreement",
                "url": "https://example.com/development-agreement.pdf",
            }
        ],
    }
    legal_response = await app_client.post(
        f"/api/v1/entitlements/{PROJECT_ID}/legal",
        headers={"X-Role": "admin"},
        json=legal_payload,
    )
    assert legal_response.status_code == 201
    legal_body = legal_response.json()
    instrument_id = legal_body["id"]

    clear_consultant = await app_client.put(
        f"/api/v1/entitlements/{PROJECT_ID}/studies/{study_id}",
        headers={"X-Role": "admin"},
        json={"consultant": None},
    )
    assert clear_consultant.status_code == 200
    assert clear_consultant.json()["consultant"] is None

    clear_engagement_notes = await app_client.put(
        f"/api/v1/entitlements/{PROJECT_ID}/stakeholders/{engagement_id}",
        headers={"X-Role": "admin"},
        json={"notes": None},
    )
    assert clear_engagement_notes.status_code == 200
    assert clear_engagement_notes.json()["notes"] is None

    clear_reference_code = await app_client.put(
        f"/api/v1/entitlements/{PROJECT_ID}/legal/{instrument_id}",
        headers={"X-Role": "admin"},
        json={"reference_code": None},
    )
    assert clear_reference_code.status_code == 200
    assert clear_reference_code.json()["reference_code"] is None

    export_response = await app_client.get(
        f"/api/v1/entitlements/{PROJECT_ID}/export?format=pdf"
    )
    assert export_response.status_code == 200
    assert export_response.headers["content-type"] in {"application/pdf", "text/html"}
    assert export_response.headers["content-disposition"].startswith(
        "attachment; filename=project-"
    )

    metrics_response = await app_client.get("/health/metrics")
    assert metrics_response.status_code == 200
    metrics_body = metrics_response.text
    assert "entitlements_study_requests_total" in metrics_body
    assert "entitlements_export_requests_total" in metrics_body


@pytest.mark.asyncio
async def test_entitlements_export_smoke(
    async_session_factory, app_client: AsyncClient
) -> None:
    """Exports should stream CSV payloads with appropriate headers."""

    metrics.reset_metrics()

    async with async_session_factory() as session:
        await seed_entitlements(session, project_id=PROJECT_ID)
        await session.commit()

    response = await app_client.get(f"/api/v1/entitlements/{PROJECT_ID}/export")
    assert response.status_code == 200

    content_type = response.headers.get("content-type", "")
    assert content_type.startswith("text/csv")

    disposition = response.headers.get("content-disposition") or response.headers.get(
        "Content-Disposition"
    )
    assert disposition is not None
    assert disposition.startswith("attachment; filename=project-")

    body = response.text
    assert "Entitlements roadmap for project" in body
    assert str(PROJECT_ID) in body

    export_counter = metrics.counter_value(
        metrics.ENTITLEMENTS_EXPORT_COUNTER, {"format": "csv"}
    )
    request_counter = metrics.counter_value(
        metrics.REQUEST_COUNTER, {"endpoint": "entitlements_export"}
    )
    assert export_counter == pytest.approx(1.0)
    assert request_counter == pytest.approx(1.0)
