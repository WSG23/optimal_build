"""Jurisdiction registry for currency/unit defaults."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
from typing import Any, Mapping


@dataclass(frozen=True)
class JurisdictionConfig:
    """Immutable configuration describing a supported jurisdiction."""

    code: str
    name: str
    currency_code: str
    currency_symbol: str
    area_units: str
    rent_metric: str
    market_data: Mapping[str, Any]


def _normalise_code(value: str | None) -> str:
    if not value:
        return "SG"
    cleaned = value.strip().upper()
    return cleaned or "SG"


@lru_cache(maxsize=1)
def _load_registry() -> dict[str, JurisdictionConfig]:
    try:
        text = (
            resources.files("app.data")
            .joinpath("jurisdictions.json")
            .read_text(encoding="utf-8")
        )
    except FileNotFoundError as exc:  # pragma: no cover - defensive guard
        raise RuntimeError("Missing jurisdiction registry file") from exc
    except OSError as exc:  # pragma: no cover - defensive guard
        raise RuntimeError("Unable to read jurisdiction registry") from exc

    try:
        raw_registry: Mapping[str, Mapping[str, Any]] = json.loads(text)
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive guard
        raise RuntimeError("Invalid jurisdiction registry JSON") from exc

    registry: dict[str, JurisdictionConfig] = {}
    for raw_code, payload in raw_registry.items():
        code = _normalise_code(str(payload.get("code") or raw_code))
        registry[code] = JurisdictionConfig(
            code=code,
            name=str(payload.get("name", code)),
            currency_code=str(payload.get("currency_code", "SGD")),
            currency_symbol=str(payload.get("currency_symbol", "S$")),
            area_units=str(payload.get("area_units", "sqm")),
            rent_metric=str(payload.get("rent_metric", "psm_month")),
            market_data=payload.get("market_data", {}),
        )
    if "SG" not in registry:
        registry["SG"] = JurisdictionConfig(
            code="SG",
            name="Singapore",
            currency_code="SGD",
            currency_symbol="S$",
            area_units="sqm",
            rent_metric="psm_month",
            market_data={},
        )
    return registry


def get_jurisdiction_config(code: str | None) -> JurisdictionConfig:
    """Return the configuration for the requested jurisdiction."""

    registry = _load_registry()
    normalised = _normalise_code(code)
    return registry.get(normalised, registry["SG"])


__all__ = ["JurisdictionConfig", "get_jurisdiction_config"]
