"""Investigation analytics endpoints for the advanced intelligence UI."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from app.api.deps import require_viewer

router = APIRouter(prefix="/analytics/intelligence", tags=["advanced-intelligence"])


def _empty_graph_payload(_: str) -> dict[str, Any]:
    return {
        "kind": "graph",
        "status": "empty",
        "summary": ("No investigation graph is available for this workspace yet."),
    }


def _empty_predictive_payload(_: str) -> dict[str, Any]:
    return {
        "kind": "predictive",
        "status": "empty",
        "summary": ("No predictive analytics are available for this workspace yet."),
    }


def _empty_correlation_payload(_: str) -> dict[str, Any]:
    return {
        "kind": "correlation",
        "status": "empty",
        "summary": (
            "No cross-correlation signals are available for this workspace yet."
        ),
    }


@router.get("/graph")
async def graph_intelligence(
    workspace_id: str = Query(..., alias="workspaceId"),
    _: str = Depends(require_viewer),
) -> dict[str, Any]:
    """Return relationship intelligence for the requested workspace."""

    return _empty_graph_payload(workspace_id)


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
    workspace_id: str = Query(..., alias="workspaceId"),
    query: str = Query(None, description="Optional natural language query"),
    _: str = Depends(require_viewer),
) -> dict[str, Any]:
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

    return _empty_predictive_payload(workspace_id)


@router.get("/cross-correlation")
async def cross_correlation_intelligence(
    workspace_id: str = Query(..., alias="workspaceId"),
    _: str = Depends(require_viewer),
) -> dict[str, Any]:
    """Return cross-correlation analytics for the requested workspace."""

    return _empty_correlation_payload(workspace_id)
