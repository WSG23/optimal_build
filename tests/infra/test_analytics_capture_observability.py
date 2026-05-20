from __future__ import annotations

from pathlib import Path

import yaml

PROMETHEUS_DIR = (
    Path(__file__).resolve().parents[2] / "infra" / "observability" / "prometheus"
)


def test_prometheus_loads_analytics_capture_alerts() -> None:
    config = yaml.safe_load((PROMETHEUS_DIR / "prometheus.yml").read_text())

    assert "alerting_rules.yml" in config["rule_files"]


def test_analytics_capture_failure_alert_exists() -> None:
    rules = yaml.safe_load((PROMETHEUS_DIR / "alerting_rules.yml").read_text())
    alerts = [
        rule
        for group in rules["groups"]
        for rule in group.get("rules", [])
        if rule.get("alert") == "AnalyticsCaptureFailures"
    ]

    assert alerts
    assert "analytics_capture_failures_total" in alerts[0]["expr"]
    assert alerts[0]["labels"]["severity"] == "critical"
