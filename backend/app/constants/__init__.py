"""
Constants Module - Single Source of Truth

This module exports all canonical constants for the backend.
These values MUST stay synchronized with frontend/src/constants/

To maintain SSoT:
1. Update values here first
2. Update frontend/src/constants/ to match
3. Run tests to verify synchronization
"""

from .defaults import (
    # Building assumptions
    DEFAULT_ASSUMPTIONS,
    TYP_FLOOR_TO_FLOOR_M,
    EFFICIENCY_RATIO,
    CONSTRUCTION_COST_PSM,
    LAND_COST_PREMIUM,
    PARKING_RATIO,
    DEVELOPMENT_TIMELINE_MONTHS,
    CAP_RATE,
    DISCOUNT_RATE,
    RENTAL_ESCALATION,
    VACANCY_RATE,
    # Coordinates
    COORDINATES,
    DEFAULT_COORDINATES,
    JURISDICTIONS,
    DEFAULT_JURISDICTION,
    # Timeouts
    TIMEOUTS,
    # Fetch limits
    FETCH_LIMITS,
)

__all__ = [
    # Building assumptions
    "DEFAULT_ASSUMPTIONS",
    "TYP_FLOOR_TO_FLOOR_M",
    "EFFICIENCY_RATIO",
    "CONSTRUCTION_COST_PSM",
    "LAND_COST_PREMIUM",
    "PARKING_RATIO",
    "DEVELOPMENT_TIMELINE_MONTHS",
    "CAP_RATE",
    "DISCOUNT_RATE",
    "RENTAL_ESCALATION",
    "VACANCY_RATE",
    # Coordinates
    "COORDINATES",
    "DEFAULT_COORDINATES",
    "JURISDICTIONS",
    "DEFAULT_JURISDICTION",
    # Timeouts
    "TIMEOUTS",
    # Fetch limits
    "FETCH_LIMITS",
]
