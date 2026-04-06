"""Investigation analytics endpoints for the advanced intelligence UI."""

from __future__ import annotations

from typing import Any, cast

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequestIdentity, get_db, require_viewer
from app.schemas.advanced_intelligence import (
    CrossCorrelationIntelligenceResponse,
    GraphIntelligenceResponse,
    PredictiveIntelligenceResponse,
    WorkspaceSignalsResponse,
)
from app.services.analytics import (
    ProjectAnalyticsSnapshotRefresher,
    WorkspaceAnalyticsSnapshotService,
    resolve_analytics_scope,
)

router = APIRouter(prefix="/analytics/intelligence", tags=["advanced-intelligence"])


async def _ensure_project_snapshots(
    db: AsyncSession,
    *,
    project_id: str | None,
    workspace_id: str,
    snapshot_kind: str,
) -> None:
    if not project_id:
        return
    refresher = ProjectAnalyticsSnapshotRefresher(db)
    await refresher.ensure_project_snapshots(
        project_id=project_id,
        workspace_id=workspace_id,
        snapshot_kind=snapshot_kind,
    )


@router.get("/graph", response_model=GraphIntelligenceResponse)
async def graph_intelligence(
    project_id: str | None = Query(None, alias="projectId"),
    workspace_id: str | None = Query(None, alias="workspaceId"),
    _: RequestIdentity = Depends(require_viewer),
    db: AsyncSession = Depends(get_db),
) -> GraphIntelligenceResponse:
    """Return relationship intelligence for the requested workspace."""

    scope = await resolve_analytics_scope(
        db,
        project_id=project_id,
        workspace_id=workspace_id,
    )
    await _ensure_project_snapshots(
        db,
        project_id=scope.project_id,
        workspace_id=scope.scope_id,
        snapshot_kind="graph",
    )
    service = WorkspaceAnalyticsSnapshotService(db)
    payload = await service.get_graph_snapshot(scope.scope_id)
    return cast(GraphIntelligenceResponse, payload)


@router.post("/ingest")
async def ingest_knowledge(
    text: str = Query(..., description="Text content to ingest"),
    source: str = Query(..., description="Source identifier"),
    _: str = Depends(require_viewer),
) -> dict[str, Any]:
    """Ingest new knowledge into the RAG engine."""
    from app.services.intelligence import intelligence_service

    success = intelligence_service.ingest_text(text, source)
    return {
        "status": "ok" if success else "error",
        "message": (
            "Ingested successfully" if success else "Failed to ingest (check logs)"
        ),
    }


@router.get("/predictive")
async def predictive_intelligence(
    project_id: str | None = Query(None, alias="projectId"),
    workspace_id: str | None = Query(None, alias="workspaceId"),
    query: str | None = Query(None, description="Optional natural language query"),
    _: RequestIdentity = Depends(require_viewer),
    db: AsyncSession = Depends(get_db),
) -> PredictiveIntelligenceResponse | dict[str, object]:
    """Return predictive analytics. If 'query' is provided, uses RAG agent."""

    if query:
        from app.services.intelligence import intelligence_service

        # Use Real AI
        answer = intelligence_service.query_agent(query)

        return {
            "kind": "predictive_agent",
            "status": "ok",
            "summary": answer,
            # Keep stubs for UI compatibility
            "horizonMonths": 6,
            "segments": [],
        }

    scope = await resolve_analytics_scope(
        db,
        project_id=project_id,
        workspace_id=workspace_id,
    )
    await _ensure_project_snapshots(
        db,
        project_id=scope.project_id,
        workspace_id=scope.scope_id,
        snapshot_kind="predictive",
    )
    service = WorkspaceAnalyticsSnapshotService(db)
    payload = await service.get_predictive_snapshot(scope.scope_id)
    return cast(PredictiveIntelligenceResponse, payload)


@router.get(
    "/cross-correlation",
    response_model=CrossCorrelationIntelligenceResponse,
)
async def cross_correlation_intelligence(
    project_id: str | None = Query(None, alias="projectId"),
    workspace_id: str | None = Query(None, alias="workspaceId"),
    _: RequestIdentity = Depends(require_viewer),
    db: AsyncSession = Depends(get_db),
) -> CrossCorrelationIntelligenceResponse:
    """Return cross-correlation analytics for the requested workspace."""

    scope = await resolve_analytics_scope(
        db,
        project_id=project_id,
        workspace_id=workspace_id,
    )
    await _ensure_project_snapshots(
        db,
        project_id=scope.project_id,
        workspace_id=scope.scope_id,
        snapshot_kind="correlation",
    )
    service = WorkspaceAnalyticsSnapshotService(db)
    payload = await service.get_correlation_snapshot(scope.scope_id)
    return cast(CrossCorrelationIntelligenceResponse, payload)


@router.get("/signals", response_model=WorkspaceSignalsResponse)
async def workspace_signals(
    project_id: str | None = Query(None, alias="projectId"),
    workspace_id: str | None = Query(None, alias="workspaceId"),
    _: RequestIdentity = Depends(require_viewer),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceSignalsResponse:
    """Return KPI signal cards for the requested project scope."""

    scope = await resolve_analytics_scope(
        db,
        project_id=project_id,
        workspace_id=workspace_id,
    )
    await _ensure_project_snapshots(
        db,
        project_id=scope.project_id,
        workspace_id=scope.scope_id,
        snapshot_kind="signals",
    )
    service = WorkspaceAnalyticsSnapshotService(db)
    payload = await service.get_signal_snapshot(scope.scope_id)
    return cast(WorkspaceSignalsResponse, payload)
