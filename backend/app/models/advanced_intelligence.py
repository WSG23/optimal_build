"""Persisted snapshot models for Advanced Intelligence analytics."""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar
from uuid import uuid4

from app.models.base import UUID, BaseModel
from app.models.types import FlexibleJSONB
from sqlalchemy import DateTime, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, declared_attr, mapped_column
from sqlalchemy.sql import func

JSONType = FlexibleJSONB


class _WorkspaceSnapshotBase(BaseModel):
    """Shared fields for persisted workspace analytics snapshots."""

    __abstract__ = True

    id: Mapped[str] = mapped_column(
        UUID(), primary_key=True, default=lambda: str(uuid4())
    )
    workspace_id: Mapped[str] = mapped_column(String(255), nullable=False)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="empty")
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    payload_json: Mapped[dict] = mapped_column("payload_json", JSONType, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    _unique_name: ClassVar[str]
    _workspace_index_name: ClassVar[str]

    @declared_attr.directive
    def __table_args__(cls) -> tuple[object, ...]:
        return (
            UniqueConstraint("workspace_id", name=cls._unique_name),
            Index(cls._workspace_index_name, "workspace_id"),
            {"extend_existing": True},
        )


class WorkspaceGraphSnapshot(_WorkspaceSnapshotBase):
    """Stored relationship intelligence payload for a workspace."""

    __tablename__ = "workspace_graph_snapshots"
    _unique_name = "uq_workspace_graph_snapshots_workspace_id"
    _workspace_index_name = "ix_workspace_graph_snapshots_workspace_id"


class WorkspacePredictiveSnapshot(_WorkspaceSnapshotBase):
    """Stored predictive intelligence payload for a workspace."""

    __tablename__ = "workspace_predictive_snapshots"
    _unique_name = "uq_workspace_predictive_snapshots_workspace_id"
    _workspace_index_name = "ix_workspace_predictive_snapshots_workspace_id"


class WorkspaceCorrelationSnapshot(_WorkspaceSnapshotBase):
    """Stored cross-correlation payload for a workspace."""

    __tablename__ = "workspace_correlation_snapshots"
    _unique_name = "uq_workspace_correlation_snapshots_workspace_id"
    _workspace_index_name = "ix_workspace_correlation_snapshots_workspace_id"


class WorkspaceSignalSnapshot(_WorkspaceSnapshotBase):
    """Stored KPI and trend payload for a workspace."""

    __tablename__ = "workspace_signal_snapshots"
    _unique_name = "uq_workspace_signal_snapshots_workspace_id"
    _workspace_index_name = "ix_workspace_signal_snapshots_workspace_id"


__all__ = [
    "WorkspaceGraphSnapshot",
    "WorkspacePredictiveSnapshot",
    "WorkspaceCorrelationSnapshot",
    "WorkspaceSignalSnapshot",
]
