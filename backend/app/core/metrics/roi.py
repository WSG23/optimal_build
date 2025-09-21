"""ROI metric computations for CAD automation workflows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import math
from typing import Iterable, Mapping

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import ProjectAuditLog
from app.models.overlay import OverlayDecision


@dataclass(slots=True)
class RoiSnapshot:
    """Container for derived ROI metrics."""

    project_id: int
    iterations: int
    approvals: int
    total_decisions: int
    acceptance_rate: float
    automation_score: float
    savings_percent: float
    review_hours_saved: float
    payback_weeks: int
    baseline_hours: float
    automated_hours: float
    event_count: int
    last_event_at: datetime | None

    def to_payload(self) -> Mapping[str, object]:
        """Serialize the snapshot for API responses."""

        return {
            "project_id": self.project_id,
            "iterations": self.iterations,
            "approvals": self.approvals,
            "total_decisions": self.total_decisions,
            "acceptance_rate": round(self.acceptance_rate, 4),
            "automation_score": round(self.automation_score, 4),
            "savings_percent": round(self.savings_percent, 2),
            "review_hours_saved": round(self.review_hours_saved, 2),
            "payback_weeks": self.payback_weeks,
            "baseline_hours": round(self.baseline_hours, 2),
            "automated_hours": round(self.automated_hours, 2),
            "event_count": self.event_count,
            "last_event_at": self.last_event_at.isoformat() if self.last_event_at else None,
        }


def _sum(values: Iterable[int | float | None]) -> float:
    total = 0.0
    for value in values:
        if value is None:
            continue
        total += float(value)
    return total


async def compute_project_roi(session: AsyncSession, project_id: int) -> RoiSnapshot:
    """Aggregate audit logs and overlay decisions into ROI metrics."""

    approval_case = case((OverlayDecision.decision == "approved", 1), else_=0)
    counts_result = await session.execute(
        select(
            func.count(OverlayDecision.id),
            func.coalesce(func.sum(approval_case), 0),
        ).where(OverlayDecision.project_id == project_id)
    )
    total_decisions, approvals = counts_result.one()
    total_decisions = int(total_decisions or 0)
    approvals = int(approvals or 0)

    audit_rows = (
        await session.execute(
            select(ProjectAuditLog)
            .where(ProjectAuditLog.project_id == project_id)
            .order_by(ProjectAuditLog.created_at)
        )
    ).scalars().all()

    baseline_seconds = _sum(log.baseline_seconds for log in audit_rows)
    automated_seconds = _sum(log.automated_seconds for log in audit_rows)
    time_saved_seconds = max(0.0, baseline_seconds - automated_seconds)

    baseline_hours = baseline_seconds / 3600.0
    automated_hours = automated_seconds / 3600.0
    review_hours_saved = time_saved_seconds / 3600.0

    acceptance_rate = approvals / total_decisions if total_decisions else 0.0
    savings_ratio = time_saved_seconds / baseline_seconds if baseline_seconds else 0.0

    automation_score = min(1.0, (acceptance_rate * 0.6) + (savings_ratio * 0.4))
    savings_percent = savings_ratio * 100.0

    if review_hours_saved <= 0:
        payback_weeks = 0
    else:
        payback_weeks = max(1, math.ceil(40.0 / review_hours_saved))

    last_event_at = max((log.created_at for log in audit_rows if log.created_at), default=None)

    iterations = sum(1 for log in audit_rows if log.event_type.startswith("overlay_"))
    event_count = len(audit_rows)

    return RoiSnapshot(
        project_id=project_id,
        iterations=iterations,
        approvals=approvals,
        total_decisions=total_decisions,
        acceptance_rate=acceptance_rate,
        automation_score=automation_score,
        savings_percent=savings_percent,
        review_hours_saved=review_hours_saved,
        payback_weeks=payback_weeks,
        baseline_hours=baseline_hours,
        automated_hours=automated_hours,
        event_count=event_count,
        last_event_at=last_event_at,
    )


__all__ = ["RoiSnapshot", "compute_project_roi"]
