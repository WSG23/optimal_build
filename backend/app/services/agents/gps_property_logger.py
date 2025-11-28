"""GPS Property Logger for Commercial Property Advisors agent."""

import asyncio
from datetime import datetime
from decimal import Decimal
from enum import Enum
from statistics import mean
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

import structlog
from geoalchemy2.functions import ST_GeomFromText

try:  # pragma: no cover - geoalchemy may be optional in some environments
    from geoalchemy2.elements import WKTElement
except ModuleNotFoundError:  # pragma: no cover - fallback when geoalchemy missing
    WKTElement = None
from backend._compat.datetime import utcnow

from app.models.property import Property, PropertyStatus, PropertyType
from app.services.agents.ura_integration import URAIntegrationService
from app.services.developer_checklist_service import (
    DEFAULT_TEMPLATE_DEFINITIONS,
    DeveloperChecklistService,
)
from app.services.geocoding import Address, GeocodingService
from app.services.heritage_overlay import HeritageOverlayService
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class DevelopmentScenario(str, Enum):
    """Supported development scenarios for quick GPS analysis."""

    RAW_LAND = "raw_land"
    EXISTING_BUILDING = "existing_building"
    HERITAGE_PROPERTY = "heritage_property"
    UNDERUSED_ASSET = "underused_asset"
    MIXED_USE_REDEVELOPMENT = "mixed_use_redevelopment"

    @classmethod
    def default_set(cls) -> List["DevelopmentScenario"]:
        """Return the default ordered list of scenarios to analyse."""

        return [
            cls.RAW_LAND,
            cls.EXISTING_BUILDING,
            cls.HERITAGE_PROPERTY,
            cls.UNDERUSED_ASSET,
            cls.MIXED_USE_REDEVELOPMENT,
        ]


# Accuracy bands for Quick Analysis metrics by asset class.
# Values represent percentage range (±%) based on data completeness and market volatility.
# Source: Phase 1A spec "Accuracy Bands display (±8-15% by asset class)"
# Dict structure: { metric_category: { low_pct: float, high_pct: float, source: str } }
QUICK_ANALYSIS_ACCURACY_BANDS: Dict[str, Dict[str, Any]] = {
    # Metric-level bands (apply across all scenarios)
    "gfa": {"low_pct": -10, "high_pct": 8, "source": "plot_ratio_variance"},
    "site_area": {"low_pct": -5, "high_pct": 5, "source": "survey_tolerance"},
    "plot_ratio": {"low_pct": -3, "high_pct": 3, "source": "zoning_interpretation"},
    "price_psf": {"low_pct": -12, "high_pct": 10, "source": "transaction_variance"},
    "rent_psm": {"low_pct": -15, "high_pct": 12, "source": "market_volatility"},
    "valuation": {"low_pct": -12, "high_pct": 12, "source": "appraisal_variance"},
    "noi": {"low_pct": -15, "high_pct": 10, "source": "income_projection"},
    "heritage_risk": {"low_pct": -8, "high_pct": 15, "source": "regulatory_assessment"},
    "uplift": {"low_pct": -15, "high_pct": 10, "source": "gfa_variance_compound"},
}

# Asset class-specific adjustments (multiplier on base bands)
ASSET_CLASS_ACCURACY_MODIFIERS: Dict[str, float] = {
    "office": 1.0,  # baseline
    "retail": 1.15,  # +15% wider bands due to higher volatility
    "industrial": 0.9,  # -10% narrower bands, more standardised
    "residential": 1.1,  # +10% wider bands
    "mixed_use": 1.2,  # +20% wider bands due to complexity
    "heritage": 1.25,  # +25% wider bands due to regulatory uncertainty
}


