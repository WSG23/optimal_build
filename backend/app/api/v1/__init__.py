"""API v1 router."""

from fastapi import APIRouter

from . import costs, standards

api_router = APIRouter()
api_router.include_router(standards.router)
api_router.include_router(costs.router)

__all__ = ["api_router"]
