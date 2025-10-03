"""Geocoding service for address lookup and reverse geocoding."""

from typing import Optional, Dict, Tuple, Any
from decimal import Decimal
import httpx
from pydantic import BaseModel
from app.core.config import settings
from app.services.base import AsyncClientService
import structlog

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
    """Service for geocoding and reverse geocoding using OneMap API (Singapore)."""
    
    def __init__(self):
        self.onemap_base_url = "https://www.onemap.gov.sg/api"
        self.google_maps_api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', None)
        try:
            self.client = httpx.AsyncClient(timeout=30.0)
        except RuntimeError:  # pragma: no cover - httpx stub unavailable
            logger.warning("httpx AsyncClient unavailable; geocoding service will operate in mock mode")
            self.client = None  # type: ignore[assignment]
    
    async def reverse_geocode(self, latitude: float, longitude: float) -> Optional[Address]:
        """Convert coordinates to address using OneMap API."""
        try:
            # Try OneMap first (free for Singapore)
            if self.client is None:
                raise RuntimeError("Geocoding client unavailable")

            response = await self.client.get(
                f"{self.onemap_base_url}/public/revgeocodexy",
                params={
                    "location": f"{latitude},{longitude}",
                    "buffer": 50,
                    "addressType": "all"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("GeocodeInfo") and len(data["GeocodeInfo"]) > 0:
                    geocode_info = data["GeocodeInfo"][0]
                    
                    return Address(
                        full_address=geocode_info.get("ROAD", "Unknown"),
                        street_name=geocode_info.get("ROAD"),
                        building_name=geocode_info.get("BUILDINGNAME"),
                        block_number=geocode_info.get("BLOCK"),
                        postal_code=geocode_info.get("POSTALCODE"),
                        district=self._get_district_from_postal(geocode_info.get("POSTALCODE", "")),
                        country="Singapore"
                    )
            
            # Fallback to Google Maps if available
            if self.google_maps_api_key:
                return await self._google_reverse_geocode(latitude, longitude)
            
            logger.warning(f"Reverse geocoding failed for {latitude}, {longitude}")
            return None
            
        except Exception as e:
            logger.error(f"Error in reverse geocoding: {str(e)}")
            return None
    
    async def geocode(self, address: str) -> Optional[Tuple[float, float]]:
        """Convert address to coordinates using OneMap API."""
        try:
            if self.client is None:
                raise RuntimeError("Geocoding client unavailable")

            response = await self.client.get(
                f"{self.onemap_base_url}/common/elastic/search",
                params={
                    "searchVal": address,
                    "returnGeom": "Y",
                    "getAddrDetails": "Y",
                    "pageNum": 1
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("results") and len(data["results"]) > 0:
                    result = data["results"][0]
                    latitude = float(result.get("LATITUDE", 0))
                    longitude = float(result.get("LONGITUDE", 0))
                    
                    if latitude and longitude:
                        return (latitude, longitude)
            
            # Fallback to Google Maps if available
            if self.google_maps_api_key:
                return await self._google_geocode(address)
            
            logger.warning(f"Geocoding failed for address: {address}")
            return None
            
        except Exception as e:
            logger.error(f"Error in geocoding: {str(e)}")
            return None
    
    async def get_nearby_amenities(
        self, 
        latitude: float, 
        longitude: float, 
        radius_m: int = 1000
    ) -> Dict[str, Any]:
        """Get nearby amenities using OneMap themes."""
        amenities = {
            "mrt_stations": [],
            "bus_stops": [],
            "schools": [],
            "shopping_malls": [],
            "parks": []
        }

        if self.client is None:
            logger.warning("Geocoding client unavailable; returning empty amenity list")
            return amenities
        
        # OneMap theme queries
        themes = {
            "mrt_stations": "railway_stn_exit",
            "bus_stops": "bus_stop",
            "schools": "schooldirectory",
            "shopping_malls": "shoppingmall",
            "parks": "parks"
        }
        
        for amenity_type, theme in themes.items():
            try:
                response = await self.client.get(
                    f"{self.onemap_base_url}/privateapi/themesvc/retrieveTheme",
                    params={
                        "queryName": theme,
                        "extents": f"{longitude-0.01},{latitude-0.01},{longitude+0.01},{latitude+0.01}"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "SrchResults" in data and data["SrchResults"]:
                        for result in data["SrchResults"][1:]:  # Skip header row
                            distance = self._calculate_distance(
                                latitude, longitude,
                                float(result.get("LatLng", "0,0").split(",")[0]),
                                float(result.get("LatLng", "0,0").split(",")[1])
                            )
                            if distance <= radius_m:
                                amenities[amenity_type].append({
                                    "name": result.get("NAME", "Unknown"),
                                    "distance_m": distance
                                })
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
            (79, 80): "D28 - Seletar, Yio Chu Kang"
        }
        
        for postal_range, district in district_map.items():
            if postal_range[0] <= prefix <= postal_range[1]:
                return district
        
        return None
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in meters using Haversine formula."""
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)
        
        a = sin(delta_lat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    async def _google_reverse_geocode(self, latitude: float, longitude: float) -> Optional[Address]:
        """Fallback to Google Maps for reverse geocoding."""
        # Implementation for Google Maps API
        # This is a placeholder - implement if Google Maps API key is provided
        return None
    
    async def _google_geocode(self, address: str) -> Optional[Tuple[float, float]]:
        """Fallback to Google Maps for geocoding."""
        # Implementation for Google Maps API
        # This is a placeholder - implement if Google Maps API key is provided
        return None
    
