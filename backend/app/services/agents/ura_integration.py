"""URA (Urban Redevelopment Authority) integration service for Singapore property data."""

from typing import Optional, Dict, List, Any
from datetime import datetime, date
import httpx
from pydantic import BaseModel
from backend.app.core.config import settings
import structlog

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


class URAIntegrationService:
    """Service for integrating with URA APIs for property and zoning data."""
    
    def __init__(self):
        self.base_url = "https://www.ura.gov.sg/uraDataService/insertNewToken.action"
        self.access_key = getattr(settings, 'URA_ACCESS_KEY', None)
        self.token = None
        self.token_expiry = None
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def _get_token(self) -> Optional[str]:
        """Get or refresh URA API token."""
        if self.token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.token
        
        if not self.access_key:
            logger.warning("URA access key not configured")
            return None
        
        try:
            response = await self.client.get(
                self.base_url,
                headers={"AccessKey": self.access_key}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("Result")
                # Token valid for 24 hours
                self.token_expiry = datetime.now().replace(hour=23, minute=59, second=59)
                return self.token
            else:
                logger.error(f"Failed to get URA token: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting URA token: {str(e)}")
            return None
    
    async def get_zoning_info(self, address: str) -> Optional[URAZoningInfo]:
        """Get zoning information for a property address."""
        # This is a mock implementation as URA API requires specific endpoints
        # In production, this would call the actual URA Master Plan API
        
        # Mock data based on common Singapore zones
        mock_zones = {
            "Commercial": URAZoningInfo(
                zone_code="C",
                zone_description="Commercial",
                plot_ratio=12.0,
                building_height_limit=280.0,
                site_coverage=100.0,
                use_groups=["Office", "Retail", "Hotel", "Restaurant"],
                special_conditions="Subject to urban design guidelines"
            ),
            "Residential": URAZoningInfo(
                zone_code="R",
                zone_description="Residential",
                plot_ratio=2.8,
                building_height_limit=36.0,
                site_coverage=50.0,
                use_groups=["Residential", "Home Office"],
                special_conditions="Minimum unit size applies"
            ),
            "Business": URAZoningInfo(
                zone_code="B1",
                zone_description="Business 1",
                plot_ratio=2.5,
                building_height_limit=None,
                site_coverage=60.0,
                use_groups=["Light Industrial", "Office", "Warehouse"],
                special_conditions="No pollutive uses allowed"
            ),
            "Mixed": URAZoningInfo(
                zone_code="MU",
                zone_description="Mixed Use",
                plot_ratio=5.0,
                building_height_limit=100.0,
                site_coverage=70.0,
                use_groups=["Commercial", "Residential", "Office"],
                special_conditions="Minimum 40% residential component"
            )
        }
        
        # Simple mock logic - in reality would use actual API
        if "orchard" in address.lower() or "raffles" in address.lower():
            return mock_zones["Commercial"]
        elif "industrial" in address.lower() or "jurong" in address.lower():
            return mock_zones["Business"]
        elif "marina" in address.lower():
            return mock_zones["Mixed"]
        else:
            return mock_zones["Residential"]
    
    async def get_existing_use(self, address: str) -> Optional[str]:
        """Get existing use of a property."""
        # Mock implementation
        existing_uses = {
            "office": "Office Building",
            "retail": "Shopping Mall",
            "residential": "Condominium",
            "industrial": "Warehouse",
            "hotel": "Hotel",
            "mixed": "Mixed Development"
        }
        
        # Simple keyword matching
        for keyword, use in existing_uses.items():
            if keyword in address.lower():
                return use
        
        return "Commercial Building"
    
    async def get_property_info(self, address: str) -> Optional[URAPropertyInfo]:
        """Get detailed property information from URA."""
        # Mock implementation - in production would call URA REALIS API
        
        return URAPropertyInfo(
            property_name="Mock Property",
            tenure="99-year leasehold",
            site_area_sqm=5000.0,
            gfa_approved=25000.0,
            building_height=50.0,
            completion_year=2015,
            last_transaction_date=date(2023, 6, 15),
            last_transaction_price=150000000.0
        )
    
    async def get_development_plans(
        self, 
        latitude: float, 
        longitude: float, 
        radius_km: float = 2.0
    ) -> List[Dict[str, Any]]:
        """Get nearby development plans and proposals."""
        # Mock implementation - in production would call URA Development Control API
        
        mock_plans = [
            {
                "project_name": "New Commercial Development",
                "developer": "Major Developer Pte Ltd",
                "status": "Approved",
                "gfa": 50000,
                "use": "Office/Retail",
                "expected_completion": "2026",
                "distance_km": 0.5
            },
            {
                "project_name": "Mixed-Use Tower",
                "developer": "Property Giant Ltd",
                "status": "Under Construction",
                "gfa": 80000,
                "use": "Residential/Commercial",
                "expected_completion": "2025",
                "distance_km": 1.2
            }
        ]
        
        return mock_plans
    
    async def get_transaction_data(
        self, 
        property_type: str,
        district: Optional[str] = None,
        months_back: int = 12
    ) -> List[Dict[str, Any]]:
        """Get recent transaction data from URA REALIS."""
        # Mock implementation - in production would call URA REALIS API
        
        mock_transactions = []
        
        # Generate some mock transaction data
        import random
        from datetime import timedelta
        
        for i in range(10):
            transaction_date = date.today() - timedelta(days=random.randint(1, months_back * 30))
            
            mock_transactions.append({
                "transaction_date": transaction_date.isoformat(),
                "property_type": property_type,
                "district": district or f"D{random.randint(1, 28):02d}",
                "project_name": f"Project {i+1}",
                "floor_area_sqm": random.randint(50, 500),
                "price": random.randint(1000000, 10000000),
                "psf_price": random.randint(1000, 3000),
                "buyer_type": random.choice(["Individual", "Company", "Foreign Individual"]),
                "tenure": random.choice(["Freehold", "99-year leasehold"])
            })
        
        return sorted(mock_transactions, key=lambda x: x["transaction_date"], reverse=True)
    
    async def get_rental_data(
        self,
        property_type: str,
        district: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get rental transaction data."""
        # Mock implementation
        
        mock_rentals = []
        import random
        
        for i in range(5):
            mock_rentals.append({
                "property_name": f"Building {i+1}",
                "property_type": property_type,
                "district": district or f"D{random.randint(1, 28):02d}",
                "floor_area_sqm": random.randint(100, 1000),
                "monthly_rent": random.randint(5000, 50000),
                "psf_monthly": random.uniform(3.0, 10.0),
                "lease_commencement": date.today().isoformat(),
                "lease_term_years": random.choice([1, 2, 3, 5])
            })
        
        return mock_rentals
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
        

# Singleton instance
ura_service = URAIntegrationService()