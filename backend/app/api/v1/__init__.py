"""API v1 router registration."""

from fastapi import APIRouter

from . import (
    costs,
    ergonomics,
    export,
    overlay,
    products,
    review,
    roi,
    rules,
    screen,
    standards,
)

api_router = APIRouter()
api_router.include_router(review.router)
api_router.include_router(rules.router)
api_router.include_router(screen.router)
api_router.include_router(ergonomics.router)
api_router.include_router(products.router)
api_router.include_router(standards.router)
api_router.include_router(costs.router)
api_router.include_router(overlay.router)
api_router.include_router(export.router)
api_router.include_router(roi.router)

__all__ = ["api_router"]
