"""API v1 router registration."""

from types import ModuleType
from typing import Callable, Final, Protocol, cast


class _RouterModule(Protocol):
    """Protocol describing API submodules that expose a FastAPI router."""

    router: "Router"


class Router(Protocol):
    """Subset of FastAPI's router interface used within the aggregator."""

    def include_router(self, router: "Router") -> None:
        ...


TAGS_METADATA: Final[list[dict[str, str]]] = [
    {
        "name": "entitlements",
        "description": (
            "Roadmaps, studies, stakeholder engagements, and legal instruments "
            "captured for entitlement delivery."
        ),
    },
    {
        "name": "Commercial Property Agent",
        "description": (
            "Market intelligence and property development analysis tools for "
            "commercial real estate advisors. Includes GPS logging, development "
            "potential scanning, photo documentation, 3D scenarios, and market analytics."
        ),
    },
    {
        "name": "market-intelligence",
        "description": "Market analytics reports encompassing comparables, supply, yields, and absorption trends.",
    },
    {
        "name": "compliance",
        "description": "Compliance assessment endpoints for jurisdiction-specific checks.",
    },
]

_ROUTER_MODULES: Final[tuple[str, ...]] = (
    "review",
    "rules",
    "rulesets",
    "screen",
    "ergonomics",
    "products",
    "standards",
    "costs",
    "overlay",
    "export",
    "roi",
    "imports",
    "audit",
    # Finance flows rely on both feasibility and export endpoints being present in
    # the main application so that the interactive documentation exposes them.
    "feasibility",
    "finance",
    "entitlements",
    "test_users",  # Simple user API for learning
    "users_secure",  # Secure user API with validation
    "users_db",  # Database-backed user API
    "projects_api",  # Projects CRUD API
    "singapore_property_api",  # Singapore property with BCA/URA compliance
    "market_intelligence",  # Market intelligence analytics API
    "agents",  # Commercial property advisor agent endpoints
    "advanced_intelligence",  # Investigation analytics stubs
)


def _router_factory() -> Callable[[], Router]:
    """Return a callable that produces FastAPI router instances."""

    module: ModuleType = __import__("fastapi", fromlist=["APIRouter"])
    try:
        factory = module.APIRouter
    except AttributeError as exc:  # pragma: no cover - enforced by runtime tests
        raise AttributeError("fastapi.APIRouter is unavailable") from exc
    if not callable(factory):  # pragma: no cover - defensive guardrail
        raise TypeError("fastapi.APIRouter must be callable")
    return cast(Callable[[], Router], factory)


def _load_router(module_name: str) -> Router:
    """Import an API submodule and return its FastAPI router."""

    module: ModuleType = __import__(f"{__name__}.{module_name}", fromlist=["router"])
    if not hasattr(module, "router"):
        raise AttributeError(
            f"Module '{module_name}' must define an APIRouter named 'router'"
        )

    router = cast(_RouterModule, module).router
    if not hasattr(router, "include_router"):
        raise TypeError(
            f"Module '{module_name}' router must expose an 'include_router' method"
        )
    return router


_APIRouter: Final[Callable[[], Router]] = _router_factory()
api_router: Final[Router] = _APIRouter()
for _module_name in _ROUTER_MODULES:
    api_router.include_router(_load_router(_module_name))


__all__: Final[tuple[str, ...]] = ("api_router", "TAGS_METADATA")
