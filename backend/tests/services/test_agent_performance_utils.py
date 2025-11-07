from __future__ import annotations

from datetime import date, datetime, timedelta
from types import SimpleNamespace

import pytest

from app.core.metrics.roi import RoiSnapshot
from app.services.deals.performance import (
    AgentPerformanceService,
    _coerce_date,
    _coerce_float,
    _deal_cycle_days,
    _derive_snapshot_context,
    _normalise_roi_snapshot,
    _safe_float,
    _safe_int,
    _summarise_roi_snapshots,
)


def test_safe_int_handles_strings_and_invalid():
    assert _safe_int("42") == 42
    assert _safe_int(" 17 ") == 17
    assert _safe_int(True) is None
    assert _safe_int("abc") is None


def test_safe_float_converts_and_ignores_invalid():
    assert _safe_float("2.5") == pytest.approx(2.5)
    assert _safe_float(7) == pytest.approx(7.0)
    assert _safe_float(False) is None
    assert _safe_float("invalid") is None


def test_normalise_roi_snapshot_requires_project_id():
    payload = {
        "project_id": "12",
        "iterations": "3",
        "automation_score": "0.6",
    }
    snapshot = _normalise_roi_snapshot(payload)
    assert snapshot["project_id"] == 12
    assert snapshot["automation_score"] == pytest.approx(0.6)
    assert snapshot["total_suggestions"] == 0

    assert _normalise_roi_snapshot({"iterations": 2}) is None


def test_summarise_roi_snapshots_builds_rollup():
    samples = [
        {
            "project_id": 1,
            "review_hours_saved": 12.5,
            "baseline_hours": 30.0,
            "actual_hours": 10.0,
            "iterations": 3,
            "automation_score": 0.5,
            "acceptance_rate": 0.75,
            "savings_percent": 55,
            "payback_weeks": 8,
        },
        {
            "project_id": 2,
            "review_hours_saved": 7.0,
            "baseline_hours": 20.0,
            "actual_hours": 12.0,
            "iterations": 1,
            "automation_score": 0.3,
            "acceptance_rate": 0.6,
            "savings_percent": 40,
            "payback_weeks": 0,
        },
    ]
    summary = _summarise_roi_snapshots(samples)

    assert summary["project_count"] == 2
    assert summary["total_review_hours_saved"] == 19.5
    assert summary["total_iterations"] == 4
    assert summary["average_automation_score"] == pytest.approx(0.4)
    assert summary["best_payback_weeks"] == 8


def test_derive_snapshot_context_calculates_ratios():
    context = _derive_snapshot_context(
        gross_pipeline=1_000_000,
        weighted_pipeline=400_000,
        deals_open=5,
        deals_closed_won=3,
    )
    assert context["weighted_to_gross_ratio"] == pytest.approx(0.4)
    assert context["average_pipeline_per_open_deal"] == pytest.approx(200000.0)
    assert context["win_ratio"] == pytest.approx(0.375)
    assert "generated_at" in context


def test_deal_cycle_days_uses_stage_events():
    created = datetime(2025, 1, 1)
    stage_time = created + timedelta(days=5)
    closed = created + timedelta(days=12)
    deal = SimpleNamespace(
        created_at=created,
        updated_at=closed,
        actual_close_date=None,
        stage_events=[SimpleNamespace(recorded_at=stage_time)],
    )

    value = _deal_cycle_days(deal)

    assert value == pytest.approx(7.0)


def test_coerce_date_accepts_strings_and_datetime():
    today = date.today()
    assert _coerce_date(today.isoformat()) == today
    now = datetime.now()
    assert _coerce_date(now) == now
    assert _coerce_date(today) == today
    with pytest.raises(TypeError):
        _coerce_date(123)


def test_coerce_float_errors_on_invalid():
    assert _coerce_float("3.14") == pytest.approx(3.14)
    assert _coerce_float(4) == pytest.approx(4.0)
    with pytest.raises(TypeError):
        _coerce_float(object())


@pytest.mark.asyncio
async def test_aggregate_roi_metrics_merges_online_and_offline(monkeypatch):
    service = AgentPerformanceService()

    roi_snapshot = RoiSnapshot(
        project_id=2,
        iterations=4,
        total_suggestions=10,
        decided_suggestions=8,
        accepted_suggestions=6,
        acceptance_rate=0.75,
        review_hours_saved=5.0,
        automation_score=0.4,
        savings_percent=40,
        payback_weeks=6,
        baseline_hours=20.0,
        actual_hours=12.0,
    )

    async def fake_compute_project_roi(session, project_id):
        assert project_id == 2
        return roi_snapshot

    monkeypatch.setattr(
        "app.services.deals.performance.compute_project_roi",
        fake_compute_project_roi,
    )

    deals = [
        SimpleNamespace(
            id=1,
            metadata={
                "roi_project_id": "2",
            },
        ),
        SimpleNamespace(
            id=2,
            metadata={
                "roi_metrics": {
                    "project_id": "2",
                    "automation_score": "0.8",
                    "iterations": "2",
                },
            },
        ),
        SimpleNamespace(
            id=3,
            metadata={
                "roi_metrics": {
                    "project_id": "3",
                    "automation_score": "0.6",
                    "review_hours_saved": "4.5",
                },
            },
        ),
    ]

    payload = await service._aggregate_roi_metrics(
        session=SimpleNamespace(),
        deals=deals,
    )

    assert payload["projects"][0]["project_id"] == 2
    assert payload["projects"][0]["automation_score"] == pytest.approx(0.8)
    assert payload["projects"][1]["project_id"] == 3
    assert payload["summary"]["project_count"] == 2
