"""Persistence helpers for Advanced Intelligence snapshots."""

from __future__ import annotations

from typing import Any, Callable, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.advanced_intelligence import (
    WorkspaceCorrelationSnapshot,
    WorkspaceGraphSnapshot,
    WorkspacePredictiveSnapshot,
    WorkspaceSignalSnapshot,
)
from app.schemas.advanced_intelligence import (
    CrossCorrelationIntelligenceResponse,
    GraphIntelligenceResponse,
    PredictiveIntelligenceResponse,
    WorkspaceSignalsResponse,
    parse_correlation_response,
    parse_graph_response,
    parse_predictive_response,
    parse_signals_response,
)

SnapshotModel = TypeVar(
    "SnapshotModel",
    WorkspaceGraphSnapshot,
    WorkspacePredictiveSnapshot,
    WorkspaceCorrelationSnapshot,
    WorkspaceSignalSnapshot,
)


def _empty_graph_payload(workspace_id: str) -> dict[str, Any]:
    return {
        "kind": "graph",
        "status": "empty",
        "summary": (
            f"No investigation graph is available for workspace '{workspace_id}' yet."
        ),
    }


def _empty_predictive_payload(workspace_id: str) -> dict[str, Any]:
    return {
        "kind": "predictive",
        "status": "empty",
        "summary": (
            "No predictive analytics are available for "
            f"workspace '{workspace_id}' yet."
        ),
    }


def _empty_correlation_payload(workspace_id: str) -> dict[str, Any]:
    return {
        "kind": "correlation",
        "status": "empty",
        "summary": (
            "No cross-correlation signals are available for "
            f"workspace '{workspace_id}' yet."
        ),
    }


def _empty_signals_payload(workspace_id: str) -> dict[str, Any]:
    return {
        "kind": "signals",
        "status": "empty",
        "summary": f"No workspace signal snapshots are available for '{workspace_id}' yet.",
    }


class WorkspaceAnalyticsSnapshotService:
    """Read and write persisted analytics snapshots for a workspace."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_graph_snapshot(self, workspace_id: str) -> GraphIntelligenceResponse:
        snapshot = await self._get_or_create_snapshot(
            WorkspaceGraphSnapshot,
            workspace_id,
            payload_factory=_empty_graph_payload,
        )
        return parse_graph_response(snapshot.payload_json)

    async def get_predictive_snapshot(
        self, workspace_id: str
    ) -> PredictiveIntelligenceResponse:
        snapshot = await self._get_or_create_snapshot(
            WorkspacePredictiveSnapshot,
            workspace_id,
            payload_factory=_empty_predictive_payload,
        )
        return parse_predictive_response(snapshot.payload_json)

    async def get_correlation_snapshot(
        self, workspace_id: str
    ) -> CrossCorrelationIntelligenceResponse:
        snapshot = await self._get_or_create_snapshot(
            WorkspaceCorrelationSnapshot,
            workspace_id,
            payload_factory=_empty_correlation_payload,
        )
        return parse_correlation_response(snapshot.payload_json)

    async def get_signal_snapshot(self, workspace_id: str) -> WorkspaceSignalsResponse:
        snapshot = await self._get_or_create_snapshot(
            WorkspaceSignalSnapshot,
            workspace_id,
            payload_factory=_empty_signals_payload,
        )
        return parse_signals_response(snapshot.payload_json)

    async def save_graph_snapshot(
        self,
        workspace_id: str,
        *,
        payload: dict[str, Any],
        sample_size: int,
        version: int = 1,
    ) -> WorkspaceGraphSnapshot:
        return await self._save_snapshot(
            WorkspaceGraphSnapshot,
            workspace_id,
            payload=payload,
            sample_size=sample_size,
            version=version,
        )

    async def save_predictive_snapshot(
        self,
        workspace_id: str,
        *,
        payload: dict[str, Any],
        sample_size: int,
        version: int = 1,
    ) -> WorkspacePredictiveSnapshot:
        return await self._save_snapshot(
            WorkspacePredictiveSnapshot,
            workspace_id,
            payload=payload,
            sample_size=sample_size,
            version=version,
        )

    async def save_correlation_snapshot(
        self,
        workspace_id: str,
        *,
        payload: dict[str, Any],
        sample_size: int,
        version: int = 1,
    ) -> WorkspaceCorrelationSnapshot:
        return await self._save_snapshot(
            WorkspaceCorrelationSnapshot,
            workspace_id,
            payload=payload,
            sample_size=sample_size,
            version=version,
        )

    async def save_signal_snapshot(
        self,
        workspace_id: str,
        *,
        payload: dict[str, Any],
        sample_size: int,
        version: int = 1,
    ) -> WorkspaceSignalSnapshot:
        return await self._save_snapshot(
            WorkspaceSignalSnapshot,
            workspace_id,
            payload=payload,
            sample_size=sample_size,
            version=version,
        )

    async def _get_or_create_snapshot(
        self,
        model: type[SnapshotModel],
        workspace_id: str,
        *,
        payload_factory: Callable[[str], dict[str, Any]],
    ) -> SnapshotModel:
        snapshot = await self._get_snapshot(model, workspace_id)
        if snapshot is not None:
            return snapshot

        payload = payload_factory(workspace_id)
        snapshot = model(
            workspace_id=workspace_id,
            sample_size=0,
            status=payload["status"],
            summary=payload.get("summary", ""),
            payload_json=payload,
            version=1,
        )
        self._session.add(snapshot)
        await self._session.commit()
        await self._session.refresh(snapshot)
        return snapshot

    async def _save_snapshot(
        self,
        model: type[SnapshotModel],
        workspace_id: str,
        *,
        payload: dict[str, Any],
        sample_size: int,
        version: int,
    ) -> SnapshotModel:
        snapshot = await self._get_snapshot(model, workspace_id)
        if snapshot is None:
            snapshot = model(
                workspace_id=workspace_id,
                sample_size=sample_size,
                status=payload["status"],
                summary=payload.get("summary", ""),
                payload_json=payload,
                version=version,
            )
            self._session.add(snapshot)
        else:
            snapshot.sample_size = sample_size
            snapshot.status = payload["status"]
            snapshot.summary = payload.get("summary", "")
            snapshot.payload_json = payload
            snapshot.version = version

        await self._session.commit()
        await self._session.refresh(snapshot)
        return snapshot

    async def _get_snapshot(
        self,
        model: type[SnapshotModel],
        workspace_id: str,
    ) -> SnapshotModel | None:
        result = await self._session.execute(
            select(model).where(model.workspace_id == workspace_id)
        )
        return result.scalar_one_or_none()


__all__ = ["WorkspaceAnalyticsSnapshotService"]
