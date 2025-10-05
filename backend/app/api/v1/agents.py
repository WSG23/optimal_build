"""API endpoints for Commercial Property Advisors agent features."""

from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, File, HTTPException, Path, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import Role, get_request_role, require_reviewer
from app.core.database import get_session
from app.models.property import Property, PropertyType
from app.services.agents.development_potential_scanner import (
    DevelopmentPotentialScanner,
)
from app.services.agents.gps_property_logger import (
    DevelopmentScenario,
    GPSPropertyLogger,
)
from app.services.agents.photo_documentation import PhotoDocumentationManager
from app.services.agents.ura_integration import ura_service
from app.services.geocoding import Address, GeocodingService

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
from app.services.buildable import BuildableService
from app.services.finance import (
    calculate_comprehensive_metrics,
    value_property_multiple_approaches,
)
from app.services.postgis import PostGISService

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


class MarketIntelligenceResponse(BaseModel):
    property_id: UUID
    report: Dict[str, Any]


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
        result = await gps_logger.log_property_from_gps(
            latitude=request.latitude,
            longitude=request.longitude,
            session=db,
            user_id=None,  # TODO: Get from auth context
            scenarios=request.development_scenarios,
        )
        quick_analysis_payload = result.quick_analysis or {
            "generated_at": datetime.utcnow().isoformat(),
            "scenarios": [],
        }
        quick_analysis = QuickAnalysisEnvelope.model_validate(quick_analysis_payload)

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
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


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

    try:
        report = await market_analytics.generate_market_report(
            property_type=property_data.property_type,
            location=location,
            period_months=months,
            session=db,
        )
    except Exception as exc:  # pragma: no cover - analytics layer may raise
        logger.error("Market intelligence generation failed", exc_info=exc)
        raise HTTPException(
            status_code=503,
            detail="Market intelligence service is temporarily unavailable",
        ) from exc

    return MarketIntelligenceResponse(
        property_id=property_uuid,
        report=report.to_dict(),
    )


