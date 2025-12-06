"""LoopNet integration client (mock for US commercial real estate)."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import structlog
from backend._compat.datetime import utcnow

logger = structlog.get_logger()


_DATACLASS_KWARGS = {"slots": True} if sys.version_info >= (3, 10) else {}


@dataclass(**_DATACLASS_KWARGS)
class LoopNetOAuthBundle:
    access_token: str
    refresh_token: str
    expires_at: datetime


@dataclass(**_DATACLASS_KWARGS)
class LoopNetListing:
    """LoopNet commercial listing data structure."""

    listing_id: str
    address: str
    city: str
    state: str
    zipcode: str
    property_type: str  # Office, Retail, Industrial, MultiFamily, Land, Mixed-Use
    transaction_type: str  # ForSale, ForLease
    price: Optional[float] = None  # Sale price if ForSale
    price_per_sqft: Optional[float] = None
    lease_rate: Optional[float] = None  # $/sqft/year if ForLease
    lease_type: Optional[str] = None  # NNN, Gross, Modified Gross
    building_sqft: Optional[int] = None
    land_acres: Optional[float] = None
    year_built: Optional[int] = None
    cap_rate: Optional[float] = None
    noi: Optional[float] = None  # Net Operating Income
    occupancy_pct: Optional[float] = None
    zoning: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    days_on_market: int = 0


class LoopNetClient:
    """Mock client for LoopNet/CoStar API interactions.

    LoopNet (owned by CoStar) requires commercial API partnership.
    This stub provides the expected interface for future implementation.
    """

    AUTH_BASE_URL = "https://api.loopnet.com/oauth2"
    LISTING_BASE_URL = "https://api.loopnet.com/v2/listings"
    COMPS_BASE_URL = "https://api.loopnet.com/v2/comps"

    def __init__(
        self,
        api_key: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
    ):
        self.api_key = api_key
        self.client_id = client_id
        self.client_secret = client_secret

    async def exchange_authorization_code(
        self, code: str, redirect_uri: str
    ) -> LoopNetOAuthBundle:
        """Exchange an authorization code for access/refresh tokens."""
        logger.info("loopnet.exchange_code", redirect_uri=redirect_uri)
        now = utcnow()
        return LoopNetOAuthBundle(
            access_token=f"loopnet-access-{code}",
            refresh_token=f"loopnet-refresh-{code}",
            expires_at=now + timedelta(hours=1),
        )

    async def refresh_tokens(self, refresh_token: str) -> LoopNetOAuthBundle:
        """Refresh the OAuth tokens."""
        logger.info("loopnet.refresh_token")
        now = utcnow()
        return LoopNetOAuthBundle(
            access_token=f"loopnet-access-{refresh_token[:8]}",
            refresh_token=refresh_token,
            expires_at=now + timedelta(hours=1),
        )

    async def search_listings(
        self,
        city: str,
        state: str,
        property_type: str = "Office",
        transaction_type: str = "ForSale",
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_sqft: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> List[LoopNetListing]:
        """Search for commercial listings on LoopNet (mock data)."""
        logger.info(
            "loopnet.search_listings",
            city=city,
            state=state,
            property_type=property_type,
            transaction_type=transaction_type,
        )

        # Mock listings for Seattle commercial
        if state.upper() == "WA" and city.lower() == "seattle":
            return [
                LoopNetListing(
                    listing_id="LN-SEA-001",
                    address="1201 Third Ave",
                    city="Seattle",
                    state="WA",
                    zipcode="98101",
                    property_type="Office",
                    transaction_type="ForSale",
                    price=45000000,
                    price_per_sqft=485,
                    building_sqft=92780,
                    year_built=1988,
                    cap_rate=0.055,
                    noi=2475000,
                    occupancy_pct=0.92,
                    zoning="DOC2",
                    latitude=47.6062,
                    longitude=-122.3321,
                    days_on_market=45,
                ),
                LoopNetListing(
                    listing_id="LN-SEA-002",
                    address="400 Pine St",
                    city="Seattle",
                    state="WA",
                    zipcode="98101",
                    property_type="Retail",
                    transaction_type="ForLease",
                    lease_rate=65.0,
                    lease_type="NNN",
                    building_sqft=12500,
                    year_built=2005,
                    occupancy_pct=0.85,
                    zoning="DMC",
                    latitude=47.6110,
                    longitude=-122.3375,
                    days_on_market=30,
                ),
                LoopNetListing(
                    listing_id="LN-SEA-003",
                    address="3500 Airport Way S",
                    city="Seattle",
                    state="WA",
                    zipcode="98134",
                    property_type="Industrial",
                    transaction_type="ForSale",
                    price=8500000,
                    price_per_sqft=175,
                    building_sqft=48500,
                    land_acres=2.1,
                    year_built=1975,
                    cap_rate=0.065,
                    noi=552500,
                    occupancy_pct=1.0,
                    zoning="IG2",
                    latitude=47.5745,
                    longitude=-122.3215,
                    days_on_market=60,
                ),
            ]

        # Generic mock response
        return [
            LoopNetListing(
                listing_id=f"LN-{city[:3].upper()}-001",
                address="100 Commercial Blvd",
                city=city,
                state=state,
                zipcode="00000",
                property_type=property_type,
                transaction_type=transaction_type,
                price=5000000 if transaction_type == "ForSale" else None,
                lease_rate=35.0 if transaction_type == "ForLease" else None,
                building_sqft=25000,
                days_on_market=21,
            )
        ]

    async def get_sale_comps(
        self,
        latitude: float,
        longitude: float,
        radius_miles: float = 1.0,
        property_type: str = "Office",
        months_back: int = 12,
    ) -> List[Dict[str, Any]]:
        """Get comparable sales for a location (mock)."""
        logger.info(
            "loopnet.get_sale_comps",
            lat=latitude,
            lon=longitude,
            property_type=property_type,
        )
        return [
            {
                "address": "Comparable 1",
                "sale_date": "2024-06-15",
                "sale_price": 12500000,
                "price_per_sqft": 425,
                "building_sqft": 29400,
                "cap_rate": 0.058,
                "distance_miles": 0.3,
            },
            {
                "address": "Comparable 2",
                "sale_date": "2024-03-22",
                "sale_price": 8200000,
                "price_per_sqft": 390,
                "building_sqft": 21025,
                "cap_rate": 0.062,
                "distance_miles": 0.7,
            },
        ]

    async def publish_listing(
        self, listing_payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Publish or update a listing on LoopNet (stub)."""
        logger.info(
            "loopnet.publish_listing", payload_keys=list(listing_payload.keys())
        )
        listing_id = listing_payload.get("external_id", f"LN-{utcnow().timestamp()}")
        return listing_id, {"echo": listing_payload, "status": "published"}

    async def remove_listing(self, listing_id: str) -> bool:
        """Remove a listing from LoopNet."""
        logger.info("loopnet.remove_listing", listing_id=listing_id)
        return True

    async def get_market_stats(
        self, city: str, state: str, property_type: str = "Office"
    ) -> Dict[str, Any]:
        """Get commercial market statistics for an area (mock)."""
        logger.info(
            "loopnet.get_market_stats",
            city=city,
            state=state,
            property_type=property_type,
        )
        return {
            "city": city,
            "state": state,
            "property_type": property_type,
            "vacancy_rate": 0.085,
            "asking_rent_psf": 42.50,
            "net_absorption_sqft": 125000,
            "inventory_sqft": 45000000,
            "under_construction_sqft": 1200000,
            "avg_cap_rate": 0.058,
            "median_sale_price_psf": 415,
            "year_over_year_rent_change": 0.032,
        }
