import pytest
from pydantic import ValidationError
from app.services.feasibility import (
    normalise_project_payload,
    normalise_assessment_payload,
)


def test_normalise_project_payload_snake_case():
    input_data = {
        "name": "Test Project",
        "site_address": "123 Test St",
        "site_area_sqm": 1000.0,
        "land_use": "Residential",
        "target_gross_floor_area_sqm": 2000.0,
        "building_height_meters": 50.0,
        "build_envelope": {"site_area_sqm": 1000.0, "allowable_plot_ratio": 2.0},
    }
    result = normalise_project_payload(input_data)
    assert result["name"] == "Test Project"
    assert result["site_area_sqm"] == 1000.0
    assert result["build_envelope"]["allowable_plot_ratio"] == 2.0


def test_normalise_project_payload_camel_case():
    input_data = {
        "name": "Test Project",
        "siteAddress": "123 Test St",
        "siteAreaSqm": 1000.0,
        "landUse": "Residential",
        "targetGrossFloorAreaSqm": 2000.0,
        "buildingHeightMeters": 50.0,
        "buildEnvelope": {"siteAreaSqm": 1000.0, "allowablePlotRatio": 2.0},
    }
    result = normalise_project_payload(input_data)
    # Result should be normalised to snake_case storage format
    # (if model_dump uses by_alias=False by default).
    # Default model_dump() uses field names (snake_case).
    assert result["site_address"] == "123 Test St"
    assert result["site_area_sqm"] == 1000.0
    assert result["build_envelope"]["allowable_plot_ratio"] == 2.0


def test_normalise_project_payload_validation_error():
    input_data = {
        "name": "Invalid Project",
        "site_address": "123 Test St",
        # Missing site_area_sqm
        "land_use": "Residential",
    }
    with pytest.raises(ValidationError):
        normalise_project_payload(input_data)


def test_normalise_assessment_payload_camel_case():
    input_data = {
        "project": {
            "name": "Test Project",
            "siteAddress": "123 Test St",
            "siteAreaSqm": 1000.0,
            "landUse": "Residential",
        },
        "selectedRuleIds": ["rule1", "rule2"],
    }
    result = normalise_assessment_payload(input_data)
    assert result["project"]["site_address"] == "123 Test St"
    assert result["selected_rule_ids"] == ["rule1", "rule2"]


def test_normalise_assessment_payload_mixed_case():
    # Frontend might send snake_case for some fields if they were pre-processed
    input_data = {
        "project": {
            "name": "Test Project",
            "site_address": "123 Test St",
            "site_area_sqm": 1000.0,
            "land_use": "Residential",
        },
        "selected_rule_ids": ["rule1", "rule2"],
    }
    result = normalise_assessment_payload(input_data)
    assert result["project"]["site_address"] == "123 Test St"
    assert result["selected_rule_ids"] == ["rule1", "rule2"]
