"""Version 1 API router."""

from fastapi import APIRouter

from .rules import router as rules_router
from .screen import router as screen_router

api_router = APIRouter()
api_router.include_router(rules_router)
api_router.include_router(screen_router)

__all__ = ["api_router"]
