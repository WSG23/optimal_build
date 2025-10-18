"""Metrics instrumentation tests for the buildable screening endpoint."""

from __future__ import annotations

from importlib import import_module
import sys
from types import ModuleType

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")
pytest.importorskip("pytest_asyncio")

pytest_plugins = ("backend.tests.pwp.test_buildable_golden",)

try:  # pragma: no cover - structlog is optional in the test environment
    import_module("structlog")
except ModuleNotFoundError:  # pragma: no cover - fallback stub for offline testing
    structlog_module = ModuleType("structlog")
    processors_module = ModuleType("structlog.processors")
    stdlib_module = ModuleType("structlog.stdlib")

    class _StubBoundLogger:
        """Minimal stub used when structlog is unavailable."""

        def bind(self, **kwargs):
            return self

        def info(self, *args, **kwargs):  # noqa: D401 - simple stub
            return None

    def _noop(*args, **kwargs):
        return None

    def _time_stamper(*args, **kwargs):
        return _noop

    processors_module.add_log_level = _noop  # type: ignore[attr-defined]
    processors_module.TimeStamper = _time_stamper  # type: ignore[attr-defined]
    processors_module.StackInfoRenderer = lambda *a, **k: _noop  # type: ignore[attr-defined]
    processors_module.format_exc_info = (  # type: ignore[attr-defined]
        lambda logger, method_name, event_dict: event_dict
    )
    processors_module.JSONRenderer = lambda *a, **k: _noop  # type: ignore[attr-defined]

    stdlib_module.BoundLogger = _StubBoundLogger  # type: ignore[attr-defined]
    stdlib_module.LoggerFactory = (  # type: ignore[attr-defined]
        lambda *a, **k: (lambda *args, **kwargs: _StubBoundLogger())
    )

    structlog_module._IS_VENDORED_STRUCTLOG = False  # type: ignore[attr-defined]
    structlog_module.processors = processors_module  # type: ignore[attr-defined]
    structlog_module.stdlib = stdlib_module  # type: ignore[attr-defined]
    structlog_module.configure = _noop  # type: ignore[attr-defined]
    structlog_module.make_filtering_bound_logger = (  # type: ignore[attr-defined]
        lambda *a, **k: _StubBoundLogger
    )
    structlog_module.get_logger = (  # type: ignore[attr-defined]
        lambda *a, **k: _StubBoundLogger()
    )

    sys.modules.setdefault("structlog", structlog_module)
    sys.modules.setdefault("structlog.processors", processors_module)
    sys.modules.setdefault("structlog.stdlib", stdlib_module)

from backend.tests.pwp.test_buildable_golden import (
    DEFAULT_REQUEST_DEFAULTS,
    DEFAULT_REQUEST_OVERRIDES,
)

from app.utils import metrics


@pytest.mark.asyncio
async def test_buildable_metrics_increment(buildable_client) -> None:
    """Ensure buildable metrics surface in Prometheus output."""

    client, _ = buildable_client

    payload = {
        "address": "123 Example Ave",
        "defaults": dict(DEFAULT_REQUEST_DEFAULTS),
        **DEFAULT_REQUEST_OVERRIDES,
    }

    response = await client.post("/api/v1/screen/buildable", json=payload)
    assert response.status_code == 200

    assert metrics.counter_value(metrics.PWP_BUILDABLE_TOTAL, {}) == 1.0

    metrics_output = metrics.render_latest_metrics().decode()
    assert "pwp_buildable_total" in metrics_output
    assert "pwp_buildable_duration_ms" in metrics_output

    health_response = await client.get("/health/metrics")
    assert health_response.status_code == 200
    health_metrics = health_response.read().decode()
    assert "pwp_buildable_total" in health_metrics
    assert "pwp_buildable_duration_ms" in health_metrics