def _get_accuracy_band(
    metric_key: str, asset_class: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Get accuracy band for a metric, optionally adjusted by asset class.

    Args:
        metric_key: The metric name (e.g., 'potential_gfa_sqm')
        asset_class: Optional asset class for band adjustment

    Returns:
        Dict with low_pct, high_pct, source, or None if no band defined
    """
    # Map metric keys to band categories
    key_mapping = {
        "potential_gfa_sqm": "gfa",
        "gfa_sqm": "gfa",
        "approved_gfa": "gfa",
        "uplift_gfa_sqm": "uplift",
        "site_area_sqm": "site_area",
        "plot_ratio": "plot_ratio",
        "average_psf": "price_psf",
        "average_price_psf": "price_psf",
        "est_noi": "noi",
        "estimated_noi": "noi",
        "est_valuation": "valuation",
        "estimated_value": "valuation",
        "heritage_risk_score": "heritage_risk",
        "rent_psm": "rent_psm",
        "average_rent": "rent_psm",
    }

    band_key = key_mapping.get(metric_key)
    if not band_key or band_key not in QUICK_ANALYSIS_ACCURACY_BANDS:
        return None

    base_band = QUICK_ANALYSIS_ACCURACY_BANDS[band_key].copy()

    # Apply asset class modifier if provided
    if asset_class:
        modifier = ASSET_CLASS_ACCURACY_MODIFIERS.get(asset_class.lower(), 1.0)
        base_band["low_pct"] = round(base_band["low_pct"] * modifier, 1)
        base_band["high_pct"] = round(base_band["high_pct"] * modifier, 1)
        base_band["asset_class"] = asset_class

    return base_band


def _add_accuracy_bands_to_metrics(
    metrics: Dict[str, Any], asset_class: Optional[str] = None
) -> Dict[str, Any]:
    """Add accuracy bands to metrics that have defined band configurations.

    Args:
        metrics: Dictionary of metric values
        asset_class: Optional asset class for band adjustment

    Returns:
        New dictionary with accuracy_bands key containing band info per metric
    """
    accuracy_bands: Dict[str, Dict[str, Any]] = {}

    for metric_key, metric_value in metrics.items():
        if metric_value is not None and isinstance(metric_value, (int, float)):
            band = _get_accuracy_band(metric_key, asset_class)
            if band:
                accuracy_bands[metric_key] = band

    if accuracy_bands:
        return {**metrics, "accuracy_bands": accuracy_bands}
    return metrics


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
        timestamp: Optional[datetime] = None,
        heritage_overlay: Optional[Dict[str, Any]] = None,
        jurisdiction_code: str = "SG",
    ):
        self.property_id = property_id
        self.address = address
        self.coordinates = coordinates
        self.ura_zoning = ura_zoning
        self.existing_use = existing_use
        self.property_info = property_info
        self.nearby_amenities = nearby_amenities
        self.quick_analysis = quick_analysis
        self.timestamp = timestamp or utcnow()
        self.heritage_overlay = heritage_overlay
        self.jurisdiction_code = jurisdiction_code

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
            "heritage_overlay": self.heritage_overlay,
            "jurisdiction_code": self.jurisdiction_code,
        }


class GPSPropertyLogger:
    """Service for logging properties via GPS coordinates."""

    def __init__(
        self, geocoding_service: GeocodingService, ura_service: URAIntegrationService
    ):
        self.geocoding = geocoding_service
        self.ura = ura_service
        self.heritage_service = HeritageOverlayService()

    async def log_property_from_gps(
        self,
        latitude: float,
        longitude: float,
        session: AsyncSession,
        user_id: Optional[UUID] = None,
        scenarios: Optional[List[DevelopmentScenario]] = None,
        jurisdiction_code: str | None = None,
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
        jurisdiction = (jurisdiction_code or "SG").strip().upper() or "SG"
        try:
            # Step 1: Reverse geocode to get address
            logger.info(f"Reverse geocoding coordinates: {latitude}, {longitude}")
            address = await self.geocoding.reverse_geocode(latitude, longitude)

            if not address:
                raise ValueError(
                    f"Could not reverse geocode coordinates: {latitude}, {longitude}"
                )
            if jurisdiction == "HK" and address.country != "Hong Kong":
                address.country = "Hong Kong"

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

            heritage_overlay = self.heritage_service.lookup(latitude, longitude)

            # Step 5: Create or update property record
            if property_record:
                property_id = property_record.id
                await self._update_property(
                    session,
                    property_record,
                    address,
                    ura_zoning,
                    property_info,
                    jurisdiction,
                )
            else:
                property_id = await self._create_property(
                    session,
                    address,
                    latitude,
                    longitude,
                    property_type,
                    ura_zoning,
                    existing_use,
                    property_info,
                    jurisdiction,
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
                heritage_overlay=heritage_overlay,
                jurisdiction_code=jurisdiction,
            )

            if property_info is None:
                property_info_payload: Dict[str, Any] = {}
            elif hasattr(property_info, "model_dump"):
                property_info_payload = property_info.model_dump()
            elif isinstance(property_info, dict):
                property_info_payload = dict(property_info)
            else:
                property_info_payload = {}
            if heritage_overlay:
                overlay_notes = heritage_overlay.get("notes") or []
                if overlay_notes:
                    property_info_payload.setdefault(
                        "heritage_constraints", overlay_notes
                    )
                property_info_payload.setdefault(
                    "heritage_overlay", heritage_overlay.get("name")
                )
                property_info_payload.setdefault(
                    "heritage_risk", heritage_overlay.get("risk")
                )
                premium = heritage_overlay.get("heritage_premium_pct")
                if premium is not None:
                    property_info_payload.setdefault("heritage_premium_pct", premium)
                source = heritage_overlay.get("source")
                if source:
                    property_info_payload.setdefault("heritage_overlay_source", source)

            scenario_slugs = [
                (
                    scenario.value
                    if isinstance(scenario, DevelopmentScenario)
                    else str(scenario)
                )
                for scenario in (scenarios or DevelopmentScenario.default_set())
            ]
            if not scenario_slugs:
                scenario_slugs = sorted(
                    {
                        str(definition["development_scenario"])
                        for definition in DEFAULT_TEMPLATE_DEFINITIONS
                    }
                )

            await DeveloperChecklistService.ensure_templates_seeded(session)
            await DeveloperChecklistService.auto_populate_checklist(
                session=session,
                property_id=property_id,
                development_scenarios=scenario_slugs,
            )
            await session.commit()

            # Return comprehensive result
            return PropertyLogResult(
                property_id=property_id,
                address=address,
                coordinates=(latitude, longitude),
                ura_zoning=ura_zoning.model_dump() if ura_zoning else {},
                existing_use=existing_use or "Unknown",
                property_info=property_info_payload or None,
                nearby_amenities=nearby_amenities,
                quick_analysis=quick_analysis,
                timestamp=utcnow(),
                heritage_overlay=heritage_overlay,
                jurisdiction_code=jurisdiction,
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
        jurisdiction_code: str,
    ) -> UUID:
        """Create new property record."""
        property_id = uuid4()

        # Create point geometry
        point = f"SRID=4326;POINT({longitude} {latitude})"
        location_value: Any = point
        if hasattr(Property.location, "ST_GeomFromText"):
            try:
                location_value = ST_GeomFromText(point.replace("SRID=4326;", ""), 4326)
            except Exception:
                location_value = point

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
            "jurisdiction_code": jurisdiction_code,
            "location": location_value,
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
        jurisdiction_code: str,
    ) -> None:
        """Update existing property with latest information."""
        # Update fields that might have changed
        property_record.updated_at = utcnow()
        property_record.jurisdiction_code = jurisdiction_code

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
    ) -> None:
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
        heritage_overlay: Optional[Dict[str, Any]],
        jurisdiction_code: str = "SG",
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
                        heritage_overlay,
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
            elif scenario == DevelopmentScenario.MIXED_USE_REDEVELOPMENT:
                insights.append(
                    self._quick_mixed_use_analysis(
                        ura_zoning,
                        property_info,
                        existing_use,
                        nearby_amenities,
                        transactions,
                    )
                )

        return {
            "generated_at": utcnow().isoformat(),
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

        metrics = {
            "site_area_sqm": site_area,
            "plot_ratio": plot_ratio,
            "potential_gfa_sqm": potential_gfa,
            "nearby_development_count": development_count,
            "nearest_completion": nearest_completion,
        }
        return {
            "scenario": DevelopmentScenario.RAW_LAND.value,
            "headline": headline,
            "metrics": _add_accuracy_bands_to_metrics(metrics),
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

        metrics = {
            "approved_gfa_sqm": approved_gfa,
            "scenario_gfa_sqm": potential_gfa,
            "gfa_uplift_sqm": uplift,
            "recent_transaction_count": transaction_count,
            "average_psf_price": average_psf,
        }
        return {
            "scenario": DevelopmentScenario.EXISTING_BUILDING.value,
            "headline": headline,
            "metrics": _add_accuracy_bands_to_metrics(metrics),
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
        heritage_overlay: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        completion_year = (
            int(property_info.completion_year)
            if property_info and property_info.completion_year
            else None
        )
        heritage_risk = "medium"
        notes: List[str] = []

        if heritage_overlay:
            overlay_risk = str(heritage_overlay.get("risk", "medium")).lower()
            if overlay_risk in {"high", "medium", "low"}:
                heritage_risk = overlay_risk
            overlay_notes = heritage_overlay.get("notes") or []
            for note in overlay_notes:
                if note:
                    notes.append(str(note))

        if completion_year and completion_year < 1970 and heritage_risk != "high":
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

        metrics = {
            "completion_year": completion_year,
            "heritage_risk": heritage_risk,
        }
        return {
            "scenario": DevelopmentScenario.HERITAGE_PROPERTY.value,
            "headline": f"Heritage risk assessment: {heritage_risk.upper()}",
            "metrics": _add_accuracy_bands_to_metrics(metrics, asset_class="heritage"),
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

        metrics = {
            "nearby_mrt_count": amenity_summary,
            "current_use": existing_use,
            "building_height_m": building_height,
            "average_monthly_rent": average_rent,
            "rental_comparable_count": rental_count,
            "property_type": property_type.value,
        }
        return {
            "scenario": DevelopmentScenario.UNDERUSED_ASSET.value,
            "headline": "Review asset utilisation versus surrounding demand",
            "metrics": _add_accuracy_bands_to_metrics(metrics),
            "notes": notes,
        }

    def _quick_mixed_use_analysis(
        self,
        ura_zoning: Optional[Any],
        property_info: Optional[Any],
        existing_use: Optional[str],
        nearby_amenities: Optional[Dict[str, Any]],
        transactions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Analyze mixed-use redevelopment potential."""
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
        use_groups = getattr(ura_zoning, "use_groups", []) if ura_zoning else []

        notes = []
        potential_gfa = None

        if site_area and plot_ratio:
            potential_gfa = site_area * plot_ratio
            notes.append(
                f"Mixed-use GFA potential: {potential_gfa:,.0f} sqm across multiple uses"
            )

        # Check zoning flexibility for mixed-use
        if len(use_groups) >= 2:
            notes.append(
                f"Zoning permits {len(use_groups)} use groups — ideal for mixed-use"
            )
            headline = (
                f"Mixed-use opportunity with {len(use_groups)}-use zoning flexibility"
            )
        elif len(use_groups) == 1:
            notes.append(
                "Single-use zoning may limit mixed-use potential — check URA for amendments"
            )
            headline = "Single-use zoning limits mixed-use flexibility"
        else:
            headline = "Zoning data unavailable — verify mixed-use feasibility with URA"

        # Assess location suitability
        amenity_count = 0
        if nearby_amenities:
            amenity_count = len(nearby_amenities.get("mrt_stations", [])) + len(
                nearby_amenities.get("shopping_malls", [])
            )

        if amenity_count >= 3:
            notes.append(
                "Strong amenity infrastructure supports residential + retail + office mix"
            )
        elif amenity_count > 0:
            notes.append(
                "Moderate amenity access — consider residential + single commercial use"
            )

        # Market activity indicator
        recent_transactions = len(
            [
                t
                for t in transactions
                if (txn_date := t.get("transaction_date"))
                and isinstance(txn_date, str)
                and txn_date >= "2020-01-01"
            ]
        )

        if recent_transactions >= 5:
            notes.append(
                f"{recent_transactions} recent transactions signal active market"
            )

        metrics = {
            "site_area_sqm": site_area,
            "plot_ratio": plot_ratio,
            "potential_gfa_sqm": potential_gfa,
            "permitted_use_groups": len(use_groups),
            "nearby_amenities_count": amenity_count,
            "recent_transactions": recent_transactions,
            "existing_use": existing_use,
        }
        return {
            "scenario": DevelopmentScenario.MIXED_USE_REDEVELOPMENT.value,
            "headline": headline,
            "metrics": _add_accuracy_bands_to_metrics(metrics, asset_class="mixed_use"),
            "notes": notes,
        }
