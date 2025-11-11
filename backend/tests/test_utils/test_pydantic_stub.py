"""Regression tests for the repository's lightweight Pydantic shim."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest import mock


def _load_stub_without_runtime():
    """Import the repo shim while forcing the fallback code path."""

    repo_root = Path(__file__).resolve().parents[3]
    stub_path = repo_root / "pydantic" / "__init__.py"
    spec = importlib.util.spec_from_file_location("pydantic_stub_for_test", stub_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load pydantic stub for testing")
    module = importlib.util.module_from_spec(spec)
    with mock.patch("importlib.machinery.PathFinder.find_spec", return_value=None):
        spec.loader.exec_module(module)
    return module


def test_stub_exposes_configdict_and_preserves_kwargs():
    module = _load_stub_without_runtime()
    assert hasattr(
        module, "ConfigDict"
    ), "ConfigDict should be provided when runtime is missing"
    config = module.ConfigDict(extra="allow", from_attributes=True)
    assert isinstance(config, dict)
    assert config["extra"] == "allow"
    assert config["from_attributes"] is True
