"""Tests for structured logging configuration."""

from __future__ import annotations

import json
import logging

import pytest
from app.core.config import settings
from app.utils.logging import configure_logging, get_logger, log_event


def test_log_event_emits_json_with_timestamp(caplog: pytest.LogCaptureFixture) -> None:
    """Structured log events should include JSON payloads with timestamps."""

    configure_logging()
    logger = get_logger("test_json_logging")

    caplog.clear()
    with caplog.at_level(logging.INFO):
        log_event(logger, "test_event", detail="value")

    assert caplog.records, "No log records captured"
    record = caplog.records[-1]
    payload = json.loads(record.getMessage())

    assert payload["event"] == "test_event"
    assert payload["detail"] == "value"
    assert payload["app"] == settings.PROJECT_NAME
    assert "timestamp" in payload and "T" in payload["timestamp"]
