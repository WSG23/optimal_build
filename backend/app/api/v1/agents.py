"""API endpoints for Commercial Property Advisors agent features."""

from __future__ import annotations

import importlib.util
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Path, Query

from backend._compat.datetime import utcnow  # isort: skip (backend._compat ordering)
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.api.deps import Role, get_request_role, require_reviewer
from app.core.config import settings
from app.core.database import get_session
from app.core.jwt_auth import TokenData, get_optional_user
from app.models.property import Property, PropertyType
from app.services.agents.advisory import AgentAdvisoryService
from app.services.agents.gps_property_logger import (
    DevelopmentScenario,
    GPSPropertyLogger,
)
from app.services.agents.ura_integration import ura_service
from app.services.geocoding import Address, GeocodingService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

try:  # pragma: no cover - scenario builder has heavy optional deps
    from app.services.agents.scenario_builder_3d import (
        Quick3DScenarioBuilder,
        ScenarioType,
    )
except ModuleNotFoundError:  # pragma: no cover - provide fallback enum

    class ScenarioType(str, Enum):  # type: ignore[misc]
        NEW_BUILD = "new_build"
        RENOVATION = "renovation"
        MIXED_USE_CONVERSION = "mixed_use_conversion"
        VERTICAL_EXTENSION = "vertical_extension"
        PODIUM_TOWER = "podium_tower"
        PHASED_DEVELOPMENT = "phased"

    Quick3DScenarioBuilder = None  # type: ignore[assignment]
from app.services.agents.market_data_service import MarketDataService
from app.services.agents.market_intelligence_analytics import (
    MarketIntelligenceAnalytics,
)
from app.services.finance import (
    calculate_comprehensive_metrics,
    value_property_multiple_approaches,
)

try:  # pragma: no cover - optional dependency relies on reportlab
    from app.services.agents.universal_site_pack import UniversalSitePackGenerator
except ModuleNotFoundError:  # pragma: no cover
    UniversalSitePackGenerator = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency relies on reportlab
    from app.services.agents.investment_memorandum import InvestmentMemorandumGenerator
except ModuleNotFoundError:  # pragma: no cover
    InvestmentMemorandumGenerator = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency relies on reportlab
    from app.services.agents.marketing_materials import MarketingMaterialsGenerator
except ModuleNotFoundError:  # pragma: no cover
    MarketingMaterialsGenerator = None  # type: ignore[assignment]

router = APIRouter(
    prefix="/agents/commercial-property", tags=["Commercial Property Agent"]
)

logger = structlog.get_logger()

# Service instances
geocoding_service = GeocodingService()
gps_logger = GPSPropertyLogger(geocoding_service, ura_service)
market_data_service = MarketDataService()
market_analytics = MarketIntelligenceAnalytics(market_data_service)
advisory_service = AgentAdvisoryService()


def _dependency_available(module_name: str) -> bool:
    spec = importlib.util.find_spec(module_name)
    return spec is not None


def _agents_dependency_status() -> dict[str, object]:
    heavy_dependencies = {
        "numpy": _dependency_available("numpy"),
        "pandas": _dependency_available("pandas"),
        "trimesh": _dependency_available("trimesh"),
        "reportlab": _dependency_available("reportlab"),
        "PIL": _dependency_available("PIL"),
        "exifread": _dependency_available("exifread"),
        "minio": _dependency_available("minio"),
    }
    optional_features = {
        "three_d_builder": Quick3DScenarioBuilder is not None,
        "site_pack_generator": UniversalSitePackGenerator is not None,
        "investment_memorandum": InvestmentMemorandumGenerator is not None,
        "marketing_materials": MarketingMaterialsGenerator is not None,
    }
    ready = all(heavy_dependencies.values())
    return {
        "status": "ready" if ready else "degraded",
        "dependencies": heavy_dependencies,
        "optional_features": optional_features,
    }


# Request/Response Models


class GPSLogRequest(BaseModel):
    """Request model for GPS property logging."""

    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    development_scenarios: list[DevelopmentScenario] | None = Field(
        None,
        description=(
            "Optional list of development scenarios to analyse during capture. "
            "Defaults to the core commercial scenarios if omitted."
        ),
    )
    jurisdiction_code: str | None = Field(
        None,
        description=(
            "Jurisdiction code (e.g., 'SG', 'HK', 'NZ'). "
            "Defaults to 'SG' if omitted."
        ),
    )


