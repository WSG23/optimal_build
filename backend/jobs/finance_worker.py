"""Entry point for running finance Celery workers."""

from __future__ import annotations

import os

from backend.jobs import celery_app
import backend.jobs.finance_sensitivity  # noqa: F401 - register tasks with celery

if celery_app is None:  # pragma: no cover
    raise SystemExit(
        "Celery is not installed. Install optional dependencies to run finance workers."
    )

DEFAULT_QUEUES = os.getenv("FINANCE_WORKER_QUEUES", "finance,preview").split(",")


def main() -> None:
    argv = ["worker", "-Q", ",".join(DEFAULT_QUEUES)]
    celery_app.worker_main(argv)


if __name__ == "__main__":  # pragma: no cover
    main()
