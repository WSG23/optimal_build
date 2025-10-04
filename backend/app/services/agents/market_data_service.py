"""Market Data Service for managing and syncing property market data."""

from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

import structlog
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
    """Mock provider for testing and development."""

    async def fetch_transactions(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return mock transaction data."""
        import random

        property_type = params.get("property_type", "office")
        count = params.get("count", 10)

        transactions = []
        for i in range(count):
            transaction_date = date.today() - timedelta(days=random.randint(1, 180))

            transactions.append(
                {
                    "transaction_id": f"MOCK-{i}",
                    "property_name": f"Mock Building {i}",
                    "property_type": property_type,
                    "transaction_date": transaction_date.isoformat(),
                    "sale_price": random.randint(10000000, 100000000),
                    "floor_area_sqm": random.randint(500, 5000),
                    "psf_price": random.randint(1500, 3500),
                    "buyer_type": random.choice(
                        ["Individual", "Company", "REIT", "Foreign"]
                    ),
                    "district": f"D{random.randint(1, 28):02d}",
                    "tenure": random.choice(["Freehold", "99-year leasehold"]),
                }
            )

        return transactions

    async def fetch_rental_data(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return mock rental data."""
        import random

        property_type = params.get("property_type", "office")
        count = params.get("count", 10)

        rentals = []
        for i in range(count):
            listing_date = date.today() - timedelta(days=random.randint(1, 90))

            rentals.append(
                {
                    "listing_id": f"RENT-{i}",
                    "property_name": f"Mock Building {i}",
                    "property_type": property_type,
                    "listing_date": listing_date.isoformat(),
                    "floor_area_sqm": random.randint(100, 2000),
                    "asking_rent_monthly": random.randint(5000, 50000),
                    "asking_psf_monthly": random.uniform(3.0, 15.0),
                    "floor_level": f"{random.randint(1, 20)}",
                    "available_date": (listing_date + timedelta(days=30)).isoformat(),
                    "district": f"D{random.randint(1, 28):02d}",
                }
            )

        return rentals

    async def fetch_market_indices(
        self, params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Return mock market index data."""
        import random

        indices = []
        base_value = 100
        current_value = base_value

        for i in range(12):
            index_date = date.today() - timedelta(days=30 * i)

            # Random walk
            change = random.uniform(-5, 5)
            current_value = current_value * (1 + change / 100)

            indices.append(
                {
                    "index_date": index_date.isoformat(),
                    "index_name": "Mock_Property_Price_Index",
                    "index_value": current_value,
                    "mom_change": change,
                    "yoy_change": random.uniform(-10, 10),
                }
            )

        return indices


class MarketDataService:
    """Service for managing market data synchronization and storage."""

    def __init__(self):
        self.providers: Dict[str, MarketDataProvider] = {
            "mock": MockMarketDataProvider()
        }
        self.sync_history: Dict[str, datetime] = {}

    def register_provider(self, name: str, provider: MarketDataProvider):
        """Register a data provider."""
        self.providers[name] = provider
        logger.info(f"Registered market data provider: {name}")

    async def sync_all_providers(
        self, session: AsyncSession, property_types: Optional[List[PropertyType]] = None
    ) -> Dict[str, Any]:
        """Sync data from all registered providers."""
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
        sync_start = datetime.utcnow()

        if not property_types:
            property_types = list(PropertyType)

        sync_results = {"transactions": 0, "rentals": 0, "indices": 0, "errors": []}

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
                sync_results["transactions"] += stored

                # Sync rentals
                rentals = await provider.fetch_rental_data(
                    {
                        "property_type": prop_type.value,
                        "since": self._get_last_sync_date(provider_name),
                    }
                )

                stored = await self._store_rentals(rentals, provider_name, session)
                sync_results["rentals"] += stored

            except Exception as e:
                logger.error(f"Error syncing {prop_type.value}: {str(e)}")
                sync_results["errors"].append(f"{prop_type.value}: {str(e)}")

        # Sync market indices
        try:
            indices = await provider.fetch_market_indices({})
            stored = await self._store_indices(indices, provider_name, session)
            sync_results["indices"] = stored
        except Exception as e:
            logger.error(f"Error syncing indices: {str(e)}")
            sync_results["errors"].append(f"indices: {str(e)}")

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
        property_name = data.get("property_name", "Unknown Property")

        stmt = select(Property).where(Property.name == property_name).limit(1)

        result = await session.execute(stmt)
        property_record = result.scalar_one_or_none()

        if property_record:
            return str(property_record.id)

        # Create new property
        from uuid import uuid4

        from geoalchemy2.elements import WKTElement

        property_id = uuid4()

        # Create mock location (in production, geocode the address)
        import random

        lat = 1.3521 + random.uniform(-0.1, 0.1)  # Singapore latitude
        lon = 103.8198 + random.uniform(-0.1, 0.1)  # Singapore longitude
        point = WKTElement(f"POINT({lon} {lat})", srid=4326)

        property_type_map = {
            "office": PropertyType.OFFICE,
            "retail": PropertyType.RETAIL,
            "residential": PropertyType.RESIDENTIAL,
            "industrial": PropertyType.INDUSTRIAL,
        }

        new_property = {
            "id": property_id,
            "name": property_name,
            "address": data.get("address", property_name),
            "property_type": property_type_map.get(
                data.get("property_type", "office").lower(), PropertyType.OFFICE
            ),
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

    async def _calculate_yield_benchmarks(self, session: AsyncSession):
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

    async def _update_absorption_metrics(self, session: AsyncSession):
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
        return result.scalars().all()

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
            stmt = stmt.where(RentalListing.is_active == True)

        # Join with property for filtering
        stmt = stmt.join(RentalListing.property)

        if property_type:
            stmt = stmt.where(Property.property_type == property_type)

        if location:
            stmt = stmt.where(Property.district == location)

        stmt = stmt.order_by(RentalListing.listing_date.desc())

        result = await session.execute(stmt)
        return result.scalars().all()
