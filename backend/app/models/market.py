"""Market data models for yield benchmarking and absorption tracking."""

from decimal import Decimal
from datetime import datetime, date
from typing import Optional
from uuid import UUID
from enum import Enum

from sqlalchemy import (
    Column, String, Decimal as SQLDecimal, Integer, Float, Boolean,
    DateTime, Date, ForeignKey, JSON, Enum as SQLEnum, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from geoalchemy2 import Geometry

from backend.app.models.base import Base, TimestampMixin
from backend.app.models.property import PropertyType


class YieldBenchmark(Base, TimestampMixin):
    """Market yield benchmarks by property type and location."""
    __tablename__ = "yield_benchmarks"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    
    # Benchmark Period
    benchmark_date = Column(Date, nullable=False)
    period_type = Column(String(20))  # monthly, quarterly, yearly
    
    # Location
    country = Column(String(50), default="Singapore")
    district = Column(String(100))
    subzone = Column(String(100))
    location_tier = Column(String(20))  # prime, secondary, suburban
    
    # Property Classification
    property_type = Column(SQLEnum(PropertyType), nullable=False)
    property_grade = Column(String(20))  # A, B, C grade buildings
    
    # Cap Rate Metrics
    cap_rate_mean = Column(SQLDecimal(5, 3))
    cap_rate_median = Column(SQLDecimal(5, 3))
    cap_rate_p25 = Column(SQLDecimal(5, 3))  # 25th percentile
    cap_rate_p75 = Column(SQLDecimal(5, 3))  # 75th percentile
    cap_rate_min = Column(SQLDecimal(5, 3))
    cap_rate_max = Column(SQLDecimal(5, 3))
    
    # Rental Yield Metrics
    rental_yield_mean = Column(SQLDecimal(5, 3))
    rental_yield_median = Column(SQLDecimal(5, 3))
    rental_yield_p25 = Column(SQLDecimal(5, 3))
    rental_yield_p75 = Column(SQLDecimal(5, 3))
    
    # Rental Rate Metrics (PSF/month)
    rental_psf_mean = Column(SQLDecimal(8, 2))
    rental_psf_median = Column(SQLDecimal(8, 2))
    rental_psf_p25 = Column(SQLDecimal(8, 2))
    rental_psf_p75 = Column(SQLDecimal(8, 2))
    
    # Occupancy Metrics
    occupancy_rate_mean = Column(SQLDecimal(5, 2))
    vacancy_rate_mean = Column(SQLDecimal(5, 2))
    
    # Sale Price Metrics (PSF)
    sale_psf_mean = Column(SQLDecimal(10, 2))
    sale_psf_median = Column(SQLDecimal(10, 2))
    sale_psf_p25 = Column(SQLDecimal(10, 2))
    sale_psf_p75 = Column(SQLDecimal(10, 2))
    
    # Transaction Volume
    transaction_count = Column(Integer)
    total_transaction_value = Column(SQLDecimal(15, 2))
    
    # Data Quality
    sample_size = Column(Integer)
    data_quality_score = Column(SQLDecimal(3, 2))  # 0-1
    data_sources = Column(JSON)  # List of sources used
    
    __table_args__ = (
        UniqueConstraint('benchmark_date', 'property_type', 'district', name='uq_benchmark_date_type_location'),
        Index('idx_benchmark_date', 'benchmark_date'),
        Index('idx_benchmark_location', 'district', 'subzone'),
    )


class AbsorptionTracking(Base, TimestampMixin):
    """Track absorption rates for developments."""
    __tablename__ = "absorption_tracking"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    
    # Reference
    project_id = Column(PGUUID(as_uuid=True))  # Can reference properties or development_pipeline
    project_name = Column(String(255))
    tracking_date = Column(Date, nullable=False)
    
    # Location
    district = Column(String(100))
    property_type = Column(SQLEnum(PropertyType), nullable=False)
    
    # Sales Absorption (for new developments)
    total_units = Column(Integer)
    units_launched = Column(Integer)
    units_sold_cumulative = Column(Integer)
    units_sold_period = Column(Integer)  # This period only
    sales_absorption_rate = Column(SQLDecimal(5, 2))  # Percentage
    
    # Time Metrics
    months_since_launch = Column(Integer)
    avg_units_per_month = Column(SQLDecimal(8, 2))
    projected_sellout_months = Column(Integer)
    
    # Price Performance
    launch_price_psf = Column(SQLDecimal(10, 2))
    current_price_psf = Column(SQLDecimal(10, 2))
    price_change_percentage = Column(SQLDecimal(5, 2))
    
    # Leasing Absorption (for commercial)
    total_nla_sqm = Column(SQLDecimal(10, 2))
    nla_leased_cumulative = Column(SQLDecimal(10, 2))
    nla_leased_period = Column(SQLDecimal(10, 2))
    leasing_absorption_rate = Column(SQLDecimal(5, 2))  # Percentage
    
    # Market Context
    competing_supply_units = Column(Integer)
    competing_projects_count = Column(Integer)
    market_absorption_rate = Column(SQLDecimal(5, 2))  # Market average
    relative_performance = Column(SQLDecimal(5, 2))  # vs market
    
    # Velocity Metrics
    avg_days_to_sale = Column(Integer)
    avg_days_to_lease = Column(Integer)
    velocity_trend = Column(String(20))  # accelerating, stable, decelerating
    
    __table_args__ = (
        Index('idx_absorption_project_date', 'project_id', 'tracking_date'),
        Index('idx_absorption_type_date', 'property_type', 'tracking_date'),
    )


class MarketCycle(Base, TimestampMixin):
    """Track market cycles and phases."""
    __tablename__ = "market_cycles"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    
    # Period
    cycle_date = Column(Date, nullable=False)
    property_type = Column(SQLEnum(PropertyType), nullable=False)
    market_segment = Column(String(50))  # CBD, suburban, industrial zones
    
    # Cycle Phase
    cycle_phase = Column(String(50))  # recovery, expansion, hyper_supply, recession
    phase_duration_months = Column(Integer)
    phase_strength = Column(SQLDecimal(3, 2))  # 0-1 indicator strength
    
    # Leading Indicators
    price_momentum = Column(SQLDecimal(5, 2))  # YoY %
    rental_momentum = Column(SQLDecimal(5, 2))  # YoY %
    transaction_volume_change = Column(SQLDecimal(5, 2))  # YoY %
    
    # Supply/Demand Balance
    new_supply_sqm = Column(SQLDecimal(12, 2))
    net_absorption_sqm = Column(SQLDecimal(12, 2))
    supply_demand_ratio = Column(SQLDecimal(5, 2))
    
    # Forward Looking
    pipeline_supply_12m = Column(SQLDecimal(12, 2))
    expected_demand_12m = Column(SQLDecimal(12, 2))
    cycle_outlook = Column(String(20))  # improving, stable, deteriorating
    
    # Confidence
    model_confidence = Column(SQLDecimal(3, 2))  # 0-1
    
    __table_args__ = (
        UniqueConstraint('cycle_date', 'property_type', 'market_segment', name='uq_cycle_date_type_segment'),
        Index('idx_cycle_date', 'cycle_date'),
    )


class MarketIndex(Base, TimestampMixin):
    """Property market indices tracking."""
    __tablename__ = "market_indices"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    
    # Index Details
    index_date = Column(Date, nullable=False)
    index_name = Column(String(100), nullable=False)  # e.g., "PPI_Office", "RRI_Retail"
    property_type = Column(SQLEnum(PropertyType))
    
    # Index Values
    index_value = Column(SQLDecimal(10, 2), nullable=False)
    base_value = Column(SQLDecimal(10, 2), default=100)  # Base period = 100
    
    # Changes
    mom_change = Column(SQLDecimal(5, 2))  # Month-on-month %
    qoq_change = Column(SQLDecimal(5, 2))  # Quarter-on-quarter %
    yoy_change = Column(SQLDecimal(5, 2))  # Year-on-year %
    
    # Components (if composite index)
    component_values = Column(JSON)
    
    # Source
    data_source = Column(String(50))
    
    __table_args__ = (
        UniqueConstraint('index_date', 'index_name', name='uq_index_date_name'),
        Index('idx_index_date', 'index_date'),
        Index('idx_index_name', 'index_name'),
    )


class CompetitiveSet(Base, TimestampMixin):
    """Define competitive sets for benchmarking."""
    __tablename__ = "competitive_sets"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    
    # Set Definition
    set_name = Column(String(255), nullable=False)
    primary_property_id = Column(PGUUID(as_uuid=True))
    
    # Criteria
    property_type = Column(SQLEnum(PropertyType), nullable=False)
    location_bounds = Column(Geometry('POLYGON', srid=4326))
    radius_km = Column(SQLDecimal(5, 2))
    
    # Filters
    min_gfa_sqm = Column(SQLDecimal(10, 2))
    max_gfa_sqm = Column(SQLDecimal(10, 2))
    property_grades = Column(JSON)  # List of grades to include
    age_range_years = Column(JSON)  # {min: 0, max: 10}
    
    # Members
    competitor_property_ids = Column(JSON)  # List of property IDs
    
    # Metrics
    avg_rental_psf = Column(SQLDecimal(8, 2))
    avg_occupancy_rate = Column(SQLDecimal(5, 2))
    avg_cap_rate = Column(SQLDecimal(5, 3))
    
    # Usage
    is_active = Column(Boolean, default=True)
    last_refreshed = Column(DateTime)
    
    __table_args__ = (
        Index('idx_compset_primary', 'primary_property_id'),
        Index('idx_compset_active', 'is_active'),
    )


class MarketAlert(Base, TimestampMixin):
    """Market intelligence alerts and triggers."""
    __tablename__ = "market_alerts"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    
    # Alert Configuration
    alert_type = Column(String(50), nullable=False)  # price_change, new_supply, absorption_spike
    property_type = Column(SQLEnum(PropertyType))
    location = Column(String(255))
    
    # Trigger Conditions
    metric_name = Column(String(100))
    threshold_value = Column(SQLDecimal(10, 2))
    threshold_direction = Column(String(20))  # above, below, change_percentage
    
    # Alert Details
    triggered_at = Column(DateTime)
    triggered_value = Column(SQLDecimal(10, 2))
    alert_message = Column(String(1000))
    severity = Column(String(20))  # low, medium, high, critical
    
    # Context
    market_context = Column(JSON)  # Additional market data at trigger time
    affected_properties = Column(JSON)  # List of affected property IDs
    
    # Status
    is_active = Column(Boolean, default=True)
    acknowledged_at = Column(DateTime)
    acknowledged_by = Column(PGUUID(as_uuid=True))  # User ID
    
    __table_args__ = (
        Index('idx_alert_active', 'is_active'),
        Index('idx_alert_triggered', 'triggered_at'),
    )