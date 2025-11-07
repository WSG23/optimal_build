from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.core.metrics import (
    DECISION_REVIEW_BASELINE_SECONDS,
    MetricsCollector,
)
from app.core.metrics.roi import (
    RoiSnapshot,
    _aggregate_audit_metrics,
    _as_utc,
    _decision_metrics,
    compute_project_roi,
)
from app.utils import metrics as prometheus_metrics


class _ScalarsResult:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return self

    def unique(self):
        return self

    def all(self):
        return list(self._items)

    def __iter__(self):
        return iter(self._items)


class _SessionStub:
    def __init__(self, suggestion_items, audit_items):
        self._results = [
            _ScalarsResult(suggestion_items),
            _ScalarsResult(audit_items),
        ]

    async def execute(self, _stmt):
        return self._results.pop(0)


def test_metrics_collector_records_known_gauge():
    prometheus_metrics.reset_metrics()
    collector = MetricsCollector()
    collector.record_gauge(
        "market_intelligence.cap_rate",
        value=3.4,
        tags={"property_type": "office", "location": "D01"},
    )
    gauge_value = prometheus_metrics.counter_value(
        prometheus_metrics.MARKET_INTEL_CAP_RATE_GAUGE,
        {"property_type": "office", "location": "D01"},
    )
    assert gauge_value == 3.4
    with pytest.raises(KeyError):
        collector.record_gauge("unknown.metric", 1.0)


def test_as_utc_and_audit_helpers():
    naive = datetime(2024, 1, 1, 12, 0, 0)
    aware = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    assert _as_utc(None) is None
    assert _as_utc(naive).tzinfo is timezone.utc
    assert _as_utc(aware) == aware

    logs = [
        SimpleNamespace(
            event_type="overlay_run", baseline_seconds=30.0, actual_seconds=10.0
        ),
        SimpleNamespace(
            event_type="overlay_decision", baseline_seconds=50.0, actual_seconds=40.0
        ),
    ]
    baseline, actual, iterations = _aggregate_audit_metrics(logs)
    assert baseline == 30.0
    assert actual == 10.0
    assert iterations == 1


def test_decision_metrics_handles_decided_and_pending():
    created = datetime(2024, 1, 1, 8, 0, 0, tzinfo=timezone.utc)
    decided = created + timedelta(minutes=30)
    suggestions = [
        SimpleNamespace(
            status="approved",
            decision=SimpleNamespace(),
            created_at=created,
            decided_at=decided,
            updated_at=decided,
        ),
        SimpleNamespace(
            status="pending",
            decision=None,
            created_at=None,
            decided_at=None,
            updated_at=None,
        ),
    ]
    baseline, actual, total, decided_count, accepted = _decision_metrics(suggestions)
    assert total == 2
    assert decided_count == 1
    assert accepted == 1
    assert baseline > 0
    assert actual > 0


@pytest.mark.asyncio
async def test_compute_project_roi_aggregates_data():
    created = datetime(2024, 1, 1, tzinfo=timezone.utc)
    decided = created + timedelta(minutes=45)
    suggestions = [
        SimpleNamespace(
            project_id=99,
            status="approved",
            decision=SimpleNamespace(),
            created_at=created,
            decided_at=decided,
            updated_at=decided,
        )
    ]
    logs = [
        SimpleNamespace(
            event_type="overlay_run",
            baseline_seconds=DECISION_REVIEW_BASELINE_SECONDS,
            actual_seconds=DECISION_REVIEW_BASELINE_SECONDS / 2,
        )
    ]
    session = _SessionStub(suggestions, logs)
    snapshot = await compute_project_roi(session, project_id=99)
    assert isinstance(snapshot, RoiSnapshot)
    assert snapshot.accepted_suggestions == 1
    assert snapshot.iterations == 1
