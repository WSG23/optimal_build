"""Integration tests covering the CORS middleware configuration."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import _ALLOWED_HEADERS


@pytest.fixture()
def client() -> TestClient:
    """Return a FastAPI test client with the production CORS configuration."""

    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=_ALLOWED_HEADERS,
    )

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"message": "ok"}

    return TestClient(app)


def test_allowed_origin_receives_cors_headers(client: TestClient) -> None:
    """Configured origins should receive the CORS allow-origin header."""

    origin = settings.ALLOWED_ORIGINS[0]
    response = client.get("/", headers={"Origin": origin})

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin


def test_disallowed_origin_does_not_receive_cors_headers(client: TestClient) -> None:
    """Unrecognised origins must not receive CORS allow-origin headers."""

    origin = "https://malicious.example"
    assert origin not in settings.ALLOWED_ORIGINS

    response = client.get("/", headers={"Origin": origin})

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_development_identity_headers_are_allowed_for_preflight(
    client: TestClient,
) -> None:
    """Browser lowercase identity headers must pass CORS preflight."""

    origin = settings.ALLOWED_ORIGINS[0]
    response = client.options(
        "/",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-role,x-user-id,x-user-email",
        },
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin
    allowed_headers = response.headers.get("access-control-allow-headers", "")
    assert "x-user-id" in allowed_headers.lower()
