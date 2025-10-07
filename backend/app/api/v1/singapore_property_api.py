"""Singapore Property API with BCA compliance and URA zoning validation.

This API uses the SingaporeProperty model and compliance utilities for
property feasibility analysis and space optimization.

MVP: Uses synchronous database for simplicity.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.jwt_auth import TokenData, get_current_user
from app.models.singapore_property import (
    AcquisitionStatus,
    ComplianceStatus,
    DevelopmentStatus,
    FeasibilityStatus,
    PropertyTenure,
    PropertyZoning,
    SingaporeProperty,
)
from app.utils.singapore_compliance import (
    calculate_gfa_utilization,
    run_full_compliance_check_sync,
    update_property_compliance_sync,
)

router = APIRouter(prefix="/singapore-property", tags=["Singapore Property"])

# MVP: Simple synchronous database session for Singapore properties
# This creates a separate sync session just for this MVP feature
_sync_engine = None
_SessionLocal = None


def get_sync_db():
    """Get synchronous database session for MVP."""
    global _sync_engine, _SessionLocal

    if _sync_engine is None:
        # Use the same database URL but synchronous
        original_url = str(settings.SQLALCHEMY_DATABASE_URI)
        db_url = original_url.replace("+aiosqlite", "").replace("+asyncpg", "+psycopg2")

        _sync_engine = create_engine(db_url, pool_pre_ping=True)
        _SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=_sync_engine
        )

    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Pydantic Request/Response Models
class PropertyCreate(BaseModel):
    """Property creation model for MVP."""

    # Basic Information
    property_name: str = Field(..., min_length=1, max_length=255)
    address: str = Field(..., min_length=1, max_length=1000)
    postal_code: str | None = Field(None, max_length=6, pattern="^[0-9]{6}$")

    # Property Details
    zoning: PropertyZoning
    tenure: PropertyTenure | None = None

    # Land and Building
    land_area_sqm: Decimal = Field(..., gt=0, description="Land area in square meters")
    gross_plot_ratio: Decimal = Field(
        ..., gt=0, description="Maximum plot ratio allowed"
    )
    gross_floor_area_sqm: Decimal | None = Field(None, ge=0)
    building_height_m: Decimal | None = Field(None, gt=0)
    num_storeys: int | None = Field(None, gt=0)

    # MVP: Acquisition & Feasibility
    acquisition_status: AcquisitionStatus | None = AcquisitionStatus.AVAILABLE
    feasibility_status: FeasibilityStatus | None = FeasibilityStatus.ANALYZING

    # MVP: Financial
    estimated_acquisition_cost: Decimal | None = Field(None, ge=0)
    estimated_development_cost: Decimal | None = Field(None, ge=0)
    expected_revenue: Decimal | None = Field(None, ge=0)

    # Optional: Link to project
    project_id: str | None = None

    class Config:
        use_enum_values = True


class PropertyUpdate(BaseModel):
    """Property update model."""

    property_name: str | None = Field(None, min_length=1, max_length=255)
    address: str | None = Field(None, min_length=1)
    postal_code: str | None = Field(None, max_length=6, pattern="^[0-9]{6}$")
    zoning: PropertyZoning | None = None
    tenure: PropertyTenure | None = None
    land_area_sqm: Decimal | None = Field(None, gt=0)
    gross_plot_ratio: Decimal | None = Field(None, gt=0)
    gross_floor_area_sqm: Decimal | None = Field(None, ge=0)
    building_height_m: Decimal | None = Field(None, gt=0)
    num_storeys: int | None = Field(None, gt=0)
    acquisition_status: AcquisitionStatus | None = None
    feasibility_status: FeasibilityStatus | None = None
    estimated_acquisition_cost: Decimal | None = Field(None, ge=0)
    actual_acquisition_cost: Decimal | None = Field(None, ge=0)
    estimated_development_cost: Decimal | None = Field(None, ge=0)
    expected_revenue: Decimal | None = Field(None, ge=0)
    project_id: str | None = None

    class Config:
        use_enum_values = True


class PropertyResponse(BaseModel):
    """Property response model."""

    id: str
    property_name: str
    address: str
    postal_code: str | None

    zoning: str | None
    tenure: str | None

    land_area_sqm: Decimal | None
    gross_plot_ratio: Decimal | None
    gross_floor_area_sqm: Decimal | None
    building_height_m: Decimal | None
    num_storeys: int | None

    # MVP: Workflow Status
    acquisition_status: str | None
    feasibility_status: str | None

    # MVP: Financial
    estimated_acquisition_cost: Decimal | None
    actual_acquisition_cost: Decimal | None
    estimated_development_cost: Decimal | None
    expected_revenue: Decimal | None

    # Compliance
    bca_compliance_status: str | None
    ura_compliance_status: str | None
    compliance_notes: str | None
    compliance_last_checked: datetime | None

    # Space Optimization
    max_developable_gfa_sqm: Decimal | None
    gfa_utilization_percentage: Decimal | None
    potential_additional_units: int | None

    # Metadata
    project_id: str | None
    owner_email: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        """Convert SQLAlchemy model to Pydantic, handling UUIDs."""
        data = {
            "id": str(obj.id),
            "property_name": obj.property_name,
            "address": obj.address,
            "postal_code": obj.postal_code,
            "zoning": obj.zoning.value if obj.zoning else None,
            "tenure": obj.tenure.value if obj.tenure else None,
            "land_area_sqm": obj.land_area_sqm,
            "gross_plot_ratio": obj.gross_plot_ratio,
            "gross_floor_area_sqm": obj.gross_floor_area_sqm,
            "building_height_m": obj.building_height_m,
            "num_storeys": obj.num_storeys,
            "acquisition_status": (
                obj.acquisition_status.value if obj.acquisition_status else None
            ),
            "feasibility_status": (
                obj.feasibility_status.value if obj.feasibility_status else None
            ),
            "estimated_acquisition_cost": obj.estimated_acquisition_cost,
            "actual_acquisition_cost": obj.actual_acquisition_cost,
            "estimated_development_cost": obj.estimated_development_cost,
            "expected_revenue": obj.expected_revenue,
            "bca_compliance_status": (
                obj.bca_compliance_status.value if obj.bca_compliance_status else None
            ),
            "ura_compliance_status": (
                obj.ura_compliance_status.value if obj.ura_compliance_status else None
            ),
            "compliance_notes": obj.compliance_notes,
            "compliance_last_checked": obj.compliance_last_checked,
            "max_developable_gfa_sqm": obj.max_developable_gfa_sqm,
            "gfa_utilization_percentage": obj.gfa_utilization_percentage,
            "potential_additional_units": obj.potential_additional_units,
            "project_id": str(obj.project_id) if obj.project_id else None,
            "owner_email": obj.owner_email,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
        }
        return cls(**data)


class ComplianceCheckResponse(BaseModel):
    """Compliance check response."""

    property_id: str
    overall_status: str
    bca_status: str
    ura_status: str
    violations: list[str]
    warnings: list[str]
    recommendations: list[str]
    compliance_data: dict[str, Any]


# API Endpoints


@router.post("/create", response_model=PropertyResponse)
def create_property(
    property_data: PropertyCreate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_sync_db),
):
    """
    Create a new Singapore property with automatic compliance checking.

    This endpoint:
    1. Creates the property record
    2. Runs BCA and URA compliance checks
    3. Calculates GFA utilization and space optimization potential
    4. Returns property with compliance status
    """
    # Create property instance (convert enums to values for SQLAlchemy)
    if hasattr(property_data.zoning, "value"):
        zoning_value = property_data.zoning.value
    else:
        zoning_value = property_data.zoning

    new_property = SingaporeProperty(
        property_name=property_data.property_name,
        address=property_data.address,
        postal_code=property_data.postal_code,
        zoning=zoning_value,
        tenure=(
            property_data.tenure.value
            if property_data.tenure and hasattr(property_data.tenure, "value")
            else property_data.tenure
        ),
        land_area_sqm=property_data.land_area_sqm,
        gross_plot_ratio=property_data.gross_plot_ratio,
        gross_floor_area_sqm=property_data.gross_floor_area_sqm,
        building_height_m=property_data.building_height_m,
        num_storeys=property_data.num_storeys,
        acquisition_status=(
            property_data.acquisition_status.value
            if hasattr(property_data.acquisition_status, "value")
            else property_data.acquisition_status
        ),
        feasibility_status=(
            property_data.feasibility_status.value
            if hasattr(property_data.feasibility_status, "value")
            else property_data.feasibility_status
        ),
        estimated_acquisition_cost=property_data.estimated_acquisition_cost,
        estimated_development_cost=property_data.estimated_development_cost,
        expected_revenue=property_data.expected_revenue,
        owner_email=current_user.email,
        development_status=DevelopmentStatus.VACANT_LAND.value,
    )

    # Run compliance checks and update property
    update_property_compliance_sync(new_property)

    # Save to database
    db.add(new_property)
    db.commit()
    db.refresh(new_property)

    return PropertyResponse.from_orm(new_property)


@router.get("/list", response_model=list[PropertyResponse])
def list_properties(
    db: Session = Depends(get_sync_db),
    acquisition_status: AcquisitionStatus | None = Query(None),
    feasibility_status: FeasibilityStatus | None = Query(None),
    zoning: PropertyZoning | None = Query(None),
    compliance_status: ComplianceStatus | None = Query(None),
    skip: int = 0,
    limit: int = 100,
):
    """
    List all Singapore properties with optional filters.

    Public endpoint - no authentication required for viewing.
    """
    query = db.query(SingaporeProperty)

    if acquisition_status:
        query = query.filter(SingaporeProperty.acquisition_status == acquisition_status)
    if feasibility_status:
        query = query.filter(SingaporeProperty.feasibility_status == feasibility_status)
    if zoning:
        query = query.filter(SingaporeProperty.zoning == zoning)
    if compliance_status:
        query = query.filter(
            (SingaporeProperty.bca_compliance_status == compliance_status)
            | (SingaporeProperty.ura_compliance_status == compliance_status)
        )

    properties = query.offset(skip).limit(limit).all()

    return [PropertyResponse.from_orm(p) for p in properties]


@router.get("/{property_id}", response_model=PropertyResponse)
def get_property(
    property_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_sync_db),
):
    """Get a specific property by ID."""
    try:
        property_uuid = uuid.UUID(property_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid property ID format") from e

    property_obj = (
        db.query(SingaporeProperty)
        .filter(
            SingaporeProperty.id == property_uuid,
            SingaporeProperty.owner_email == current_user.email,
        )
        .first()
    )

    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")

    return PropertyResponse.from_orm(property_obj)


@router.put("/{property_id}", response_model=PropertyResponse)
def update_property(
    property_id: str,
    property_update: PropertyUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_sync_db),
):
    """
    Update a property and re-run compliance checks.

    Compliance checks run automatically whenever property details change.
    """
    try:
        property_uuid = uuid.UUID(property_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid property ID format") from e

    property_obj = (
        db.query(SingaporeProperty)
        .filter(
            SingaporeProperty.id == property_uuid,
            SingaporeProperty.owner_email == current_user.email,
        )
        .first()
    )

    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")

    # Update fields
    update_data = property_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(property_obj, field, value)

    # Re-run compliance checks
    update_property_compliance_sync(property_obj)
    property_obj.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(property_obj)

    return PropertyResponse.from_orm(property_obj)


@router.post("/{property_id}/check-compliance", response_model=ComplianceCheckResponse)
def check_property_compliance(
    property_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_sync_db),
):
    """
    Run detailed BCA and URA compliance checks for a property.

    Returns comprehensive compliance report with violations, warnings,
    and recommendations for space optimization.
    """
    try:
        property_uuid = uuid.UUID(property_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid property ID format") from e

    property_obj = (
        db.query(SingaporeProperty)
        .filter(
            SingaporeProperty.id == property_uuid,
            SingaporeProperty.owner_email == current_user.email,
        )
        .first()
    )

    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")

    # Run full compliance check
    result = run_full_compliance_check_sync(property_obj)

    return ComplianceCheckResponse(
        property_id=property_id,
        overall_status=result["overall_status"].value,
        bca_status=result["bca_status"].value,
        ura_status=result["ura_status"].value,
        violations=result["violations"],
        warnings=result["warnings"],
        recommendations=result["recommendations"],
        compliance_data=result["compliance_data"],
    )


@router.get("/calculate/gfa-utilization/{property_id}")
def calculate_property_gfa(
    property_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_sync_db),
):
    """
    Calculate GFA utilization and remaining development potential.

    Key metric for space optimization - shows how much more can be built.
    """
    try:
        property_uuid = uuid.UUID(property_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid property ID format") from e

    property_obj = (
        db.query(SingaporeProperty)
        .filter(
            SingaporeProperty.id == property_uuid,
            SingaporeProperty.owner_email == current_user.email,
        )
        .first()
    )

    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")

    result = calculate_gfa_utilization(property_obj)
    result["property_id"] = property_id
    result["land_area_sqm"] = (
        float(property_obj.land_area_sqm) if property_obj.land_area_sqm else None
    )
    result["plot_ratio"] = (
        float(property_obj.gross_plot_ratio) if property_obj.gross_plot_ratio else None
    )

    return result


@router.post("/calculate/buildable")
async def calculate_buildable_metrics(
    request: dict[str, Any], current_user: TokenData = Depends(get_current_user)
):
    """
    Calculate buildable metrics using jurisdiction-agnostic system.

    This endpoint uses the production buildable.py service which queries
    RefRule database for jurisdiction-specific regulations.

    Args:
        land_area_sqm: Land area in square meters
        zoning: Zoning code (e.g., 'residential', 'commercial')
        jurisdiction: Jurisdiction code (e.g., 'SG', 'US-NY')
        street_width_m: Optional street width for envelope calculations

    Returns:
        Buildable metrics including plot ratio, max height, GFA, NSA, etc.
    """
    from app.core.database import AsyncSessionLocal
    from app.schemas.buildable import BuildableDefaults
    from app.services.buildable import ResolvedZone, calculate_buildable

    land_area = request.get("land_area_sqm")
    zoning = request.get("zoning")
    jurisdiction = request.get("jurisdiction", "SG")
    street_width = request.get("street_width_m")

    if not land_area or not zoning:
        raise HTTPException(
            status_code=400, detail="land_area_sqm and zoning are required"
        )

    # Create buildable defaults
    defaults = BuildableDefaults(
        site_area_m2=float(land_area),
        floor_height_m=4.0,  # Building science constant
        efficiency_factor=0.82,  # 82% efficiency
    )

    # Create resolved zone for jurisdiction-agnostic lookup
    resolved = ResolvedZone(
        zone_code=f"{jurisdiction}:{zoning}",  # e.g., "SG:residential"
        parcel=None,
        zone_layers=[],
        input_kind="api_request",
        geometry_properties={"street_width_m": street_width} if street_width else None,
    )

    # Use jurisdiction-agnostic buildable service
    async with AsyncSessionLocal() as session:
        try:
            buildable_calc = await calculate_buildable(
                session=session,
                resolved=resolved,
                defaults=defaults,
                typ_floor_to_floor_m=4.0,
                efficiency_ratio=0.82,
            )

            # Extract metrics
            metrics = buildable_calc.metrics

            # Extract actual rule values from applied rules
            plot_ratio = None
            max_height = None
            site_coverage_pct = None

            for rule in buildable_calc.rules:
                if rule.parameter_key == "zoning.max_far":
                    plot_ratio = float(rule.value)
                elif rule.parameter_key == "zoning.max_building_height_m":
                    max_height = float(rule.value)
                elif rule.parameter_key == "zoning.site_coverage.max_percent":
                    site_coverage_pct = float(rule.value)

            # Fallback to derived values if rules not found
            if plot_ratio is None:
                plot_ratio = metrics.gfa_cap_m2 / land_area if land_area > 0 else 0
            if max_height is None:
                max_height = metrics.floors_max * 4.0 if metrics.floors_max > 0 else 0
            if site_coverage_pct is None:
                site_coverage_pct = (
                    (metrics.footprint_m2 / land_area * 100) if land_area > 0 else 0
                )

            # Site coverage as fraction for calculations
            site_coverage_fraction = site_coverage_pct / 100.0

            return {
                "plot_ratio": plot_ratio,
                "max_height_m": max_height,
                "site_coverage": site_coverage_fraction,
                "site_coverage_pct": site_coverage_pct,
                "max_floors": metrics.floors_max,
                "footprint_sqm": metrics.footprint_m2,
                "max_gfa_sqm": metrics.gfa_cap_m2,
                "nsa_sqm": metrics.nsa_est_m2,
                "efficiency_ratio": 0.82,
                "floor_to_floor_m": 4.0,
                "rules_applied": len(buildable_calc.rules),
                "jurisdiction": jurisdiction,
                "zone_code": zoning,
            }
        except Exception:
            # Fallback: Use simple calculation if RefRule database is empty
            # This allows MVP to work before rules are populated
            # Fallback default values (will be replaced by RefRule data)
            fallback_rules = {
                "residential": {
                    "plot_ratio": 2.8,
                    "max_height": 36,
                    "site_coverage": 0.4,
                },
                "commercial": {
                    "plot_ratio": 10.0,
                    "max_height": 280,
                    "site_coverage": 0.5,
                },
                "industrial": {
                    "plot_ratio": 2.5,
                    "max_height": 50,
                    "site_coverage": 0.6,
                },
                "mixed_use": {
                    "plot_ratio": 3.0,
                    "max_height": 80,
                    "site_coverage": 0.45,
                },
                "business_park": {
                    "plot_ratio": 2.5,
                    "max_height": 50,
                    "site_coverage": 0.45,
                },
            }

            rules = fallback_rules.get(
                zoning, {"plot_ratio": 2.8, "max_height": 36, "site_coverage": 0.4}
            )

            max_gfa = land_area * rules["plot_ratio"]
            max_floors = int(rules["max_height"] / 4.0)
            footprint = land_area * rules["site_coverage"]
            nsa = max_gfa * 0.82

            return {
                "plot_ratio": rules["plot_ratio"],
                "max_height_m": rules["max_height"],
                "site_coverage": rules["site_coverage"],
                "max_floors": max_floors,
                "footprint_sqm": footprint,
                "max_gfa_sqm": max_gfa,
                "nsa_sqm": nsa,
                "efficiency_ratio": 0.82,
                "floor_to_floor_m": 4.0,
                "rules_applied": 0,
                "jurisdiction": jurisdiction,
                "zone_code": zoning,
                "fallback_used": True,
            }


@router.post("/check-compliance")
async def check_compliance(
    request: dict[str, Any], current_user: TokenData = Depends(get_current_user)
):
    """
    Check building code compliance for proposed design against Singapore URA/BCA rules.

    Compares proposed design parameters against maximum allowed values from RefRule database.
    Returns pass/fail status with detailed violations list.
    """
    from app.core.database import AsyncSessionLocal
    from app.utils.singapore_compliance import (
        check_bca_compliance,
        check_ura_compliance,
    )

    # Extract request parameters
    land_area = request.get("land_area_sqm")
    zoning = request.get("zoning")
    proposed_gfa = request.get("proposed_gfa_sqm")
    proposed_height = request.get("proposed_height_m")
    proposed_storeys = request.get("proposed_storeys")
    _jurisdiction = request.get("jurisdiction", "SG")  # Reserved for future use

    if not land_area or not zoning:
        raise HTTPException(
            status_code=400, detail="land_area_sqm and zoning are required"
        )

    # Create a temporary property object for compliance checking
    temp_property = SingaporeProperty(
        id=uuid.uuid4(),
        property_name="Compliance Check",
        address="N/A",
        zoning=zoning,
        land_area_sqm=Decimal(str(land_area)),
        gross_floor_area_sqm=Decimal(str(proposed_gfa)) if proposed_gfa else None,
        building_height_m=Decimal(str(proposed_height)) if proposed_height else None,
        num_storeys=proposed_storeys,
        gross_plot_ratio=(
            Decimal(str(proposed_gfa / land_area))
            if proposed_gfa and land_area
            else None
        ),
        owner_email=current_user.email,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    async with AsyncSessionLocal() as session:
        try:
            # Run URA and BCA compliance checks
            ura_result = await check_ura_compliance(temp_property, session)
            bca_result = await check_bca_compliance(temp_property, session)

            # Compile all violations and warnings
            all_violations = ura_result.get("violations", []) + bca_result.get(
                "violations", []
            )
            all_warnings = ura_result.get("warnings", []) + bca_result.get(
                "warnings", []
            )
            all_recommendations = bca_result.get("recommendations", [])

            # Determine overall status
            if all_violations:
                overall_status = "FAILED"
            elif all_warnings:
                overall_status = "WARNING"
            else:
                overall_status = "PASSED"

            return {
                "status": overall_status,
                "violations": all_violations,
                "warnings": all_warnings,
                "recommendations": all_recommendations,
                "ura_check": {
                    "status": (
                        ura_result["status"].value
                        if hasattr(ura_result["status"], "value")
                        else ura_result["status"]
                    ),
                    "violations": ura_result.get("violations", []),
                    "rules_applied": ura_result.get("rules_applied", {}),
                },
                "bca_check": {
                    "status": (
                        bca_result["status"].value
                        if hasattr(bca_result["status"], "value")
                        else bca_result["status"]
                    ),
                    "violations": bca_result.get("violations", []),
                    "requirements_applied": bca_result.get("requirements_applied", {}),
                },
                "proposed_design": {
                    "land_area_sqm": float(land_area),
                    "zoning": zoning,
                    "proposed_gfa_sqm": float(proposed_gfa) if proposed_gfa else None,
                    "proposed_height_m": (
                        float(proposed_height) if proposed_height else None
                    ),
                    "proposed_storeys": proposed_storeys,
                    "calculated_plot_ratio": (
                        float(proposed_gfa / land_area)
                        if proposed_gfa and land_area
                        else None
                    ),
                },
            }
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Compliance check failed: {str(e)}"
            ) from e


@router.delete("/{property_id}")
def delete_property(
    property_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_sync_db),
):
    """Soft delete a property (marks as inactive)."""
    try:
        property_uuid = uuid.UUID(property_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid property ID format") from e

    property_obj = (
        db.query(SingaporeProperty)
        .filter(
            SingaporeProperty.id == property_uuid,
            SingaporeProperty.owner_email == current_user.email,
        )
        .first()
    )

    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")

    # Soft delete
    db.delete(property_obj)
    db.commit()

    return {"message": "Property deleted successfully", "property_id": property_id}
