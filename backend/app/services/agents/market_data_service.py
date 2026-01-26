"""Market Data Service for managing and syncing property market data."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

import structlog
from backend._compat.datetime import utcnow

from app.models.market import AbsorptionTracking, MarketIndex
from app.models.property import MarketTransaction, Property, PropertyType, RentalListing
from sqlalchemy import insert, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class MarketDataProvider(ABC):
    """Abstract base class for market data providers."""

    @abstractmethod
    async def fetch_transactions(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch transaction data."""
        pass

    @abstractmethod
    async def fetch_rental_data(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch rental listing data."""
        pass

    @abstractmethod
    async def fetch_market_indices(
        self, params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Fetch market index data."""
        pass


class MockMarketDataProvider(MarketDataProvider):
    """Mock provider for tests and local development."""

    async def fetch_transactions(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        count = int(params.get("count", 10))
        property_type = str(params.get("property_type", "office"))
        today = date.today()
        transactions: List[Dict[str, Any]] = []
        for idx in range(count):
            transactions.append(
                {
                    "transaction_id": f"mock-txn-{idx + 1}",
                    "transaction_date": (today - timedelta(days=idx)).isoformat(),
                    "transaction_type": "sale",
                    "sale_price": str(1_000_000 + (idx * 10_000)),
                    "psf_price": str(2000 + idx),
                    "floor_area_sqm": str(500 + idx),
                    "buyer_type": "Company",
                    "property_name": f"Mock {property_type.title()} {idx + 1}",
                    "property_type": property_type,
                    "district": "D01",
                }
            )
        return transactions

    async def fetch_rental_data(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        count = int(params.get("count", 10))
        property_type = str(params.get("property_type", "office"))
        today = date.today()
        rentals: List[Dict[str, Any]] = []
        for idx in range(count):
            rentals.append(
                {
                    "listing_id": f"mock-rental-{idx + 1}",
                    "listing_date": (today - timedelta(days=idx)).isoformat(),
                    "property_type": property_type,
                    "floor_area_sqm": str(600 + idx),
                    "asking_rent_monthly": str(10000 + (idx * 250)),
                    "asking_psf_monthly": str(6 + (idx * 0.1)),
                    "floor_level": str(5 + idx),
                    "available_date": (today + timedelta(days=30)).isoformat(),
                }
            )
        return rentals

    async def fetch_market_indices(
        self, params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        today = date.today()
        indices: List[Dict[str, Any]] = []
        for idx in range(12):
            month_date = today - timedelta(days=30 * idx)
            indices.append(
                {
                    "index_date": month_date.isoformat(),
                    "index_name": f"Mock_Property_Index_{month_date.strftime('%Y_%m')}",
                    "index_value": str(100 + idx),
                    "mom_change": str(0.5),
                    "yoy_change": str(2.0),
                }
            )
        return indices


class MarketDataService:
    """Service for managing market data synchronization and storage."""

    def __init__(self) -> None:
        self.providers: Dict[str, MarketDataProvider] = {
            "mock": MockMarketDataProvider()
        }
        self.sync_history: Dict[str, datetime] = {}
        from app.services.geocoding import GeocodingService

        self.geocoding = GeocodingService()

    def register_provider(self, name: str, provider: MarketDataProvider) -> None:
        """Register a data provider."""
        self.providers[name] = provider
        logger.info(f"Registered market data provider: {name}")

    async def sync_all_providers(
        self, session: AsyncSession, property_types: Optional[List[PropertyType]] = None
    ) -> Dict[str, Any]:
        """Sync data from all registered providers."""
        if not self.providers:
            logger.warning("No market data providers configured")
            return {}

        results = {}

        for provider_name, provider in self.providers.items():
            try:
                result = await self.sync_provider(
                    provider_name, provider, session, property_types
                )
                results[provider_name] = result
            except Exception as e:
                logger.error(f"Error syncing {provider_name}: {str(e)}")
                results[provider_name] = {"status": "error", "error": str(e)}

        return results

    async def sync_provider(
        self,
        provider_name: str,
        provider: MarketDataProvider,
        session: AsyncSession,
        property_types: Optional[List[PropertyType]] = None,
    ) -> Dict[str, Any]:
        """Sync data from a specific provider."""
        sync_start = utcnow()

        if not property_types:
            property_types = list(PropertyType)

        sync_results: Dict[str, Any] = {
            "transactions": 0,
            "rentals": 0,
            "indices": 0,
            "errors": [],
        }

        for prop_type in property_types:
            try:
                # Sync transactions
                transactions = await provider.fetch_transactions(
                    {
                        "property_type": prop_type.value,
                        "since": self._get_last_sync_date(provider_name),
                    }
                )

                stored = await self._store_transactions(
                    transactions, provider_name, session
                )
                sync_results["transactions"] = (
                    int(sync_results["transactions"]) + stored
                )

                # Sync rentals
                rentals = await provider.fetch_rental_data(
                    {
                        "property_type": prop_type.value,
                        "since": self._get_last_sync_date(provider_name),
                    }
                )

                stored = await self._store_rentals(rentals, provider_name, session)
                sync_results["rentals"] = int(sync_results["rentals"]) + stored

            except Exception as e:
                logger.error(f"Error syncing {prop_type.value}: {str(e)}")
                errors_list: List[str] = sync_results["errors"]
                errors_list.append(f"{prop_type.value}: {str(e)}")

        # Sync market indices
        try:
            indices = await provider.fetch_market_indices({})
            stored = await self._store_indices(indices, provider_name, session)
            sync_results["indices"] = stored
        except Exception as e:
            logger.error(f"Error syncing indices: {str(e)}")
            indices_errors_list: List[str] = sync_results["errors"]
            indices_errors_list.append(f"indices: {str(e)}")

        # Update sync history
        self.sync_history[provider_name] = sync_start

        # Calculate benchmarks after sync
        await self._calculate_yield_benchmarks(session)

        # Update absorption metrics
        await self._update_absorption_metrics(session)

        await session.commit()

        return {
            "status": "success",
            "provider": provider_name,
            "sync_time": sync_start.isoformat(),
            "results": sync_results,
        }

    async def _store_transactions(
        self, transactions: List[Dict[str, Any]], source: str, session: AsyncSession
    ) -> int:
        """Store transaction data in database."""
        stored = 0

        for txn_data in transactions:
            try:
                # Find or create property
                property_id = await self._get_or_create_property(txn_data, session)

                # Prepare transaction record
                transaction = {
                    "property_id": property_id,
                    "transaction_date": datetime.fromisoformat(
                        txn_data["transaction_date"]
                    ).date(),
                    "transaction_type": txn_data.get("transaction_type", "sale"),
                    "sale_price": Decimal(str(txn_data["sale_price"])),
                    "psf_price": Decimal(str(txn_data.get("psf_price", 0))),
                    "buyer_type": txn_data.get("buyer_type"),
                    "floor_area_sqm": Decimal(str(txn_data.get("floor_area_sqm", 0))),
                    "data_source": source,
                }

                # Upsert transaction
                stmt = pg_insert(MarketTransaction).values(**transaction)
                stmt = stmt.on_conflict_do_nothing()

                await session.execute(stmt)
                stored += 1

            except Exception as e:
                logger.error(f"Error storing transaction: {str(e)}")

        return stored

    async def _store_rentals(
        self, rentals: List[Dict[str, Any]], source: str, session: AsyncSession
    ) -> int:
        """Store rental listing data."""
        stored = 0

        for rental_data in rentals:
            try:
                # Find or create property
                property_id = await self._get_or_create_property(rental_data, session)

                # Prepare rental record
                rental = {
                    "property_id": property_id,
                    "listing_date": datetime.fromisoformat(
                        rental_data["listing_date"]
                    ).date(),
                    "listing_type": rental_data.get("listing_type", "unit"),
                    "is_active": rental_data.get("is_active", True),
                    "floor_area_sqm": Decimal(str(rental_data["floor_area_sqm"])),
                    "asking_rent_monthly": Decimal(
                        str(rental_data.get("asking_rent_monthly", 0))
                    ),
                    "asking_psf_monthly": Decimal(
                        str(rental_data.get("asking_psf_monthly", 0))
                    ),
                    "floor_level": rental_data.get("floor_level"),
                    "available_date": (
                        datetime.fromisoformat(rental_data["available_date"]).date()
                        if rental_data.get("available_date")
                        else None
                    ),
                    "listing_source": source,
                }

                # Upsert rental
                stmt = pg_insert(RentalListing).values(**rental)
                stmt = stmt.on_conflict_do_nothing()

                await session.execute(stmt)
                stored += 1

            except Exception as e:
                logger.error(f"Error storing rental: {str(e)}")

        return stored

    async def _store_indices(
        self, indices: List[Dict[str, Any]], source: str, session: AsyncSession
    ) -> int:
        """Store market index data."""
        stored = 0

        for index_data in indices:
            try:
                index_record = {
                    "index_date": datetime.fromisoformat(
                        index_data["index_date"]
                    ).date(),
                    "index_name": index_data["index_name"],
                    "index_value": Decimal(str(index_data["index_value"])),
                    "mom_change": Decimal(str(index_data.get("mom_change", 0))),
                    "yoy_change": Decimal(str(index_data.get("yoy_change", 0))),
                    "data_source": source,
                }

                stmt = pg_insert(MarketIndex).values(**index_record)
                stmt = stmt.on_conflict_do_update(
                    index_elements=["index_date", "index_name"],
                    set_={"index_value": index_record["index_value"]},
                )

                await session.execute(stmt)
                stored += 1

            except Exception as e:
                logger.error(f"Error storing index: {str(e)}")

        return stored

    async def _get_or_create_property(
        self, data: Dict[str, Any], session: AsyncSession
    ) -> str:
        """Get existing property or create new one."""
        # Try to find existing property by name
        property_name = (
            data.get("property_name") or data.get("name") or data.get("address")
        )
        if not property_name:
            raise ValueError("Property name or address is required")

        stmt = select(Property).where(Property.name == property_name).limit(1)

        result = await session.execute(stmt)
        property_record = result.scalar_one_or_none()

        if property_record:
            return str(property_record.id)

        # Create new property
        from uuid import uuid4

        from geoalchemy2.elements import WKTElement

        property_id = uuid4()

        raw_lat = data.get("latitude") or data.get("lat")
        raw_lon = data.get("longitude") or data.get("lon") or data.get("lng")

        if raw_lat is None or raw_lon is None:
            address = data.get("address") or property_name
            if not address:
                raise ValueError("Address is required to geocode property location")
            coords = await self.geocoding.geocode(str(address))
            if not coords:
                raise ValueError("Unable to geocode property location")
            lat, lon = coords
        else:
            lat = float(raw_lat)
            lon = float(raw_lon)

        point = WKTElement(f"POINT({lon} {lat})", srid=4326)

        property_type_map = {
            "office": PropertyType.OFFICE,
            "retail": PropertyType.RETAIL,
            "residential": PropertyType.RESIDENTIAL,
            "industrial": PropertyType.INDUSTRIAL,
        }

        raw_property_type = data.get("property_type")
        if not raw_property_type:
            raise ValueError("property_type is required to create a property")

        property_type_value = str(raw_property_type).lower()
        property_type = property_type_map.get(property_type_value)
        if property_type is None:
            try:
                property_type = PropertyType(property_type_value)
            except ValueError as exc:
                raise ValueError(
                    f"Unknown property_type '{raw_property_type}'"
                ) from exc

        new_property = {
            "id": property_id,
            "name": property_name,
            "address": data.get("address", property_name),
            "property_type": property_type,
            "location": point,
            "district": data.get("district"),
            "gross_floor_area_sqm": (
                Decimal(str(data.get("floor_area_sqm", 0)))
                if data.get("floor_area_sqm")
                else None
            ),
            "data_source": "market_sync",
        }

        stmt = insert(Property).values(**new_property)
        await session.execute(stmt)

        return str(property_id)

    async def _calculate_yield_benchmarks(self, session: AsyncSession) -> None:
        """Calculate and update yield benchmarks."""
        # This is a simplified version - in production, implement full calculation

        # Get recent transactions grouped by property type and district
        cutoff_date = date.today() - timedelta(days=30)

        stmt = """
        INSERT INTO yield_benchmarks (
            benchmark_date, property_type, district,
            cap_rate_median, rental_psf_median, transaction_count,
            total_transaction_value, data_quality_score
        )
        SELECT
            CURRENT_DATE as benchmark_date,
            p.property_type,
            p.district,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY mt.psf_price * 0.05) as cap_rate_median,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rl.asking_psf_monthly) as rental_psf_median,
            COUNT(DISTINCT mt.id) as transaction_count,
            SUM(mt.sale_price) as total_transaction_value,
            0.8 as data_quality_score
        FROM properties p
        LEFT JOIN market_transactions mt ON mt.property_id = p.id
            AND mt.transaction_date >= :cutoff_date
        LEFT JOIN rental_listings rl ON rl.property_id = p.id
            AND rl.is_active = true
        WHERE p.district IS NOT NULL
        GROUP BY p.property_type, p.district
        ON CONFLICT (benchmark_date, property_type, district)
        DO UPDATE SET
            cap_rate_median = EXCLUDED.cap_rate_median,
            rental_psf_median = EXCLUDED.rental_psf_median,
            transaction_count = EXCLUDED.transaction_count
        """

        # Execute raw SQL for efficiency
        await session.execute(stmt, {"cutoff_date": cutoff_date})

    async def _update_absorption_metrics(self, session: AsyncSession) -> None:
        """Update absorption tracking metrics."""
        # Simplified - in production, track actual project absorption

        from app.models.property import DevelopmentPipeline

        # Get active development projects
        stmt = select(DevelopmentPipeline).where(
            DevelopmentPipeline.development_status.in_(
                ["under_construction", "launched"]
            )
        )

        result = await session.execute(stmt)
        projects = result.scalars().all()

        for project in projects:
            if project.total_units and project.units_sold is not None:
                absorption_rate = (project.units_sold / project.total_units) * 100

                tracking = {
                    "project_id": project.id,
                    "project_name": project.project_name,
                    "tracking_date": date.today(),
                    "property_type": project.project_type,
                    "district": project.district,
                    "total_units": project.total_units,
                    "units_sold_cumulative": project.units_sold,
                    "sales_absorption_rate": Decimal(str(absorption_rate)),
                }

                stmt = pg_insert(AbsorptionTracking).values(**tracking)
                stmt = stmt.on_conflict_do_update(
                    index_elements=["project_id", "tracking_date"],
                    set_={"sales_absorption_rate": tracking["sales_absorption_rate"]},
                )

                await session.execute(stmt)

    def _get_last_sync_date(self, provider_name: str) -> Optional[date]:
        """Get last sync date for provider."""
        if provider_name in self.sync_history:
            return self.sync_history[provider_name].date()
        return None

    async def get_transactions(
        self,
        property_type: PropertyType,
        location: Optional[str],
        period: Tuple[date, date],
        session: AsyncSession,
    ) -> List[MarketTransaction]:
        """Get transactions from database."""
        stmt = select(MarketTransaction).where(
            MarketTransaction.transaction_date.between(period[0], period[1])
        )

        # Join with property for filtering
        stmt = stmt.join(MarketTransaction.property)

        if property_type:
            stmt = stmt.where(Property.property_type == property_type)

        if location:
            stmt = stmt.where(Property.district == location)

        stmt = stmt.order_by(MarketTransaction.transaction_date.desc())

        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_rental_data(
        self,
        property_type: PropertyType,
        location: Optional[str],
        session: AsyncSession,
        active_only: bool = True,
    ) -> List[RentalListing]:
        """Get rental listings from database."""
        stmt = select(RentalListing)

        if active_only:
            stmt = stmt.where(RentalListing.is_active)

        # Join with property for filtering
        stmt = stmt.join(RentalListing.property)

        if property_type:
            stmt = stmt.where(Property.property_type == property_type)

        if location:
            stmt = stmt.where(Property.district == location)

        stmt = stmt.order_by(RentalListing.listing_date.desc())

        result = await session.execute(stmt)
        return list(result.scalars().all())
