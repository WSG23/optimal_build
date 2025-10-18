"""Regression tests ensuring the vendored structlog stub is exercised."""

from __future__ import annotations

from importlib import metadata
import logging
from pathlib import Path
import sys
from types import ModuleType

import pytest


def _import_module(name: str):
    module = __import__(name)
    for part in name.split(".")[1:]:
        module = getattr(module, part)
    return module


def _load_module_from_path(name: str, path: Path) -> ModuleType:
    module = ModuleType(name)
    module.__file__ = str(path)
    package = name.rpartition(".")[0]
    module.__package__ = package or None
    module.__dict__["__builtins__"] = __builtins__
    sys.modules[name] = module
    code = compile(path.read_text(encoding="utf-8"), str(path), "exec")
    exec(code, module.__dict__)
    return module


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
        logging_module = _import_module("backend.app.utils.logging")
    assert any("vendored fallback" in record.getMessage() for record in caplog.records)

    logging_module.configure_logging()
    logger = logging_module.get_logger("structlog-fallback")
    logger.info("structlog_stub_event", detail="ok")

    caplog.clear()
    with caplog.at_level(logging.WARNING):
        logger.warning("structlog_stub_warning", detail="warn")

    assert any(
        "structlog_stub_warning" in record.getMessage() for record in caplog.records
    )

    project_root = Path(__file__).resolve().parents[2]
    script_path = project_root / "scripts" / "seed_finance_demo.py"
    module_name = "tests.structlog_cli"
    cli_module = _load_module_from_path(module_name, script_path)
    monkeypatch.setitem(sys.modules, module_name, cli_module)

    captured: dict[str, list[str] | None] = {}

    def fake_backend_main(argv: list[str] | None = None) -> None:
        captured["argv"] = list(argv) if argv is not None else None

    monkeypatch.setattr(cli_module, "backend_main", fake_backend_main)

    result = cli_module.main([])
    assert result is None
    assert captured["argv"] == []
