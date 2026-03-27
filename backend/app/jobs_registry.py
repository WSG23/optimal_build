"""Registry helpers for background jobs."""

from __future__ import annotations

from backend.jobs import job_queue
from app.core.config import settings


def enlist_default_jobs() -> None:
    """Ensure core jobs are registered with the active queue backend."""

    from backend.jobs.generate_reports import generate_market_report_bundle
    from backend.jobs.overlay_run import run_overlay_job
    from backend.jobs.parse_cad import parse_import_job
    from backend.jobs.performance import generate_snapshots_job, seed_benchmarks_job
    from backend.jobs.preview_generate import generate_preview_job  # noqa: F401

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
    job_queue.register(
        parse_import_job,
        getattr(parse_import_job, "job_name", "jobs.parse_cad.parse_import"),
        queue="imports:parse",
    )
    job_queue.register(
        run_overlay_job,
        getattr(run_overlay_job, "job_name", "jobs.overlay_run.run_for_project"),
        queue=settings.OVERLAY_QUEUE_DEFAULT,
    )


__all__ = ["enlist_default_jobs"]
