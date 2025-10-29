"""Tests for the feasibility service module."""

from __future__ import annotations

from decimal import Decimal

import pytest

pytestmark = pytest.mark.no_db

from fastapi import HTTPException

import importlib.util
import sys
from pathlib import Path

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
        "target_gross_floor_area_sqm": overrides.pop("target_gross_floor_area_sqm", 3600.0),
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
    request = FeasibilityAssessmentRequest(project=project, selected_rule_ids=["unknown-rule"])

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
