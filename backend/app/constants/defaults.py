"""
Default Constants - Single Source of Truth

These values MUST stay synchronized with frontend/src/constants/scenarios.ts

⚠️ WARNING: If you change these values, you MUST also update:
   - frontend/src/constants/scenarios.ts (DEFAULT_ASSUMPTIONS)
   - Run tests: pytest backend/tests/constants/ -v
"""

from typing import TypedDict


# =============================================================================
# BUILDING ASSUMPTIONS - MUST MATCH FRONTEND
# =============================================================================


class BuildingAssumptions(TypedDict):
    """Type definition for building assumptions."""

    TYP_FLOOR_TO_FLOOR_M: float
    EFFICIENCY_RATIO: float
    CONSTRUCTION_COST_PSM: float
    LAND_COST_PREMIUM: float
    PARKING_RATIO: float
    DEVELOPMENT_TIMELINE_MONTHS: int
    CAP_RATE: float
    DISCOUNT_RATE: float
    RENTAL_ESCALATION: float
    VACANCY_RATE: float


# Individual constants for direct access
TYP_FLOOR_TO_FLOOR_M: float = 3.5
"""Typical floor-to-floor height in meters - synced with frontend"""

EFFICIENCY_RATIO: float = 0.82
"""Building efficiency ratio (NLA/GFA) - synced with frontend"""

CONSTRUCTION_COST_PSM: float = 3500.0
"""Default construction cost per sqm (SGD) - synced with frontend"""

LAND_COST_PREMIUM: float = 1.15
"""Default land cost premium factor - synced with frontend"""

PARKING_RATIO: float = 3.5
"""Default parking ratio (lots per 1000 sqm GFA) - synced with frontend"""

DEVELOPMENT_TIMELINE_MONTHS: int = 36
"""Default development timeline in months - synced with frontend"""

CAP_RATE: float = 0.045
"""Default capitalization rate - synced with frontend"""

DISCOUNT_RATE: float = 0.08
"""Default discount rate - synced with frontend"""

RENTAL_ESCALATION: float = 0.025
"""Default rental escalation per annum - synced with frontend"""

VACANCY_RATE: float = 0.05
"""Default vacancy rate - synced with frontend"""


# Combined dictionary for bulk access
DEFAULT_ASSUMPTIONS: BuildingAssumptions = {
    "TYP_FLOOR_TO_FLOOR_M": TYP_FLOOR_TO_FLOOR_M,
    "EFFICIENCY_RATIO": EFFICIENCY_RATIO,
    "CONSTRUCTION_COST_PSM": CONSTRUCTION_COST_PSM,
    "LAND_COST_PREMIUM": LAND_COST_PREMIUM,
    "PARKING_RATIO": PARKING_RATIO,
    "DEVELOPMENT_TIMELINE_MONTHS": DEVELOPMENT_TIMELINE_MONTHS,
    "CAP_RATE": CAP_RATE,
    "DISCOUNT_RATE": DISCOUNT_RATE,
    "RENTAL_ESCALATION": RENTAL_ESCALATION,
    "VACANCY_RATE": VACANCY_RATE,
}


# =============================================================================
# COORDINATES - MUST MATCH FRONTEND
# =============================================================================


class Coordinates(TypedDict):
    """Type definition for coordinates."""

    latitude: float
    longitude: float


COORDINATES: dict[str, Coordinates] = {
    "SINGAPORE": {"latitude": 1.3521, "longitude": 103.8198},
    "SEATTLE": {"latitude": 47.6062, "longitude": -122.3321},
    "HONG_KONG": {"latitude": 22.3193, "longitude": 114.1694},
    "LONDON": {"latitude": 51.5074, "longitude": -0.1278},
    "NEW_YORK": {"latitude": 40.7128, "longitude": -74.0060},
}

DEFAULT_COORDINATES: Coordinates = COORDINATES["SINGAPORE"]


# =============================================================================
# JURISDICTION CONFIGURATION
# =============================================================================


class JurisdictionConfig(TypedDict):
    """Type definition for jurisdiction configuration."""

    id: str
    name: str
    country: str
    timezone: str
    currency: str
    currency_symbol: str
    default_coordinates: Coordinates


JURISDICTIONS: dict[str, JurisdictionConfig] = {
    "SINGAPORE": {
        "id": "singapore",
        "name": "Singapore",
        "country": "Singapore",
        "timezone": "Asia/Singapore",
        "currency": "SGD",
        "currency_symbol": "S$",
        "default_coordinates": COORDINATES["SINGAPORE"],
    },
    "SEATTLE": {
        "id": "seattle",
        "name": "Seattle",
        "country": "United States",
        "timezone": "America/Los_Angeles",
        "currency": "USD",
        "currency_symbol": "$",
        "default_coordinates": COORDINATES["SEATTLE"],
    },
    "HONG_KONG": {
        "id": "hong_kong",
        "name": "Hong Kong",
        "country": "Hong Kong SAR",
        "timezone": "Asia/Hong_Kong",
        "currency": "HKD",
        "currency_symbol": "HK$",
        "default_coordinates": COORDINATES["HONG_KONG"],
    },
}

DEFAULT_JURISDICTION: JurisdictionConfig = JURISDICTIONS["SINGAPORE"]


# =============================================================================
# TIMEOUTS (in milliseconds) - MUST MATCH FRONTEND
# =============================================================================


class TimeoutConfig(TypedDict):
    """Type definition for timeout configuration."""

    DEFAULT: int
    LONG: int
    SHORT: int
    POLL_INTERVAL: int
    POLL_MAX: int
    WS_RECONNECT: int


TIMEOUTS: TimeoutConfig = {
    "DEFAULT": 30_000,
    "LONG": 60_000,
    "SHORT": 10_000,
    "POLL_INTERVAL": 2_000,
    "POLL_MAX": 60_000,
    "WS_RECONNECT": 3_000,
}


# =============================================================================
# FETCH LIMITS - MUST MATCH FRONTEND
# =============================================================================


class FetchLimitsConfig(TypedDict):
    """Type definition for fetch limits configuration."""

    DEFAULT_PAGE_SIZE: int
    MAX_PAGE_SIZE: int
    HISTORY_FETCH_LIMIT: int
    MAX_FILE_SIZE: int
    MAX_PHOTOS_PER_PROPERTY: int


FETCH_LIMITS: FetchLimitsConfig = {
    "DEFAULT_PAGE_SIZE": 20,
    "MAX_PAGE_SIZE": 100,
    "HISTORY_FETCH_LIMIT": 10,
    "MAX_FILE_SIZE": 10 * 1024 * 1024,  # 10MB
    "MAX_PHOTOS_PER_PROPERTY": 50,
}
