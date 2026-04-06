from __future__ import annotations

import uuid
from datetime import timedelta
from decimal import Decimal

import pytest
from backend._compat.datetime import utcnow
from sqlalchemy import select

from app.models.advanced_intelligence import (
    WorkspaceCorrelationSnapshot,
    WorkspaceGraphSnapshot,
    WorkspacePredictiveSnapshot,
    WorkspaceSignalSnapshot,
)
from app.models.finance import FinCapitalStack, FinProject, FinResult, FinScenario
from app.models.projects import Project, ProjectPhase, ProjectType
from app.models.users import User
from app.models.workflow import (
    ApprovalStep,
    ApprovalWorkflow,
    StepStatus,
    WorkflowStatus,
)
from app.services.analytics import WorkspaceAnalyticsSnapshotService
from app.services.intelligence import intelligence_service


async def _create_project(db_session) -> str:
    project_id = str(uuid.uuid4())
    project = Project(
        id=project_id,
        project_name="Analytics Project",
        project_code=f"AN-{project_id[:8]}",
        project_type=ProjectType.NEW_DEVELOPMENT,
        current_phase=ProjectPhase.APPROVAL,
        owner_email="analytics-owner@example.com",
        completion_percentage=Decimal("42.5"),
    )
    db_session.add(project)
    await db_session.commit()
    return project_id


