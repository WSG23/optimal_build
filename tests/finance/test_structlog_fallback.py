"""Regression tests ensuring the vendored structlog stub is exercised."""

from __future__ import annotations

import importlib
import logging
import sys
from importlib import metadata
from pathlib import Path

import pytest


def test_seed_finance_demo_uses_structlog_fallback(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Simulate the absence of the PyPI structlog distribution and ensure the CLI works."""

    def _missing(_: str) -> str:
        raise metadata.PackageNotFoundError("structlog")

    monkeypatch.setattr(metadata, "version", _missing)
    monkeypatch.setattr("importlib.metadata.version", _missing, raising=False)
    try:
        import importlib_metadata  # type: ignore[import-not-found]
    except ImportError:
        pass
    else:
        monkeypatch.setattr(importlib_metadata, "version", _missing)  # type: ignore[arg-type]

    for name in [key for key in sys.modules if key.startswith("structlog")]:
        sys.modules.pop(name)
    sys.modules.pop("backend.app.utils.logging", None)

    caplog.clear()
    with caplog.at_level(logging.WARNING):
        logging_module = importlib.import_module("backend.app.utils.logging")
    assert any("vendored fallback" in record.getMessage() for record in caplog.records)

    logging_module.configure_logging()
    logger = logging_module.get_logger("structlog-fallback")
    logger.info("structlog_stub_event", detail="ok")

    project_root = Path(__file__).resolve().parents[2]
    script_path = project_root / "scripts" / "seed_finance_demo.py"
    spec = importlib.util.spec_from_file_location("tests.structlog_cli", script_path)
    assert spec and spec.loader, "Failed to load scripts/seed_finance_demo.py"
    cli_module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, cli_module)
    spec.loader.exec_module(cli_module)

    captured: dict[str, list[str] | None] = {}

    def fake_backend_main(argv: list[str] | None = None) -> None:
        captured["argv"] = list(argv) if argv is not None else None

    monkeypatch.setattr(cli_module, "backend_main", fake_backend_main)

    result = cli_module.main([])
    assert result is None
    assert captured["argv"] == []
