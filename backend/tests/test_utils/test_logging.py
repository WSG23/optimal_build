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


def test_serialise_for_logging_handles_json_serializable_objects() -> None:
    """Test that already JSON-serializable objects pass through."""
    from app.utils.logging import _serialise_for_logging

    # Simple JSON-serializable values
    assert _serialise_for_logging("string") == "string"
    assert _serialise_for_logging(123) == 123
    assert _serialise_for_logging(123.45) == 123.45
    assert _serialise_for_logging(True) is True
    assert _serialise_for_logging(None) is None


def test_serialise_for_logging_converts_uuid() -> None:
    """Test UUID conversion to string."""
    from app.utils.logging import _serialise_for_logging

    test_uuid = uuid4()
    result = _serialise_for_logging(test_uuid)

    assert isinstance(result, str)
    assert result == str(test_uuid)


def test_serialise_for_logging_converts_decimal() -> None:
    """Test Decimal conversion to string."""
    from app.utils.logging import _serialise_for_logging

    decimal_value = Decimal("99.99")
    result = _serialise_for_logging(decimal_value)

    assert result == "99.99"


def test_serialise_for_logging_converts_date() -> None:
    """Test date conversion to ISO format."""
    from app.utils.logging import _serialise_for_logging

    test_date = date(2024, 6, 15)
    result = _serialise_for_logging(test_date)

    assert result == "2024-06-15"


def test_serialise_for_logging_converts_datetime() -> None:
    """Test datetime conversion to ISO format."""
    from app.utils.logging import _serialise_for_logging

    test_datetime = datetime(2024, 6, 15, 14, 30, 45)
    result = _serialise_for_logging(test_datetime)

    assert result.startswith("2024-06-15T14:30:45")


def test_serialise_for_logging_converts_enum() -> None:
    """Test Enum conversion to value."""
    from app.utils.logging import _serialise_for_logging

    class Status(Enum):
        ACTIVE = "active"
        INACTIVE = "inactive"

    result = _serialise_for_logging(Status.ACTIVE)

    assert result == "active"


def test_serialise_for_logging_handles_nested_dict() -> None:
    """Test recursive serialization of nested dictionaries."""
    from app.utils.logging import _serialise_for_logging

    nested_dict = {
        "outer": {
            "inner": uuid4(),
            "deeper": {"value": Decimal("10.5")},
        }
    }
    result = _serialise_for_logging(nested_dict)

    assert isinstance(result, dict)
    assert isinstance(result["outer"], dict)
    assert isinstance(result["outer"]["inner"], str)
    assert result["outer"]["deeper"]["value"] == "10.5"


def test_serialise_for_logging_handles_list() -> None:
    """Test serialization of lists."""
    from app.utils.logging import _serialise_for_logging

    test_list = [uuid4(), Decimal("5.5"), date(2024, 1, 1)]
    result = _serialise_for_logging(test_list)

    assert isinstance(result, list)
    assert len(result) == 3
    assert isinstance(result[0], str)
    assert result[1] == "5.5"
    assert result[2] == "2024-01-01"


def test_serialise_for_logging_handles_tuple() -> None:
    """Test serialization of tuples."""
    from app.utils.logging import _serialise_for_logging

    test_tuple = (Decimal("1.1"), Decimal("2.2"))
    result = _serialise_for_logging(test_tuple)

    assert isinstance(result, list)  # Tuples become lists
    assert result == ["1.1", "2.2"]


def test_serialise_for_logging_handles_set() -> None:
    """Test serialization of sets."""
    from app.utils.logging import _serialise_for_logging

    test_set = {Decimal("3.3"), Decimal("4.4")}
    result = _serialise_for_logging(test_set)

    assert isinstance(result, list)  # Sets become lists
    assert sorted(result) == ["3.3", "4.4"]


def test_serialise_for_logging_converts_non_json_serializable_to_string() -> None:
    """Test that non-JSON-serializable objects are converted to string."""
    from app.utils.logging import _serialise_for_logging

    class CustomObject:
        def __repr__(self) -> str:
            return "<CustomObject>"

    custom_obj = CustomObject()
    result = _serialise_for_logging(custom_obj)

    assert result == "<CustomObject>"


def test_serialise_for_logging_handles_dict_with_non_string_keys() -> None:
    """Test that dict keys are converted to strings."""
    from app.utils.logging import _serialise_for_logging

    test_dict = {1: "one", 2: "two", date(2024, 1, 1): "date_key"}
    result = _serialise_for_logging(test_dict)

    assert isinstance(result, dict)
    assert "1" in result
    assert "2" in result
    assert "2024-01-01" in result or str(date(2024, 1, 1)) in result
