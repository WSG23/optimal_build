"""API endpoints for AI Configuration management."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequestIdentity, get_db, require_reviewer, require_viewer
from app.models.ai_config import AIConfigCategory
from app.schemas.ai_config import (
    AIConfigAuditResponse,
    AIConfigCreate,
    AIConfigListResponse,
    AIConfigResponse,
    AIConfigSummary,
    AIConfigUpdate,
)
from app.services.ai.config_service import ai_config_service

router = APIRouter()


@router.get("/ai-config", response_model=AIConfigListResponse)
async def list_ai_configs(
    category: str | None = Query(default=None, description="Filter by category"),
    organization_id: UUID | None = Query(
        default=None, description="Filter by organization"
    ),
    include_inactive: bool = Query(
        default=False, description="Include inactive configs"
    ),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=50, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    _: RequestIdentity = Depends(require_viewer),
) -> AIConfigListResponse:
    """List AI configurations with optional filtering.

    Returns paginated list of AI configuration summaries.
    """
    configs, total = await ai_config_service.list_configs(
        db,
        category=category,
        organization_id=organization_id,
        include_inactive=include_inactive,
        page=page,
        page_size=page_size,
    )

    items = [
        AIConfigSummary(
            id=c.id,
            category=c.category,
            config_key=c.config_key,
            display_name=c.display_name,
            is_active=c.is_active,
            value_type=c.value_type,
            organization_id=c.organization_id,
        )
        for c in configs
    ]

    return AIConfigListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/ai-config/categories")
async def list_ai_config_categories(
    _: RequestIdentity = Depends(require_viewer),
) -> list[dict[str, str]]:
    """List available AI configuration categories."""
    return [
        {"value": cat.value, "label": cat.value.replace("_", " ").title()}
        for cat in AIConfigCategory
    ]


@router.get("/ai-config/category/{category}")
async def get_configs_for_category(
    category: str,
    organization_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: RequestIdentity = Depends(require_viewer),
) -> dict[str, Any]:
    """Get all configuration values for a category.

    Returns merged view of system defaults and organization overrides.
    """
    configs = await ai_config_service.get_all_configs_for_category(
        db,
        category=category,
        organization_id=organization_id,
    )
    return {"category": category, "configs": configs}


@router.get("/ai-config/{config_id}", response_model=AIConfigResponse)
async def get_ai_config(
    config_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: RequestIdentity = Depends(require_viewer),
) -> AIConfigResponse:
    """Get a specific AI configuration by ID."""
    from sqlalchemy import select
    from app.models.ai_config import AIConfig

    stmt = select(AIConfig).where(AIConfig.id == config_id)
    result = await db.execute(stmt)
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI configuration not found",
        )

    return AIConfigResponse.model_validate(config)


@router.post(
    "/ai-config", response_model=AIConfigResponse, status_code=status.HTTP_201_CREATED
)
async def create_ai_config(
    payload: AIConfigCreate,
    db: AsyncSession = Depends(get_db),
    identity: RequestIdentity = Depends(require_reviewer),
) -> AIConfigResponse:
    """Create a new AI configuration.

    Requires reviewer or admin role.
    """
    # Parse user_id from identity
    user_id = None
    if identity.user_id:
        try:
            user_id = UUID(identity.user_id)
        except ValueError:
            pass

    try:
        config = await ai_config_service.create_config(
            db,
            category=payload.category,
            config_key=payload.config_key,
            display_name=payload.display_name,
            config_value=payload.config_value,
            description=payload.description,
            value_type=payload.value_type,
            validation_schema=payload.validation_schema,
            organization_id=payload.organization_id,
            created_by=user_id,
        )
        return AIConfigResponse.model_validate(config)
    except Exception as e:
        if "duplicate key" in str(e).lower() or "unique constraint" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Configuration with this category/key already exists",
            ) from e
        raise


@router.patch("/ai-config/{config_id}", response_model=AIConfigResponse)
async def update_ai_config(
    config_id: UUID,
    payload: AIConfigUpdate,
    db: AsyncSession = Depends(get_db),
    identity: RequestIdentity = Depends(require_reviewer),
) -> AIConfigResponse:
    """Update an AI configuration.

    Requires reviewer or admin role.
    """
    user_id = None
    if identity.user_id:
        try:
            user_id = UUID(identity.user_id)
        except ValueError:
            pass

    config = await ai_config_service.update_config(
        db,
        config_id=config_id,
        config_value=payload.config_value,
        display_name=payload.display_name,
        description=payload.description,
        value_type=payload.value_type,
        validation_schema=payload.validation_schema,
        is_active=payload.is_active,
        updated_by=user_id,
        change_reason=payload.change_reason,
    )

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI configuration not found",
        )

    return AIConfigResponse.model_validate(config)


@router.delete("/ai-config/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ai_config(
    config_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: RequestIdentity = Depends(require_reviewer),
) -> None:
    """Delete (deactivate) an AI configuration.

    Requires reviewer or admin role. Performs soft delete.
    """
    deleted = await ai_config_service.delete_config(db, config_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI configuration not found",
        )


@router.get("/ai-config/{config_id}/audit", response_model=list[AIConfigAuditResponse])
async def get_ai_config_audit(
    config_id: UUID,
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: RequestIdentity = Depends(require_viewer),
) -> list[AIConfigAuditResponse]:
    """Get audit log for an AI configuration."""
    audits = await ai_config_service.get_audit_log(db, config_id, limit=limit)
    return [AIConfigAuditResponse.model_validate(a) for a in audits]


@router.post("/ai-config/seed", status_code=status.HTTP_201_CREATED)
async def seed_default_configs(
    db: AsyncSession = Depends(get_db),
    identity: RequestIdentity = Depends(require_reviewer),
) -> dict[str, int]:
    """Seed default AI configurations.

    Creates default configurations from hardcoded values.
    Only creates configs that don't already exist.
    Requires reviewer or admin role.
    """
    user_id = None
    if identity.user_id:
        try:
            user_id = UUID(identity.user_id)
        except ValueError:
            pass

    created_count = await ai_config_service.seed_default_configs(db, user_id=user_id)
    return {"created": created_count}


@router.get("/ai-config/value/{category}/{config_key}")
async def get_config_value(
    category: str,
    config_key: str,
    organization_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: RequestIdentity = Depends(require_viewer),
) -> dict[str, Any]:
    """Get a specific configuration value by category and key.

    Returns the merged value considering organization overrides.
    Falls back to hardcoded defaults if not in database.
    """
    value = await ai_config_service.get_config(
        db,
        category=category,
        config_key=config_key,
        organization_id=organization_id,
    )

    if value is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration {category}/{config_key} not found",
        )

    return {"category": category, "config_key": config_key, "value": value}


__all__ = ["router"]
