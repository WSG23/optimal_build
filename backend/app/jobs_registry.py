"""Registry helpers for background jobs."""

from __future__ import annotations

from backend.jobs import job_queue
from backend.jobs.generate_reports import generate_market_report_bundle
from backend.jobs.performance import generate_snapshots_job, seed_benchmarks_job
from backend.jobs.preview_generate import generate_preview_job  # noqa: F401


def enlist_default_jobs() -> None:
    """Ensure core jobs are registered with the active queue backend."""

    job_queue.register(
        generate_market_report_bundle, "market.generate_report_bundle", queue="reports"
    )
    job_queue.register(
        generate_snapshots_job,
        "performance.generate_snapshots",
        queue="analytics",
    )
    job_queue.register(
        seed_benchmarks_job,
        "performance.seed_benchmarks",
        queue="analytics",
    )


__all__ = ["enlist_default_jobs"]
