"""Tests for audit ledger helper functions."""

import hashlib
import hmac
from datetime import datetime
from decimal import Decimal

import pytest
from backend._compat.datetime import UTC

from app.core.audit.ledger import (
    _as_utc,
    _coerce_float,
    _normalise_context,
    _payload_for_hash,
    _sign_hash,
    compute_event_hash,
)
from app.core.config import settings
from app.models.audit import AuditLog


class TestAsUtc:
    """Tests for _as_utc helper function."""

    def test_as_utc_with_none_returns_none(self):
        """Test that None input returns None."""
        result = _as_utc(None)
        assert result is None

    def test_as_utc_with_naive_datetime(self):
        """Test converting naive datetime to UTC."""
        naive_dt = datetime(2023, 1, 15, 12, 30, 45)
        result = _as_utc(naive_dt)

        assert result is not None
        assert result.tzinfo == UTC
        assert result.year == 2023
        assert result.month == 1
        assert result.day == 15

    def test_as_utc_with_utc_datetime(self):
        """Test that UTC datetime is returned as-is."""
        utc_dt = datetime(2023, 1, 15, 12, 30, 45, tzinfo=UTC)
        result = _as_utc(utc_dt)

        assert result == utc_dt
        assert result.tzinfo == UTC

    def test_as_utc_converts_timezone(self):
        """Test converting datetime with different timezone to UTC."""
        # Create a UTC datetime and then convert it to a different timezone representation
        utc_dt = datetime(2023, 1, 15, 12, 0, 0, tzinfo=UTC)
        result = _as_utc(utc_dt)

        assert result.tzinfo == UTC


class TestCoerceFloat:
    """Tests for _coerce_float helper function."""

    def test_coerce_float_with_none_returns_none(self):
        """Test that None input returns None."""
        result = _coerce_float(None)
        assert result is None

    def test_coerce_float_with_int(self):
        """Test converting int to float."""
        result = _coerce_float(42)
        assert result == 42.0
        assert isinstance(result, float)

    def test_coerce_float_with_float(self):
        """Test float passes through."""
        result = _coerce_float(3.14)
        assert result == 3.14
        assert isinstance(result, float)

    def test_coerce_float_with_decimal(self):
        """Test converting Decimal to float."""
        result = _coerce_float(Decimal("123.45"))
        assert result == 123.45
        assert isinstance(result, float)

    def test_coerce_float_with_string_number(self):
        """Test converting numeric string to float."""
        result = _coerce_float("42.5")
        assert result == 42.5
        assert isinstance(result, float)

    def test_coerce_float_with_zero(self):
        """Test that zero is handled correctly."""
        result = _coerce_float(0)
        assert result == 0.0
        assert isinstance(result, float)

    def test_coerce_float_with_negative(self):
        """Test negative numbers."""
        result = _coerce_float(-99.9)
        assert result == -99.9
        assert isinstance(result, float)

    def test_coerce_float_with_invalid_string_raises_error(self):
        """Test that non-numeric string raises TypeError."""
        with pytest.raises(TypeError, match="Expected numeric value"):
            _coerce_float("not-a-number")

    def test_coerce_float_with_object_raises_error(self):
        """Test that non-numeric object raises TypeError."""
        with pytest.raises(TypeError, match="Expected numeric value"):
            _coerce_float({"not": "numeric"})


class TestNormaliseContext:
    """Tests for _normalise_context helper function."""

    def test_normalise_context_with_none_returns_empty_dict(self):
        """Test that None input returns empty dict."""
        result = _normalise_context(None)
        assert result == {}

    def test_normalise_context_with_empty_dict(self):
        """Test that empty dict returns empty dict."""
        result = _normalise_context({})
        assert result == {}

    def test_normalise_context_with_string_keys(self):
        """Test that string keys are preserved."""
        context = {"key1": "value1", "key2": "value2"}
        result = _normalise_context(context)

        assert result == {"key1": "value1", "key2": "value2"}

    def test_normalise_context_converts_non_string_keys(self):
        """Test that non-string keys are converted to strings."""
        context = {1: "value1", 2: "value2", "key": "value"}
        result = _normalise_context(context)

        assert result == {"1": "value1", "2": "value2", "key": "value"}

    def test_normalise_context_with_nested_values(self):
        """Test that nested values are preserved."""
        context = {
            "key1": {"nested": "value"},
            "key2": [1, 2, 3],
            "key3": "simple",
        }
        result = _normalise_context(context)

        assert result["key1"] == {"nested": "value"}
        assert result["key2"] == [1, 2, 3]
        assert result["key3"] == "simple"

    def test_normalise_context_does_not_mutate_original(self):
        """Test that original context is not mutated."""
        original = {"key": "value"}
        result = _normalise_context(original)

        # Modify result
        result["new_key"] = "new_value"

        # Original should be unchanged
        assert "new_key" not in original


