"""Health endpoint behavior."""

from __future__ import annotations

import pytest

from app import main as main_module


@pytest.mark.asyncio
async def test_health_check_reports_degraded_when_session_factory_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def broken_session_factory() -> object:
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(main_module, "AsyncSessionLocal", broken_session_factory)

    response = await main_module.health_check()

    assert response["status"] == "degraded"
    assert response["database"] == "disconnected"
    assert response["error"] == "database unavailable"
