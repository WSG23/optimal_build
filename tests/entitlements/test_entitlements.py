"""Integration tests for entitlement workflows."""

from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path

import pytest

from app.schemas.entitlements import EntitlementStatus, RoadmapItemCreate
from app.services.entitlements import EntitlementsService


def _seed_singapore_entitlements():
    project_root = Path(__file__).resolve().parents[2]
    backend_root = project_root / "backend"

    for path in (str(project_root), str(backend_root)):
        while path in sys.path:
            sys.path.remove(path)

    sys.path.insert(0, str(project_root))
    sys.path.insert(1, str(backend_root))

    sys.modules.pop("scripts", None)
    module = import_module("scripts.seed_entitlements_sg")
    return getattr(module, "seed_singapore_entitlements")


@pytest.mark.asyncio
async def test_seed_script_populates_authorities_and_roadmap(async_session_factory) -> None:
    """The Singapore seed script should create authorities and default roadmap."""

    async with async_session_factory() as session:
        seed = _seed_singapore_entitlements()
        summary = await seed(session, project_id=321)
        await session.commit()

        service = EntitlementsService(session)
        authorities = await service.list_authorities()
        assert summary.authorities == len(authorities)

        roadmap = await service.list_roadmap(project_id=321)
        assert roadmap.total == summary.roadmap_items

        # Running the seed again should not duplicate roadmap entries.
        summary_repeat = await seed(session, project_id=321)
        await session.commit()
        assert summary_repeat.roadmap_items == 0


@pytest.mark.asyncio
async def test_roadmap_sequence_insertion(async_session_factory) -> None:
    """Creating roadmap items with explicit sequences should reorder existing rows."""

    async with async_session_factory() as session:
        service = EntitlementsService(session)
        authority = await service.upsert_authority(code="TEST-A", name="Test Authority")
        approval = await service.upsert_approval_type(
            authority=authority,
            code="TEST",
            name="Test Approval",
        )
        await session.commit()

        first = await service.create_roadmap_item(
            project_id=987,
            payload=RoadmapItemCreate(approval_type_id=approval.id, notes="First"),
        )
        await session.commit()
        assert first.sequence == 1

        second = await service.create_roadmap_item(
            project_id=987,
            payload=RoadmapItemCreate(
                approval_type_id=approval.id,
                sequence=1,
                status=EntitlementStatus.IN_PROGRESS,
                notes="Inserted",
            ),
        )
        await session.commit()

        roadmap = await service.list_roadmap(project_id=987, limit=10, offset=0)
        sequences = [item.sequence for item in roadmap.items]
        assert sequences == [1, 2]
        assert roadmap.items[0].id == second.id
        assert roadmap.items[1].id == first.id


@pytest.mark.asyncio
async def test_entitlement_api_rbac_and_metrics(
    app_client, async_session_factory
) -> None:
    """RBAC headers should guard writes and metrics should reflect requests."""

    project_id = 555
    async with async_session_factory() as session:
        service = EntitlementsService(session)
        authority = await service.upsert_authority(code="API-A", name="API Authority")
        approval = await service.upsert_approval_type(
            authority=authority,
            code="API-APP",
            name="API Approval",
        )
        await session.commit()
        approval_id = approval.id

    response = await app_client.post(
        f"/api/v1/entitlements/roadmap/{project_id}",
        json={"approval_type_id": approval_id},
    )
    assert response.status_code == 403

    create_response = await app_client.post(
        f"/api/v1/entitlements/roadmap/{project_id}",
        headers={"X-User-Roles": "reviewer"},
        json={"approval_type_id": approval_id, "notes": "Stage 1"},
    )
    assert create_response.status_code == 201
    created_item = create_response.json()
    assert created_item["status"] == EntitlementStatus.PLANNED.value

    update_response = await app_client.put(
        f"/api/v1/entitlements/roadmap/{project_id}/{created_item['id']}",
        headers={"X-User-Roles": "reviewer"},
        json={"status": EntitlementStatus.IN_PROGRESS.value},
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == EntitlementStatus.IN_PROGRESS.value

    metrics_response = await app_client.get("/health/metrics")
    metrics_text = metrics_response.text
    assert "entitlements_requests_total" in metrics_text


@pytest.mark.asyncio
async def test_entitlement_export_fallback_to_html(
    app_client, async_session_factory
) -> None:
    """PDF exports should fall back to HTML when no renderer is available."""

    project_id = 777
    async with async_session_factory() as session:
        service = EntitlementsService(session)
        authority = await service.upsert_authority(code="EXP-A", name="Export Authority")
        approval = await service.upsert_approval_type(
            authority=authority,
            code="EXP",
            name="Export Approval",
        )
        await session.commit()
        await service.create_roadmap_item(
            project_id=project_id,
            payload=RoadmapItemCreate(approval_type_id=approval.id, notes="Prepare export"),
        )
        await session.commit()

    response = await app_client.get(
        f"/api/v1/entitlements/export/{project_id}?fmt=pdf",
        headers={"X-User-Roles": "viewer"},
    )
    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("text/html")
    assert response.headers.get("X-Export-Fallback") == "html"

    metrics_response = await app_client.get("/health/metrics")
    assert 'entitlements_exports_total{format="html",fallback="yes"}' in metrics_response.text