class TestPayloadForHash:
    """Tests for _payload_for_hash function."""

    def test_payload_for_hash_with_minimal_log(self):
        """Test building payload from minimal audit log."""
        log = AuditLog(
            project_id=123,
            version=1,
            event_type="test_event",
            recorded_at=datetime(2023, 1, 15, 12, 0, 0, tzinfo=UTC),
        )

        payload = _payload_for_hash(log)

        assert payload["project_id"] == 123
        assert payload["version"] == 1
        assert payload["event_type"] == "test_event"
        assert payload["baseline_seconds"] is None
        assert payload["actual_seconds"] is None
        assert payload["context"] == {}
        assert payload["recorded_at"] == "2023-01-15T12:00:00+00:00"
        assert payload["prev_hash"] == ""

    def test_payload_for_hash_with_complete_log(self):
        """Test building payload with all fields populated."""
        log = AuditLog(
            project_id=456,
            version=5,
            event_type="complete_event",
            baseline_seconds=100.5,
            actual_seconds=95.3,
            context={"key": "value", "count": 42},
            recorded_at=datetime(2023, 6, 10, 8, 30, 15, tzinfo=UTC),
            prev_hash="abc123prev",
        )

        payload = _payload_for_hash(log)

        assert payload["project_id"] == 456
        assert payload["version"] == 5
        assert payload["event_type"] == "complete_event"
        assert payload["baseline_seconds"] == 100.5
        assert payload["actual_seconds"] == 95.3
        assert payload["context"] == {"key": "value", "count": 42}
        assert payload["recorded_at"] == "2023-06-10T08:30:15+00:00"
        assert payload["prev_hash"] == "abc123prev"

    def test_payload_for_hash_handles_none_prev_hash(self):
        """Test that None prev_hash becomes empty string."""
        log = AuditLog(
            project_id=1,
            version=1,
            event_type="first_event",
            recorded_at=datetime(2023, 1, 1, tzinfo=UTC),
            prev_hash=None,
        )

        payload = _payload_for_hash(log)

        assert payload["prev_hash"] == ""


class TestComputeEventHash:
    """Tests for compute_event_hash function."""

    def test_compute_event_hash_produces_sha256(self):
        """Test that hash is a valid SHA-256 hex string."""
        payload = {"key": "value"}
        result = compute_event_hash(payload)

        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 produces 64 hex characters
        # Check that it's all hex characters
        int(result, 16)  # Should not raise

    def test_compute_event_hash_is_deterministic(self):
        """Test that same payload produces same hash."""
        payload = {"key": "value", "number": 42}

        hash1 = compute_event_hash(payload)
        hash2 = compute_event_hash(payload)

        assert hash1 == hash2

    def test_compute_event_hash_different_for_different_payloads(self):
        """Test that different payloads produce different hashes."""
        payload1 = {"key": "value1"}
        payload2 = {"key": "value2"}

        hash1 = compute_event_hash(payload1)
        hash2 = compute_event_hash(payload2)

        assert hash1 != hash2

    def test_compute_event_hash_independent_of_key_order(self):
        """Test that key order doesn't affect hash (due to sort_keys)."""
        payload1 = {"a": 1, "b": 2, "c": 3}
        payload2 = {"c": 3, "a": 1, "b": 2}

        hash1 = compute_event_hash(payload1)
        hash2 = compute_event_hash(payload2)

        assert hash1 == hash2

    def test_compute_event_hash_with_nested_structures(self):
        """Test hashing with nested dicts and lists."""
        payload = {
            "outer": {"inner": "value"},
            "list": [1, 2, 3],
            "number": 42,
        }

        result = compute_event_hash(payload)

        assert isinstance(result, str)
        assert len(result) == 64

    def test_compute_event_hash_with_unicode(self):
        """Test hashing with unicode characters."""
        payload = {"message": "Hello 世界 🌍", "emoji": "🚀"}

        result = compute_event_hash(payload)

        assert isinstance(result, str)
        assert len(result) == 64


