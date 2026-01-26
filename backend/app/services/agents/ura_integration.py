"""URA (Urban Redevelopment Authority) integration service for Singapore property data."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

import structlog
from pydantic import BaseModel

import httpx
from app.core.config import settings
from app.services.base import AsyncClientService

logger = structlog.get_logger()


class URAZoningInfo(BaseModel):
    """URA zoning information."""

    zone_code: str
    zone_description: str
    plot_ratio: float
    building_height_limit: Optional[float] = None
    site_coverage: Optional[float] = None
    use_groups: List[str] = []
    special_conditions: Optional[str] = None


class URAPropertyInfo(BaseModel):
    """URA property information."""

    property_name: Optional[str] = None
    tenure: str
    site_area_sqm: Optional[float] = None
    gfa_approved: Optional[float] = None
    building_height: Optional[float] = None
    completion_year: Optional[int] = None
    last_transaction_date: Optional[date] = None
    last_transaction_price: Optional[float] = None


class URAIntegrationService(AsyncClientService):
    """Service for integrating with URA APIs for property and zoning data."""

    def __init__(self) -> None:
        self.access_key = settings.URA_ACCESS_KEY
        self.access_key_header = settings.URA_ACCESS_KEY_HEADER
        self.token_url = settings.URA_TOKEN_URL
        self.token_header = settings.URA_TOKEN_HEADER
        self.zoning_url = settings.URA_ZONING_URL
        self.existing_use_url = settings.URA_EXISTING_USE_URL
        self.property_url = settings.URA_PROPERTY_URL
        self.development_plans_url = settings.URA_DEVELOPMENT_PLANS_URL
        self.transactions_url = settings.URA_TRANSACTIONS_URL
        self.rental_url = settings.URA_RENTAL_URL
        self.timeout_seconds = settings.URA_TIMEOUT_SECONDS

        self.token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None

        try:
            self.client = httpx.AsyncClient(timeout=self.timeout_seconds)
        except RuntimeError:  # pragma: no cover - httpx stub unavailable
            logger.warning("httpx AsyncClient unavailable; URA integration disabled")
            self.client = None

    def _require_client(self) -> httpx.AsyncClient:
        if self.client is None:
            raise RuntimeError("URA HTTP client is unavailable")
        return self.client

    @staticmethod
    def _require_url(url: str, label: str) -> str:
        if not url:
            raise RuntimeError(f"URA {label} endpoint not configured")
        return url

    async def _get_token(self) -> str:
        """Get or refresh URA API token."""
        if self.token and self.token_expiry and datetime.utcnow() < self.token_expiry:
            return self.token

        if not self.access_key:
            raise RuntimeError("URA access key not configured")

        token_url = self._require_url(self.token_url, "token")
        client = self._require_client()

        response = await client.get(
            token_url, headers={self.access_key_header: self.access_key}
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"URA token request failed with status {response.status_code}"
            )

        payload = response.json()
        token = (
            payload.get("Result") or payload.get("token") or payload.get("access_token")
        )
        if not token:
            raise RuntimeError("URA token response missing token")

        expires_in = payload.get("expires_in") or payload.get("expiresIn")
        if isinstance(expires_in, int):
            self.token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
        else:
            self.token_expiry = datetime.utcnow().replace(
                hour=23, minute=59, second=59, microsecond=0
            )

        self.token = str(token)
        return self.token

    @staticmethod
    def _extract_record(payload: Any) -> Optional[Dict[str, Any]]:
        if isinstance(payload, list):
            return payload[0] if payload else None
        if isinstance(payload, dict):
            for key in ("result", "data", "item", "record"):
                value = payload.get(key)
                if isinstance(value, list):
                    return value[0] if value else None
                if isinstance(value, dict):
                    return value
            return payload
        return None

    @staticmethod
    def _extract_list(payload: Any) -> List[Dict[str, Any]]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict):
            for key in ("results", "data", "items", "transactions", "rentals"):
                value = payload.get(key)
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, dict)]
        return []

    @staticmethod
    def _coerce_float(value: Any) -> Optional[float]:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _get_field(self, data: Dict[str, Any], *keys: str) -> Any:
        for key in keys:
            if key in data:
                return data[key]
        return None

    async def _request_json(self, url: str, params: Dict[str, Any]) -> Any:
        endpoint = self._require_url(url, "data")
        token = await self._get_token()
        client = self._require_client()
        response = await client.get(
            endpoint, params=params, headers={self.token_header: token}
        )
        if response.status_code != 200:
            raise RuntimeError(f"URA request failed with status {response.status_code}")
        return response.json()

    async def get_zoning_info(self, address: str) -> Optional[URAZoningInfo]:
        """Get zoning information for a property address."""
        payload = await self._request_json(self.zoning_url, {"address": address})
        record = self._extract_record(payload)
        if not record:
            return None

        zone_code = self._get_field(record, "zone_code", "zoneCode")
        zone_description = self._get_field(
            record, "zone_description", "zoneDescription"
        )
        plot_ratio = self._coerce_float(
            self._get_field(record, "plot_ratio", "plotRatio")
        )

        if not zone_code or not zone_description or plot_ratio is None:
            return None

        use_groups = self._get_field(record, "use_groups", "useGroups") or []
        if isinstance(use_groups, str):
            use_groups = [
                item.strip() for item in use_groups.split(",") if item.strip()
            ]
        elif not isinstance(use_groups, list):
            use_groups = []

        return URAZoningInfo(
            zone_code=str(zone_code),
            zone_description=str(zone_description),
            plot_ratio=plot_ratio,
            building_height_limit=self._coerce_float(
                self._get_field(record, "building_height_limit", "buildingHeightLimit")
            ),
            site_coverage=self._coerce_float(
                self._get_field(record, "site_coverage", "siteCoverage")
            ),
            use_groups=use_groups,
            special_conditions=self._get_field(
                record, "special_conditions", "specialConditions"
            ),
        )

    async def get_existing_use(self, address: str) -> Optional[str]:
        """Get existing use of a property."""
        payload = await self._request_json(self.existing_use_url, {"address": address})
        record = self._extract_record(payload)
        if not record:
            return None
        existing_use = self._get_field(
            record, "existing_use", "existingUse", "use", "primary_use"
        )
        return str(existing_use) if existing_use else None

    async def get_property_info(self, address: str) -> Optional[URAPropertyInfo]:
        """Get detailed property information from URA."""
        payload = await self._request_json(self.property_url, {"address": address})
        record = self._extract_record(payload)
        if not record:
            return None

        tenure = self._get_field(record, "tenure")
        if not tenure:
            return None

        last_transaction_date = self._get_field(
            record, "last_transaction_date", "lastTransactionDate"
        )
        parsed_date = None
        if isinstance(last_transaction_date, str):
            try:
                parsed_date = date.fromisoformat(last_transaction_date)
            except ValueError:
                parsed_date = None

        return URAPropertyInfo(
            property_name=self._get_field(record, "property_name", "propertyName"),
            tenure=str(tenure),
            site_area_sqm=self._coerce_float(
                self._get_field(record, "site_area_sqm", "siteAreaSqm")
            ),
            gfa_approved=self._coerce_float(
                self._get_field(record, "gfa_approved", "gfaApproved")
            ),
            building_height=self._coerce_float(
                self._get_field(record, "building_height", "buildingHeight")
            ),
            completion_year=self._get_field(
                record, "completion_year", "completionYear"
            ),
            last_transaction_date=parsed_date,
            last_transaction_price=self._coerce_float(
                self._get_field(
                    record, "last_transaction_price", "lastTransactionPrice"
                )
            ),
        )

    async def get_development_plans(
        self, latitude: float, longitude: float, radius_km: float = 2.0
    ) -> List[Dict[str, Any]]:
        """Get nearby development plans and proposals."""
        payload = await self._request_json(
            self.development_plans_url,
            {
                "latitude": latitude,
                "longitude": longitude,
                "radius_km": radius_km,
            },
        )
        return self._extract_list(payload)

    async def get_transaction_data(
        self, property_type: str, district: Optional[str] = None, months_back: int = 12
    ) -> List[Dict[str, Any]]:
        """Get recent transaction data from URA REALIS."""
        params: Dict[str, Any] = {
            "property_type": property_type,
            "months_back": months_back,
        }
        if district:
            params["district"] = district
        payload = await self._request_json(self.transactions_url, params)
        return self._extract_list(payload)

    async def get_rental_data(
        self, property_type: str, district: Optional[str] = None, months_back: int = 12
    ) -> List[Dict[str, Any]]:
        """Get rental data from URA."""
        params: Dict[str, Any] = {
            "property_type": property_type,
            "months_back": months_back,
        }
        if district:
            params["district"] = district
        payload = await self._request_json(self.rental_url, params)
        return self._extract_list(payload)


# Singleton instance
ura_service = URAIntegrationService()
