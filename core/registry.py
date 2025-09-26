"""Jurisdiction plug-in registry."""
from __future__ import annotations

import importlib
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, Protocol, runtime_checkable

from .canonical_models import CanonicalReg, ProvenanceRecord


@runtime_checkable
class JurisdictionParser(Protocol):
    """Protocol describing jurisdiction plug-ins."""

    code: str
    display_name: str | None

    def fetch_raw(self, since: date) -> Iterable[ProvenanceRecord]:
        """Return raw regulation payloads with provenance metadata."""

    def parse(self, records: Iterable[ProvenanceRecord]) -> Iterable[CanonicalReg]:
        """Transform raw payloads into canonical regulations."""

    def map_overrides_path(self) -> Path | None:
        """Return a path to jurisdiction-specific mapping overrides."""


@dataclass
class RegisteredJurisdiction:
    """Wrapper storing parser metadata and module reference."""

    code: str
    parser: JurisdictionParser
    display_name: str | None = None


class RegistryError(RuntimeError):
    """Raised when a jurisdiction plug-in cannot be loaded."""


def load_jurisdiction(code: str) -> RegisteredJurisdiction:
    """Load the jurisdiction plug-in with the provided code."""

    module_name = f"jurisdictions.{code}.parse"
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:  # pragma: no cover - defensive
        raise RegistryError(f"Jurisdiction '{code}' not found") from exc

    if not hasattr(module, "PARSER"):
        raise RegistryError(
            f"Jurisdiction '{code}' must expose a PARSER instance in {module_name}"
        )

    parser = getattr(module, "PARSER")
    if not isinstance(parser, JurisdictionParser):  # type: ignore[misc]
        # The Protocol check is structural at runtime; this protects misconfigured parsers.
        missing_attrs = [
            attr
            for attr in ("fetch_raw", "parse", "map_overrides_path")
            if not hasattr(parser, attr)
        ]
        if missing_attrs:
            raise RegistryError(
                f"Jurisdiction '{code}' is missing required attributes: {missing_attrs}"
            )

    display_name = getattr(parser, "display_name", None)
    return RegisteredJurisdiction(code=code, parser=parser, display_name=display_name)
