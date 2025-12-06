"""Zillow integration client (mock for US residential listings)."""

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
class ZillowOAuthBundle:
    access_token: str
    refresh_token: str
    expires_at: datetime


@dataclass(**_DATACLASS_KWARGS)
class ZillowListing:
    """Zillow listing data structure."""

    zpid: str  # Zillow Property ID
    address: str
    city: str
    state: str
    zipcode: str
    price: float
    bedrooms: int
    bathrooms: float
    sqft: int
    lot_size_sqft: Optional[int] = None
    year_built: Optional[int] = None
    property_type: str = "SingleFamily"  # SingleFamily, Condo, Townhouse, MultiFamily
    listing_status: str = "ForSale"  # ForSale, Pending, Sold
    zestimate: Optional[float] = None
    rent_zestimate: Optional[float] = None
    days_on_market: int = 0
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ZillowClient:
    """Mock client for Zillow API interactions.

    Zillow's real API (Zillow API / Bridge Interactive) requires partnership approval.
    This stub provides the expected interface for future implementation.
    """

    AUTH_BASE_URL = "https://api.zillow.com/oauth2"
    LISTING_BASE_URL = "https://api.zillow.com/v2/listings"
    ZESTIMATE_BASE_URL = "https://api.zillow.com/v2/zestimate"

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
    ) -> ZillowOAuthBundle:
        """Exchange an authorization code for access/refresh tokens."""
        logger.info("zillow.exchange_code", redirect_uri=redirect_uri)
        now = utcnow()
        return ZillowOAuthBundle(
            access_token=f"zillow-access-{code}",
            refresh_token=f"zillow-refresh-{code}",
            expires_at=now + timedelta(hours=1),
        )

    async def refresh_tokens(self, refresh_token: str) -> ZillowOAuthBundle:
        """Refresh the OAuth tokens."""
        logger.info("zillow.refresh_token")
        now = utcnow()
        return ZillowOAuthBundle(
            access_token=f"zillow-access-{refresh_token[:8]}",
            refresh_token=refresh_token,
            expires_at=now + timedelta(hours=1),
        )

    async def search_listings(
        self,
        city: str,
        state: str,
        property_type: str = "SingleFamily",
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_beds: Optional[int] = None,
        min_sqft: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> List[ZillowListing]:
        """Search for listings on Zillow (mock data)."""
        logger.info(
            "zillow.search_listings",
            city=city,
            state=state,
            property_type=property_type,
            min_price=min_price,
            max_price=max_price,
        )

        # Return mock listings for Seattle (SEA jurisdiction)
        if state.upper() == "WA" and city.lower() == "seattle":
            return [
                ZillowListing(
                    zpid="2077104123",
                    address="1420 Terry Ave",
                    city="Seattle",
                    state="WA",
                    zipcode="98101",
                    price=1250000,
                    bedrooms=3,
                    bathrooms=2.5,
                    sqft=2100,
                    lot_size_sqft=4500,
                    year_built=2019,
                    property_type="Condo",
                    listing_status="ForSale",
                    zestimate=1280000,
                    rent_zestimate=4200,
                    days_on_market=14,
                    latitude=47.6097,
                    longitude=-122.3331,
                ),
                ZillowListing(
                    zpid="2077104456",
                    address="500 Wall St",
                    city="Seattle",
                    state="WA",
                    zipcode="98121",
                    price=875000,
                    bedrooms=2,
                    bathrooms=2.0,
                    sqft=1450,
                    year_built=2015,
                    property_type="Condo",
                    listing_status="ForSale",
                    zestimate=890000,
                    rent_zestimate=3100,
                    days_on_market=28,
                    latitude=47.6149,
                    longitude=-122.3485,
                ),
            ]

        # Generic mock response
        return [
            ZillowListing(
                zpid=f"mock-{city}-001",
                address="123 Main St",
                city=city,
                state=state,
                zipcode="00000",
                price=500000,
                bedrooms=3,
                bathrooms=2.0,
                sqft=1800,
                property_type=property_type,
                listing_status="ForSale",
                days_on_market=7,
            )
        ]

    async def get_zestimate(self, zpid: str) -> Optional[Dict[str, Any]]:
        """Get Zestimate for a property (mock)."""
        logger.info("zillow.get_zestimate", zpid=zpid)
        return {
            "zpid": zpid,
            "zestimate": 1000000,
            "rent_zestimate": 3500,
            "value_change_30day": 15000,
            "value_change_1year": 50000,
            "low_estimate": 950000,
            "high_estimate": 1050000,
            "last_updated": utcnow().isoformat(),
        }

    async def publish_listing(
        self, listing_payload: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Publish or update a listing on Zillow (stub)."""
        logger.info("zillow.publish_listing", payload_keys=list(listing_payload.keys()))
        listing_id = listing_payload.get(
            "external_id", f"zillow-{utcnow().timestamp()}"
        )
        return listing_id, {"echo": listing_payload, "status": "published"}

    async def remove_listing(self, listing_id: str) -> bool:
        """Remove a listing from Zillow."""
        logger.info("zillow.remove_listing", listing_id=listing_id)
        return True

    async def get_market_stats(
        self, city: str, state: str, property_type: str = "SingleFamily"
    ) -> Dict[str, Any]:
        """Get market statistics for an area (mock)."""
        logger.info("zillow.get_market_stats", city=city, state=state)
        return {
            "city": city,
            "state": state,
            "property_type": property_type,
            "median_list_price": 750000,
            "median_sale_price": 725000,
            "median_days_on_market": 21,
            "inventory_count": 1250,
            "price_per_sqft": 425,
            "year_over_year_change": 0.045,
            "month_over_month_change": 0.008,
        }
