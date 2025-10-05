"""GPS Property Logger for Commercial Property Advisors agent."""

import asyncio
from datetime import datetime
from decimal import Decimal
from enum import Enum
from statistics import mean
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

import structlog
from app.models.property import Property, PropertyStatus, PropertyType
from app.services.agents.ura_integration import URAIntegrationService
from app.services.geocoding import Address, GeocodingService
from geoalchemy2.functions import ST_GeomFromText
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class DevelopmentScenario(str, Enum):
    """Supported development scenarios for quick GPS analysis."""

    RAW_LAND = "raw_land"
    EXISTING_BUILDING = "existing_building"
    HERITAGE_PROPERTY = "heritage_property"
    UNDERUSED_ASSET = "underused_asset"

    @classmethod
    def default_set(cls) -> List["DevelopmentScenario"]:
        """Return the default ordered list of scenarios to analyse."""

        return [
            cls.RAW_LAND,
            cls.EXISTING_BUILDING,
            cls.HERITAGE_PROPERTY,
            cls.UNDERUSED_ASSET,
        ]


class PropertyLogResult:
    """Result of GPS property logging."""

    def __init__(
        self,
        property_id: UUID,
        address: Address,
        coordinates: Tuple[float, float],
        ura_zoning: Dict[str, Any],
        existing_use: str,
        property_info: Optional[Dict[str, Any]] = None,
        nearby_amenities: Optional[Dict[str, Any]] = None,
        quick_analysis: Optional[Dict[str, Any]] = None,
        timestamp: datetime = None,
    ):
        self.property_id = property_id
        self.address = address
        self.coordinates = coordinates
        self.ura_zoning = ura_zoning
        self.existing_use = existing_use
        self.property_info = property_info
        self.nearby_amenities = nearby_amenities
        self.quick_analysis = quick_analysis
        self.timestamp = timestamp or datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "property_id": str(self.property_id),
            "address": self.address.model_dump(),
            "coordinates": {
                "latitude": self.coordinates[0],
                "longitude": self.coordinates[1],
            },
            "ura_zoning": self.ura_zoning,
            "existing_use": self.existing_use,
            "property_info": self.property_info,
            "nearby_amenities": self.nearby_amenities,
            "quick_analysis": self.quick_analysis,
            "timestamp": self.timestamp.isoformat(),
        }