class CoordinatePair(BaseModel):
    latitude: float
    longitude: float


class QuickAnalysisScenario(BaseModel):
    scenario: DevelopmentScenario
    headline: str
    metrics: Dict[str, Any]
    notes: list[str]


class QuickAnalysisEnvelope(BaseModel):
    generated_at: datetime
    scenarios: list[QuickAnalysisScenario]


class GPSLogResponse(BaseModel):
    property_id: UUID
    address: Address
    coordinates: CoordinatePair
    ura_zoning: Dict[str, Any]
    existing_use: str
    property_info: Optional[Dict[str, Any]]
    nearby_amenities: Optional[Dict[str, Any]]
    quick_analysis: QuickAnalysisEnvelope
    timestamp: datetime
    jurisdiction_code: str
    currency_symbol: str


@router.get("/health")
async def agents_health() -> dict[str, object]:
    """Expose agent router readiness for CI smoke tests."""

    return _agents_dependency_status()


class MarketIntelligenceResponse(BaseModel):
    property_id: UUID
    report: Dict[str, Any]


class AdvisoryAssetMixSegment(BaseModel):
    use: str
    allocation_pct: float
    target_gfa_sqm: float | None = None
    rationale: str


class AdvisoryAssetMix(BaseModel):
    property_id: UUID
    total_programmable_gfa_sqm: float | None = None
    mix_recommendations: list[AdvisoryAssetMixSegment]
    notes: list[str] = []


class AdvisoryMarketPositioning(BaseModel):
    market_tier: str
    pricing_guidance: Dict[str, Dict[str, float]]
    target_segments: list[Dict[str, Any]]
    messaging: list[str]


class AdvisoryTimelineMilestone(BaseModel):
    milestone: str
    month: int
    expected_absorption_pct: float


class AdvisoryAbsorptionForecast(BaseModel):
    expected_months_to_stabilize: int
    monthly_velocity_target: int
    confidence: str
    timeline: list[AdvisoryTimelineMilestone]


class AdvisoryFeedbackItem(BaseModel):
    id: UUID
    property_id: UUID
    submitted_by: Optional[str]
    channel: Optional[str]
    sentiment: str
    notes: str
    metadata: Dict[str, Any]
    created_at: datetime


class AdvisoryFeedbackRequest(BaseModel):
    sentiment: str = Field(..., description="positive, neutral, or negative sentiment.")
    notes: str = Field(
        ..., min_length=3, description="Qualitative feedback from agents."
    )
    channel: Optional[str] = Field(
        None, description="Communication channel (e.g., call, meeting, email)."
    )
    submitted_by: Optional[str] = Field(
        None,
        description="Optional identifier for the agent submitting feedback if not authenticated.",
    )
    metadata: Dict[str, Any] | None = Field(
        default=None,
        description="Optional structured metadata such as objections or follow-up actions.",
    )


class AdvisorySummaryResponse(BaseModel):
    asset_mix: AdvisoryAssetMix
    market_positioning: AdvisoryMarketPositioning
    absorption_forecast: AdvisoryAbsorptionForecast
    feedback: list[AdvisoryFeedbackItem]


class SalesVelocityBenchmarks(BaseModel):
    inventory_months: float | None
    velocity_p25: float | None
    velocity_median: float | None
    velocity_p75: float | None
    median_psf: float | None


class SalesVelocityForecast(BaseModel):
    velocity_units_per_month: float | None
    absorption_months: float | None
    confidence: float


class SalesVelocityRisk(BaseModel):
    label: str
    level: str


class SalesVelocityRequest(BaseModel):
    jurisdiction: str = Field(
        ..., description="Jurisdiction code, e.g. SG, NZ, TOR, SEA, HK."
    )
    asset_type: str = Field(
        ..., description="Asset type, e.g. residential, office, retail."
    )
    price_band: str | None = Field(
        default=None, description="Price band label (e.g. 1800-2200_psf)."
    )
    units_planned: int | None = Field(
        default=None, description="Total units planned for launch."
    )
    launch_window: str | None = Field(
        default=None, description="Planned launch window (e.g. 2025-Q2)."
    )
    inventory_months: float | None = Field(
        default=None, description="Optional override for months of inventory."
    )
    recent_absorption: float | None = Field(
        default=None, description="Optional override: recent absorption (units/month)."
    )
    benchmarks_override: dict[str, float] | None = Field(
        default=None,
        description="Optional overrides for benchmarks (velocityPctl25/Median/75, medianPsf).",
    )


