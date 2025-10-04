"""GPS Property Logger for Commercial Property Advisors agent."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional, Tuple
from uuid import UUID, uuid4

import structlog
from app.models.property import Property, PropertyStatus, PropertyType
from app.services.agents.ura_integration import URAIntegrationService
from app.services.geocoding import Address, GeocodingService
from geoalchemy2.functions import ST_GeomFromText
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


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
        timestamp: datetime = None,
    ):
        self.property_id = property_id
        self.address = address
        self.coordinates = coordinates
        self.ura_zoning = ura_zoning
        self.existing_use = existing_use
        self.property_info = property_info
        self.nearby_amenities = nearby_amenities
        self.timestamp = timestamp or datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "property_id": str(self.property_id),
            "address": self.address.dict(),
            "coordinates": {
                "latitude": self.coordinates[0],
                "longitude": self.coordinates[1],
            },
            "ura_zoning": self.ura_zoning,
            "existing_use": self.existing_use,
            "property_info": self.property_info,
            "nearby_amenities": self.nearby_amenities,
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
                    ura_zoning,
                    existing_use,
                    property_info,
                )

            await session.commit()

            # Step 6: Log the property access
            await self._log_property_access(session, property_id, user_id)

            # Return comprehensive result
            return PropertyLogResult(
                property_id=property_id,
                address=address,
                coordinates=(latitude, longitude),
                ura_zoning=ura_zoning.dict() if ura_zoning else {},
                existing_use=existing_use or "Unknown",
                property_info=property_info.dict() if property_info else None,
                nearby_amenities=nearby_amenities,
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
        ura_zoning: Any,
        existing_use: str,
        property_info: Any,
    ) -> UUID:
        """Create new property record."""
        property_id = uuid4()

        # Determine property type from existing use
        property_type = self._determine_property_type(existing_use)

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
