"""Regression tests for request metrics and problem-details responses."""

from __future__ import annotations

import json

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("starlette.middleware.base")

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

from app.api.error_handlers import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.middleware.observability import RequestMetricsMiddleware
from app.middleware.request_guards import (
    CorrelationIdMiddleware,
    RequestSizeLimitMiddleware,
)
from app.utils import metrics


@pytest.fixture(autouse=True)
def reset_metrics() -> None:
    metrics.reset_metrics()


def _create_app(*, max_size_bytes: int = 2) -> TestClient:
    app = FastAPI()
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
    app.add_middleware(RequestMetricsMiddleware)
    app.add_middleware(RequestSizeLimitMiddleware, max_size_bytes=max_size_bytes)
    app.add_middleware(CorrelationIdMiddleware)

    @app.get("/items/{item_id}")
    def read_item(item_id: int) -> dict[str, int]:
        return {"item_id": item_id}

    @app.get("/not-found")
    def not_found() -> None:
        raise HTTPException(status_code=404, detail="Item missing")

    @app.get("/boom")
    def boom() -> None:
        raise RuntimeError("boom")

    @app.post("/limited")
    def limited() -> dict[str, str]:
        return {"status": "ok"}

    return TestClient(app, raise_server_exceptions=False)


def test_request_metrics_use_route_templates() -> None:
    client = _create_app()

    response = client.get("/items/42")

    assert response.status_code == 200
    assert (
        metrics.counter_value(metrics.REQUEST_COUNTER, {"endpoint": "/items/{item_id}"})
        == 1.0
    )
    assert (
        metrics.counter_value(metrics.REQUEST_COUNTER, {"endpoint": "/items/42"}) == 0.0
    )


def test_http_errors_return_problem_details_with_correlation_id() -> None:
    client = _create_app()

    response = client.get("/not-found", headers={"X-Correlation-ID": "cid-404"})

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.headers["x-correlation-id"] == "cid-404"
    payload = response.json()
    assert payload["detail"] == "Item missing"
    assert payload["status"] == 404
    assert payload["instance"] == "/not-found"
    assert payload["correlation_id"] == "cid-404"
    assert payload["code"] == "not_found"


def test_validation_errors_return_problem_details() -> None:
    client = _create_app()

    response = client.get(
        "/items/not-a-number", headers={"X-Correlation-ID": "cid-422"}
    )

    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    payload = response.json()
    assert payload["detail"] == "Request validation failed"
    assert payload["status"] == 422
    assert payload["correlation_id"] == "cid-422"
    assert payload["code"] == "request_validation_failed"
    assert isinstance(payload["errors"], list)
    assert payload["errors"]


@pytest.mark.asyncio
async def test_validation_errors_sanitise_exception_context() -> None:
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/validated",
            "headers": [],
            "scheme": "http",
            "server": ("testserver", 80),
            "client": ("testclient", 123),
            "root_path": "",
            "query_string": b"",
        }
    )
    exc = RequestValidationError(
        [
            {
                "loc": ("body", "value"),
                "msg": "Value error, value must not be blank",
                "type": "value_error",
                "ctx": {"error": ValueError("value must not be blank")},
            }
        ]
    )

    response = await validation_exception_handler(request, exc)

    assert response.status_code == 422
    payload = json.loads(response.body)
    assert payload["errors"][0]["ctx"]["error"] == "value must not be blank"


def test_unhandled_errors_return_problem_details_with_correlation_id() -> None:
    client = _create_app()

    response = client.get("/boom", headers={"X-Correlation-ID": "cid-500"})

    assert response.status_code == 500
    assert response.headers["content-type"].startswith("application/problem+json")
    payload = response.json()
    assert payload["detail"] == "Internal server error"
    assert payload["status"] == 500
    assert payload["correlation_id"] == "cid-500"
    assert payload["code"] == "internal_server_error"


def test_request_size_limit_returns_problem_details() -> None:
    client = _create_app()

    response = client.post(
        "/limited",
        headers={"X-Correlation-ID": "cid-413"},
        content=b"abc",
    )

    assert response.status_code == 413
    assert response.headers["content-type"].startswith("application/problem+json")
    payload = response.json()
    assert payload["status"] == 413
    assert payload["correlation_id"] == "cid-413"
    assert payload["code"] == "request_entity_too_large"
