"""Project-wide Python interpreter customisations."""

from __future__ import annotations

import os


def _ensure_pytest_cov_loaded() -> None:
    addopts = os.environ.get("PYTEST_ADDOPTS", "").strip()
    token = "-p pytest_cov"
    if token in addopts:
        return
    if addopts:
        addopts = f"{token} {addopts}"
    else:
        addopts = token
    os.environ["PYTEST_ADDOPTS"] = addopts


_ensure_pytest_cov_loaded()