async def _create_user(db_session) -> User:
    user = User(
        id=uuid.uuid4(),
        email=f"creator-{uuid.uuid4()}@example.com",
        username=f"creator_{uuid.uuid4().hex[:8]}",
        full_name="Analytics Creator",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _seed_live_analytics_inputs(db_session, project_id: str) -> None:
    creator = await _create_user(db_session)
    now = utcnow()

    workflows = [
        ApprovalWorkflow(
            id=uuid.uuid4(),
            project_id=project_id,
            title="Feasibility Sign-off",
            description="Initial feasibility review",
            workflow_type="feasibility_signoff",
            status=WorkflowStatus.IN_PROGRESS,
            created_by_id=creator.id,
            created_at=now - timedelta(days=21),
            updated_at=now - timedelta(days=2),
        ),
        ApprovalWorkflow(
            id=uuid.uuid4(),
            project_id=project_id,
            title="Design Review",
            description="Architectural review",
            workflow_type="design_review",
            status=WorkflowStatus.IN_PROGRESS,
            created_by_id=creator.id,
            created_at=now - timedelta(days=12),
            updated_at=now - timedelta(days=1),
        ),
        ApprovalWorkflow(
            id=uuid.uuid4(),
            project_id=project_id,
            title="Authority Submission",
            description="Regulatory submission pack",
            workflow_type="authority_submission",
            status=WorkflowStatus.DRAFT,
            created_by_id=creator.id,
            created_at=now - timedelta(days=4),
            updated_at=now - timedelta(hours=8),
        ),
    ]
    db_session.add_all(workflows)
    await db_session.commit()

    steps = [
        ApprovalStep(
            id=uuid.uuid4(),
            workflow_id=workflows[0].id,
            name="Model review",
            sequence_order=1,
            required_role="developer",
            status=StepStatus.APPROVED,
        ),
        ApprovalStep(
            id=uuid.uuid4(),
            workflow_id=workflows[0].id,
            name="Cost review",
            sequence_order=2,
            required_role="developer",
            status=StepStatus.APPROVED,
        ),
        ApprovalStep(
            id=uuid.uuid4(),
            workflow_id=workflows[0].id,
            name="Executive approval",
            sequence_order=3,
            required_role="reviewer",
            status=StepStatus.IN_REVIEW,
        ),
        ApprovalStep(
            id=uuid.uuid4(),
            workflow_id=workflows[1].id,
            name="Architect markup",
            sequence_order=1,
            required_role="developer",
            status=StepStatus.APPROVED,
        ),
        ApprovalStep(
            id=uuid.uuid4(),
            workflow_id=workflows[1].id,
            name="MEP coordination",
            sequence_order=2,
            required_role="developer",
            status=StepStatus.PENDING,
        ),
        ApprovalStep(
            id=uuid.uuid4(),
            workflow_id=workflows[2].id,
            name="Submission checklist",
            sequence_order=1,
            required_role="reviewer",
            status=StepStatus.PENDING,
        ),
        ApprovalStep(
            id=uuid.uuid4(),
            workflow_id=workflows[2].id,
            name="Pack assembly",
            sequence_order=2,
            required_role="developer",
            status=StepStatus.PENDING,
        ),
        ApprovalStep(
            id=uuid.uuid4(),
            workflow_id=workflows[2].id,
            name="Final sign-off",
            sequence_order=3,
            required_role="reviewer",
            status=StepStatus.PENDING,
        ),
        ApprovalStep(
            id=uuid.uuid4(),
            workflow_id=workflows[2].id,
            name="Release",
            sequence_order=4,
            required_role="reviewer",
            status=StepStatus.PENDING,
        ),
    ]
    db_session.add_all(steps)

    fin_project = FinProject(
        project_id=project_id,
        name="Analytics Finance",
        total_development_cost=Decimal("24000000"),
    )
    db_session.add(fin_project)
    await db_session.commit()
    await db_session.refresh(fin_project)

    scenarios = [
        FinScenario(
            project_id=project_id,
            fin_project_id=fin_project.id,
            name="Base Case",
            is_primary=True,
            assumptions={"leasing_velocity": 0.85},
            ltv_limit_pct=Decimal("0.55"),
            construction_loan_rate_pct=Decimal("0.0425"),
            created_at=now - timedelta(days=18),
            updated_at=now - timedelta(days=2),
        ),
        FinScenario(
            project_id=project_id,
            fin_project_id=fin_project.id,
            name="Upside Case",
            is_primary=False,
            assumptions={"leasing_velocity": 0.92},
            ltv_limit_pct=Decimal("0.62"),
            construction_loan_rate_pct=Decimal("0.0475"),
            created_at=now - timedelta(days=10),
            updated_at=now - timedelta(days=1),
        ),
        FinScenario(
            project_id=project_id,
            fin_project_id=fin_project.id,
            name="Defensive Case",
            is_primary=False,
            assumptions={"leasing_velocity": 0.78},
            ltv_limit_pct=Decimal("0.48"),
            construction_loan_rate_pct=Decimal("0.0395"),
            created_at=now - timedelta(days=5),
            updated_at=now - timedelta(hours=12),
        ),
    ]
    db_session.add_all(scenarios)
    await db_session.commit()
    for scenario in scenarios:
        await db_session.refresh(scenario)

    capital_stack_entries = [
        FinCapitalStack(
            project_id=project_id,
            scenario_id=scenarios[0].id,
            name="Senior debt",
            source_type="debt",
            amount=Decimal("12000000"),
        ),
        FinCapitalStack(
            project_id=project_id,
            scenario_id=scenarios[0].id,
            name="Sponsor equity",
            source_type="equity",
            amount=Decimal("8000000"),
        ),
        FinCapitalStack(
            project_id=project_id,
            scenario_id=scenarios[1].id,
            name="Senior debt",
            source_type="debt",
            amount=Decimal("15000000"),
        ),
        FinCapitalStack(
            project_id=project_id,
            scenario_id=scenarios[1].id,
            name="Sponsor equity",
            source_type="equity",
            amount=Decimal("6000000"),
        ),
        FinCapitalStack(
            project_id=project_id,
            scenario_id=scenarios[1].id,
            name="Mezzanine",
            source_type="mezzanine",
            amount=Decimal("2000000"),
        ),
        FinCapitalStack(
            project_id=project_id,
            scenario_id=scenarios[2].id,
            name="Senior debt",
            source_type="debt",
            amount=Decimal("10000000"),
        ),
    ]
    db_session.add_all(capital_stack_entries)

    results = [
        FinResult(
            project_id=project_id,
            scenario_id=scenarios[0].id,
            name="project_irr",
            value=Decimal("0.1380"),
            unit="ratio",
        ),
        FinResult(
            project_id=project_id,
            scenario_id=scenarios[1].id,
            name="project_irr",
            value=Decimal("0.1620"),
            unit="ratio",
        ),
        FinResult(
            project_id=project_id,
            scenario_id=scenarios[2].id,
            name="project_irr",
            value=Decimal("0.1110"),
            unit="ratio",
        ),
    ]
    db_session.add_all(results)
    await db_session.commit()


@pytest.mark.asyncio
async def test_graph_intelligence_persists_empty_snapshot(client, db_session):
    project_id = await _create_project(db_session)

    response = await client.get(
        "/api/v1/analytics/intelligence/graph",
        params={"projectId": project_id},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["kind"] == "graph"
    assert payload["status"] == "empty"
    assert "Add approval workflows or finance scenarios" in payload["summary"]

    snapshot = await db_session.scalar(
        select(WorkspaceGraphSnapshot).where(
            WorkspaceGraphSnapshot.workspace_id == f"project:{project_id}"
        )
    )
    assert snapshot is not None
    assert snapshot.status == "empty"
    assert snapshot.sample_size == 0
    assert snapshot.payload_json["kind"] == "graph"


@pytest.mark.asyncio
async def test_graph_intelligence_returns_persisted_snapshot(client, db_session):
    project_id = await _create_project(db_session)
    service = WorkspaceAnalyticsSnapshotService(db_session)
    await service.save_graph_snapshot(
        f"project:{project_id}",
        payload={
            "kind": "graph",
            "status": "ok",
            "summary": "Persisted relationship graph",
            "generatedAt": "2026-04-06T00:00:00Z",
            "graph": {
                "nodes": [
                    {
                        "id": "user-1",
                        "label": "Analyst",
                        "category": "Team",
                        "score": 0.8,
                    }
                ],
                "edges": [
                    {
                        "id": "edge-1",
                        "source": "user-1",
                        "target": "workflow-1",
                        "weight": 0.4,
                    }
                ],
            },
        },
        sample_size=5,
    )

    response = await client.get(
        "/api/v1/analytics/intelligence/graph",
        params={"projectId": project_id},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["graph"]["nodes"][0]["label"] == "Analyst"


@pytest.mark.asyncio
async def test_predictive_intelligence_persists_empty_snapshot_without_query(
    client, db_session
):
    project_id = await _create_project(db_session)
    response = await client.get(
        "/api/v1/analytics/intelligence/predictive",
        params={"projectId": project_id},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["kind"] == "predictive"
    assert payload["status"] == "empty"
    assert "Predictive signals need at least one workflow" in payload["summary"]

    snapshot = await db_session.scalar(
        select(WorkspacePredictiveSnapshot).where(
            WorkspacePredictiveSnapshot.workspace_id == f"project:{project_id}"
        )
    )
    assert snapshot is not None
    assert snapshot.status == "empty"
    assert snapshot.sample_size == 0


@pytest.mark.asyncio
async def test_predictive_intelligence_returns_persisted_snapshot(client, db_session):
    project_id = await _create_project(db_session)
    service = WorkspaceAnalyticsSnapshotService(db_session)
    await service.save_predictive_snapshot(
        f"project:{project_id}",
        payload={
            "kind": "predictive",
            "status": "ok",
            "summary": "Persisted predictive snapshot",
            "generatedAt": "2026-04-06T00:00:00Z",
            "horizonMonths": 6,
            "segments": [
                {
                    "segmentId": "seg-1",
                    "segmentName": "High fit",
                    "baseline": 10,
                    "projection": 14,
                    "probability": 0.7,
                }
            ],
        },
        sample_size=8,
    )

    response = await client.get(
        "/api/v1/analytics/intelligence/predictive",
        params={"projectId": project_id},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["segments"][0]["segmentName"] == "High fit"


@pytest.mark.asyncio
async def test_predictive_intelligence_query_path_still_returns_agent_payload(
    client, monkeypatch
):
    monkeypatch.setattr(
        intelligence_service,
        "query_agent",
        lambda query: f"Agent answer for {query}",
    )

    response = await client.get(
        "/api/v1/analytics/intelligence/predictive",
        params={"workspaceId": "ws-agent", "query": "status"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["kind"] == "predictive_agent"
    assert payload["status"] == "ok"
    assert payload["summary"] == "Agent answer for status"


@pytest.mark.asyncio
async def test_cross_correlation_intelligence_persists_empty_snapshot(
    client, db_session
):
    project_id = await _create_project(db_session)
    response = await client.get(
        "/api/v1/analytics/intelligence/cross-correlation",
        params={"projectId": project_id},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["kind"] == "correlation"
    assert payload["status"] == "empty"
    assert "Cross-correlation needs at least three varying" in payload["summary"]

    snapshot = await db_session.scalar(
        select(WorkspaceCorrelationSnapshot).where(
            WorkspaceCorrelationSnapshot.workspace_id == f"project:{project_id}"
        )
    )
    assert snapshot is not None
    assert snapshot.status == "empty"
    assert snapshot.sample_size == 0


@pytest.mark.asyncio
async def test_cross_correlation_intelligence_returns_persisted_snapshot(
    client, db_session
):
    project_id = await _create_project(db_session)
    service = WorkspaceAnalyticsSnapshotService(db_session)
    await service.save_correlation_snapshot(
        f"project:{project_id}",
        payload={
            "kind": "correlation",
            "status": "ok",
            "summary": "Persisted cross-correlation snapshot",
            "updatedAt": "2026-04-06T00:00:00Z",
            "relationships": [
                {
                    "pairId": "finance_speed",
                    "driver": "Finance readiness",
                    "outcome": "Approval speed",
                    "coefficient": 0.62,
                    "pValue": 0.03,
                }
            ],
        },
        sample_size=12,
    )

    response = await client.get(
        "/api/v1/analytics/intelligence/cross-correlation",
        params={"projectId": project_id},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["relationships"][0]["pairId"] == "finance_speed"


@pytest.mark.asyncio
async def test_workspace_signals_builds_live_snapshot(client, db_session):
    project_id = await _create_project(db_session)
    await _seed_live_analytics_inputs(db_session, project_id)

    response = await client.get(
        "/api/v1/analytics/intelligence/signals",
        params={"projectId": project_id},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["kind"] == "signals"
    assert payload["status"] == "ok"
    assert [signal["label"] for signal in payload["signals"]] == [
        "Approval Readiness",
        "Finance Coverage",
        "Active Workflows",
        "Intelligence Score",
    ]
    assert payload["signals"][0]["trend"]
    assert payload["signals"][1]["value"] > 0

    snapshot = await db_session.scalar(
        select(WorkspaceSignalSnapshot).where(
            WorkspaceSignalSnapshot.workspace_id == f"project:{project_id}"
        )
    )
    assert snapshot is not None
    assert snapshot.status == "ok"
    assert snapshot.sample_size == 6


@pytest.mark.asyncio
async def test_live_project_routes_return_real_project_analytics(client, db_session):
    project_id = await _create_project(db_session)
    await _seed_live_analytics_inputs(db_session, project_id)

    graph_response = await client.get(
        "/api/v1/analytics/intelligence/graph",
        params={"projectId": project_id},
    )
    predictive_response = await client.get(
        "/api/v1/analytics/intelligence/predictive",
        params={"projectId": project_id},
    )
    correlation_response = await client.get(
        "/api/v1/analytics/intelligence/cross-correlation",
        params={"projectId": project_id},
    )

    assert graph_response.status_code == 200
    graph_payload = graph_response.json()
    assert graph_payload["status"] == "ok"
    categories = {node["category"] for node in graph_payload["graph"]["nodes"]}
    assert {"Project", "Workflow", "Finance"} <= categories

    assert predictive_response.status_code == 200
    predictive_payload = predictive_response.json()
    assert predictive_payload["status"] == "ok"
    assert (
        predictive_payload["segments"][0]["segmentName"] == "Project delivery readiness"
    )
    assert any(
        segment["segmentName"] == "Base Case"
        for segment in predictive_payload["segments"]
    )

    assert correlation_response.status_code == 200
    correlation_payload = correlation_response.json()
    assert correlation_payload["status"] == "ok"
    assert any(
        relationship["pairId"] == "workflow-steps-completion"
        for relationship in correlation_payload["relationships"]
    )


@pytest.mark.asyncio
async def test_graph_intelligence_rejects_unknown_project(client):
    response = await client.get(
        "/api/v1/analytics/intelligence/graph",
        params={"projectId": str(uuid.uuid4())},
    )

    assert response.status_code == 404
