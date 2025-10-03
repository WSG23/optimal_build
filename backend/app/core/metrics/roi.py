"""Return-on-investment metric calculations for overlay workflows."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import datetime
from math import ceil

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend._compat import compat_dataclass
from backend._compat.datetime import UTC
from app.models.audit import AuditLog
from app.models.overlay import OverlaySuggestion

# Baseline timing assumptions (in seconds) used when estimating automation ROI.
# These constants are shared with the instrumentation hooks that populate the
# audit log so changes remain consistent across the stack.
OVERLAY_BASELINE_SECONDS = 30.0 * 60.0  # Manual overlay evaluation per geometry.
EXPORT_BASELINE_SECONDS = 20.0 * 60.0  # Manual export packaging effort.
DECISION_REVIEW_BASELINE_SECONDS = 15.0 * 60.0  # Manual overlay review per item.
PAYBACK_BASELINE_HOURS = 40.0  # Typical onboarding effort amortised in hours.


@compat_dataclass(slots=True)
class RoiSnapshot:
    """Aggregated ROI insights for a single project."""

    project_id: int
    iterations: int
    total_suggestions: int
    decided_suggestions: int
    accepted_suggestions: int
    acceptance_rate: float
    review_hours_saved: float
    automation_score: float
    savings_percent: int
    payback_weeks: int
    baseline_hours: float
    actual_hours: float

    def as_dict(self) -> dict[str, object]:
        """Serialise the snapshot for API responses."""

        return {
            "project_id": self.project_id,
            "iterations": self.iterations,
            "total_suggestions": self.total_suggestions,
            "decided_suggestions": self.decided_suggestions,
            "accepted_suggestions": self.accepted_suggestions,
            "acceptance_rate": self.acceptance_rate,
            "review_hours_saved": self.review_hours_saved,
            "automation_score": self.automation_score,
            "savings_percent": self.savings_percent,
            "payback_weeks": self.payback_weeks,
            "baseline_hours": self.baseline_hours,
            "actual_hours": self.actual_hours,
        }


def _as_utc(timestamp: datetime | None) -> datetime | None:
    """Normalise timestamps to timezone-aware UTC values."""

    if timestamp is None:
        return None
    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=UTC)
    return timestamp.astimezone(UTC)


def _decision_metrics(
    suggestions: Sequence[OverlaySuggestion],
) -> tuple[float, float, int, int, int]:
    """Compute decision timing, acceptance counts and totals."""

    decision_seconds = 0.0
    decided = 0
    accepted = 0
    total = len(suggestions)

    for suggestion in suggestions:
        decision = (suggestion.status or "").lower()
        is_decided = suggestion.decision is not None or decision not in {"", "pending"}
        if is_decided:
            decided += 1
            if decision == "approved":
                accepted += 1
            created_at = _as_utc(suggestion.created_at)
            decided_at = _as_utc(suggestion.decided_at or suggestion.updated_at)
            if created_at and decided_at:
                elapsed = (decided_at - created_at).total_seconds()
                decision_seconds += max(elapsed, 0.0)
            else:
                decision_seconds += DECISION_REVIEW_BASELINE_SECONDS / 2
    baseline_seconds = decided * DECISION_REVIEW_BASELINE_SECONDS
    return baseline_seconds, decision_seconds, total, decided, accepted


def _aggregate_audit_metrics(logs: Iterable[AuditLog]) -> tuple[float, float, int]:
    """Summarise baseline and actual timing information from audit logs."""

    baseline_seconds = 0.0
    actual_seconds = 0.0
    iterations = 0

    for log in logs:
        if log.event_type == "overlay_run":
            iterations += 1
        if log.event_type == "overlay_decision":
            # Decision timing is derived from suggestion timestamps to prevent
            # double-counting when aggregating audit logs.
            continue
        if log.baseline_seconds:
            baseline_seconds += float(log.baseline_seconds)
        if log.actual_seconds:
            actual_seconds += float(log.actual_seconds)
    return baseline_seconds, actual_seconds, iterations


async def compute_project_roi(session: AsyncSession, *, project_id: int) -> RoiSnapshot:
    """Calculate ROI metrics for the supplied project."""

    suggestion_stmt = (
        select(OverlaySuggestion)
        .where(OverlaySuggestion.project_id == project_id)
        .options(selectinload(OverlaySuggestion.decision))
    )
    suggestion_result = await session.execute(suggestion_stmt)
    suggestions: Sequence[OverlaySuggestion] = list(
        suggestion_result.scalars().unique()
    )

    audit_stmt = select(AuditLog).where(AuditLog.project_id == project_id)
    audit_result = await session.execute(audit_stmt)
    audit_logs = list(audit_result.scalars().all())

    audit_baseline, audit_actual, iterations = _aggregate_audit_metrics(audit_logs)
    decision_baseline, decision_actual, total, decided, accepted = _decision_metrics(
        suggestions
    )

    total_baseline = audit_baseline + decision_baseline
    total_actual = audit_actual + decision_actual

    baseline_hours = round(total_baseline / 3600.0, 2)
    actual_hours = round(total_actual / 3600.0, 2)

    savings_seconds = max(total_baseline - total_actual, 0.0)
    review_hours_saved = round(savings_seconds / 3600.0, 2)

    acceptance_rate = round(accepted / decided, 4) if decided else 0.0

    automation_score = 0.0
    if total_baseline > 0:
        automation_score = max(0.0, min(savings_seconds / total_baseline, 0.99))

    savings_percent = int(round(automation_score * 100))
    effective_hours_saved = max(review_hours_saved, 0.25)
    payback_weeks = max(1, int(ceil(PAYBACK_BASELINE_HOURS / effective_hours_saved)))

    return RoiSnapshot(
        project_id=project_id,
        iterations=iterations,
        total_suggestions=total,
        decided_suggestions=decided,
        accepted_suggestions=accepted,
        acceptance_rate=acceptance_rate,
        review_hours_saved=review_hours_saved,
        automation_score=round(automation_score, 4),
        savings_percent=savings_percent,
        payback_weeks=payback_weeks,
        baseline_hours=baseline_hours,
        actual_hours=actual_hours,
    )


__all__ = [
    "OVERLAY_BASELINE_SECONDS",
    "EXPORT_BASELINE_SECONDS",
    "DECISION_REVIEW_BASELINE_SECONDS",
    "PAYBACK_BASELINE_HOURS",
    "RoiSnapshot",
    "compute_project_roi",
]
