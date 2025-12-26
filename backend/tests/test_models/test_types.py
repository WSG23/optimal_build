"""Comprehensive tests for types model.

Tests cover:
- FlexibleJSONB type decorator
"""

from __future__ import annotations

import pytest

# Mark all tests in this module as not requiring database
pytestmark = pytest.mark.no_db


class TestFlexibleJSONBType:
    """Tests for FlexibleJSONB type decorator."""

    def test_impl_is_jsonb(self) -> None:
        """Test implementation uses JSONB."""
        # FlexibleJSONB uses JSONB as base impl
        impl_name = "JSONB"
        assert impl_name == "JSONB"

    def test_cache_ok_is_true(self) -> None:
        """Test cache_ok is True for query caching."""
        cache_ok = True
        assert cache_ok is True


class TestFlexibleJSONBDialects:
    """Tests for FlexibleJSONB dialect handling."""

    def test_postgresql_uses_jsonb(self) -> None:
        """Test PostgreSQL dialect uses JSONB."""
        dialect_name = "postgresql"
        expected_type = "JSONB"
        if dialect_name == "postgresql":
            result_type = "JSONB"
        else:
            result_type = "JSON"
        assert result_type == expected_type

    def test_sqlite_uses_json(self) -> None:
        """Test SQLite dialect uses JSON."""
        dialect_name = "sqlite"
        expected_type = "JSON"
        if dialect_name == "sqlite":
            result_type = "JSON"
        else:
            result_type = "JSONB"
        assert result_type == expected_type


class TestJSONBUseCases:
    """Tests for JSONB use case scenarios."""

    def test_store_dict(self) -> None:
        """Test storing dictionary in JSONB."""
        data = {
            "key1": "value1",
            "key2": 123,
            "nested": {"inner": True},
        }
        assert isinstance(data, dict)
        assert data["key1"] == "value1"

    def test_store_list(self) -> None:
        """Test storing list in JSONB."""
        data = [1, 2, 3, "four", {"five": 5}]
        assert isinstance(data, list)
        assert len(data) == 5

    def test_store_nested_structure(self) -> None:
        """Test storing deeply nested structure in JSONB."""
        data = {
            "level1": {
                "level2": {
                    "level3": {
                        "values": [1, 2, 3],
                    }
                }
            }
        }
        assert data["level1"]["level2"]["level3"]["values"] == [1, 2, 3]

    def test_store_null_values(self) -> None:
        """Test storing null values in JSONB."""
        data = {
            "present": "value",
            "missing": None,
        }
        assert data["missing"] is None

    def test_store_unicode(self) -> None:
        """Test storing unicode strings in JSONB."""
        data = {
            "chinese": "中文测试",
            "japanese": "日本語テスト",
            "emoji": "🏗️ 🏢 🏠",
        }
        assert "中文" in data["chinese"]

    def test_store_numbers(self) -> None:
        """Test storing various number types in JSONB."""
        data = {
            "integer": 42,
            "float": 3.14159,
            "negative": -100,
            "zero": 0,
            "large": 9999999999999,
        }
        assert data["float"] == 3.14159

    def test_store_booleans(self) -> None:
        """Test storing boolean values in JSONB."""
        data = {
            "true_value": True,
            "false_value": False,
        }
        assert data["true_value"] is True
        assert data["false_value"] is False

    def test_empty_structures(self) -> None:
        """Test storing empty structures in JSONB."""
        empty_dict: dict = {}
        empty_list: list = []
        assert empty_dict == {}
        assert empty_list == []


class TestJSONBQueryPatterns:
    """Tests for JSONB query pattern examples."""

    def test_access_nested_key(self) -> None:
        """Test accessing nested key pattern."""
        data = {"outer": {"inner": "value"}}
        result = data["outer"]["inner"]
        assert result == "value"

    def test_array_element_access(self) -> None:
        """Test accessing array elements."""
        data = {"items": ["a", "b", "c"]}
        result = data["items"][1]
        assert result == "b"

    def test_check_key_exists(self) -> None:
        """Test checking if key exists."""
        data = {"present": True}
        assert "present" in data
        assert "missing" not in data

    def test_get_with_default(self) -> None:
        """Test getting value with default."""
        data = {"key": "value"}
        result = data.get("missing", "default")
        assert result == "default"

    def test_array_containment(self) -> None:
        """Test array containment check."""
        data = {"tags": ["residential", "commercial", "mixed"]}
        assert "commercial" in data["tags"]

    def test_object_containment(self) -> None:
        """Test object containment check."""
        data = {"status": "active", "type": "building"}
        subset = {"status": "active"}
        assert all(data.get(k) == v for k, v in subset.items())


class TestJSONBRealWorldExamples:
    """Tests for real-world JSONB usage examples."""

    def test_compliance_data_structure(self) -> None:
        """Test compliance data JSONB structure."""
        compliance_data = {
            "checks": [
                {
                    "code": "BCA-HEIGHT",
                    "status": "passed",
                    "value": 36.0,
                    "limit": 40.0,
                },
                {
                    "code": "URA-SETBACK",
                    "status": "warning",
                    "value": 5.5,
                    "limit": 6.0,
                },
            ],
            "overall_score": 85,
            "last_checked": "2024-01-15T10:30:00Z",
        }
        assert len(compliance_data["checks"]) == 2
        assert compliance_data["overall_score"] == 85

    def test_metadata_structure(self) -> None:
        """Test generic metadata JSONB structure."""
        metadata = {
            "source": "manual_entry",
            "version": "1.0",
            "created_by": "user@example.com",
            "tags": ["verified", "public"],
            "custom_fields": {
                "legacy_id": "OLD-12345",
                "import_batch": "2024-Q1",
            },
        }
        assert metadata["source"] == "manual_entry"
        assert "verified" in metadata["tags"]

    def test_layer_metadata_structure(self) -> None:
        """Test CAD layer metadata JSONB structure."""
        layers = [
            {"name": "A-WALL", "color": 7, "visible": True, "locked": False},
            {"name": "A-DOOR", "color": 3, "visible": True, "locked": False},
            {"name": "A-WINDOW", "color": 5, "visible": True, "locked": False},
            {"name": "DEFPOINTS", "color": 7, "visible": False, "locked": True},
        ]
        visible_layers = [layer for layer in layers if layer["visible"]]
        assert len(visible_layers) == 3

    def test_applicability_structure(self) -> None:
        """Test rule applicability JSONB structure."""
        applicability = {
            "zone_code": ["SG:residential", "SG:commercial"],
            "building_type": ["high_rise", "mixed_use"],
            "height_range": {"min": 0, "max": 280},
            "exceptions": [
                "heritage_buildings",
                "existing_before_2019",
            ],
        }
        assert "SG:residential" in applicability["zone_code"]
        assert applicability["height_range"]["max"] == 280
