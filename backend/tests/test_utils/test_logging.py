"""Tests for structured logging configuration."""

from __future__ import annotations

import json
import logging
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from uuid import uuid4

import pytest

pytestmark = pytest.mark.no_db

import app.utils.logging as logging_utils
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


def test_configure_logging_respects_log_level(monkeypatch: pytest.MonkeyPatch) -> None:
    """The logging configuration should honour the configured log level."""

    captured: dict[str, object] = {}

    def fake_basic_config(**kwargs: object) -> None:
        captured["basicConfig"] = kwargs

    monkeypatch.setattr(logging, "basicConfig", fake_basic_config)

    def fake_make_filtering_bound_logger(level: int) -> str:
        captured["wrapper_level"] = level
        return f"wrapper:{level}"

    monkeypatch.setattr(
        logging_utils.structlog,
        "make_filtering_bound_logger",
        fake_make_filtering_bound_logger,
    )

    def fake_configure(**kwargs: object) -> None:
        captured["configure"] = kwargs

    monkeypatch.setattr(logging_utils.structlog, "configure", fake_configure)
    monkeypatch.setattr(
        logging_utils.structlog.stdlib,
        "LoggerFactory",
        lambda: "logger-factory",
    )
    monkeypatch.setattr(
        logging_utils.structlog.processors,
        "TimeStamper",
        lambda fmt, utc: ("timestamper", fmt, utc),
    )
    monkeypatch.setattr(
        logging_utils.structlog.processors,
        "StackInfoRenderer",
        lambda: "stack-info",
    )
    monkeypatch.setattr(
        logging_utils.structlog.processors,
        "JSONRenderer",
        lambda: "json-renderer",
    )

    monkeypatch.setattr(logging_utils.settings, "LOG_LEVEL", "warning")

    configure_logging()

    basic_kwargs = captured["basicConfig"]
    assert isinstance(basic_kwargs, dict)
    assert basic_kwargs["level"] == logging.WARNING

    configure_kwargs = captured["configure"]
    assert isinstance(configure_kwargs, dict)
    assert configure_kwargs["wrapper_class"] == "wrapper:30"

    processors = list(configure_kwargs["processors"])
    assert processors[0] is logging_utils.structlog.processors.add_log_level
    assert processors[1] == ("timestamper", "iso", True)
    assert processors[2] == "stack-info"
    assert processors[3] is logging_utils.structlog.processors.format_exc_info
    assert processors[4] == "json-renderer"


def test_get_logger_binds_project_name(monkeypatch: pytest.MonkeyPatch) -> None:
    """The helper should bind the project name for downstream consumers."""

    class DummyLogger:
        def __init__(self) -> None:
            self.bound: dict[str, object] | None = None

        def bind(self, **kwargs: object) -> "DummyLogger":
            self.bound = kwargs
            return self

    dummy_logger = DummyLogger()
    monkeypatch.setattr(
        logging_utils.structlog,
        "get_logger",
        lambda name=None: dummy_logger,
    )
    monkeypatch.setattr(logging_utils.settings, "PROJECT_NAME", "Compliance Studio")

    logger = get_logger("app.tests")

    assert logger is dummy_logger
    assert dummy_logger.bound == {"app": "Compliance Studio"}


def test_log_event_serialises_complex_payload(caplog: pytest.LogCaptureFixture) -> None:
    """Values passed to ``log_event`` should be serialised for JSON output."""

    class SampleColour(Enum):
        RED = "red"

    unique_id = uuid4()
    configure_logging()
    logger = get_logger("test_serialisation")

    complex_payload = {
        "uuid_value": unique_id,
        "decimal_value": Decimal("2.50"),
        "date_value": date(2024, 1, 1),
        "datetime_value": datetime(2024, 2, 3, 4, 5, 6),
        "enum_value": SampleColour.RED,
        "nested": {
            "set_values": {Decimal("1.25")},
            SampleColour.RED: {"inner": Decimal("3.75")},
        },
    }

    caplog.clear()
    with caplog.at_level(logging.INFO):
        log_event(logger, "complex_event", **complex_payload)

    record = caplog.records[-1]
    payload = json.loads(record.getMessage())

    assert payload["uuid_value"] == str(unique_id)
    assert payload["decimal_value"] == "2.50"
    assert payload["date_value"] == "2024-01-01"
    assert payload["datetime_value"].startswith("2024-02-03T04:05:06")
    assert payload["enum_value"] == "red"
    nested = payload["nested"]
    assert sorted(nested["set_values"]) == ["1.25"]
    assert nested["SampleColour.RED"] == {"inner": "3.75"}
