"""Background worker entrypoint.

The module ensures all job definitions are imported so that Celery or RQ
workers discover them automatically. When Celery is installed the
``celery_app`` attribute can be used as the application reference, e.g.:

.. code-block:: bash

    celery -A backend.worker:celery_app worker

For environments that rely on the inline queue the module still exposes the
``job_queue`` allowing management commands or tests to introspect the active
backend.
"""

from __future__ import annotations

from backend.jobs import celery_app, job_queue  # noqa: F401  (re-exported for workers)

# Import job modules to register tasks with the configured backend.
from backend.jobs import overlay_run as _overlay_run  # noqa: F401
from backend.jobs import parse_cad as _parse_cad  # noqa: F401
from backend.jobs import raster_vector as _raster_vector  # noqa: F401

__all__ = ["celery_app", "job_queue"]
