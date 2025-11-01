"""Tests for API error logging middleware."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("starlette.middleware.base")

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.middleware.observability import ApiErrorLoggingMiddleware


class _Recorder:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def __call__(self, logger: Any, event: str, **kwargs: Any) -> None:
        self.calls.append((event, kwargs))


@pytest.fixture()
def recorder(monkeypatch: pytest.MonkeyPatch) -> _Recorder:
    recorder = _Recorder()
    monkeypatch.setattr(
        "app.middleware.observability.log_event",
        recorder,
    )
    return recorder


def _create_app() -> TestClient:
    app = FastAPI()

    class _DummyLogger:
        def info(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - structlog API
            pass

    app.add_middleware(ApiErrorLoggingMiddleware, logger=_DummyLogger())

    @app.get("/boom")
    def boom() -> JSONResponse:
        raise RuntimeError("boom")

    @app.get("/error")
    def error_response() -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": "unavailable"})

    @app.get("/ok")
    def ok() -> JSONResponse:
        return JSONResponse(status_code=200, content={"detail": "ok"})

    return TestClient(app, raise_server_exceptions=False)


def test_logs_exceptions(recorder: _Recorder) -> None:
    client = _create_app()

    response = client.get("/boom")

    assert response.status_code == 500
    assert any(event == "api_exception" for event, _ in recorder.calls)


def test_logs_server_errors(recorder: _Recorder) -> None:
    client = _create_app()

    response = client.get("/error")

    assert response.status_code == 503
    assert any(event == "api_error_response" for event, _ in recorder.calls)


def test_ignores_successful_responses(recorder: _Recorder) -> None:
    client = _create_app()

    response = client.get("/ok")

    assert response.status_code == 200
    assert recorder.calls == []