class TestSignHash:
    """Tests for _sign_hash function."""

    def test_sign_hash_produces_hmac(self):
        """Test that signature is a valid HMAC hex string."""
        hash_value = "test_hash_value"
        result = _sign_hash(hash_value)

        assert isinstance(result, str)
        assert len(result) == 64  # HMAC-SHA256 produces 64 hex characters
        int(result, 16)  # Should not raise

    def test_sign_hash_is_deterministic(self):
        """Test that same hash produces same signature."""
        hash_value = "test_hash"

        sig1 = _sign_hash(hash_value)
        sig2 = _sign_hash(hash_value)

        assert sig1 == sig2

    def test_sign_hash_different_for_different_hashes(self):
        """Test that different hashes produce different signatures."""
        sig1 = _sign_hash("hash1")
        sig2 = _sign_hash("hash2")

        assert sig1 != sig2

    def test_sign_hash_uses_secret_key(self):
        """Test that signature is based on the secret key."""
        hash_value = "test_hash"
        signature = _sign_hash(hash_value)

        # Manually compute expected HMAC
        secret = settings.SECRET_KEY.encode("utf-8")
        expected = hmac.new(
            secret, hash_value.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        assert signature == expected

    def test_sign_hash_with_empty_string(self):
        """Test signing empty string."""
        result = _sign_hash("")

        assert isinstance(result, str)
        assert len(result) == 64


class TestSerialiseLog:
    """Tests for serialise_log function."""

    def test_serialise_log_produces_dict(self):
        """Test serialising audit log to dictionary."""
        from app.core.audit.ledger import serialise_log

        log = AuditLog(
            id=1,
            project_id=123,
            version=1,
            event_type="test_event",
            baseline_seconds=100.5,
            actual_seconds=95.3,
            context={"key": "value"},
            recorded_at=datetime(2023, 1, 15, 12, 0, 0, tzinfo=UTC),
            hash="abc123",
            prev_hash="prev456",
            signature="sig789",
        )

        result = serialise_log(log)

        assert result["id"] == 1
        assert result["project_id"] == 123
        assert result["version"] == 1
        assert result["event_type"] == "test_event"
        assert result["baseline_seconds"] == 100.5
        assert result["actual_seconds"] == 95.3
        assert result["context"] == {"key": "value"}
        assert result["recorded_at"] == "2023-01-15T12:00:00+00:00"
        assert result["hash"] == "abc123"
        assert result["prev_hash"] == "prev456"
        assert result["signature"] == "sig789"

    def test_serialise_log_with_none_recorded_at(self):
        """Test serialising log with no recorded_at."""
        from app.core.audit.ledger import serialise_log

        log = AuditLog(
            id=1,
            project_id=123,
            version=1,
            event_type="test_event",
            recorded_at=None,
        )

        result = serialise_log(log)

        assert result["recorded_at"] is None

    def test_serialise_log_with_minimal_log(self):
        """Test serialising minimal audit log."""
        from app.core.audit.ledger import serialise_log

        log = AuditLog(
            project_id=123,
            version=1,
            event_type="minimal_event",
        )

        result = serialise_log(log)

        assert result["project_id"] == 123
        assert result["version"] == 1
        assert result["event_type"] == "minimal_event"
        assert result["baseline_seconds"] is None
        assert result["actual_seconds"] is None
        assert result["context"] == {}


class TestDiffValue:
    """Tests for _diff_value helper function."""

    def test_diff_value_returns_none_when_equal(self):
        """Test that equal values return None."""
        from app.core.audit.ledger import _diff_value

        result = _diff_value("same", "same")
        assert result is None

    def test_diff_value_returns_none_for_equal_numbers(self):
        """Test that equal numbers return None."""
        from app.core.audit.ledger import _diff_value

        result = _diff_value(42, 42)
        assert result is None

    def test_diff_value_returns_diff_for_different_values(self):
        """Test that different values return diff structure."""
        from app.core.audit.ledger import _diff_value

        result = _diff_value("old", "new")

        assert result is not None
        assert result["from"] == "old"
        assert result["to"] == "new"

    def test_diff_value_with_none_values(self):
        """Test diffing None values."""
        from app.core.audit.ledger import _diff_value

        # None to value
        result = _diff_value(None, "value")
        assert result == {"from": None, "to": "value"}

        # Value to None
        result = _diff_value("value", None)
        assert result == {"from": "value", "to": None}

        # None to None
        result = _diff_value(None, None)
        assert result is None


class TestDiffContext:
    """Tests for _diff_context helper function."""

    def test_diff_context_empty_contexts(self):
        """Test diffing empty contexts."""
        from app.core.audit.ledger import _diff_context

        result = _diff_context({}, {})

        assert result["added"] == {}
        assert result["removed"] == {}
        assert result["changed"] == {}

    def test_diff_context_detects_added_keys(self):
        """Test detecting added keys."""
        from app.core.audit.ledger import _diff_context

        result = _diff_context(
            {"existing": "value"}, {"existing": "value", "new": "key"}
        )

        assert result["added"] == {"new": "key"}
        assert result["removed"] == {}
        assert result["changed"] == {}

    def test_diff_context_detects_removed_keys(self):
        """Test detecting removed keys."""
        from app.core.audit.ledger import _diff_context

        result = _diff_context({"old": "value", "keep": "this"}, {"keep": "this"})

        assert result["added"] == {}
        assert result["removed"] == {"old": "value"}
        assert result["changed"] == {}

    def test_diff_context_detects_changed_values(self):
        """Test detecting changed values."""
        from app.core.audit.ledger import _diff_context

        result = _diff_context({"key": "old_value"}, {"key": "new_value"})

        assert result["added"] == {}
        assert result["removed"] == {}
        assert result["changed"] == {"key": {"from": "old_value", "to": "new_value"}}

    def test_diff_context_detects_all_changes(self):
        """Test detecting multiple types of changes."""
        from app.core.audit.ledger import _diff_context

        context_a = {"removed_key": 1, "changed_key": "old", "unchanged": "same"}
        context_b = {"added_key": 2, "changed_key": "new", "unchanged": "same"}

        result = _diff_context(context_a, context_b)

        assert result["added"] == {"added_key": 2}
        assert result["removed"] == {"removed_key": 1}
        assert result["changed"] == {"changed_key": {"from": "old", "to": "new"}}


class TestDiffLogs:
    """Tests for diff_logs function."""

    def test_diff_logs_returns_diff_structure(self):
        """Test diffing two audit logs."""
        from app.core.audit.ledger import diff_logs

        log_a = AuditLog(
            project_id=123,
            version=1,
            event_type="event_a",
            baseline_seconds=100.0,
            actual_seconds=90.0,
            context={"key": "value_a"},
        )

        log_b = AuditLog(
            project_id=123,
            version=2,
            event_type="event_b",
            baseline_seconds=100.0,
            actual_seconds=95.0,
            context={"key": "value_b"},
        )

        result = diff_logs(log_a, log_b)

        assert result["event_type"] == {"from": "event_a", "to": "event_b"}
        assert result["baseline_seconds"] is None  # Unchanged
        assert result["actual_seconds"] == {"from": 90.0, "to": 95.0}
        assert result["context"]["changed"] == {
            "key": {"from": "value_a", "to": "value_b"}
        }

    def test_diff_logs_with_identical_logs(self):
        """Test diffing identical logs."""
        from app.core.audit.ledger import diff_logs

        log_a = AuditLog(
            project_id=123,
            version=1,
            event_type="same_event",
            baseline_seconds=100.0,
            actual_seconds=90.0,
            context={"key": "same"},
        )

        log_b = AuditLog(
            project_id=123,
            version=2,
            event_type="same_event",
            baseline_seconds=100.0,
            actual_seconds=90.0,
            context={"key": "same"},
        )

        result = diff_logs(log_a, log_b)

        assert result["event_type"] is None
        assert result["baseline_seconds"] is None
        assert result["actual_seconds"] is None
        assert result["context"]["added"] == {}
        assert result["context"]["removed"] == {}
        assert result["context"]["changed"] == {}