class GPSPropertyLogger:
    """Service for logging properties via GPS coordinates."""

    def __init__(
        self, geocoding_service: GeocodingService, ura_service: URAIntegrationService
    ):
        self.geocoding = geocoding_service
        self.ura = ura_service

    async def log_property_from_gps(
        self,
        latitude: float,
        longitude: float,
        session: AsyncSession,
        user_id: Optional[UUID] = None,
        scenarios: Optional[List[DevelopmentScenario]] = None,
    ) -> PropertyLogResult:
        """
        Log a property from GPS coordinates.

        This will:
        1. Reverse geocode to get address
        2. Fetch URA zoning information
        3. Determine existing use
        4. Get nearby amenities
        5. Create or update property record
        6. Return comprehensive property information
        """
        try:
            # Step 1: Reverse geocode to get address
            logger.info(f"Reverse geocoding coordinates: {latitude}, {longitude}")
            address = await self.geocoding.reverse_geocode(latitude, longitude)

            if not address:
                raise ValueError(
                    f"Could not reverse geocode coordinates: {latitude}, {longitude}"
                )

            # Step 2: Check if property already exists at this location
            property_record = await self._find_existing_property(
                session, latitude, longitude, address
            )

            # Step 3: Fetch URA data
            ura_zoning = await self.ura.get_zoning_info(address.full_address)
            existing_use = await self.ura.get_existing_use(address.full_address)
            property_info = await self.ura.get_property_info(address.full_address)
            property_type = self._determine_property_type(existing_use or "")

            development_plans_task = asyncio.create_task(
                self.ura.get_development_plans(latitude, longitude)
            )
            transactions_task = asyncio.create_task(
                self.ura.get_transaction_data(property_type.value, address.district)
            )
            rentals_task = asyncio.create_task(
                self.ura.get_rental_data(property_type.value, address.district)
            )

            # Step 4: Get nearby amenities
            nearby_amenities = await self.geocoding.get_nearby_amenities(
                latitude, longitude, radius_m=1000
            )

            # Step 5: Create or update property record
            if property_record:
                property_id = property_record.id
                # Update existing property with latest info
                await self._update_property(
                    session, property_record, address, ura_zoning, property_info
                )
            else:
                # Create new property record
                property_id = await self._create_property(
                    session,
                    address,
                    latitude,
                    longitude,
                    property_type,
                    ura_zoning,
                    existing_use,
                    property_info,
                )

            await session.commit()

            # Step 6: Log the property access
            await self._log_property_access(session, property_id, user_id)

            development_plans = await development_plans_task
            transactions = await transactions_task
            rentals = await rentals_task

            quick_analysis = self._generate_quick_analysis(
                scenarios or DevelopmentScenario.default_set(),
                ura_zoning=ura_zoning,
                property_info=property_info,
                existing_use=existing_use,
                nearby_amenities=nearby_amenities,
                property_type=property_type,
                development_plans=development_plans,
                transactions=transactions,
                rentals=rentals,
            )

            # Return comprehensive result
            return PropertyLogResult(
                property_id=property_id,
                address=address,
                coordinates=(latitude, longitude),
                ura_zoning=ura_zoning.model_dump() if ura_zoning else {},
                existing_use=existing_use or "Unknown",
                property_info=property_info.model_dump() if property_info else None,
                nearby_amenities=nearby_amenities,
                quick_analysis=quick_analysis,
            )

        except Exception as e:
            logger.error(f"Error logging property from GPS: {str(e)}")
            await session.rollback()
            raise

    async def _find_existing_property(
        self, session: AsyncSession, latitude: float, longitude: float, address: Address
    ) -> Optional[Property]:
        """Find existing property at location or with same address."""
        # First try to find by coordinates (within 50m radius)
        point_wkt = f"POINT({longitude} {latitude})"

        if hasattr(Property.location, "ST_DWithin"):
            stmt = select(Property).where(
                Property.location.ST_DWithin(
                    ST_GeomFromText(point_wkt, 4326), 50  # 50 meters
                )
            )
            result = await session.execute(stmt)
            property_record = result.scalar_one_or_none()
            if property_record:
                return property_record

        # Try to find by postal code if available
        if address.postal_code:
            stmt = select(Property).where(Property.postal_code == address.postal_code)
            result = await session.execute(stmt)
            property_record = result.scalar_one_or_none()

            if property_record:
                return property_record

        return None

    async def _create_property(
        self,
        session: AsyncSession,
        address: Address,
        latitude: float,
        longitude: float,
        property_type: PropertyType,
        ura_zoning: Any,
        existing_use: str,
        property_info: Any,
    ) -> UUID:
        """Create new property record."""
        property_id = uuid4()

        # Create point geometry
        point = f"POINT({longitude} {latitude})"

        property_data = {
            "id": property_id,
            "name": (
                property_info.property_name
                if property_info
                else address.building_name or "Unknown Property"
            ),
            "address": address.full_address,
            "postal_code": address.postal_code,
            "property_type": property_type,
            "status": PropertyStatus.EXISTING,
            "location": point,
            "district": address.district,
            "zoning_code": ura_zoning.zone_code if ura_zoning else None,
            "plot_ratio": float(ura_zoning.plot_ratio) if ura_zoning else None,
            "data_source": "GPS_LOGGER",
        }

        # Add property info if available
        if property_info:
            property_data.update(
                {
                    "land_area_sqm": (
                        Decimal(str(property_info.site_area_sqm))
                        if property_info.site_area_sqm
                        else None
                    ),
                    "gross_floor_area_sqm": (
                        Decimal(str(property_info.gfa_approved))
                        if property_info.gfa_approved
                        else None
                    ),
                    "building_height_m": (
                        Decimal(str(property_info.building_height))
                        if property_info.building_height
                        else None
                    ),
                    "year_built": property_info.completion_year,
                    "tenure_type": self._map_tenure_type(property_info.tenure),
                }
            )

        stmt = insert(Property).values(**property_data)
        await session.execute(stmt)

        logger.info(f"Created new property record: {property_id}")
        return property_id

    async def _update_property(
        self,
        session: AsyncSession,
        property_record: Property,
        address: Address,
        ura_zoning: Any,
        property_info: Any,
    ):
        """Update existing property with latest information."""
        # Update fields that might have changed
        property_record.updated_at = datetime.utcnow()

        if ura_zoning:
            property_record.zoning_code = ura_zoning.zone_code
            property_record.plot_ratio = float(ura_zoning.plot_ratio)

        if property_info and property_info.gfa_approved:
            property_record.gross_floor_area_sqm = Decimal(
                str(property_info.gfa_approved)
            )

        logger.info(f"Updated property record: {property_record.id}")

    async def _log_property_access(
        self, session: AsyncSession, property_id: UUID, user_id: Optional[UUID]
    ):
        """Log property access for audit trail."""
        # This would integrate with the existing audit system
        # For now, we'll just log it
        logger.info(f"Property accessed: {property_id} by user: {user_id}")

    def _determine_property_type(self, existing_use: str) -> PropertyType:
        """Map existing use string to PropertyType enum."""
        use_lower = existing_use.lower()

        if "office" in use_lower:
            return PropertyType.OFFICE
        elif "retail" in use_lower or "shop" in use_lower or "mall" in use_lower:
            return PropertyType.RETAIL
        elif (
            "industrial" in use_lower
            or "warehouse" in use_lower
            or "factory" in use_lower
        ):
            return PropertyType.INDUSTRIAL
        elif (
            "residential" in use_lower
            or "condo" in use_lower
            or "apartment" in use_lower
        ):
            return PropertyType.RESIDENTIAL
        elif "hotel" in use_lower:
            return PropertyType.HOTEL
        elif "mixed" in use_lower:
            return PropertyType.MIXED_USE
        else:
            return PropertyType.SPECIAL_PURPOSE

    def _map_tenure_type(self, tenure_str: str) -> str:
        """Map tenure string to TenureType enum value."""
        tenure_lower = tenure_str.lower()

        if "freehold" in tenure_lower:
            return "freehold"
        elif "999" in tenure_lower:
            return "leasehold_999"
        elif "99" in tenure_lower:
            return "leasehold_99"
        elif "60" in tenure_lower:
            return "leasehold_60"
        elif "30" in tenure_lower:
            return "leasehold_30"
        else:
            return "leasehold_other"

    def _generate_quick_analysis(
        self,
        scenarios: List[DevelopmentScenario],
        *,
        ura_zoning: Optional[Any],
        property_info: Optional[Any],
        existing_use: Optional[str],
        nearby_amenities: Optional[Dict[str, Any]],
        property_type: PropertyType,
        development_plans: List[Dict[str, Any]],
        transactions: List[Dict[str, Any]],
        rentals: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate a lightweight, scenario-based analysis for GPS captures."""

        insights: List[Dict[str, Any]] = []
        for scenario in scenarios:
            if scenario == DevelopmentScenario.RAW_LAND:
                insights.append(
                    self._quick_raw_land_analysis(
                        ura_zoning, property_info, development_plans
                    )
                )
            elif scenario == DevelopmentScenario.EXISTING_BUILDING:
                insights.append(
                    self._quick_existing_asset_analysis(
                        ura_zoning, property_info, transactions
                    )
                )
            elif scenario == DevelopmentScenario.HERITAGE_PROPERTY:
                insights.append(
                    self._quick_heritage_analysis(
                        property_info,
                        existing_use,
                        ura_zoning,
                        development_plans,
                    )
                )
            elif scenario == DevelopmentScenario.UNDERUSED_ASSET:
                insights.append(
                    self._quick_underused_analysis(
                        existing_use,
                        nearby_amenities,
                        property_info,
                        rentals,
                        property_type,
                    )
                )

        return {
            "generated_at": datetime.utcnow().isoformat(),
            "scenarios": insights,
        }

    @staticmethod
    def _safe_float(value: Optional[Any]) -> Optional[float]:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_int(value: Optional[Any]) -> Optional[int]:
        coerced = GPSPropertyLogger._safe_float(value)
        if coerced is None:
            return None
        return int(round(coerced))

    @staticmethod
    def _average(values: List[Optional[float]]) -> Optional[float]:
        numeric = [value for value in values if value is not None]
        if not numeric:
            return None
        return float(mean(numeric))

    @staticmethod
    def _nearest_plan_completion(
        development_plans: List[Dict[str, Any]]
    ) -> Optional[str]:
        nearest_ribbon: Optional[str] = None
        shortest_distance = float("inf")
        for plan in development_plans:
            distance = GPSPropertyLogger._safe_float(plan.get("distance_km"))
            completion = plan.get("expected_completion")
            if distance is None or completion is None:
                continue
            if distance < shortest_distance:
                shortest_distance = distance
                nearest_ribbon = str(completion)
        return nearest_ribbon

    def _quick_raw_land_analysis(
        self,
        ura_zoning: Optional[Any],
        property_info: Optional[Any],
        development_plans: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        site_area = (
            self._safe_float(getattr(property_info, "site_area_sqm", None))
            if property_info
            else None
        )
        plot_ratio = (
            self._safe_float(getattr(ura_zoning, "plot_ratio", None))
            if ura_zoning
            else None
        )
        potential_gfa = site_area * plot_ratio if site_area and plot_ratio else None
        development_count = len(development_plans)
        nearest_completion = self._nearest_plan_completion(development_plans)

        headline: str
        if potential_gfa:
            headline = (
                f"Est. max GFA ≈ {potential_gfa:,.0f} sqm using plot ratio {plot_ratio}"
            )
        else:
            headline = "Plot ratio or site area missing — manual GFA check needed"

        return {
            "scenario": DevelopmentScenario.RAW_LAND.value,
            "headline": headline,
            "metrics": {
                "site_area_sqm": site_area,
                "plot_ratio": plot_ratio,
                "potential_gfa_sqm": potential_gfa,
                "nearby_development_count": development_count,
                "nearest_completion": nearest_completion,
            },
            "notes": list(
                filter(
                    None,
                    [
                        getattr(
                            ura_zoning, "zone_description", "Zoning data unavailable"
                        ),
                        getattr(ura_zoning, "special_conditions", None),
                        f"{development_count} upcoming projects within 2 km",
                    ],
                )
            ),
        }

    def _quick_existing_asset_analysis(
        self,
        ura_zoning: Optional[Any],
        property_info: Optional[Any],
        transactions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        approved_gfa = (
            self._safe_float(getattr(property_info, "gfa_approved", None))
            if property_info
            else None
        )
        plot_ratio = (
            self._safe_float(getattr(ura_zoning, "plot_ratio", None))
            if ura_zoning
            else None
        )
        site_area = (
            self._safe_float(getattr(property_info, "site_area_sqm", None))
            if property_info
            else None
        )
        potential_gfa = plot_ratio * site_area if plot_ratio and site_area else None
        uplift = (
            (potential_gfa - approved_gfa) if potential_gfa and approved_gfa else None
        )

        transaction_psf = [
            self._safe_float(transaction.get("psf_price"))
            for transaction in transactions
        ]
        average_psf = self._average(transaction_psf)
        transaction_count = len(transactions)

        if uplift and uplift > 0:
            headline = (
                f"Potential uplift of ≈ {uplift:,.0f} sqm compared to approved GFA"
            )
        elif approved_gfa:
            headline = "Existing approvals already near zoning limit"
        else:
            headline = "No approved GFA data — assess existing building efficiency"

        return {
            "scenario": DevelopmentScenario.EXISTING_BUILDING.value,
            "headline": headline,
            "metrics": {
                "approved_gfa_sqm": approved_gfa,
                "scenario_gfa_sqm": potential_gfa,
                "gfa_uplift_sqm": uplift,
                "recent_transaction_count": transaction_count,
                "average_psf_price": average_psf,
            },
            "notes": [
                "Consider retrofit or adaptive reuse options to unlock unused GFA",
            ],
        }

    def _quick_heritage_analysis(
        self,
        property_info: Optional[Any],
        existing_use: Optional[str],
        ura_zoning: Optional[Any],
        development_plans: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        completion_year = (
            int(property_info.completion_year)
            if property_info and property_info.completion_year
            else None
        )
        heritage_risk = "medium"
        notes: List[str] = []

        if completion_year and completion_year < 1970:
            notes.append("Asset predates 1970 — likely conservation review required")
            heritage_risk = "high"
        elif "conservation" in (existing_use or "").lower():
            notes.append("Existing use indicates conservation-sensitive asset")
            heritage_risk = "high"
        else:
            notes.append(
                getattr(
                    ura_zoning,
                    "special_conditions",
                    "Check URA conservation portal for obligations",
                )
            )

        if development_plans:
            notes.append(
                f"{len(development_plans)} planned projects nearby may influence heritage dialogue"
            )

        return {
            "scenario": DevelopmentScenario.HERITAGE_PROPERTY.value,
            "headline": f"Heritage risk assessment: {heritage_risk.upper()}",
            "metrics": {
                "completion_year": completion_year,
                "heritage_risk": heritage_risk,
            },
            "notes": [note for note in notes if note],
        }

    def _quick_underused_analysis(
        self,
        existing_use: Optional[str],
        nearby_amenities: Optional[Dict[str, Any]],
        property_info: Optional[Any],
        rentals: List[Dict[str, Any]],
        property_type: PropertyType,
    ) -> Dict[str, Any]:
        amenity_summary = (
            len(nearby_amenities.get("mrt_stations", [])) if nearby_amenities else 0
        )
        building_height = (
            self._safe_float(getattr(property_info, "building_height", None))
            if property_info
            else None
        )

        notes = []
        if amenity_summary == 0:
            notes.append("Limited transit access — consider last-mile improvements")
        else:
            notes.append("Strong transit presence supports repositioning")

        if building_height and building_height < 20:
            notes.append(
                "Low-rise profile — explore vertical expansion if zoning permits"
            )

        average_rent = self._average(
            [self._safe_float(rental.get("monthly_rent")) for rental in rentals]
        )
        rental_count = len(rentals)

        if rental_count == 0:
            notes.append(
                "No nearby rental comps in dataset — check brokerage feeds for fresh pricing"
            )

        return {
            "scenario": DevelopmentScenario.UNDERUSED_ASSET.value,
            "headline": "Review asset utilisation versus surrounding demand",
            "metrics": {
                "nearby_mrt_count": amenity_summary,
                "current_use": existing_use,
                "building_height_m": building_height,
                "average_monthly_rent": average_rent,
                "rental_comparable_count": rental_count,
                "property_type": property_type.value,
            },
            "notes": notes,
        }
