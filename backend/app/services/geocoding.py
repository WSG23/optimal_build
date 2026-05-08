"""Geocoding service for address lookup and reverse geocoding."""

import re
from typing import Any, Dict, Optional, Tuple

import structlog
from pydantic import BaseModel

import httpx
from app.core.config import settings
from app.schemas.external_sources import ExternalSourceMetadata, ExternalSourceState
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


class GeocodeLookupResult(BaseModel):
    """Forward-geocode result with structured provenance."""

    latitude: float
    longitude: float
    formatted_address: str
    address: Address
    source: ExternalSourceMetadata


class GeocodingService(AsyncClientService):
    """Service for geocoding and reverse geocoding using Google Maps."""

    def __init__(self) -> None:
        self.onemap_base_url = "https://www.onemap.gov.sg/api"
        self.google_maps_base_url = "https://maps.googleapis.com/maps/api/geocode/json"
        self.google_places_details_url = (
            "https://maps.googleapis.com/maps/api/place/details/json"
        )
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

    def get_google_geocoding_metadata(self) -> ExternalSourceMetadata:
        """Describe the current Google geocoding integration mode."""

        if self.offline_mode:
            return ExternalSourceMetadata(
                provider="google_maps",
                state=ExternalSourceState.MOCK,
                configured=False,
                synthetic=True,
                reason="OFFLINE_MODE enabled",
            )
        if not self.google_maps_api_key:
            return ExternalSourceMetadata(
                provider="google_maps",
                state=ExternalSourceState.MOCK,
                configured=False,
                synthetic=True,
                reason="GOOGLE_MAPS_API_KEY not configured",
            )
        if self.client is None:
            return ExternalSourceMetadata(
                provider="google_maps",
                state=ExternalSourceState.UNAVAILABLE,
                configured=True,
                synthetic=False,
                reason="Geocoding client unavailable",
            )
        return ExternalSourceMetadata(
            provider="google_maps",
            state=ExternalSourceState.LIVE,
            configured=True,
            synthetic=False,
        )

    def get_onemap_amenities_metadata(self) -> ExternalSourceMetadata:
        """Describe the current OneMap amenities integration mode."""

        if self.offline_mode:
            return ExternalSourceMetadata(
                provider="onemap",
                state=ExternalSourceState.MOCK,
                configured=False,
                synthetic=True,
                reason="OFFLINE_MODE enabled",
            )
        if self.client is None:
            return ExternalSourceMetadata(
                provider="onemap",
                state=ExternalSourceState.UNAVAILABLE,
                configured=True,
                synthetic=False,
                reason="Geocoding client unavailable",
            )
        return ExternalSourceMetadata(
            provider="onemap",
            state=ExternalSourceState.LIVE,
            configured=True,
            synthetic=False,
        )

    def get_onemap_address_metadata(self) -> ExternalSourceMetadata:
        """Describe the current OneMap address-search integration mode."""

        if self.offline_mode:
            return ExternalSourceMetadata(
                provider="onemap_address_search",
                state=ExternalSourceState.MOCK,
                configured=False,
                synthetic=True,
                reason="OFFLINE_MODE enabled",
            )
        if self.client is None:
            return ExternalSourceMetadata(
                provider="onemap_address_search",
                state=ExternalSourceState.UNAVAILABLE,
                configured=True,
                synthetic=False,
                reason="Geocoding client unavailable",
            )
        return ExternalSourceMetadata(
            provider="onemap_address_search",
            state=ExternalSourceState.LIVE,
            configured=True,
            synthetic=False,
        )

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
        if not self.google_maps_api_key:
            logger.warning(
                "reverse_geocode_mock_fallback",
                latitude=latitude,
                longitude=longitude,
            )
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
        result = await self.geocode_lookup(address)
        if result is None:
            logger.warning("geocode_no_results", address=address)
            return None
        return (result.latitude, result.longitude)

    async def geocode_details(self, address: str) -> Optional[Tuple[float, float, str]]:
        """Return coordinates plus a formatted address for the input."""
        result = await self.geocode_lookup(address)
        if result is None:
            return None
        return (result.latitude, result.longitude, result.formatted_address)

    async def geocode_lookup(self, address: str) -> Optional[GeocodeLookupResult]:
        """Return coordinates, formatted address, structured address, and source."""

        if self.offline_mode:
            mock_address = Address(
                full_address=address,
                street_name=None,
                building_name=None,
                block_number=None,
                postal_code=self._extract_singapore_postal(address),
                district=None,
            )
            return GeocodeLookupResult(
                latitude=1.3000,
                longitude=103.8500,
                formatted_address=address,
                address=mock_address,
                source=self.get_google_geocoding_metadata(),
            )

        if self._looks_like_singapore_address(address):
            try:
                onemap_result = await self._onemap_geocode(address)
                if onemap_result is not None:
                    return onemap_result
            except Exception as exc:
                logger.warning(
                    "onemap_address_geocode_failed",
                    error=str(exc),
                    address=address,
                )

        if not self.google_maps_api_key:
            logger.warning("geocode_details_mock_fallback", address=address)
            mock_address = Address(
                full_address=address,
                postal_code=self._extract_singapore_postal(address),
            )
            return GeocodeLookupResult(
                latitude=1.3000,
                longitude=103.8500,
                formatted_address=address,
                address=mock_address,
                source=self.get_google_geocoding_metadata(),
            )

        result = await self._google_geocode(address)
        if result is None:
            return None
        latitude, longitude, formatted = result
        parsed_address = await self._google_address_for_forward_result(
            formatted=formatted,
            fallback=address,
        )
        return GeocodeLookupResult(
            latitude=latitude,
            longitude=longitude,
            formatted_address=formatted,
            address=parsed_address,
            source=self.get_google_geocoding_metadata(),
        )

    async def get_google_place_details(
        self, place_id: str | None
    ) -> Optional[Dict[str, Any]]:
        """Return selected Google Place details for current-use enrichment."""
        if not place_id:
            return None
        trimmed_place_id = place_id.strip()
        if not trimmed_place_id:
            return None
        if self.offline_mode or not self.google_maps_api_key or self.client is None:
            return None

        response = await self.client.get(
            self.google_places_details_url,
            params={
                "place_id": trimmed_place_id,
                "fields": "place_id,name,types,business_status,formatted_address",
                "key": self.google_maps_api_key,
            },
        )
        if response.status_code != 200:
            logger.warning(
                "google_place_details_failed",
                status_code=response.status_code,
                place_id=trimmed_place_id,
            )
            return None

        payload = response.json()
        if payload.get("status") != "OK" or not isinstance(payload.get("result"), dict):
            logger.info(
                "google_place_details_no_result",
                status=payload.get("status"),
                place_id=trimmed_place_id,
            )
            return None
        return payload["result"]

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

    async def _google_address_for_forward_result(
        self,
        *,
        formatted: str,
        fallback: str,
    ) -> Address:
        postal_code = self._extract_singapore_postal(formatted) or (
            self._extract_singapore_postal(fallback)
        )
        return Address(
            full_address=formatted or fallback,
            postal_code=postal_code,
            district=(
                self._get_district_from_postal(postal_code) if postal_code else None
            ),
            country="Singapore" if postal_code else "Unknown",
        )

    async def _onemap_geocode(self, address: str) -> Optional[GeocodeLookupResult]:
        if self.client is None:
            return None

        client = self.client
        response = await client.get(
            f"{self.onemap_base_url}/common/elastic/search",
            params={
                "searchVal": address,
                "returnGeom": "Y",
                "getAddrDetails": "Y",
                "pageNum": 1,
            },
        )
        if response.status_code != 200:
            logger.warning(
                "onemap_address_geocode_status",
                status_code=response.status_code,
                address=address,
            )
            return None

        payload = response.json()
        raw_results = payload.get("results")
        if not isinstance(raw_results, list) or not raw_results:
            return None

        candidates = [
            result
            for result in raw_results
            if isinstance(result, dict)
            and self._coerce_coordinate(result.get("LATITUDE")) is not None
            and self._coerce_coordinate(result.get("LONGITUDE")) is not None
        ]
        if not candidates:
            return None

        best = max(
            candidates,
            key=lambda entry: self._score_onemap_candidate(address, entry),
        )
        latitude = self._coerce_coordinate(best.get("LATITUDE"))
        longitude = self._coerce_coordinate(best.get("LONGITUDE"))
        if latitude is None or longitude is None:
            return None

        address_payload = self._parse_onemap_address(best, fallback=address)
        return GeocodeLookupResult(
            latitude=latitude,
            longitude=longitude,
            formatted_address=address_payload.full_address,
            address=address_payload,
            source=self.get_onemap_address_metadata(),
        )

    def _parse_onemap_address(
        self,
        result: dict[str, Any],
        *,
        fallback: str,
    ) -> Address:
        raw_address = str(result.get("ADDRESS") or "").strip()
        postal_code = self._normalise_onemap_text(result.get("POSTAL"))
        if not postal_code:
            postal_code = self._extract_singapore_postal(raw_address) or (
                self._extract_singapore_postal(fallback)
            )
        road_name = self._normalise_onemap_text(result.get("ROAD_NAME"))
        block_number = self._normalise_onemap_text(result.get("BLK_NO"))
        building_name = self._normalise_onemap_text(result.get("BUILDING"))
        search_value = self._normalise_onemap_text(result.get("SEARCHVAL"))

        formatted = raw_address or search_value or fallback
        if formatted and "singapore" not in formatted.lower():
            formatted = f"{formatted}, Singapore"
        if postal_code and postal_code not in formatted:
            formatted = f"{formatted} {postal_code}"

        return Address(
            full_address=formatted,
            street_name=road_name,
            building_name=building_name,
            block_number=block_number,
            postal_code=postal_code,
            district=self._get_district_from_postal(postal_code or ""),
            country="Singapore",
        )

    def _score_onemap_candidate(
        self,
        submitted_address: str,
        candidate: dict[str, Any],
    ) -> int:
        submitted = submitted_address.lower()
        candidate_address = " ".join(
            str(candidate.get(key) or "").lower()
            for key in ("ADDRESS", "SEARCHVAL", "ROAD_NAME", "BLK_NO", "POSTAL")
        )
        score = 0
        submitted_postal = self._extract_singapore_postal(submitted_address)
        candidate_postal = self._normalise_onemap_text(candidate.get("POSTAL"))
        if submitted_postal and candidate_postal == submitted_postal:
            score += 100

        submitted_number = self._leading_block_number(submitted_address)
        candidate_block = self._normalise_onemap_text(candidate.get("BLK_NO"))
        if (
            submitted_number
            and candidate_block
            and submitted_number == candidate_block.lower()
        ):
            score += 30

        for token in re.findall(r"[a-z0-9]+", submitted):
            if len(token) >= 3 and token in candidate_address:
                score += 3

        return score

    @staticmethod
    def _normalise_onemap_text(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        if not text or text.upper() == "NIL":
            return None
        return text

    @staticmethod
    def _coerce_coordinate(value: Any) -> float | None:
        try:
            coordinate = float(value)
        except (TypeError, ValueError):
            return None
        return coordinate if coordinate else None

    @staticmethod
    def _extract_singapore_postal(value: str | None) -> str | None:
        if not value:
            return None
        matches = re.findall(r"\b(\d{6})\b", value)
        return matches[-1] if matches else None

    @staticmethod
    def _leading_block_number(value: str | None) -> str | None:
        if not value:
            return None
        match = re.match(r"^\s*(\d+[a-zA-Z]?)(?=\s)", value)
        return match.group(1).lower() if match else None

    def _looks_like_singapore_address(self, address: str) -> bool:
        lower = address.lower()
        return (
            "singapore" in lower or self._extract_singapore_postal(address) is not None
        )

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
