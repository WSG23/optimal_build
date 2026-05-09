from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from backend.scripts import smoke_ura_data_service


def _args(**overrides):
    defaults = {
        "address": "10 Jln Besar, #11-06 Sim Lim Tower, Singapore 208787",
        "latitude": 1.3007,
        "longitude": 103.8556,
        "property_type": "residential",
        "district": None,
        "months_back": 60,
        "require_live": False,
        "require_all": False,
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


@pytest.mark.asyncio
async def test_smoke_skips_without_ura_access_key(monkeypatch) -> None:
    monkeypatch.delenv("URA_ACCESS_KEY", raising=False)
    monkeypatch.setattr(smoke_ura_data_service, "REPO_ROOT", Path("/missing"))

    exit_code, payload = await smoke_ura_data_service.run_smoke(_args())

    assert exit_code == 0
    assert payload["status"] == "skipped"
    assert payload["source"]["state"] == "unavailable"
    assert payload["source"]["synthetic"] is False


@pytest.mark.asyncio
async def test_smoke_require_live_fails_without_ura_access_key(monkeypatch) -> None:
    monkeypatch.delenv("URA_ACCESS_KEY", raising=False)
    monkeypatch.setattr(smoke_ura_data_service, "REPO_ROOT", Path("/missing"))

    exit_code, payload = await smoke_ura_data_service.run_smoke(
        _args(require_live=True)
    )

    assert exit_code == 2
    assert payload["status"] == "skipped"
    assert payload["reason"] == "URA_ACCESS_KEY not configured"