class SalesVelocityResponse(BaseModel):
    forecast: SalesVelocityForecast
    benchmarks: SalesVelocityBenchmarks
    recommendations: list[str]
    risks: list[SalesVelocityRisk]
    context: dict[str, Any]


class PropertyAnalysisRequest(BaseModel):
    """Request model for property development analysis."""

    property_id: str
    analysis_type: str = Field(
        ..., pattern="^(raw_land|existing_building|historical_property)$"
    )
    save_results: bool = True


class ScenarioGenerationRequest(BaseModel):
    """Request model for 3D scenario generation."""

    property_id: str
    scenario_types: list[ScenarioType]


class MarketReportRequest(BaseModel):
    """Request model for market intelligence report."""

    property_type: PropertyType
    location: str = "all"
    period_months: int = Field(12, ge=1, le=36)
    competitive_set_id: str | None = None


class PhotoUploadResponse(BaseModel):
    """Response model for photo upload."""

    photo_id: str
    storage_key: str
    location: dict[str, float] | None = None
    capture_timestamp: datetime
    auto_tags: list[str]
    public_url: str


class VoiceNoteUploadRequest(BaseModel):
    """Request model for voice note upload metadata."""

    duration_seconds: float | None = Field(
        None, description="Duration of the recording in seconds"
    )
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    title: str | None = Field(None, max_length=255)
    tags: list[str] | None = None
    photo_id: str | None = Field(None, description="Optional associated photo ID")


class VoiceNoteResponse(BaseModel):
    """Response model for voice note."""

    voice_note_id: str
    property_id: str
    storage_key: str
    location: dict[str, float] | None = None
    capture_timestamp: datetime
    duration_seconds: float | None = None
    file_size: int
    title: str | None = None
    photo_id: str | None = None
    public_url: str


class VoiceNoteUpdateRequest(BaseModel):
    """Request model for updating voice note metadata."""

    title: str | None = Field(None, max_length=255)
    tags: list[str] | None = None
    transcript: str | None = None


class MarketSyncRequest(BaseModel):
    """Request model for market data sync."""

    providers: list[str] | None = None
    property_types: list[PropertyType] | None = None


class FinancialMetricsRequest(BaseModel):
    """Request model for financial metrics calculation."""

    property_value: float
    gross_rental_income: float
    operating_expenses: float
    loan_amount: float | None = None
    annual_debt_service: float | None = None
    initial_cash_investment: float | None = None
    vacancy_rate: float = 0.05
    other_income: float = 0


class PropertyValuationRequest(BaseModel):
    """Request model for property valuation."""

    noi: float
    market_cap_rate: float
    comparable_psf: float | None = None
    property_size_sqf: float | None = None
    replacement_cost_psf: float | None = None
    land_value: float | None = None
    depreciation_factor: float = 0.8


# API Endpoints


@router.post("/properties/log-gps", response_model=GPSLogResponse)
async def log_property_by_gps(
    request: GPSLogRequest,
    db: AsyncSession = Depends(get_session),
    role: Role = Depends(get_request_role),
    current_user: TokenData | None = Depends(get_optional_user),
) -> GPSLogResponse:
    """
    Log a property using GPS coordinates.

    This endpoint will:
    - Reverse geocode the coordinates to get address
    - Fetch URA zoning information
    - Determine existing use
    - Create or update property record
    - Return comprehensive property information
    """
    try:
        user_uuid: Optional[UUID] = None
        if current_user and current_user.user_id:
            try:
                user_uuid = UUID(current_user.user_id)
            except ValueError:
                logger.warning(
                    "gps_logger_invalid_user_id",
                    supplied_user_id=current_user.user_id,
                )

        result = await gps_logger.log_property_from_gps(
            latitude=request.latitude,
            longitude=request.longitude,
            session=db,
            user_id=user_uuid,
            scenarios=request.development_scenarios,
            jurisdiction_code=request.jurisdiction_code,
        )
        quick_analysis_payload = result.quick_analysis or {
            "generated_at": utcnow().isoformat(),
            "scenarios": [],
        }
        quick_analysis = QuickAnalysisEnvelope.model_validate(quick_analysis_payload)

        # Get jurisdiction config for currency info
        from app.services.jurisdictions import get_jurisdiction_config

        jurisdiction = get_jurisdiction_config(result.jurisdiction_code)

        return GPSLogResponse(
            property_id=result.property_id,
            address=result.address,
            coordinates=CoordinatePair(
                latitude=result.coordinates[0],
                longitude=result.coordinates[1],
            ),
            ura_zoning=result.ura_zoning,
            existing_use=result.existing_use,
            property_info=result.property_info,
            nearby_amenities=result.nearby_amenities,
            quick_analysis=quick_analysis,
            timestamp=result.timestamp,
            jurisdiction_code=jurisdiction.code,
            currency_symbol=jurisdiction.currency_symbol,
        )

    except Exception as exc:
        logger.warning(
            "gps_logger_failed",
            error=str(exc),
            latitude=request.latitude,
            longitude=request.longitude,
        )
        if not settings.OFFLINE_MODE:
            raise HTTPException(
                status_code=503,
                detail="GPS capture unavailable: geocoding failed",
            ) from exc

        fallback = _build_mock_gps_response(
            latitude=request.latitude,
            longitude=request.longitude,
            scenarios=request.development_scenarios,
            jurisdiction_code=request.jurisdiction_code,
        )
        return fallback


