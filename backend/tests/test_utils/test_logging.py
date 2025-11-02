"""Tests for structured logging configuration."""

from __future__ import annotations

import json
import logging
import os
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import uuid4

import pytest

pytestmark = [pytest.mark.no_db]

os.environ.setdefault("SECRET_KEY", "test-secret")

import app.utils.logging as logging_utils
from app.core.config import settings
from app.utils.logging import (
    configure_logging,
    get_logger,
    log_event,
    _serialise_for_logging,
    _structlog_distribution_present,
)


# ============================================================================
# Tests for configure_logging()
# ============================================================================


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


def test_configure_logging_with_debug_level(monkeypatch: pytest.MonkeyPatch) -> None:
    """Logging configuration should support DEBUG level."""

    captured: dict[str, object] = {}

    def fake_basic_config(**kwargs: object) -> None:
        captured["basicConfig"] = kwargs

    monkeypatch.setattr(logging, "basicConfig", fake_basic_config)
    monkeypatch.setattr(
        logging_utils.structlog,
        "make_filtering_bound_logger",
        lambda level: f"wrapper:{level}",
    )
    monkeypatch.setattr(logging_utils.structlog, "configure", lambda **kwargs: None)
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

    monkeypatch.setattr(logging_utils.settings, "LOG_LEVEL", "debug")

    configure_logging()

    basic_kwargs = captured["basicConfig"]
    assert basic_kwargs["level"] == logging.DEBUG


def test_configure_logging_with_error_level(monkeypatch: pytest.MonkeyPatch) -> None:
    """Logging configuration should support ERROR level."""

    captured: dict[str, object] = {}

    def fake_basic_config(**kwargs: object) -> None:
        captured["basicConfig"] = kwargs

    monkeypatch.setattr(logging, "basicConfig", fake_basic_config)
    monkeypatch.setattr(
        logging_utils.structlog,
        "make_filtering_bound_logger",
        lambda level: f"wrapper:{level}",
    )
    monkeypatch.setattr(logging_utils.structlog, "configure", lambda **kwargs: None)
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

    monkeypatch.setattr(logging_utils.settings, "LOG_LEVEL", "error")

    configure_logging()

    basic_kwargs = captured["basicConfig"]
    assert basic_kwargs["level"] == logging.ERROR


