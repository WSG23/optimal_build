"""Stubbed investigation analytics endpoints for the advanced intelligence UI."""

from __future__ import annotations

from typing import Any

from backend._compat.datetime import utcnow  # noqa: I001
from fastapi import APIRouter, Depends, Query

from app.api.deps import require_viewer

router = APIRouter(prefix="/analytics/intelligence", tags=["advanced-intelligence"])


def _timestamp() -> str:
    """Return an ISO-formatted timestamp used by the dummy payloads."""

    return utcnow().isoformat(timespec="seconds") + "Z"


def _sample_graph_payload(_: str) -> dict[str, Any]:
    generated_at = _timestamp()
    return {
        "kind": "graph",
        "status": "ok",
        "summary": (
            "Collaboration graph derived from recent investigations. Lead Operations, "
            "Capital Stack Review, and Legal Counsel show the highest co-occurrence."
        ),
        "generatedAt": generated_at,
        "graph": {
            "nodes": [
                {
                    "id": "lead_ops",
                    "label": "Lead Operations",
                    "category": "team",
                    "score": 0.92,
                },
                {
                    "id": "capital_stack",
                    "label": "Capital Stack Review",
                    "category": "workflow",
                    "score": 0.87,
                },
                {
                    "id": "feasibility",
                    "label": "Feasibility Analysis",
                    "category": "workflow",
                    "score": 0.81,
                },
                {
                    "id": "legal",
                    "label": "Legal Counsel",
                    "category": "partner",
                    "score": 0.76,
                },
                {
                    "id": "compliance",
                    "label": "Compliance Ops",
                    "category": "team",
                    "score": 0.7,
                },
            ],
            "edges": [
                {
                    "id": "lead_ops-capital_stack",
                    "source": "lead_ops",
                    "target": "capital_stack",
                    "weight": 0.8,
                },
                {
                    "id": "lead_ops-feasibility",
                    "source": "lead_ops",
                    "target": "feasibility",
                    "weight": 0.7,
                },
                {
                    "id": "capital_stack-legal",
                    "source": "capital_stack",
                    "target": "legal",
                    "weight": 0.6,
                },
                {
                    "id": "feasibility-compliance",
                    "source": "feasibility",
                    "target": "compliance",
                    "weight": 0.5,
                },
                {
                    "id": "legal-compliance",
                    "source": "legal",
                    "target": "compliance",
                    "weight": 0.4,
                },
            ],
        },
    }


def _sample_predictive_payload(_: str) -> dict[str, Any]:
    generated_at = _timestamp()
    return {
        "kind": "predictive",
        "status": "ok",
        "summary": (
            "Predictive models highlight adoption gains when capital alignment and early "
            "legal review occur within the first two phases."
        ),
        "generatedAt": generated_at,
        "horizonMonths": 6,
        "segments": [
            {
                "segmentId": "ops-champions",
                "segmentName": "Operations champions",
                "baseline": 120,
                "projection": 168,
                "probability": 0.74,
            },
            {
                "segmentId": "compliance-fastlane",
                "segmentName": "Compliance fast-lane",
                "baseline": 90,
                "projection": 135,
                "probability": 0.68,
            },
            {
                "segmentId": "legal-momentum",
                "segmentName": "Early legal engagement",
                "baseline": 75,
                "projection": 108,
                "probability": 0.62,
            },
        ],
    }


def _sample_correlation_payload(_: str) -> dict[str, Any]:
    updated_at = _timestamp()
    return {
        "kind": "correlation",
        "status": "ok",
        "summary": (
            "Cross correlations show finance readiness and legal cycle time as the key drivers "
            "for overall approval speed, while logistics planning reduces schedule risk."
        ),
        "updatedAt": updated_at,
        "relationships": [
            {
                "pairId": "finance-readiness_approval-speed",
                "driver": "Finance readiness score",
                "outcome": "Approval speed (days)",
                "coefficient": 0.68,
                "pValue": 0.012,
            },
            {
                "pairId": "legal-latency_iteration-count",
                "driver": "Legal review latency",
                "outcome": "Iteration count",
                "coefficient": -0.54,
                "pValue": 0.025,
            },
            {
                "pairId": "capital-stack_alignment",
                "driver": "Capital stack completeness",
                "outcome": "Stakeholder alignment index",
                "coefficient": 0.49,
                "pValue": 0.041,
            },
            {
                "pairId": "logistics_schedule-risk",
                "driver": "Site logistics score",
                "outcome": "Schedule risk",
                "coefficient": -0.37,
                "pValue": 0.09,
            },
        ],
    }


@router.get("/graph")
async def graph_intelligence(
    workspace_id: str = Query(..., alias="workspaceId"),
    _: str = Depends(require_viewer),
) -> dict[str, Any]:
    """Return stubbed relationship intelligence for the requested workspace."""

    return _sample_graph_payload(workspace_id)


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
            "generatedAt": _timestamp(),
            # Keep stubs for UI compatibility
            "horizonMonths": 6,
            "segments": [],
        }

    # Fallback to stub if no query
    return _sample_predictive_payload(workspace_id)


@router.get("/cross-correlation")
async def cross_correlation_intelligence(
    workspace_id: str = Query(..., alias="workspaceId"),
    _: str = Depends(require_viewer),
) -> dict[str, Any]:
    """Return stubbed cross-correlation analytics for the requested workspace."""

    return _sample_correlation_payload(workspace_id)
