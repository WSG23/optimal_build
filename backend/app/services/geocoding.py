"""Geocoding service for address lookup and reverse geocoding."""

from typing import Any, Dict, Optional, Tuple

import structlog
from pydantic import BaseModel

import httpx
from app.core.config import settings
from app.services.base import AsyncClientService

logger = structlog.get_logger()


class Address(BaseModel):
    """Structured address information."""

    full_address: str
    street_name: Optional[str] = None
    building_name: Optional[str] = None
    block_number: Optional[str] = None
    postal_code: Optional[str] = None
    district: Optional[str] = None
    country: str = "Singapore"


class GeocodingService(AsyncClientService):
    """Service for geocoding and reverse geocoding using Google Maps."""

    def __init__(self) -> None:
        self.onemap_base_url = "https://www.onemap.gov.sg/api"
        self.google_maps_base_url = "https://maps.googleapis.com/maps/api/geocode/json"
        self.google_maps_api_key = settings.GOOGLE_MAPS_API_KEY
        self.offline_mode = settings.OFFLINE_MODE
        if self.offline_mode:
            logger.info(
                "Geocoding service running in offline mode; using mock address/amenity data"
            )
            self.client = None
        else:
            try:
                self.client = httpx.AsyncClient(timeout=30.0)
            except RuntimeError:  # pragma: no cover - httpx stub unavailable
                logger.warning(
                    "httpx AsyncClient unavailable; geocoding service will operate in mock mode"
                )
                self.client = None

    @staticmethod
    def _build_mock_address(latitude: float, longitude: float) -> Address:
        """Return a deterministic fallback address for offline environments."""

        return Address(
            full_address=f"Mocked Address near ({latitude:.5f}, {longitude:.5f})",
            street_name="Mock Street",
            building_name="Mock Building",
            block_number="000",
            postal_code="000000",
            district="D00 - Mock District",
            country="Singapore",
        )

    @staticmethod
    def _mock_amenities(
        latitude: float = 1.3, longitude: float = 103.85
    ) -> Dict[str, Any]:
        """Return canned amenity data when external services are unavailable.

        Includes coordinates offset from the provided location for map display.
        """
        return {
            "mrt_stations": [
                {
                    "name": "Mock MRT",
                    "distance_m": 250,
                    "latitude": latitude + 0.002,
                    "longitude": longitude + 0.001,
                }
            ],
            "bus_stops": [
                {
                    "name": "Mock Bus Stop",
                    "distance_m": 120,
                    "latitude": latitude + 0.001,
                    "longitude": longitude - 0.001,
                }
            ],
            "schools": [
                {
                    "name": "Mock Primary School",
                    "distance_m": 480,
                    "latitude": latitude - 0.003,
                    "longitude": longitude + 0.002,
                }
            ],
            "shopping_malls": [
                {
                    "name": "Mock Mall",
                    "distance_m": 650,
                    "latitude": latitude + 0.004,
                    "longitude": longitude - 0.003,
                }
            ],
            "parks": [
                {
                    "name": "Mock Park",
                    "distance_m": 320,
                    "latitude": latitude - 0.002,
                    "longitude": longitude + 0.003,
                }
            ],
        }

    async def reverse_geocode(
        self, latitude: float, longitude: float
    ) -> Optional[Address]:
        """Convert coordinates to address using Google Maps."""
        if self.offline_mode:
            return self._build_mock_address(latitude, longitude)

        try:
            address = await self._google_reverse_geocode(latitude, longitude)
        except Exception as exc:
            logger.error("reverse_geocode_failed", error=str(exc))
            raise

        if address is None:
            logger.warning(
                "reverse_geocode_no_results",
                latitude=latitude,
                longitude=longitude,
            )
        return address

    async def geocode(self, address: str) -> Optional[Tuple[float, float]]:
        """Convert address to coordinates using Google Maps."""
        if self.offline_mode:
            return (1.3000, 103.8500)

        try:
            result = await self._google_geocode(address)
        except Exception as exc:
            logger.error("geocode_failed", error=str(exc), address=address)
            raise

        if result is None:
            logger.warning("geocode_no_results", address=address)
            return None

        latitude, longitude, _ = result
        return (latitude, longitude)

    async def geocode_details(self, address: str) -> Optional[Tuple[float, float, str]]:
        """Return coordinates plus a formatted address for the input."""
        if self.offline_mode:
            return (1.3000, 103.8500, address)

        result = await self._google_geocode(address)
        if result is None:
            return None
        return result

    async def get_nearby_amenities(
        self, latitude: float, longitude: float, radius_m: int = 1000
    ) -> Dict[str, Any]:
        """Get nearby amenities using OneMap themes.

        Returns amenities with name, distance_m, latitude, and longitude for map display.
        """
        amenities: Dict[str, Any] = {
            "mrt_stations": [],
            "bus_stops": [],
            "schools": [],
            "shopping_malls": [],
            "parks": [],
        }

        if self.offline_mode:
            logger.warning("Geocoding offline; returning mock amenity list")
            return self._mock_amenities(latitude, longitude)

        if self.client is None:
            logger.warning("Geocoding client unavailable; returning empty amenity list")
            return amenities

        # OneMap theme queries
        themes = {
            "mrt_stations": "railway_stn_exit",
            "bus_stops": "bus_stop",
            "schools": "schooldirectory",
            "shopping_malls": "shoppingmall",
            "parks": "parks",
        }

        for amenity_type, theme in themes.items():
            try:
                response = await self.client.get(
                    f"{self.onemap_base_url}/privateapi/themesvc/retrieveTheme",
                    params={
                        "queryName": theme,
                        "extents": f"{longitude-0.01},{latitude-0.01},{longitude+0.01},{latitude+0.01}",
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    if "SrchResults" in data and data["SrchResults"]:
                        for result in data["SrchResults"][1:]:  # Skip header row
                            latlng = result.get("LatLng", "0,0").split(",")
                            amenity_lat = float(latlng[0]) if len(latlng) > 0 else 0.0
                            amenity_lon = float(latlng[1]) if len(latlng) > 1 else 0.0
                            distance = self._calculate_distance(
                                latitude, longitude, amenity_lat, amenity_lon
                            )
                            if distance <= radius_m:
                                amenities[amenity_type].append(
                                    {
                                        "name": result.get("NAME", "Unknown"),
                                        "distance_m": round(distance),
                                        "latitude": amenity_lat,
                                        "longitude": amenity_lon,
                                    }
                                )
            except Exception as e:
                logger.error(f"Error fetching {amenity_type}: {str(e)}")

        return amenities

    def _get_district_from_postal(self, postal_code: str) -> Optional[str]:
        """Map Singapore postal code to district."""
        if not postal_code or len(postal_code) < 2:
            return None

        prefix = int(postal_code[:2])

        # Singapore postal code to district mapping
        district_map = {
            (1, 6): "D01 - Raffles Place, Marina, Cecil",
            (7, 8): "D02 - Chinatown, Tanjong Pagar",
            (14, 16): "D03 - Alexandra, Tiong Bahru, Queenstown",
            (9, 10): "D04 - Mount Faber, Telok Blangah, Harbourfront",
            (11, 13): "D05 - Buona Vista, West Coast, Clementi",
            (17, 17): "D06 - City Hall, High Street, Beach Road",
            (18, 19): "D07 - Bugis, Rochor, Bencoolen",
            (20, 21): "D08 - Farrer Park, Little India",
            (22, 23): "D09 - Orchard Road, River Valley",
            (24, 27): "D10 - Tanglin, Holland, Bukit Timah",
            (28, 30): "D11 - Newton, Novena",
            (31, 33): "D12 - Toa Payoh, Serangoon, Balestier",
            (34, 37): "D13 - Macpherson, Potong Pasir",
            (38, 41): "D14 - Eunos, Kembangan, Paya Lebar",
            (42, 45): "D15 - Marine Parade, Siglap, Katong",
            (46, 48): "D16 - Upper East Coast, Bedok",
            (49, 50): "D17 - Changi, Loyang",
            (51, 52): "D18 - Simei, Tampines, Pasir Ris",
            (53, 55): "D19 - Punggol, Sengkang, Serangoon",
            (56, 57): "D20 - Bishan, Ang Mo Kio",
            (58, 59): "D21 - Clementi Park, Upper Bukit Timah",
            (60, 64): "D22 - Boon Lay, Jurong, Tuas",
            (65, 68): "D23 - Choa Chu Kang, Bukit Batok",
            (69, 71): "D24 - Kranji, Lim Chu Kang",
            (72, 73): "D25 - Woodlands, Admiralty",
            (75, 76): "D26 - Mandai, Upper Thomson",
            (77, 78): "D27 - Sembawang, Yishun",
            (79, 80): "D28 - Seletar, Yio Chu Kang",
        }

        for postal_range, district in district_map.items():
            if postal_range[0] <= prefix <= postal_range[1]:
                return district

        return None

    def _calculate_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """Calculate distance between two points in meters using Haversine formula."""
        from math import atan2, cos, radians, sin, sqrt

        R = 6371000  # Earth's radius in meters

        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)

        a = (
            sin(delta_lat / 2) ** 2
            + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
        )
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return R * c

    async def _google_reverse_geocode(
        self, latitude: float, longitude: float
    ) -> Optional[Address]:
        """Lookup an address using Google Maps reverse geocoding."""
        client = self._require_google_client()
        response = await client.get(
            self.google_maps_base_url,
            params={
                "latlng": f"{latitude},{longitude}",
                "key": self.google_maps_api_key,
            },
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"Google Maps reverse geocoding failed with status {response.status_code}"
            )

        payload = response.json()
        if payload.get("status") != "OK" or not payload.get("results"):
            return None

        return self._parse_google_address(payload["results"][0])

    async def _google_geocode(self, address: str) -> Optional[Tuple[float, float, str]]:
        """Lookup coordinates using Google Maps geocoding."""
        client = self._require_google_client()
        response = await client.get(
            self.google_maps_base_url,
            params={
                "address": address,
                "key": self.google_maps_api_key,
            },
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"Google Maps geocoding failed with status {response.status_code}"
            )

        payload = response.json()
        if payload.get("status") != "OK" or not payload.get("results"):
            return None

        result = payload["results"][0]
        location = result.get("geometry", {}).get("location", {})
        lat = location.get("lat")
        lng = location.get("lng")
        if lat is None or lng is None or not lat or not lng:
            return None

        formatted = result.get("formatted_address") or address
        return (float(lat), float(lng), formatted)

    def _require_google_client(self) -> httpx.AsyncClient:
        if not self.google_maps_api_key:
            raise RuntimeError("GOOGLE_MAPS_API_KEY is required for geocoding")
        if self.client is None:
            raise RuntimeError("Geocoding client unavailable")
        return self.client

    def _parse_google_address(self, result: dict[str, Any]) -> Address:
        formatted = result.get("formatted_address") or "Unknown"
        components = result.get("address_components", [])

        def component_value(component_types: set[str]) -> Optional[str]:
            for component in components:
                types = set(component.get("types", []))
                if component_types.intersection(types):
                    return component.get("long_name") or component.get("short_name")
            return None

        street_number = component_value({"street_number"})
        route = component_value({"route"})
        postal_code = component_value({"postal_code"})
        country = component_value({"country"}) or "Singapore"
        district = None
        if country.lower() == "singapore" and postal_code:
            district = self._get_district_from_postal(postal_code)
        if district is None:
            district = component_value({"administrative_area_level_2", "locality"})

        return Address(
            full_address=formatted,
            street_name=route,
            building_name=None,
            block_number=street_number,
            postal_code=postal_code,
            district=district,
            country=country,
        )
