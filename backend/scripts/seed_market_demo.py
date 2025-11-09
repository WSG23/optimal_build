"""Seed market intelligence demo data for analytics and agent flows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Sequence
from uuid import UUID, uuid4

from app.models.market import (
    AbsorptionTracking,
    MarketCycle,
    MarketIndex,
    PropertyType,
    YieldBenchmark,
)
from app.models.property import (
    MarketTransaction,
    Property,
    PropertyStatus,
    RentalListing,
    TenureType,
)
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

_DEMO_TAG = "market_demo"


@dataclass
class MarketDemoSummary:
    """Summary information about seeded market intelligence records."""

    property_id: UUID
    transactions: int
    rental_listings: int
    yield_benchmarks: int
    absorption_rows: int
    market_cycles: int
    market_indices: int


async def _purge_existing(session: AsyncSession) -> None:
    """Remove previously-seeded demo records."""

    await session.execute(
        delete(MarketTransaction).where(MarketTransaction.data_source == _DEMO_TAG)
    )
    await session.execute(
        delete(RentalListing).where(RentalListing.listing_source == _DEMO_TAG)
    )
    await session.execute(
        delete(YieldBenchmark).where(
            YieldBenchmark.district == "D01",
            YieldBenchmark.property_type == PropertyType.OFFICE,
            YieldBenchmark.period_type == "monthly",
        )
    )
    await session.execute(
        delete(AbsorptionTracking).where(
            AbsorptionTracking.project_name.ilike("Market Demo%")
        )
    )
    await session.execute(
        delete(MarketCycle).where(MarketCycle.market_segment == "Market Demo")
    )
    await session.execute(
        delete(MarketIndex).where(MarketIndex.data_source == _DEMO_TAG)
    )
    await session.execute(delete(Property).where(Property.data_source == _DEMO_TAG))
    await session.commit()


async def seed_market_demo(
    session: AsyncSession,
    *,
    reset_existing: bool = True,
) -> MarketDemoSummary:
    """Seed representative market intelligence rows for demo usage."""

    if reset_existing:
        await _purge_existing(session)

    property_id = uuid4()
    property_record = Property(
        id=property_id,
        name="Market Demo Tower",
        address="1 Demo Way, Singapore",
        postal_code="049999",
        property_type=PropertyType.OFFICE,
        status=PropertyStatus.EXISTING,
        location="POINT(103.851959 1.290270)",
        district="D01",
        planning_area="Downtown Core",
        land_area_sqm=Decimal("4500"),
        gross_floor_area_sqm=Decimal("52000"),
        net_lettable_area_sqm=Decimal("48000"),
        building_height_m=Decimal("210"),
        floors_above_ground=45,
        units_total=25,
        year_built=2018,
        tenure_type=TenureType.LEASEHOLD_99,
        lease_start_date=date(2015, 7, 1),
        lease_expiry_date=date(2114, 6, 30),
        zoning_code="C1",
        plot_ratio=Decimal("11.5"),
        data_source=_DEMO_TAG,
    )
    session.add(property_record)

    transactions: Sequence[MarketTransaction] = (
        MarketTransaction(
            id=uuid4(),
            property_id=property_id,
            transaction_date=date.today() - timedelta(days=120),
            transaction_type="sale",
            sale_price=Decimal("165000000"),
            psf_price=Decimal("2950"),
            psm_price=Decimal("31750"),
            buyer_type="REIT",
            seller_type="Developer",
            buyer_profile={"origin": "Singapore"},
            unit_number="#25-01",
            floor_area_sqm=Decimal("2000"),
            floor_level=25,
            market_segment="CBD",
            financing_type="term_loan",
            data_source=_DEMO_TAG,
            confidence_score=Decimal("0.95"),
        ),
        MarketTransaction(
            id=uuid4(),
            property_id=property_id,
            transaction_date=date.today() - timedelta(days=400),
            transaction_type="sale",
            sale_price=Decimal("158000000"),
            psf_price=Decimal("2800"),
            psm_price=Decimal("30100"),
            buyer_type="Foreign",
            seller_type="REIT",
            buyer_profile={"origin": "Hong Kong"},
            unit_number="#18-01",
            floor_area_sqm=Decimal("2100"),
            floor_level=18,
            market_segment="CBD",
            financing_type="bond",
            data_source=_DEMO_TAG,
            confidence_score=Decimal("0.92"),
        ),
    )
    session.add_all(transactions)

    rental_listing = RentalListing(
        id=uuid4(),
        property_id=property_id,
        listing_date=date.today() - timedelta(days=30),
        listing_type="unit",
        is_active=True,
        floor_area_sqm=Decimal("1150"),
        floor_level="24",
        unit_number="24-03",
        asking_rent_monthly=Decimal("16500"),
        asking_psf_monthly=Decimal("12.8"),
        available_date=date.today() + timedelta(days=15),
        listing_source=_DEMO_TAG,
        agent_company="Demo Realty",
    )
    session.add(rental_listing)

    benchmark = YieldBenchmark(
        id=uuid4(),
        benchmark_date=date.today().replace(day=1),
        period_type="monthly",
        district="D01",
        property_type=PropertyType.OFFICE,
        property_grade="Premium",
        cap_rate_mean=Decimal("0.048"),
        cap_rate_median=Decimal("0.046"),
        rental_yield_mean=Decimal("0.052"),
        rental_yield_median=Decimal("0.051"),
        rental_psf_mean=Decimal("11.8"),
        rental_psf_median=Decimal("12.2"),
        occupancy_rate_mean=Decimal("0.94"),
        vacancy_rate_mean=Decimal("0.06"),
        sale_psf_mean=Decimal("2850"),
        sale_psf_median=Decimal("2900"),
        transaction_count=12,
        total_transaction_value=Decimal("190000000"),
        sample_size=12,
        data_quality_score=Decimal("0.9"),
        data_sources=[_DEMO_TAG],
    )
    session.add(benchmark)

    absorption = AbsorptionTracking(
        id=uuid4(),
        project_id=property_id,
        project_name="Market Demo Tower",
        tracking_date=date.today() - timedelta(days=30),
        district="D01",
        property_type=PropertyType.OFFICE,
        total_units=25,
        units_launched=25,
        units_sold_cumulative=23,
        units_sold_period=3,
        sales_absorption_rate=Decimal("0.92"),
        months_since_launch=36,
        avg_units_per_month=Decimal("0.7"),
        projected_sellout_months=6,
        launch_price_psf=Decimal("2500"),
        current_price_psf=Decimal("2900"),
        price_change_percentage=Decimal("0.16"),
        total_nla_sqm=Decimal("48000"),
        nla_leased_cumulative=Decimal("45200"),
        nla_leased_period=Decimal("1200"),
        leasing_absorption_rate=Decimal("0.94"),
        competing_projects_count=3,
        market_absorption_rate=Decimal("0.88"),
        relative_performance=Decimal("0.06"),
        avg_days_to_lease=45,
        velocity_trend="accelerating",
    )
    session.add(absorption)

    cycle = MarketCycle(
        id=uuid4(),
        cycle_date=date.today().replace(day=1),
        property_type=PropertyType.OFFICE,
        market_segment="Market Demo",
        cycle_phase="expansion",
        phase_duration_months=9,
        phase_strength=Decimal("0.7"),
        price_momentum=Decimal("0.04"),
        rental_momentum=Decimal("0.03"),
        transaction_volume_change=Decimal("0.05"),
        new_supply_sqm=Decimal("12000"),
        net_absorption_sqm=Decimal("15000"),
        supply_demand_ratio=Decimal("0.8"),
        pipeline_supply_12m=Decimal("18000"),
        expected_demand_12m=Decimal("20000"),
        cycle_outlook="improving",
        model_confidence=Decimal("0.8"),
    )
    session.add(cycle)

    indices = [
        MarketIndex(
            id=uuid4(),
            index_date=date.today() - timedelta(days=30 * idx),
            index_name="OFFICE_PPI",
            property_type=PropertyType.OFFICE,
            index_value=Decimal("100") + Decimal(idx) * Decimal("1.75"),
            base_value=Decimal("100"),
            mom_change=Decimal("1.2"),
            qoq_change=Decimal("2.5"),
            yoy_change=Decimal("5.1"),
            data_source=_DEMO_TAG,
        )
        for idx in range(0, 6)
    ]
    session.add_all(indices)

    await session.commit()

    return MarketDemoSummary(
        property_id=property_id,
        transactions=len(transactions),
        rental_listings=1,
        yield_benchmarks=1,
        absorption_rows=1,
        market_cycles=1,
        market_indices=len(indices),
    )


__all__ = ["MarketDemoSummary", "seed_market_demo"]
