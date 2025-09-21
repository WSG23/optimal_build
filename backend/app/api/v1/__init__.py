"""API v1 router registration."""

from fastapi import APIRouter

from . import ergonomics, products, review, rules, screen


api_router = APIRouter()
api_router.include_router(review.router)
api_router.include_router(rules.router)
api_router.include_router(screen.router)
api_router.include_router(ergonomics.router)
api_router.include_router(products.router)


__all__ = ["api_router"]
