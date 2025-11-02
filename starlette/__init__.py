"""Minimal Starlette stub providing limited middleware helpers."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from .background import BackgroundTask  # noqa: F401

__all__ = ["background", "middleware"]


def __getattr__(name: str) -> Any:
    if name == "middleware":
        return import_module("starlette.middleware")
    if name == "types":
        return import_module("starlette.types")
    raise AttributeError(f"module 'starlette' has no attribute {name!r}")