def _build_mock_gps_response(
    *,
    latitude: float,
    longitude: float,
    scenarios: Optional[list[DevelopmentScenario]],
    jurisdiction_code: str | None = None,
) -> GPSLogResponse:
    """Return a deterministic sample response when live services are unavailable."""

    from uuid import uuid4

    from app.services.jurisdictions import get_jurisdiction_config

    generated_at = utcnow()
    resolved_scenarios = scenarios or DevelopmentScenario.default_set()
    jurisdiction = get_jurisdiction_config(jurisdiction_code)

    quick_scenarios: list[QuickAnalysisScenario] = []
    for scenario in resolved_scenarios:
        if scenario == DevelopmentScenario.RAW_LAND:
            quick_scenarios.append(
                QuickAnalysisScenario(
                    scenario=scenario,
                    headline="Estimated max GFA ≈ 18,000 sqm using plot ratio 3.6",
                    metrics={
                        "site_area_sqm": 5000,
                        "plot_ratio": 3.6,
                        "potential_gfa_sqm": 18000,
                        "nearby_development_count": 3,
                        "nearest_completion": "2026",
                    },
                    notes=[
                        "Mixed-use zoning permits office and hospitality",
                        "3 upcoming projects detected within 2 km",
                    ],
                )
            )
        elif scenario == DevelopmentScenario.EXISTING_BUILDING:
            quick_scenarios.append(
                QuickAnalysisScenario(
                    scenario=scenario,
                    headline="Existing approvals within 12% of zoning limit",
                    metrics={
                        "approved_gfa_sqm": 15800,
                        "scenario_gfa_sqm": 18000,
                        "gfa_uplift_sqm": 2200,
                        "recent_transaction_count": 14,
                        "average_psf_price": 2480,
                    },
                    notes=["Consider light retrofit to unlock unused GFA"],
                )
            )
        elif scenario == DevelopmentScenario.HERITAGE_PROPERTY:
            quick_scenarios.append(
                QuickAnalysisScenario(
                    scenario=scenario,
                    headline="Heritage risk assessment: MEDIUM",
                    metrics={"completion_year": 1984, "heritage_risk": "medium"},
                    notes=[
                        "Check URA conservation portal for obligations",
                        "Nearby redevelopment pipeline may tighten regulators' scrutiny",
                    ],
                )
            )
        elif scenario == DevelopmentScenario.UNDERUSED_ASSET:
            quick_scenarios.append(
                QuickAnalysisScenario(
                    scenario=scenario,
                    headline="Under-utilised logistics hub with strong transit access",
                    metrics={
                        "nearby_mrt_count": 2,
                        "average_monthly_rent": 7.5,
                        "rental_comparable_count": 9,
                        "building_height_m": 18,
                    },
                    notes=[
                        "Strong transit presence supports repositioning",
                        "Explore vertical expansion subject to mixed-use guidelines",
                    ],
                )
            )

    quick_analysis = QuickAnalysisEnvelope(
        generated_at=generated_at,
        scenarios=quick_scenarios,
    )

    address = Address(
        full_address=f"Sample Address near ({latitude:.4f}, {longitude:.4f})",
        street_name="Harbourfront Ave",
        building_name="Sample Tower",
        block_number="88",
        postal_code="098633",
        district="D04 - Harbourfront",
        country="Singapore",
    )

    nearby_amenities = {
        "mrt_stations": [{"name": "HarbourFront MRT", "distance_m": 240}],
        "bus_stops": [{"name": "Telok Blangah Rd - Opp VivoCity", "distance_m": 110}],
        "schools": [{"name": "Radin Mas Primary", "distance_m": 620}],
        "shopping_malls": [{"name": "VivoCity", "distance_m": 150}],
        "parks": [{"name": "Mount Faber Park", "distance_m": 480}],
    }

    property_info = {
        "property_name": "Sample Tower",
        "tenure": "99-year leasehold",
        "site_area_sqm": 5050.0,
        "gfa_approved": 15800.0,
        "building_height": 58.0,
        "completion_year": 2012,
        "last_transaction_date": date(2022, 11, 4).isoformat(),
        "last_transaction_price": 168_000_000.0,
    }

    return GPSLogResponse(
        property_id=uuid4(),
        address=address,
        coordinates=CoordinatePair(latitude=latitude, longitude=longitude),
        ura_zoning={
            "zone_code": "MU",
            "zone_description": "Mixed Use",
            "plot_ratio": 3.6,
            "building_height_limit": 120.0,
            "site_coverage": 70.0,
            "use_groups": ["Commercial", "Residential", "Office"],
            "special_conditions": "Minimum 40% residential component",
        },
        existing_use="Mixed Development",
        property_info=property_info,
        nearby_amenities=nearby_amenities,
        quick_analysis=quick_analysis,
        timestamp=generated_at,
        jurisdiction_code=jurisdiction.code,
        currency_symbol=jurisdiction.currency_symbol,
    )


