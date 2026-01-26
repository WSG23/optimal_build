"""Advanced intelligence analytics endpoints."""

from __future__ import annotations

from typing import Any

import structlog
from backend._compat.datetime import utcnow  # noqa: I001
from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import require_viewer
from app.services.advanced_intelligence_provider import (
    AdvancedIntelligenceProviderError,
    get_advanced_intelligence_provider,
)

router = APIRouter(prefix="/analytics/intelligence", tags=["advanced-intelligence"])
logger = structlog.get_logger()


def _timestamp() -> str:
    """Return an ISO-formatted timestamp for generated responses."""

    return utcnow().isoformat(timespec="seconds") + "Z"


def _error_payload(kind: str, message: str) -> dict[str, Any]:
    return {"kind": kind, "status": "error", "error": message}


def _normalize_graph_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("kind") == "graph" and payload.get("status"):
        return payload
    if payload.get("status") == "empty":
        return {"kind": "graph", "status": "empty", "summary": payload.get("summary")}
    graph = payload.get("graph")
    if isinstance(graph, dict):
        nodes = graph.get("nodes") or []
        edges = graph.get("edges") or []
        if not isinstance(nodes, list) or not isinstance(edges, list):
            return _error_payload("graph", "Invalid graph payload from provider.")
        return {
            "kind": "graph",
            "status": "ok",
            "summary": str(payload.get("summary", "")),
            "generatedAt": payload.get("generatedAt") or _timestamp(),
            "graph": {"nodes": nodes, "edges": edges},
        }
    return _error_payload("graph", "Advanced intelligence payload missing graph data.")


def _normalize_predictive_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("kind") == "predictive" and payload.get("status"):
        return payload
    if payload.get("status") == "empty":
        return {
            "kind": "predictive",
            "status": "empty",
            "summary": payload.get("summary"),
        }
    segments = payload.get("segments") or []
    if not isinstance(segments, list):
        return _error_payload("predictive", "Invalid predictive payload from provider.")
    horizon = payload.get("horizonMonths") or payload.get("horizon_months") or 0
    return {
        "kind": "predictive",
        "status": "ok",
        "summary": str(payload.get("summary", "")),
        "generatedAt": payload.get("generatedAt") or _timestamp(),
        "horizonMonths": int(horizon) if horizon is not None else 0,
        "segments": segments,
    }


def _normalize_correlation_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("kind") == "correlation" and payload.get("status"):
        return payload
    if payload.get("status") == "empty":
        return {
            "kind": "correlation",
            "status": "empty",
            "summary": payload.get("summary"),
        }
    relationships = payload.get("relationships") or []
    if not isinstance(relationships, list):
        return _error_payload(
            "correlation", "Invalid correlation payload from provider."
        )
    return {
        "kind": "correlation",
        "status": "ok",
        "summary": str(payload.get("summary", "")),
        "updatedAt": payload.get("updatedAt") or _timestamp(),
        "relationships": relationships,
    }


@router.get("/graph")
async def graph_intelligence(
    workspace_id: str = Query(..., alias="workspaceId"),
    _: str = Depends(require_viewer),
) -> dict[str, Any]:
    """Return relationship intelligence for the requested workspace."""

    try:
        provider = get_advanced_intelligence_provider()
        payload = await provider.fetch_graph(workspace_id)
        return _normalize_graph_payload(payload)
    except AdvancedIntelligenceProviderError as exc:
        logger.warning("advanced_intelligence.graph_unavailable", error=str(exc))
        raise HTTPException(status_code=503, detail=str(exc)) from exc


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
    """Return predictive analytics for the requested workspace."""

    if query:
        from app.services.intelligence import intelligence_service

        answer = intelligence_service.query_agent(query)
        return {
            "kind": "predictive",
            "status": "ok",
            "summary": answer,
            "generatedAt": _timestamp(),
            "horizonMonths": 0,
            "segments": [],
        }

    try:
        provider = get_advanced_intelligence_provider()
        payload = await provider.fetch_predictive(workspace_id)
        return _normalize_predictive_payload(payload)
    except AdvancedIntelligenceProviderError as exc:
        logger.warning("advanced_intelligence.predictive_unavailable", error=str(exc))
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/cross-correlation")
async def cross_correlation_intelligence(
    workspace_id: str = Query(..., alias="workspaceId"),
    _: str = Depends(require_viewer),
) -> dict[str, Any]:
    """Return cross-correlation analytics for the requested workspace."""

    try:
        provider = get_advanced_intelligence_provider()
        payload = await provider.fetch_correlation(workspace_id)
        return _normalize_correlation_payload(payload)
    except AdvancedIntelligenceProviderError as exc:
        logger.warning("advanced_intelligence.correlation_unavailable", error=str(exc))
        raise HTTPException(status_code=503, detail=str(exc)) from exc
