"""Registry helpers for background jobs."""

from __future__ import annotations

from backend.jobs import job_queue
from backend.jobs.generate_reports import generate_market_report_bundle


def enlist_default_jobs() -> None:
    """Ensure core jobs are registered with the active queue backend."""

    job_queue.register(generate_market_report_bundle, "market.generate_report_bundle", queue="reports")


__all__ = ["enlist_default_jobs"]