@router.get(
    "/properties/{property_id}/market-intelligence",
    response_model=MarketIntelligenceResponse,
)
async def get_property_market_intelligence(
    property_id: str,
    months: int = 12,
    db: AsyncSession = Depends(get_session),
    role: Role = Depends(get_request_role),
) -> MarketIntelligenceResponse:
    """Generate market intelligence snapshot for a captured property."""

    try:
        property_uuid = UUID(property_id)
    except ValueError as exc:  # pragma: no cover
        raise HTTPException(status_code=400, detail="Invalid property ID") from exc

    stmt = select(Property).where(Property.id == property_uuid)
    result = await db.execute(stmt)
    property_data = result.scalar_one_or_none()

    if not property_data:
        raise HTTPException(status_code=404, detail="Property not found")

    location = property_data.district or "all"
    property_type = property_data.property_type
    if isinstance(property_type, str):
        try:
            property_type = PropertyType(property_type)
        except ValueError:
            logger.warning(
                "unknown_property_type_string",
                property_id=str(property_uuid),
                value=property_type,
            )
            property_type = PropertyType.OFFICE

    try:
        report = await market_analytics.generate_market_report(
            property_type=property_type,
            location=location,
            period_months=months,
            session=db,
        )
        payload = report.to_dict()
    except Exception as exc:  # pragma: no cover - analytics layer may raise
        logger.warning(
            "market_intelligence_failed",
            error=str(exc),
            property_id=str(property_uuid),
            months=months,
        )
        raise HTTPException(
            status_code=503,
            detail="Market intelligence unavailable",
        ) from exc

    return MarketIntelligenceResponse(
        property_id=property_uuid,
        report=payload,
    )


def _convert_asset_mix(payload: dict[str, Any]) -> AdvisoryAssetMix:
    mix_payload = payload.copy()
    mix_payload["property_id"] = UUID(mix_payload["property_id"])
    mix_payload["mix_recommendations"] = [
        AdvisoryAssetMixSegment(**segment)
        for segment in mix_payload.get("mix_recommendations", [])
    ]
    return AdvisoryAssetMix(**mix_payload)


def _convert_feedback_items(items: list[dict[str, Any]]) -> list[AdvisoryFeedbackItem]:
    converted: list[AdvisoryFeedbackItem] = []
    for item in items:
        # Handle both UUID objects (from DB) and strings (from API)
        item_id = item["id"] if isinstance(item["id"], UUID) else UUID(item["id"])
        prop_id = (
            item["property_id"]
            if isinstance(item["property_id"], UUID)
            else UUID(item["property_id"])
        )
        # Handle both datetime objects and ISO strings
        created = (
            item["created_at"]
            if isinstance(item["created_at"], datetime)
            else datetime.fromisoformat(item["created_at"])
        )

        converted.append(
            AdvisoryFeedbackItem(
                id=item_id,
                property_id=prop_id,
                submitted_by=item.get("submitted_by"),
                channel=item.get("channel"),
                sentiment=item["sentiment"],
                notes=item["notes"],
                metadata=item.get("metadata", {}),
                created_at=created,
            )
        )
    return converted


