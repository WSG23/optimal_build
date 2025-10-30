"""Tests for performance flow helper functions."""

from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

import pytest

pytestmark = pytest.mark.no_db

import importlib.util
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]


def _load_module(name: str, relative_path: str):
    module_path = _ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module {name} from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


_perf_module = _load_module(
    "performance_flows_stub", "backend/app/flows/performance.py"
)

_parse_agent_ids = _perf_module._parse_agent_ids
_parse_date = _perf_module._parse_date


def test_parse_agent_ids_with_valid_uuids() -> None:
    """Test parsing valid UUID strings."""
    uuid1 = str(uuid4())
    uuid2 = str(uuid4())

    result = _parse_agent_ids([uuid1, uuid2])

    assert result is not None
    assert len(result) == 2
    assert all(isinstance(id, UUID) for id in result)
    assert str(result[0]) == uuid1
    assert str(result[1]) == uuid2


def test_parse_agent_ids_with_none() -> None:
    """Test that None input returns None."""
    result = _parse_agent_ids(None)
    assert result is None


def test_parse_agent_ids_with_empty_list() -> None:
    """Test that empty list returns None."""
    result = _parse_agent_ids([])
    assert result is None


def test_parse_agent_ids_filters_invalid_uuids() -> None:
    """Test that invalid UUIDs are filtered out."""
    valid_uuid = str(uuid4())
    invalid_uuids = ["not-a-uuid", "12345", "invalid"]

    result = _parse_agent_ids([valid_uuid] + invalid_uuids)

    assert result is not None
    assert len(result) == 1
    assert str(result[0]) == valid_uuid


def test_parse_agent_ids_returns_none_if_all_invalid() -> None:
    """Test that None is returned if all UUIDs are invalid."""
    invalid_uuids = ["not-a-uuid", "invalid", "123"]

    result = _parse_agent_ids(invalid_uuids)

    assert result is None


def test_parse_date_with_valid_iso_date() -> None:
    """Test parsing valid ISO format date."""
    result = _parse_date("2024-01-15")

    assert result is not None
    assert result == date(2024, 1, 15)


def test_parse_date_with_none() -> None:
    """Test that None input returns None."""
    result = _parse_date(None)
    assert result is None


def test_parse_date_with_empty_string() -> None:
    """Test that empty string returns None."""
    result = _parse_date("")
    assert result is None


def test_parse_date_with_whitespace_only() -> None:
    """Test that whitespace-only string returns None."""
    result = _parse_date("   ")
    assert result is None


def test_parse_date_with_padded_whitespace() -> None:
    """Test that date with surrounding whitespace is parsed correctly."""
    result = _parse_date("  2024-03-20  ")

    assert result is not None
    assert result == date(2024, 3, 20)


def test_parse_agent_ids_with_mixed_valid_invalid() -> None:
    """Test parsing a mix of valid and invalid UUIDs."""
    uuid1 = str(uuid4())
    uuid2 = str(uuid4())
    mixed = [uuid1, "invalid1", uuid2, "invalid2", "not-uuid"]

    result = _parse_agent_ids(mixed)

    assert result is not None
    assert len(result) == 2
    assert str(result[0]) == uuid1
    assert str(result[1]) == uuid2


def test_parse_agent_ids_handles_type_errors() -> None:
    """Test that TypeErrors in UUID parsing are handled gracefully."""
    # This should handle cases where the input can't be converted to UUID
    result = _parse_agent_ids([None, "valid-looking-but-not-uuid"])

    # Should filter out both
    assert result is None or len(result) == 0
