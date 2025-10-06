"""Tests for the lightweight OpenAPI generation helper."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")

from app.api.v1 import TAGS_METADATA  # noqa: E402  (import after dependency checks)
from app.core.config import settings  # noqa: E402
from app.main import app  # noqa: E402
from fastapi.testclient import TestClient


def test_openapi_includes_expected_paths() -> None:
    """Ensure the generated OpenAPI schema documents key endpoints."""

    schema = app.openapi()
    assert app.openapi() is schema  # cached result

    assert schema["info"]["title"] == settings.PROJECT_NAME
    assert schema.get("tags") == TAGS_METADATA

    paths = schema["paths"]
    assert "/api/v1/screen/buildable" in paths
    assert "/api/v1/finance/feasibility" in paths
    assert "/api/v1/finance/scenarios" in paths

    buildable_post = paths["/api/v1/screen/buildable"]["post"]
    request_example = buildable_post["requestBody"]["content"]["application/json"][
        "example"
    ]
    assert request_example["address"] == "string"
    assert request_example["defaults"]["plot_ratio"] == 3.5
    assert request_example["geometry"] == {"string": None}

    response_example = buildable_post["responses"]["200"]["content"][
        "application/json"
    ]["example"]
    assert response_example["input_kind"] == "address"
    assert response_example["zone_source"]["kind"] == "parcel"
    assert response_example["rules"][0]["provenance"]["rule_id"] == 0

    finance_post = paths["/api/v1/finance/feasibility"]["post"]
    finance_request = finance_post["requestBody"]["content"]["application/json"][
        "example"
    ]
    assert finance_request["scenario"]["cost_escalation"]["jurisdiction"] == "SG"
    assert finance_request["scenario"]["cash_flow"]["cash_flows"] == ["0"]
    assert "capital_stack" in finance_request["scenario"]
    assert "drawdown_schedule" in finance_request["scenario"]

    finance_response = finance_post["responses"]["200"]["content"]["application/json"][
        "example"
    ]
    assert finance_response["cost_index"]["base_index"]["value"] == "0"
    assert finance_response["results"][0]["metadata"] == {}
    assert "capital_stack" in finance_response
    assert "drawdown_schedule" in finance_response


def test_openapi_endpoint_returns_cached_schema() -> None:
    """The generated OpenAPI schema is exposed via the HTTP route."""

    schema = app.openapi()
    client = TestClient(app)
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.json() == schema
    # Route should return the cached object rather than rebuilding.
    assert app.openapi() is schema