@router.post("/properties/{property_id}/analyze")
async def analyze_development_potential(
    property_id: str,
    request: PropertyAnalysisRequest,
    db: AsyncSession = Depends(get_session),
    role: Role = Depends(get_request_role),
) -> dict[str, Any]:
    """
    Analyze development potential for a property.

    Analysis types:
    - raw_land: GFA potential, optimal use mix, scenarios
    - existing_building: Renovation/redevelopment potential
    - historical_property: Heritage constraints and adaptive reuse
    """
    # Get required services
    buildable_service = BuildableService(db)
    from app.services.finance.calculator import FinanceCalculator

    finance_calc = FinanceCalculator()

    scanner = DevelopmentPotentialScanner(buildable_service, finance_calc, ura_service)

    # Get property data
    from sqlalchemy import select

    from app.models.property import Property

    stmt = select(Property).where(Property.id == UUID(property_id))
    result = await db.execute(stmt)
    property_data = result.scalar_one_or_none()

    if not property_data:
        raise HTTPException(status_code=404, detail="Property not found")

    try:
        analysis_result = await scanner.analyze_property(
            property_data=property_data,
            property_type=request.analysis_type,
            session=db,
            save_analysis=request.save_results,
        )

        return {
            "property_id": property_id,
            "analysis_type": request.analysis_type,
            "analysis_date": datetime.utcnow().isoformat(),
            "results": analysis_result,
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/properties/{property_id}/photos")
async def upload_property_photo(
    property_id: str,
    file: UploadFile = File(...),
    notes: str | None = None,
    tags: str | None = None,
    db: AsyncSession = Depends(get_session),
    role: Role = Depends(get_request_role),
) -> PhotoUploadResponse:
    """
    Upload and analyze a property photo.

    This endpoint will:
    - Extract EXIF data for location and timestamp
    - Auto-tag site conditions
    - Generate multiple image versions
    - Store in S3/MinIO
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Read file data
    photo_data = await file.read()

    # Prepare user metadata
    user_metadata = {}
    if notes:
        user_metadata["notes"] = notes
    if tags:
        user_metadata["tags"] = tags.split(",")

    photo_manager = PhotoDocumentationManager()

    try:
        metadata = await photo_manager.process_photo(
            photo_data=photo_data,
            property_id=property_id,
            filename=file.filename or "photo.jpg",
            session=db,
            user_metadata=user_metadata,
        )

        result = metadata.to_dict()

        return PhotoUploadResponse(
            photo_id=result["photo_id"],
            storage_key=result["storage_key"],
            location=result.get("location"),
            capture_timestamp=datetime.fromisoformat(result["capture_timestamp"]),
            auto_tags=result["auto_tagged_conditions"],
            public_url=result["public_url"],
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/properties/{property_id}/photos")
async def get_property_photos(
    property_id: str,
    db: AsyncSession = Depends(get_session),
    role: Role = Depends(get_request_role),
) -> list[dict[str, Any]]:
    """Get all photos for a property."""
    photo_manager = PhotoDocumentationManager()

    try:
        photos = await photo_manager.get_property_photos(
            property_id=property_id, session=db, include_urls=True
        )

        return photos

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/properties/{property_id}/scenarios/3d")
async def generate_3d_scenarios(
    property_id: str,
    request: ScenarioGenerationRequest,
    db: AsyncSession = Depends(get_session),
    role: Role = Depends(get_request_role),
) -> list[dict[str, Any]]:
    """
    Generate 3D massing scenarios for property development.

    Scenario types:
    - new_build: New construction based on zoning
    - renovation: Existing building modifications
    - mixed_use_conversion: Convert to mixed-use
    - vertical_extension: Add floors to existing
    - podium_tower: Podium with towers configuration
    - phased_development: Multi-phase development
    """
    if Quick3DScenarioBuilder is None:
        raise HTTPException(
            status_code=503,
            detail="3D scenario generation is unavailable in the current environment",
        )

    postgis_service = PostGISService(db)
    scenario_builder = Quick3DScenarioBuilder(postgis_service)

    # Get property data
    from sqlalchemy import select

    from app.models.property import Property

    stmt = select(Property).where(Property.id == UUID(property_id))
    result = await db.execute(stmt)
    property_data = result.scalar_one_or_none()

    if not property_data:
        raise HTTPException(status_code=404, detail="Property not found")

    try:
        # Get zoning info
        zoning_info = await ura_service.get_zoning_info(property_data.address)

        # Generate scenarios
        scenarios = await scenario_builder.generate_massing_scenarios(
            property_data=property_data,
            scenario_types=request.scenario_types,
            session=db,
            zoning_info=zoning_info,
        )

        # Convert to response format
        return [scenario.to_dict() for scenario in scenarios]

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/properties/{property_id}/scenarios/3d/{scenario_index}/export")
async def export_3d_scenario(
    property_id: str,
    scenario_index: int,
    format: str = Query("obj", pattern="^(obj|stl|glb|json)$"),
    db: AsyncSession = Depends(get_session),
    role: Role = Depends(get_request_role),
) -> bytes:
    """Export a 3D scenario in various formats."""
    # This is simplified - in production, store scenarios and retrieve by index
    raise HTTPException(
        status_code=501, detail="Export functionality not yet implemented"
    )


@router.post("/market-intelligence/report")
async def generate_market_report(
    request: MarketReportRequest,
    db: AsyncSession = Depends(get_session),
    role: Role = Depends(get_request_role),
) -> dict[str, Any]:
    """
    Generate comprehensive market intelligence report.

    Includes:
    - Comparable transaction analysis
    - Supply pipeline dynamics
    - Yield benchmarks and trends
    - Absorption and velocity metrics
    - Market cycle position
    - Actionable recommendations
    """
    try:
        report = await market_analytics.generate_market_report(
            property_type=request.property_type,
            location=request.location,
            period_months=request.period_months,
            session=db,
            competitive_set_id=(
                UUID(request.competitive_set_id) if request.competitive_set_id else None
            ),
        )

        return report.to_dict()

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


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
            "sync_time": datetime.utcnow().isoformat(),
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

        # Save to storage and get URL
        url = await generator.save_to_storage(
            pdf_buffer=pdf_buffer, filename=filename, property_id=property_id
        )

        return {
            "pack_type": pack_type,
            "property_id": property_id,
            "filename": filename,
            "download_url": url,
            "generated_at": datetime.utcnow().isoformat(),
            "size_bytes": len(pdf_buffer.getvalue()),
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


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
            "generated_at": datetime.utcnow().isoformat(),
            "size_bytes": len(pdf_buffer.getvalue()),
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
