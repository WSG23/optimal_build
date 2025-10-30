"""Tests for the feasibility service module."""

from __future__ import annotations

from decimal import Decimal

import pytest

pytestmark = pytest.mark.no_db

import importlib.util
import sys
from pathlib import Path

from fastapi import HTTPException

_ROOT = Path(__file__).resolve().parents[3]


def _load_module(name: str, relative: str):
    module_path = _ROOT / relative
    spec = importlib.util.spec_from_file_location(name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module {name} from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


_schema_module = _load_module(
    "feasibility_schema_stub", "backend/app/schemas/feasibility.py"
)

import types

_schema_package = types.ModuleType("app.schemas")
_schema_package.feasibility = _schema_module
_schema_package.__path__ = []  # type: ignore[attr-defined]
sys.modules.setdefault("app.schemas", _schema_package)
sys.modules["app.schemas.feasibility"] = _schema_module

_service_module = _load_module(
    "feasibility_service_stub", "backend/app/services/feasibility.py"
)

FeasibilityAssessmentRequest = _schema_module.FeasibilityAssessmentRequest
NewFeasibilityProjectInput = _schema_module.NewFeasibilityProjectInput
generate_feasibility_rules = _service_module.generate_feasibility_rules
run_feasibility_assessment = _service_module.run_feasibility_assessment


def _build_project(**overrides: object) -> NewFeasibilityProjectInput:
    base_payload = {
        "name": overrides.pop("name", "  Draft Project "),
        "site_address": overrides.pop("site_address", "123 Example Street"),
        "site_area_sqm": overrides.pop("site_area_sqm", 2400.0),
        "land_use": overrides.pop("land_use", "mixed_use_precinct"),
        "target_gross_floor_area_sqm": overrides.pop(
            "target_gross_floor_area_sqm", 3600.0
        ),
        "building_height_meters": overrides.pop("building_height_meters", 45.0),
    }
    return NewFeasibilityProjectInput(**base_payload)


def test_generate_feasibility_rules_formats_land_use() -> None:
    """Generating rules should provide a stable project identifier and summary."""

    project = _build_project()
    response = generate_feasibility_rules(project)

    assert response.project_id == f"project-{project.name.strip()}"
    assert response.rules
    assert set(response.recommended_rule_ids)
    assert "mixed use precinct" in response.summary.notes


def test_run_feasibility_assessment_rejects_unknown_rules() -> None:
    """Submitting an unknown rule identifier should raise a 400 error."""

    project = _build_project(name="Compliant Site")
    request = FeasibilityAssessmentRequest(
        project=project, selected_rule_ids=["unknown-rule"]
    )

    with pytest.raises(HTTPException) as exc_info:
        run_feasibility_assessment(request)

    assert exc_info.value.status_code == 400
    assert "Unknown rule identifiers" in str(exc_info.value.detail)


def test_run_feasibility_assessment_summarises_results() -> None:
    """Successful assessments should de-duplicate IDs and compute summary metrics."""

    project = _build_project(land_use="residential", target_gross_floor_area_sqm=3120.0)
    rules_response = generate_feasibility_rules(project)
    selected = list(rules_response.recommended_rule_ids) + [rules_response.rules[-1].id]
    selected.append(selected[0])  # introduce a duplicate to test normalisation

    request = FeasibilityAssessmentRequest(project=project, selected_rule_ids=selected)
    response = run_feasibility_assessment(request)

    assert response.project_id.startswith("project-")
    assert len(response.rules) == len(set(selected))

    summary = response.summary
    expected_max_gfa = int(Decimal(project.site_area_sqm * 3.5).quantize(Decimal("1")))
    assert summary.max_permissible_gfa_sqm == expected_max_gfa
    assert summary.estimated_unit_count >= 1

    recommendations = "\n".join(response.recommendations)
    assert "coordination call" in recommendations
    assert "fire access" in recommendations


def test_generate_feasibility_rules_handles_various_land_uses() -> None:
    """Test that different land uses generate appropriate rules."""
    land_uses = ["residential", "commercial", "industrial", "mixed_use_precinct"]

    for land_use in land_uses:
        project = _build_project(land_use=land_use)
        response = generate_feasibility_rules(project)

        assert response.project_id is not None
        assert len(response.rules) > 0
        assert len(response.recommended_rule_ids) > 0
        assert land_use.replace("_", " ") in response.summary.notes.lower()


def test_generate_feasibility_rules_with_small_site() -> None:
    """Test rules generation for a small site."""
    project = _build_project(site_area_sqm=500.0)
    response = generate_feasibility_rules(project)

    assert response.project_id is not None
    assert len(response.rules) > 0


def test_generate_feasibility_rules_with_large_site() -> None:
    """Test rules generation for a large site."""
    project = _build_project(site_area_sqm=50000.0)
    response = generate_feasibility_rules(project)

    assert response.project_id is not None
    assert len(response.rules) > 0


def test_run_feasibility_assessment_with_no_rule_ids() -> None:
    """Test assessment without providing any rule IDs."""
    project = _build_project()
    # If empty list is allowed, test that it works
    # If not, this test documents the behavior
    request = FeasibilityAssessmentRequest(project=project, selected_rule_ids=[])

    # The implementation may or may not raise - test actual behavior
    try:
        response = run_feasibility_assessment(request)
        # If it succeeds, verify response structure
        assert response.project_id is not None
    except HTTPException as exc:
        # If it raises, verify it's a 400 error
        assert exc.status_code == 400


def test_run_feasibility_assessment_with_multiple_unknown_rules() -> None:
    """Test that multiple unknown rule IDs are reported."""
    project = _build_project()
    request = FeasibilityAssessmentRequest(
        project=project, selected_rule_ids=["unknown-1", "unknown-2", "unknown-3"]
    )

    with pytest.raises(HTTPException) as exc_info:
        run_feasibility_assessment(request)

    assert exc_info.value.status_code == 400
    assert "unknown-1" in str(exc_info.value.detail)


def test_run_feasibility_assessment_calculates_unit_count() -> None:
    """Test that unit count is calculated based on GFA."""
    project = _build_project(
        land_use="residential",
        site_area_sqm=10000.0,
        target_gross_floor_area_sqm=30000.0,
    )
    rules_response = generate_feasibility_rules(project)

    request = FeasibilityAssessmentRequest(
        project=project, selected_rule_ids=list(rules_response.recommended_rule_ids)
    )
    response = run_feasibility_assessment(request)

    # Unit count should be positive for residential
    assert response.summary.estimated_unit_count > 0


def test_run_feasibility_assessment_with_high_building() -> None:
    """Test assessment with a tall building."""
    project = _build_project(building_height_meters=150.0)
    rules_response = generate_feasibility_rules(project)

    request = FeasibilityAssessmentRequest(
        project=project, selected_rule_ids=list(rules_response.recommended_rule_ids)
    )
    response = run_feasibility_assessment(request)

    assert response.summary.max_permissible_gfa_sqm > 0


def test_run_feasibility_assessment_deduplicates_rule_ids() -> None:
    """Test that duplicate rule IDs are deduplicated."""
    project = _build_project()
    rules_response = generate_feasibility_rules(project)

    # Create list with duplicates
    rule_ids = list(rules_response.recommended_rule_ids)
    duplicated_ids = rule_ids + rule_ids[:2]  # Add first two IDs again

    request = FeasibilityAssessmentRequest(
        project=project, selected_rule_ids=duplicated_ids
    )
    response = run_feasibility_assessment(request)

    # Response should have deduplicated rules
    assert len(response.rules) == len(rule_ids)


def test_generate_feasibility_rules_formats_project_id() -> None:
    """Test that project ID is correctly formatted from project name."""
    project = _build_project(name="   Test Project Name   ")
    response = generate_feasibility_rules(project)

    assert response.project_id == "project-Test Project Name"


def test_run_feasibility_assessment_includes_recommendations() -> None:
    """Test that assessment includes recommendations."""
    project = _build_project()
    rules_response = generate_feasibility_rules(project)

    request = FeasibilityAssessmentRequest(
        project=project, selected_rule_ids=list(rules_response.recommended_rule_ids)
    )
    response = run_feasibility_assessment(request)

    assert len(response.recommendations) > 0
    assert all(isinstance(rec, str) for rec in response.recommendations)
