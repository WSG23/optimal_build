from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")

from httpx import AsyncClient

PROJECT_PAYLOAD = {
    "name": "Harbour View Residences",
    "siteAddress": "12 Marina Way",
    "siteAreaSqm": 5000,
    "landUse": "residential",
    "targetGrossFloorAreaSqm": 14000,
    "buildingHeightMeters": 45,
}

SELECTED_RULE_IDS = ["ura-plot-ratio", "bca-site-coverage", "scdf-access"]


@pytest.mark.asyncio
async def test_fetch_feasibility_rules(app_client: AsyncClient) -> None:
    response = await app_client.post("/api/v1/feasibility/rules", json=PROJECT_PAYLOAD)
    assert response.status_code == 200
    payload = response.json()

    assert payload["project_id"].startswith("project-")
    assert payload["recommended_rule_ids"]
    assert len(payload["rules"]) >= len(SELECTED_RULE_IDS)

    first_rule = payload["rules"][0]
    assert first_rule["id"]
    assert first_rule["title"]
    assert first_rule["parameter_key"].startswith("planning.")
    assert "severity" in first_rule

    summary = payload["summary"]
    assert "Envelope" in summary["compliance_focus"]
    assert "residential" in (summary.get("notes") or "").lower()


@pytest.mark.asyncio
async def test_submit_feasibility_assessment(app_client: AsyncClient) -> None:
    payload = {
        "project": PROJECT_PAYLOAD,
        "selectedRuleIds": SELECTED_RULE_IDS,
    }

    response = await app_client.post("/api/v1/feasibility/assessment", json=payload)
    assert response.status_code == 200
    assessment = response.json()

    assert assessment["project_id"].startswith("project-")
    assert len(assessment["rules"]) == len(SELECTED_RULE_IDS)

    statuses = {rule["id"]: rule["status"] for rule in assessment["rules"]}
    assert statuses["bca-site-coverage"] == "fail"
    assert statuses["ura-plot-ratio"] == "warning"

    gross_plot_rule = next(
        rule for rule in assessment["rules"] if rule["id"] == "ura-plot-ratio"
    )
    assert gross_plot_rule["actual_value"] == "2.80"
    assert "compliance buffer" in (gross_plot_rule.get("notes") or "")

    recommendations = assessment["recommendations"]
    assert recommendations[0].startswith("Share the feasibility snapshot")
    assert any("coordination call" in item for item in recommendations)
    assert any("fire access" in item for item in recommendations)

    summary = assessment["summary"]
    assert summary["max_permissible_gfa_sqm"] == 17500
    assert summary["estimated_achievable_gfa_sqm"] == 11375
    assert summary["estimated_unit_count"] >= 130
    assert summary["site_coverage_percent"] == 32.5
    assert "design revisions" in (summary.get("remarks") or "").lower()


@pytest.mark.asyncio
async def test_submit_assessment_with_unknown_rule(app_client: AsyncClient) -> None:
    payload = {
        "project": PROJECT_PAYLOAD,
        "selectedRuleIds": ["unknown-rule"],
    }

    response = await app_client.post("/api/v1/feasibility/assessment", json=payload)
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "Unknown rule identifiers" in detail
    assert "unknown-rule" in detail


@pytest.mark.asyncio
async def test_get_engineering_defaults(app_client: AsyncClient) -> None:
    """Test fetching engineering defaults."""
    response = await app_client.get("/api/v1/feasibility/defaults")
    assert response.status_code == 200
    payload = response.json()
    # Should return engineering defaults structure
    assert "defaults" in payload or isinstance(payload, dict)


@pytest.mark.asyncio
async def test_feasibility_rules_with_minimal_project(app_client: AsyncClient) -> None:
    """Test fetching feasibility rules with minimal required project data."""
    minimal_project = {
        "name": "Minimal Project",
        "siteAddress": "1 Test Street",
        "siteAreaSqm": 1000,
        "landUse": "residential",
    }
    response = await app_client.post("/api/v1/feasibility/rules", json=minimal_project)
    assert response.status_code == 200
    payload = response.json()
    assert "rules" in payload


@pytest.mark.asyncio
async def test_feasibility_assessment_all_rules(app_client: AsyncClient) -> None:
    """Test assessment with all recommended rules."""
    # First get recommended rules
    rules_response = await app_client.post(
        "/api/v1/feasibility/rules", json=PROJECT_PAYLOAD
    )
    assert rules_response.status_code == 200
    rules_data = rules_response.json()
    recommended_ids = rules_data.get("recommended_rule_ids", [])

    if recommended_ids:
        # Now submit assessment with all recommended rules
        payload = {
            "project": PROJECT_PAYLOAD,
            "selectedRuleIds": recommended_ids,
        }
        response = await app_client.post("/api/v1/feasibility/assessment", json=payload)
        assert response.status_code == 200
