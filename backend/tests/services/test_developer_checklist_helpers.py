"""Additional unit tests for developer checklist service helper functions."""

from __future__ import annotations

import pytest

from app.models.developer_checklists import (
    ChecklistCategory,
    ChecklistPriority,
)

# Import private functions for testing
from app.services import developer_checklist_service as dcs_module

_new_summary_bucket = dcs_module._new_summary_bucket
_coerce_category = dcs_module._coerce_category
_coerce_priority = dcs_module._coerce_priority


# -----------------------------------------------------------
# _new_summary_bucket tests
# -----------------------------------------------------------


def test_new_summary_bucket_returns_zeroes():
    """Test new summary bucket initializes to zeros."""
    bucket = _new_summary_bucket()

    assert bucket["total"] == 0
    assert bucket["pending"] == 0
    assert bucket["in_progress"] == 0
    assert bucket["completed"] == 0
    assert bucket["not_applicable"] == 0


def test_new_summary_bucket_returns_new_instance():
    """Test new summary bucket returns a new instance each time."""
    bucket1 = _new_summary_bucket()
    bucket2 = _new_summary_bucket()

    bucket1["total"] = 10
    assert bucket2["total"] == 0  # Independent instance


# -----------------------------------------------------------
# _coerce_category tests
# -----------------------------------------------------------


def test_coerce_category_from_enum_title_verification():
    """Test coercing title_verification category from enum."""
    result = _coerce_category(ChecklistCategory.TITLE_VERIFICATION)
    assert result == ChecklistCategory.TITLE_VERIFICATION


def test_coerce_category_from_enum_zoning():
    """Test coercing zoning category from enum."""
    result = _coerce_category(ChecklistCategory.ZONING_COMPLIANCE)
    assert result == ChecklistCategory.ZONING_COMPLIANCE


def test_coerce_category_from_string_title_verification():
    """Test coercing category from string."""
    result = _coerce_category("title_verification")
    assert result == ChecklistCategory.TITLE_VERIFICATION


def test_coerce_category_from_string_zoning():
    """Test coercing zoning from string."""
    result = _coerce_category("zoning_compliance")
    assert result == ChecklistCategory.ZONING_COMPLIANCE


def test_coerce_category_from_string_environmental():
    """Test coercing environmental from string."""
    result = _coerce_category("environmental_assessment")
    assert result == ChecklistCategory.ENVIRONMENTAL_ASSESSMENT


def test_coerce_category_from_invalid_raises():
    """Test coercing category from invalid value raises."""
    with pytest.raises(ValueError):
        _coerce_category("invalid_category")


def test_coerce_category_from_none_raises():
    """Test coercing category from None raises."""
    with pytest.raises((ValueError, TypeError)):
        _coerce_category(None)


# -----------------------------------------------------------
# _coerce_priority tests
# -----------------------------------------------------------


def test_coerce_priority_from_enum_critical():
    """Test coercing critical priority from enum."""
    result = _coerce_priority(ChecklistPriority.CRITICAL)
    assert result == ChecklistPriority.CRITICAL


def test_coerce_priority_from_enum_high():
    """Test coercing high priority from enum."""
    result = _coerce_priority(ChecklistPriority.HIGH)
    assert result == ChecklistPriority.HIGH


def test_coerce_priority_from_enum_medium():
    """Test coercing medium priority from enum."""
    result = _coerce_priority(ChecklistPriority.MEDIUM)
    assert result == ChecklistPriority.MEDIUM


def test_coerce_priority_from_string_critical():
    """Test coercing priority from string."""
    result = _coerce_priority("critical")
    assert result == ChecklistPriority.CRITICAL


def test_coerce_priority_from_string_high():
    """Test coercing high from string."""
    result = _coerce_priority("high")
    assert result == ChecklistPriority.HIGH


def test_coerce_priority_from_string_low():
    """Test coercing low from string."""
    result = _coerce_priority("low")
    assert result == ChecklistPriority.LOW


def test_coerce_priority_from_invalid_raises():
    """Test coercing priority from invalid value raises."""
    with pytest.raises(ValueError):
        _coerce_priority("invalid_priority")


def test_coerce_priority_from_none_raises():
    """Test coercing priority from None raises."""
    with pytest.raises((ValueError, TypeError)):
        _coerce_priority(None)


# -----------------------------------------------------------
# _normalise_definition tests
# -----------------------------------------------------------

_normalise_definition = dcs_module._normalise_definition


def test_normalise_definition_basic():
    """Test normalizing a valid definition with required fields."""
    input_def = {
        "development_scenario": "new_build",
        "item_title": "Title Search",
        "category": ChecklistCategory.TITLE_VERIFICATION,
        "priority": ChecklistPriority.HIGH,
    }
    result = _normalise_definition(input_def)

    assert result["development_scenario"] == "new_build"
    assert result["item_title"] == "Title Search"
    assert result["category"] == ChecklistCategory.TITLE_VERIFICATION
    assert result["priority"] == ChecklistPriority.HIGH
    assert result["item_description"] is None
    assert result["typical_duration_days"] is None
    assert result["requires_professional"] is False
    assert result["professional_type"] is None
    assert result["display_order"] is None


