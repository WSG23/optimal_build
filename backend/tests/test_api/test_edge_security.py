"""App-level HTTP edge hardening regression tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_trusted_host_middleware_rejects_unknown_hosts() -> None:
    """Unknown Host headers should be rejected before routing."""

    client = TestClient(app, raise_server_exceptions=False)

    good = client.get("/", headers={"host": "testserver"})
    bad = client.get("/", headers={"host": "evil.example"})

    assert good.status_code == 200
    assert bad.status_code == 400
    assert bad.headers["x-frame-options"] == "DENY"