def test_configure_logging_uses_iso_timestamp(monkeypatch: pytest.MonkeyPatch) -> None:
    """Logging configuration should use ISO 8601 timestamps in UTC."""

    captured: dict[str, list] = {"timestamps": []}

    def fake_timestamper(fmt: str, utc: bool) -> None:
        captured["timestamps"].append((fmt, utc))

    monkeypatch.setattr(logging, "basicConfig", lambda **kwargs: None)
    monkeypatch.setattr(
        logging_utils.structlog,
        "make_filtering_bound_logger",
        lambda level: "wrapper",
    )
    monkeypatch.setattr(logging_utils.structlog, "configure", lambda **kwargs: None)
    monkeypatch.setattr(
        logging_utils.structlog.stdlib,
        "LoggerFactory",
        lambda: "logger-factory",
    )
    monkeypatch.setattr(
        logging_utils.structlog.processors,
        "TimeStamper",
        fake_timestamper,
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

    monkeypatch.setattr(logging_utils.settings, "LOG_LEVEL", "info")

    configure_logging()

    assert captured["timestamps"] == [("iso", True)]


def test_configure_logging_sets_json_renderer(monkeypatch: pytest.MonkeyPatch) -> None:
    """Logging configuration should use JSON renderer for structured output."""

    captured: dict[str, object] = {}

    def fake_configure(**kwargs: object) -> None:
        captured["configure"] = kwargs

    monkeypatch.setattr(logging, "basicConfig", lambda **kwargs: None)
    monkeypatch.setattr(
        logging_utils.structlog,
        "make_filtering_bound_logger",
        lambda level: "wrapper",
    )
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

    monkeypatch.setattr(logging_utils.settings, "LOG_LEVEL", "info")

    configure_logging()

    configure_kwargs = captured["configure"]
    processors = list(configure_kwargs["processors"])
    assert processors[-1] == "json-renderer"


# ============================================================================
# Tests for get_logger()
# ============================================================================


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


def test_get_logger_with_none_name(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_logger should accept None as logger name."""

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
    monkeypatch.setattr(logging_utils.settings, "PROJECT_NAME", "Test App")

    logger = get_logger(None)

    assert logger is dummy_logger
    assert dummy_logger.bound == {"app": "Test App"}


def test_get_logger_with_custom_name(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_logger should pass custom logger names to structlog."""

    called_with: list[str] = []

    def fake_get_logger(name: str | None = None) -> Any:
        called_with.append(name)

        class DummyLogger:
            def bind(self, **kwargs: object) -> "DummyLogger":
                return self

        return DummyLogger()

    monkeypatch.setattr(
        logging_utils.structlog,
        "get_logger",
        fake_get_logger,
    )
    monkeypatch.setattr(logging_utils.settings, "PROJECT_NAME", "Test App")

    get_logger("my.custom.logger")

    assert called_with == ["my.custom.logger"]


# ============================================================================
# Tests for log_event()
# ============================================================================


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


def test_log_event_with_multiple_kwargs(caplog: pytest.LogCaptureFixture) -> None:
    """log_event should handle multiple keyword arguments."""

    configure_logging()
    logger = get_logger("test_multi_kwargs")

    caplog.clear()
    with caplog.at_level(logging.INFO):
        log_event(logger, "user_action", user_id=123, action="login", status="success")

    record = caplog.records[-1]
    payload = json.loads(record.getMessage())

    assert payload["event"] == "user_action"
    assert payload["user_id"] == 123
    assert payload["action"] == "login"
    assert payload["status"] == "success"


def test_log_event_with_empty_kwargs(caplog: pytest.LogCaptureFixture) -> None:
    """log_event should work with only event name and no additional kwargs."""

    configure_logging()
    logger = get_logger("test_no_kwargs")

    caplog.clear()
    with caplog.at_level(logging.INFO):
        log_event(logger, "simple_event")

    record = caplog.records[-1]
    payload = json.loads(record.getMessage())

    assert payload["event"] == "simple_event"
    assert payload["app"] == settings.PROJECT_NAME


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


def test_log_event_with_none_values(caplog: pytest.LogCaptureFixture) -> None:
    """log_event should handle None values gracefully."""

    configure_logging()
    logger = get_logger("test_none_values")

    caplog.clear()
    with caplog.at_level(logging.INFO):
        log_event(logger, "test_event", value=None, other="data")

    record = caplog.records[-1]
    payload = json.loads(record.getMessage())

    assert payload["event"] == "test_event"
    assert payload["value"] is None
    assert payload["other"] == "data"


def test_log_event_with_boolean_values(caplog: pytest.LogCaptureFixture) -> None:
    """log_event should handle boolean values correctly."""

    configure_logging()
    logger = get_logger("test_booleans")

    caplog.clear()
    with caplog.at_level(logging.INFO):
        log_event(logger, "test_event", enabled=True, disabled=False)

    record = caplog.records[-1]
    payload = json.loads(record.getMessage())

    assert payload["event"] == "test_event"
    assert payload["enabled"] is True
    assert payload["disabled"] is False


def test_log_event_with_numeric_values(caplog: pytest.LogCaptureFixture) -> None:
    """log_event should handle various numeric types."""

    configure_logging()
    logger = get_logger("test_numerics")

    caplog.clear()
    with caplog.at_level(logging.INFO):
        log_event(
            logger,
            "numeric_event",
            int_val=42,
            float_val=3.14,
            negative=-100,
            zero=0,
        )

    record = caplog.records[-1]
    payload = json.loads(record.getMessage())

    assert payload["event"] == "numeric_event"
    assert payload["int_val"] == 42
    assert payload["float_val"] == 3.14
    assert payload["negative"] == -100
    assert payload["zero"] == 0


# ============================================================================
# Tests for _serialise_for_logging()
# ============================================================================


def test_serialise_uuid() -> None:
    """UUID values should be converted to strings."""

    unique_id = uuid4()
    result = _serialise_for_logging(unique_id)

    assert result == str(unique_id)
    assert isinstance(result, str)


def test_serialise_decimal() -> None:
    """Decimal values should be converted to strings."""

    decimal_value = Decimal("123.45")
    result = _serialise_for_logging(decimal_value)

    assert result == "123.45"
    assert isinstance(result, str)


def test_serialise_decimal_quantised() -> None:
    """Decimal values with quantisation should be preserved."""

    decimal_value = Decimal("10.50")
    result = _serialise_for_logging(decimal_value)

    assert result == "10.50"


def test_serialise_datetime() -> None:
    """datetime objects should be converted to ISO format strings."""

    dt = datetime(2024, 3, 15, 10, 30, 45, 123456)
    result = _serialise_for_logging(dt)

    assert result == "2024-03-15T10:30:45.123456"
    assert isinstance(result, str)


def test_serialise_date() -> None:
    """date objects should be converted to ISO format strings."""

    d = date(2024, 3, 15)
    result = _serialise_for_logging(d)

    assert result == "2024-03-15"
    assert isinstance(result, str)


def test_serialise_enum() -> None:
    """Enum values should be converted to their value."""

    class Status(Enum):
        ACTIVE = "active"
        INACTIVE = "inactive"

    result = _serialise_for_logging(Status.ACTIVE)

    assert result == "active"


def test_serialise_enum_with_int_value() -> None:
    """Enum values with integer values should be serialised correctly."""

    class Priority(Enum):
        LOW = 1
        MEDIUM = 2
        HIGH = 3

    result = _serialise_for_logging(Priority.HIGH)

    assert result == 3


def test_serialise_dict_with_simple_values() -> None:
    """Dictionaries with simple values should remain dicts."""

    data = {"key1": "value1", "key2": 42}
    result = _serialise_for_logging(data)

    assert isinstance(result, dict)
    assert result == {"key1": "value1", "key2": 42}


def test_serialise_dict_with_complex_values() -> None:
    """Dictionaries with complex values should have those values serialised."""

    unique_id = uuid4()
    data = {"uuid": unique_id, "decimal": Decimal("10.5")}
    result = _serialise_for_logging(data)

    assert isinstance(result, dict)
    assert result["uuid"] == str(unique_id)
    assert result["decimal"] == "10.5"


def test_serialise_dict_with_enum_keys() -> None:
    """Dictionaries with enum keys should convert keys to strings."""

    class Status(Enum):
        ACTIVE = "active"

    data = {Status.ACTIVE: "is_active"}
    result = _serialise_for_logging(data)

    assert isinstance(result, dict)
    assert "Status.ACTIVE" in result
    assert result["Status.ACTIVE"] == "is_active"


def test_serialise_list() -> None:
    """Lists should have their items serialised."""

    unique_id = uuid4()
    data = [1, "string", unique_id, Decimal("5.5")]
    result = _serialise_for_logging(data)

    assert isinstance(result, list)
    assert result[0] == 1
    assert result[1] == "string"
    assert result[2] == str(unique_id)
    assert result[3] == "5.5"


def test_serialise_tuple() -> None:
    """Tuples should be converted to lists with serialised items."""

    unique_id = uuid4()
    data = (1, unique_id, Decimal("3.14"))
    result = _serialise_for_logging(data)

    assert isinstance(result, list)
    assert result[0] == 1
    assert result[1] == str(unique_id)
    assert result[2] == "3.14"


def test_serialise_set() -> None:
    """Sets should be converted to lists with serialised items."""

    data = {1, 2, 3}
    result = _serialise_for_logging(data)

    assert isinstance(result, list)
    assert sorted(result) == [1, 2, 3]


def test_serialise_set_with_decimal() -> None:
    """Sets containing decimals should be serialised correctly."""

    data = {Decimal("1.5"), Decimal("2.5")}
    result = _serialise_for_logging(data)

    assert isinstance(result, list)
    assert sorted(result) == ["1.5", "2.5"]


def test_serialise_json_serialisable_value() -> None:
    """Values that are already JSON serialisable should pass through."""

    assert _serialise_for_logging("string") == "string"
    assert _serialise_for_logging(42) == 42
    assert _serialise_for_logging(3.14) == 3.14
    assert _serialise_for_logging(True) is True
    assert _serialise_for_logging(None) is None


def test_serialise_non_json_serialisable_value() -> None:
    """Non-JSON-serialisable objects should be converted to strings."""

    class CustomObject:
        def __str__(self) -> str:
            return "CustomObject()"

    obj = CustomObject()
    result = _serialise_for_logging(obj)

    assert result == "CustomObject()"
    assert isinstance(result, str)


def test_serialise_nested_complex_structure() -> None:
    """Deeply nested structures should be fully serialised."""

    unique_id = uuid4()

    class Status(Enum):
        PENDING = "pending"

    data = {
        "users": [
            {"id": unique_id, "status": Status.PENDING, "balance": Decimal("100.50")},
            {"id": uuid4(), "status": Status.PENDING, "balance": Decimal("50.25")},
        ],
        "created": datetime(2024, 1, 1, 12, 0),
    }

    result = _serialise_for_logging(data)

    assert isinstance(result, dict)
    assert isinstance(result["users"], list)
    assert len(result["users"]) == 2
    assert result["users"][0]["id"] == str(unique_id)
    assert result["users"][0]["status"] == "pending"
    assert result["users"][0]["balance"] == "100.50"
    assert result["created"] == "2024-01-01T12:00:00"


def test_serialise_date_range() -> None:
    """Date objects should maintain ISO format for date ranges."""

    start_date = date(2024, 1, 1)
    end_date = date(2024, 12, 31)
    data = {"start": start_date, "end": end_date}

    result = _serialise_for_logging(data)

    assert result["start"] == "2024-01-01"
    assert result["end"] == "2024-12-31"


def test_serialise_datetime_with_timezone_info() -> None:
    """datetime objects should be converted to ISO format with timezone if present."""

    dt = datetime(2024, 3, 15, 10, 30, 45)
    result = _serialise_for_logging(dt)

    assert "2024-03-15T10:30:45" in result


# ============================================================================
# Tests for _structlog_distribution_present()
# ============================================================================


def test_structlog_distribution_present_when_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Should return True when structlog is installed."""

    class FakeMetadata:
        def version(self, distribution: str) -> str:
            if distribution == "structlog":
                return "21.1.0"
            raise logging_utils.PackageNotFoundError("Not found")

    monkeypatch.setattr(logging_utils, "importlib_metadata", FakeMetadata())

    result = _structlog_distribution_present()

    assert result is True


def test_structlog_distribution_present_when_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Should return False when structlog is not installed."""

    class FakeMetadata:
        def version(self, distribution: str) -> str:
            raise logging_utils.PackageNotFoundError("Not found")

    monkeypatch.setattr(logging_utils, "importlib_metadata", FakeMetadata())

    result = _structlog_distribution_present()

    assert result is False


def test_structlog_distribution_present_when_metadata_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Should return False when metadata module is unavailable."""

    monkeypatch.setattr(logging_utils, "importlib_metadata", None)

    result = _structlog_distribution_present()

    assert result is False


def test_structlog_distribution_present_handles_generic_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Should return False when metadata access raises any exception."""

    class FakeMetadata:
        def version(self, distribution: str) -> str:
            raise RuntimeError("Metadata error")

    monkeypatch.setattr(logging_utils, "importlib_metadata", FakeMetadata())

    result = _structlog_distribution_present()

    assert result is False
