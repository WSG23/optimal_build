"""Delegate to the repository-level Pydantic stub when running backend tests."""

from __future__ import annotations

from backend._stub_loader import load_optional_package

_pydantic = load_optional_package(__name__, "pydantic", "Pydantic")
globals().update(_pydantic.__dict__)