def test_normalise_definition_with_all_fields():
    """Test normalizing a definition with all fields populated."""
    input_def = {
        "development_scenario": "redevelopment",
        "item_title": "Environmental Assessment",
        "category": "environmental_assessment",
        "priority": "critical",
        "item_description": "Full environmental impact study",
        "typical_duration_days": 30,
        "requires_professional": True,
        "professional_type": "Environmental Consultant",
        "display_order": 5,
    }
    result = _normalise_definition(input_def)

    assert result["development_scenario"] == "redevelopment"
    assert result["item_title"] == "Environmental Assessment"
    assert result["category"] == ChecklistCategory.ENVIRONMENTAL_ASSESSMENT
    assert result["priority"] == ChecklistPriority.CRITICAL
    assert result["item_description"] == "Full environmental impact study"
    assert result["typical_duration_days"] == 30
    assert result["requires_professional"] is True
    assert result["professional_type"] == "Environmental Consultant"
    assert result["display_order"] == 5


def test_normalise_definition_missing_scenario_raises():
    """Test normalizing a definition without development_scenario raises."""
    input_def = {
        "item_title": "Title Search",
        "category": ChecklistCategory.TITLE_VERIFICATION,
        "priority": ChecklistPriority.HIGH,
    }
    with pytest.raises(ValueError, match="development_scenario is required"):
        _normalise_definition(input_def)


def test_normalise_definition_empty_scenario_raises():
    """Test normalizing a definition with empty scenario raises."""
    input_def = {
        "development_scenario": "   ",
        "item_title": "Title Search",
        "category": ChecklistCategory.TITLE_VERIFICATION,
        "priority": ChecklistPriority.HIGH,
    }
    with pytest.raises(ValueError, match="development_scenario is required"):
        _normalise_definition(input_def)


def test_normalise_definition_missing_title_raises():
    """Test normalizing a definition without item_title raises."""
    input_def = {
        "development_scenario": "new_build",
        "category": ChecklistCategory.TITLE_VERIFICATION,
        "priority": ChecklistPriority.HIGH,
    }
    with pytest.raises(ValueError, match="item_title is required"):
        _normalise_definition(input_def)


def test_normalise_definition_empty_title_raises():
    """Test normalizing a definition with empty title raises."""
    input_def = {
        "development_scenario": "new_build",
        "item_title": "  ",
        "category": ChecklistCategory.TITLE_VERIFICATION,
        "priority": ChecklistPriority.HIGH,
    }
    with pytest.raises(ValueError, match="item_title is required"):
        _normalise_definition(input_def)


def test_normalise_definition_strips_whitespace():
    """Test normalizing strips whitespace from string fields."""
    input_def = {
        "development_scenario": "  new_build  ",
        "item_title": "  Title Search  ",
        "category": ChecklistCategory.TITLE_VERIFICATION,
        "priority": ChecklistPriority.HIGH,
        "item_description": "  Description with spaces  ",
    }
    result = _normalise_definition(input_def)

    assert result["development_scenario"] == "new_build"
    assert result["item_title"] == "Title Search"
    assert result["item_description"] == "Description with spaces"


def test_normalise_definition_empty_description_becomes_none():
    """Test normalizing converts empty description to None."""
    input_def = {
        "development_scenario": "new_build",
        "item_title": "Title Search",
        "category": ChecklistCategory.TITLE_VERIFICATION,
        "priority": ChecklistPriority.HIGH,
        "item_description": "",
    }
    result = _normalise_definition(input_def)

    assert result["item_description"] is None


def test_normalise_definition_duration_string_converted():
    """Test normalizing converts string duration to int."""
    input_def = {
        "development_scenario": "new_build",
        "item_title": "Title Search",
        "category": ChecklistCategory.TITLE_VERIFICATION,
        "priority": ChecklistPriority.HIGH,
        "typical_duration_days": "14",
    }
    result = _normalise_definition(input_def)

    assert result["typical_duration_days"] == 14


def test_normalise_definition_empty_duration_becomes_none():
    """Test normalizing converts empty duration to None."""
    input_def = {
        "development_scenario": "new_build",
        "item_title": "Title Search",
        "category": ChecklistCategory.TITLE_VERIFICATION,
        "priority": ChecklistPriority.HIGH,
        "typical_duration_days": "",
    }
    result = _normalise_definition(input_def)

    assert result["typical_duration_days"] is None


def test_normalise_definition_professional_type_cleared_when_not_required():
    """Test professional_type is cleared when requires_professional is False."""
    input_def = {
        "development_scenario": "new_build",
        "item_title": "Title Search",
        "category": ChecklistCategory.TITLE_VERIFICATION,
        "priority": ChecklistPriority.HIGH,
        "requires_professional": False,
        "professional_type": "Lawyer",
    }
    result = _normalise_definition(input_def)

    assert result["requires_professional"] is False
    assert result["professional_type"] is None


def test_normalise_definition_display_order_string_converted():
    """Test normalizing converts string display_order to int."""
    input_def = {
        "development_scenario": "new_build",
        "item_title": "Title Search",
        "category": ChecklistCategory.TITLE_VERIFICATION,
        "priority": ChecklistPriority.HIGH,
        "display_order": "10",
    }
    result = _normalise_definition(input_def)

    assert result["display_order"] == 10


def test_normalise_definition_empty_display_order_becomes_none():
    """Test normalizing converts empty display_order to None."""
    input_def = {
        "development_scenario": "new_build",
        "item_title": "Title Search",
        "category": ChecklistCategory.TITLE_VERIFICATION,
        "priority": ChecklistPriority.HIGH,
        "display_order": "",
    }
    result = _normalise_definition(input_def)

    assert result["display_order"] is None