@router.get(
    "/properties/{property_id}/advisory", response_model=AdvisorySummaryResponse
)
async def get_property_advisory_summary(
    property_id: UUID,
    db: AsyncSession = Depends(get_session),
    role: Role = Depends(get_request_role),
) -> AdvisorySummaryResponse:
    """Return advisory insights (mix, positioning, absorption, feedback)."""

    try:
        summary = await advisory_service.build_summary(
            property_id=property_id, session=db
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    asset_mix = _convert_asset_mix(summary.asset_mix)
    market_positioning = AdvisoryMarketPositioning(**summary.market_positioning)

    # Build absorption forecast, converting timeline milestones
    absorption_data = dict(summary.absorption_forecast)
    absorption_data["timeline"] = [
        AdvisoryTimelineMilestone(**milestone)
        for milestone in summary.absorption_forecast.get("timeline", [])
    ]
    absorption_forecast = AdvisoryAbsorptionForecast(**absorption_data)

    feedback_items = _convert_feedback_items(summary.feedback)

    return AdvisorySummaryResponse(
        asset_mix=asset_mix,
        market_positioning=market_positioning,
        absorption_forecast=absorption_forecast,
        feedback=feedback_items,
    )


@router.get(
    "/properties/{property_id}/advisory/feedback",
    response_model=list[AdvisoryFeedbackItem],
)
async def list_property_advisory_feedback(
    property_id: UUID,
    db: AsyncSession = Depends(get_session),
    role: Role = Depends(get_request_role),
) -> list[AdvisoryFeedbackItem]:
    """Return previously captured advisory feedback entries."""

    items = await advisory_service.list_feedback(property_id=property_id, session=db)
    return _convert_feedback_items(items)


@router.post(
    "/properties/{property_id}/advisory/feedback",
    response_model=AdvisoryFeedbackItem,
    status_code=201,
)
async def submit_property_advisory_feedback(
    property_id: UUID,
    payload: AdvisoryFeedbackRequest,
    db: AsyncSession = Depends(get_session),
    role: Role = Depends(get_request_role),
    token: TokenData | None = Depends(get_optional_user),
) -> AdvisoryFeedbackItem:
    """Record market feedback from agents for developers to review."""

    submitted_by = token.sub if token else payload.submitted_by
    try:
        stored = await advisory_service.record_feedback(
            property_id=property_id,
            session=db,
            submitted_by=submitted_by,
            sentiment=payload.sentiment,
            notes=payload.notes,
            channel=payload.channel,
            metadata=payload.metadata or {},
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return _convert_feedback_items([stored])[0]


@router.post(
    "/advisory/sales-velocity", response_model=SalesVelocityResponse, status_code=200
)
async def compute_sales_velocity(
    payload: SalesVelocityRequest,
    role: Role = Depends(get_request_role),
) -> SalesVelocityResponse:
    """Return a lightweight sales velocity forecast using market defaults and optional overrides."""

    result = advisory_service.build_sales_velocity(payload.dict())

    return SalesVelocityResponse(
        forecast=SalesVelocityForecast(**result["forecast"]),
        benchmarks=SalesVelocityBenchmarks(**result["benchmarks"]),
        recommendations=result["recommendations"],
        risks=[SalesVelocityRisk(**risk) for risk in result.get("risks", [])],
        context=result.get("context", {}),
    )


@router.post("/market-intelligence/sync", dependencies=[Depends(require_reviewer)])
async def sync_market_data(
    request: MarketSyncRequest, db: AsyncSession = Depends(get_session)
) -> dict[str, Any]:
    """
    Sync market data from configured providers.

    Admin only endpoint to refresh market data.
    """
    try:
        results = await market_data_service.sync_all_providers(
            session=db, property_types=request.property_types
        )

        return {
            "status": "completed",
            "sync_time": utcnow().isoformat(),
            "results": results,
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/market-intelligence/transactions")
async def get_market_transactions(
    property_type: PropertyType,
    location: str | None = Query(None),
    days_back: int = Query(90, ge=1, le=365),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_session),
    role: Role = Depends(get_request_role),
) -> list[dict[str, Any]]:
    """Get recent market transactions."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days_back)

    transactions = await market_data_service.get_transactions(
        property_type=property_type,
        location=location,
        period=(start_date, end_date),
        session=db,
    )

    # Convert to dict and limit results
    return [
        {
            "transaction_id": str(txn.id),
            "property_name": txn.property.name if txn.property else "Unknown",
            "transaction_date": txn.transaction_date.isoformat(),
            "sale_price": float(txn.sale_price),
            "psf_price": float(txn.psf_price) if txn.psf_price else None,
            "property_type": property_type.value,
            "district": txn.property.district if txn.property else None,
        }
        for txn in transactions[:limit]
    ]


@router.post("/financial/metrics")
async def calculate_financial_metrics(
    request: FinancialMetricsRequest, role: Role = Depends(get_request_role)
) -> dict[str, Any]:
    """
    Calculate comprehensive real estate financial metrics.

    Includes:
    - NOI (Net Operating Income)
    - Cap Rate
    - Cash-on-Cash Return
    - Gross Rent Multiplier
    - Debt Yield
    - LTV Ratio
    - DSCR
    - Rental Yield
    - Operating Expense Ratio
    """
    try:
        from decimal import Decimal

        metrics = calculate_comprehensive_metrics(
            property_value=Decimal(str(request.property_value)),
            gross_rental_income=Decimal(str(request.gross_rental_income)),
            operating_expenses=Decimal(str(request.operating_expenses)),
            loan_amount=(
                Decimal(str(request.loan_amount)) if request.loan_amount else None
            ),
            annual_debt_service=(
                Decimal(str(request.annual_debt_service))
                if request.annual_debt_service
                else None
            ),
            initial_cash_investment=(
                Decimal(str(request.initial_cash_investment))
                if request.initial_cash_investment
                else None
            ),
            vacancy_rate=Decimal(str(request.vacancy_rate)),
            other_income=Decimal(str(request.other_income)),
        )

        return {
            "noi": float(metrics.noi),
            "cap_rate": float(metrics.cap_rate) if metrics.cap_rate else None,
            "cash_on_cash_return": (
                float(metrics.cash_on_cash_return)
                if metrics.cash_on_cash_return
                else None
            ),
            "gross_rent_multiplier": (
                float(metrics.gross_rent_multiplier)
                if metrics.gross_rent_multiplier
                else None
            ),
            "debt_yield": float(metrics.debt_yield) if metrics.debt_yield else None,
            "ltv_ratio": float(metrics.ltv_ratio) if metrics.ltv_ratio else None,
            "dscr": float(metrics.dscr) if metrics.dscr else None,
            "rental_yield": (
                float(metrics.rental_yield) if metrics.rental_yield else None
            ),
            "operating_expense_ratio": (
                float(metrics.operating_expense_ratio)
                if metrics.operating_expense_ratio
                else None
            ),
            "currency": metrics.currency,
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/financial/valuation")
async def value_property(
    request: PropertyValuationRequest, role: Role = Depends(get_request_role)
) -> dict[str, Any]:
    """
    Value property using multiple approaches.

    Approaches:
    - Income Approach (Cap Rate)
    - Sales Comparison Approach
    - Cost Approach
    """
    try:
        from decimal import Decimal

        valuation = value_property_multiple_approaches(
            noi=Decimal(str(request.noi)),
            market_cap_rate=Decimal(str(request.market_cap_rate)),
            comparable_psf=(
                Decimal(str(request.comparable_psf)) if request.comparable_psf else None
            ),
            property_size_sqf=(
                Decimal(str(request.property_size_sqf))
                if request.property_size_sqf
                else None
            ),
            replacement_cost_psf=(
                Decimal(str(request.replacement_cost_psf))
                if request.replacement_cost_psf
                else None
            ),
            land_value=Decimal(str(request.land_value)) if request.land_value else None,
            depreciation_factor=Decimal(str(request.depreciation_factor)),
        )

        return {
            "income_approach_value": float(valuation.income_approach_value),
            "comparable_sales_value": (
                float(valuation.comparable_sales_value)
                if valuation.comparable_sales_value
                else None
            ),
            "replacement_cost_value": (
                float(valuation.replacement_cost_value)
                if valuation.replacement_cost_value
                else None
            ),
            "recommended_value": float(valuation.recommended_value),
            "currency": valuation.currency,
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/properties/{property_id}/generate-pack/{pack_type}")
async def generate_professional_pack(
    property_id: str,
    pack_type: str = Path(..., pattern="^(universal|investment|sales|lease)$"),
    db: AsyncSession = Depends(get_session),
    role: Role = Depends(get_request_role),
) -> dict[str, Any]:
    """
    Generate professional PDF packs.

    Pack types:
    - universal: 20-page Universal Site Pack
    - investment: Institutional-grade Investment Memorandum
    - sales: Sales marketing brochure
    - lease: Leasing marketing brochure
    """
    try:
        property_uuid = UUID(property_id)

        if pack_type == "universal":
            if UniversalSitePackGenerator is None:
                raise HTTPException(
                    status_code=503,
                    detail="Universal Site Pack generation unavailable in this environment",
                )
            generator = UniversalSitePackGenerator()
            pdf_buffer = await generator.generate(property_id=property_uuid, session=db)
            filename = f"universal_site_pack_{property_id}.pdf"

        elif pack_type == "investment":
            if InvestmentMemorandumGenerator is None:
                raise HTTPException(
                    status_code=503,
                    detail="Investment memorandum generation unavailable in this environment",
                )
            generator = InvestmentMemorandumGenerator()
            pdf_buffer = await generator.generate(property_id=property_uuid, session=db)
            filename = f"investment_memorandum_{property_id}.pdf"

        elif pack_type in ["sales", "lease"]:
            if MarketingMaterialsGenerator is None:
                raise HTTPException(
                    status_code=503,
                    detail="Marketing material generation unavailable in this environment",
                )
            generator = MarketingMaterialsGenerator()
            pdf_buffer = await generator.generate_sales_brochure(
                property_id=property_uuid,
                session=db,
                material_type="sale" if pack_type == "sales" else "lease",
            )
            filename = f"{pack_type}_brochure_{property_id}.pdf"

        else:
            raise HTTPException(status_code=400, detail="Invalid pack type")

        # Save to storage (for record keeping)
        await generator.save_to_storage(
            pdf_buffer=pdf_buffer, filename=filename, property_id=property_id
        )

        # Convert to API download URL (absolute URL for cross-origin requests)
        # Use the backend's base URL so frontend can access it regardless of its port
        download_url = f"http://localhost:9400/api/v1/agents/commercial-property/files/{property_id}/{filename}"

        return {
            "pack_type": pack_type,
            "property_id": property_id,
            "filename": filename,
            "download_url": download_url,
            "generated_at": utcnow().isoformat(),
            "size_bytes": len(pdf_buffer.getvalue()),
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/files/{property_id}/{filename}")
async def download_generated_file(
    property_id: str,
    filename: str,
) -> FileResponse:
    """
    Download a generated PDF file from storage.

    This endpoint serves files that were previously generated and stored.
    """
    import os
    from pathlib import Path as PathLib

    # Construct the file path in storage
    storage_base = PathLib(os.getenv("STORAGE_LOCAL_PATH", ".storage"))
    storage_prefix = os.getenv("STORAGE_PREFIX", "uploads")
    file_path = storage_base / storage_prefix / "reports" / property_id / filename

    # Security check: ensure the resolved path is within storage directory
    try:
        file_path = file_path.resolve()
        storage_base_resolved = (storage_base / storage_prefix).resolve()
        if not str(file_path).startswith(str(storage_base_resolved)):
            raise HTTPException(status_code=403, detail="Access denied")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=403, detail="Invalid file path") from None

    # Check if file exists
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    # Return the file
    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=filename,
    )


@router.post("/properties/{property_id}/generate-flyer")
async def generate_email_flyer(
    property_id: str,
    material_type: str = Query("lease", pattern="^(sale|lease)$"),
    db: AsyncSession = Depends(get_session),
    role: Role = Depends(get_request_role),
) -> dict[str, Any]:
    """Generate single-page email flyer."""
    try:
        property_uuid = UUID(property_id)

        generator = MarketingMaterialsGenerator()
        pdf_buffer = await generator.generate_email_flyer(
            property_id=property_uuid, session=db, material_type=material_type
        )

        filename = f"flyer_{material_type}_{property_id}.pdf"

        # Save to storage
        url = await generator.save_to_storage(
            pdf_buffer=pdf_buffer, filename=filename, property_id=property_id
        )

        return {
            "property_id": property_id,
            "flyer_type": material_type,
            "filename": filename,
            "download_url": url,
            "generated_at": utcnow().isoformat(),
            "size_bytes": len(pdf_buffer.getvalue()),
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
