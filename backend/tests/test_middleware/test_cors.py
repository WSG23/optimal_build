"""Integration tests covering the CORS middleware configuration."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from app.core.config import settings


@pytest.fixture()
def client() -> TestClient:
    """Return a FastAPI test client with the production CORS configuration."""

    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
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
