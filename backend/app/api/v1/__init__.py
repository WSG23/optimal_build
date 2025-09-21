"""API v1 router registration."""

from __future__ import annotations

from importlib import import_module
from typing import Any

try:  # pragma: no cover - FastAPI may be unavailable in offline testing
    from fastapi import APIRouter
except ModuleNotFoundError:  # pragma: no cover - provide a minimal stub
    class APIRouter:  # type: ignore[override]
        def __init__(self) -> None:
            self.routes: list[tuple[str, str, Any]] = []

        def include_router(self, router: Any, prefix: str | None = None) -> None:
            if hasattr(router, "routes"):
                self.routes.extend(getattr(router, "routes"))


api_router = APIRouter()

_ROUTER_MODULES = [
    "review",
    "rules",
    "screen",
    "ergonomics",
    "products",
    "standards",
    "costs",
    "overlay",
    "rulesets",
]

for module_name in _ROUTER_MODULES:
    try:  # pragma: no cover - some modules may require optional dependencies
        module = import_module(f"{__name__}.{module_name}")
    except Exception:  # pragma: no cover - skip routers that fail to import
        continue
    router = getattr(module, "router", None)
    if router is not None:
        api_router.include_router(router)

__all__ = ["api_router"]
