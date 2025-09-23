"""API v1 router registration."""

from fastapi import APIRouter

from . import (
    audit,
    costs,
    entitlements,
    ergonomics,
    export,
    feasibility,
    finance,
    imports,
    overlay,
    products,
    review,
    roi,
    rules,
    rulesets,
    screen,
    standards,
)

TAGS_METADATA = [
    {
        "name": "entitlements",
        "description": (
            "Roadmaps, studies, stakeholder engagements, and legal instruments "
            "captured for entitlement delivery."
        ),
    }
]

api_router = APIRouter()
api_router.include_router(review.router)
api_router.include_router(rules.router)
api_router.include_router(rulesets.router)
api_router.include_router(screen.router)
api_router.include_router(ergonomics.router)
api_router.include_router(products.router)
api_router.include_router(standards.router)
api_router.include_router(costs.router)
api_router.include_router(overlay.router)
api_router.include_router(export.router)
api_router.include_router(roi.router)
api_router.include_router(imports.router)
api_router.include_router(audit.router)
# Finance flows rely on both feasibility and export endpoints being present in the
# main application so that the interactive documentation exposes them.
api_router.include_router(feasibility.router)
api_router.include_router(finance.router)
api_router.include_router(entitlements.router)

__all__ = ["api_router", "TAGS_METADATA"]
