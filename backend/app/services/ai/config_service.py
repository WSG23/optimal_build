"""Service for managing AI configuration.

Provides CRUD operations and caching for AI configuration values,
as well as seeding default configurations from the model defaults.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_config import (
    AIConfig,
    AIConfigAudit,
    AIConfigCategory,
    DEFAULT_AI_CONFIGS,
)

logger = logging.getLogger(__name__)


class AIConfigService:
    """Service for managing AI configuration values."""

    # In-memory cache for frequently accessed configs
    _cache: dict[str, dict[str, Any]] = {}
    _cache_initialized: bool = False

    async def get_config(
        self,
        db: AsyncSession,
        category: str,
        config_key: str,
        organization_id: UUID | None = None,
    ) -> dict[str, Any] | None:
        """Get a specific configuration value.

        Looks up organization-specific config first, then falls back to system default.

        Args:
            db: Database session
            category: Configuration category
            config_key: Configuration key
            organization_id: Optional organization ID for org-specific config

        Returns:
            Configuration value dict or None if not found
        """
        # Try organization-specific config first
        if organization_id:
            org_config = await self._get_config_from_db(
                db, category, config_key, organization_id
            )
            if org_config:
                return org_config.config_value

        # Fall back to system default (organization_id = None)
        system_config = await self._get_config_from_db(db, category, config_key, None)
        if system_config:
            return system_config.config_value

        # Fall back to hardcoded defaults if not in database
        return self._get_default_config(category, config_key)

    async def get_all_configs_for_category(
        self,
        db: AsyncSession,
        category: str,
        organization_id: UUID | None = None,
    ) -> dict[str, dict[str, Any]]:
        """Get all configuration values for a category.

        Args:
            db: Database session
            category: Configuration category
            organization_id: Optional organization ID

        Returns:
            Dictionary of config_key -> config_value
        """
        configs: dict[str, dict[str, Any]] = {}

        # Get system defaults first
        stmt = select(AIConfig).where(
            and_(
                AIConfig.category == category,
                AIConfig.organization_id.is_(None),
                AIConfig.is_active.is_(True),
            )
        )
        result = await db.execute(stmt)
        for config in result.scalars().all():
            configs[config.config_key] = config.config_value

        # Override with organization-specific if provided
        if organization_id:
            stmt = select(AIConfig).where(
                and_(
                    AIConfig.category == category,
                    AIConfig.organization_id == organization_id,
                    AIConfig.is_active.is_(True),
                )
            )
            result = await db.execute(stmt)
            for config in result.scalars().all():
                configs[config.config_key] = config.config_value

        # Fill in any missing configs from hardcoded defaults
        try:
            cat_enum = AIConfigCategory(category)
            defaults = DEFAULT_AI_CONFIGS.get(cat_enum, {})
            for key, default_config in defaults.items():
                if key not in configs:
                    configs[key] = default_config["config_value"]
        except ValueError:
            pass

        return configs

    async def create_config(
        self,
        db: AsyncSession,
        category: str,
        config_key: str,
        display_name: str,
        config_value: dict[str, Any],
        description: str | None = None,
        value_type: str = "object",
        validation_schema: dict[str, Any] | None = None,
        organization_id: UUID | None = None,
        created_by: UUID | None = None,
    ) -> AIConfig:
        """Create a new configuration.

        Args:
            db: Database session
            category: Configuration category
            config_key: Configuration key
            display_name: Human-readable name
            config_value: Configuration value
            description: Optional description
            value_type: Type of value for UI rendering
            validation_schema: Optional JSON Schema for validation
            organization_id: Optional organization ID
            created_by: User ID who created this config

        Returns:
            Created AIConfig instance
        """
        config = AIConfig(
            category=category,
            config_key=config_key,
            display_name=display_name,
            description=description,
            config_value=config_value,
            value_type=value_type,
            validation_schema=validation_schema,
            organization_id=organization_id,
            created_by=created_by,
            updated_by=created_by,
        )
        db.add(config)
        await db.commit()
        await db.refresh(config)

        # Create audit entry
        audit = AIConfigAudit(
            config_id=config.id,
            previous_value=None,
            new_value=config_value,
            change_reason="Initial creation",
            changed_by=created_by,
        )
        db.add(audit)
        await db.commit()

        logger.info(f"Created AI config: {category}/{config_key}")
        return config

    async def update_config(
        self,
        db: AsyncSession,
        config_id: UUID,
        config_value: dict[str, Any] | None = None,
        display_name: str | None = None,
        description: str | None = None,
        value_type: str | None = None,
        validation_schema: dict[str, Any] | None = None,
        is_active: bool | None = None,
        updated_by: UUID | None = None,
        change_reason: str | None = None,
    ) -> AIConfig | None:
        """Update an existing configuration.

        Args:
            db: Database session
            config_id: ID of config to update
            config_value: New configuration value
            display_name: New display name
            description: New description
            value_type: New value type
            validation_schema: New validation schema
            is_active: New active status
            updated_by: User ID who updated this config
            change_reason: Reason for the change

        Returns:
            Updated AIConfig or None if not found
        """
        stmt = select(AIConfig).where(AIConfig.id == config_id)
        result = await db.execute(stmt)
        config = result.scalar_one_or_none()

        if not config:
            return None

        previous_value = config.config_value

        # Update fields if provided
        if config_value is not None:
            config.config_value = config_value
        if display_name is not None:
            config.display_name = display_name
        if description is not None:
            config.description = description
        if value_type is not None:
            config.value_type = value_type
        if validation_schema is not None:
            config.validation_schema = validation_schema
        if is_active is not None:
            config.is_active = is_active
        if updated_by is not None:
            config.updated_by = updated_by

        await db.commit()
        await db.refresh(config)

        # Create audit entry if value changed
        if config_value is not None and previous_value != config_value:
            audit = AIConfigAudit(
                config_id=config.id,
                previous_value=previous_value,
                new_value=config_value,
                change_reason=change_reason,
                changed_by=updated_by,
            )
            db.add(audit)
            await db.commit()

        logger.info(f"Updated AI config: {config.category}/{config.config_key}")
        return config

    async def delete_config(
        self,
        db: AsyncSession,
        config_id: UUID,
    ) -> bool:
        """Delete a configuration (soft delete by setting is_active=False).

        Args:
            db: Database session
            config_id: ID of config to delete

        Returns:
            True if deleted, False if not found
        """
        stmt = select(AIConfig).where(AIConfig.id == config_id)
        result = await db.execute(stmt)
        config = result.scalar_one_or_none()

        if not config:
            return False

        config.is_active = False
        await db.commit()

        logger.info(f"Soft deleted AI config: {config.category}/{config.config_key}")
        return True

    async def list_configs(
        self,
        db: AsyncSession,
        category: str | None = None,
        organization_id: UUID | None = None,
        include_inactive: bool = False,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[AIConfig], int]:
        """List configurations with optional filtering.

        Args:
            db: Database session
            category: Optional category filter
            organization_id: Optional organization filter
            include_inactive: Include inactive configs
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Tuple of (configs list, total count)
        """
        # Build base query
        conditions = []
        if category:
            conditions.append(AIConfig.category == category)
        if organization_id is not None:
            conditions.append(AIConfig.organization_id == organization_id)
        if not include_inactive:
            conditions.append(AIConfig.is_active.is_(True))

        # Count total
        count_stmt = select(AIConfig)
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        count_result = await db.execute(count_stmt)
        total = len(count_result.scalars().all())

        # Get paginated results
        stmt = select(AIConfig).order_by(AIConfig.category, AIConfig.config_key)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(stmt)
        configs = list(result.scalars().all())

        return configs, total

    async def get_audit_log(
        self,
        db: AsyncSession,
        config_id: UUID,
        limit: int = 50,
    ) -> list[AIConfigAudit]:
        """Get audit log for a configuration.

        Args:
            db: Database session
            config_id: ID of config
            limit: Maximum number of entries

        Returns:
            List of audit entries, most recent first
        """
        stmt = (
            select(AIConfigAudit)
            .where(AIConfigAudit.config_id == config_id)
            .order_by(AIConfigAudit.changed_at.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def seed_default_configs(
        self,
        db: AsyncSession,
        user_id: UUID | None = None,
    ) -> int:
        """Seed default configurations from DEFAULT_AI_CONFIGS.

        Only creates configs that don't already exist.

        Args:
            db: Database session
            user_id: Optional user ID for audit trail

        Returns:
            Number of configs created
        """
        created_count = 0

        for category, configs in DEFAULT_AI_CONFIGS.items():
            for config_key, config_data in configs.items():
                # Check if config already exists
                existing = await self._get_config_from_db(
                    db, category.value, config_key, None
                )
                if existing:
                    continue

                # Create the config
                config = AIConfig(
                    category=category.value,
                    config_key=config_key,
                    display_name=config_data["display_name"],
                    description=config_data.get("description"),
                    config_value=config_data["config_value"],
                    value_type=config_data.get("value_type", "object"),
                    organization_id=None,
                    created_by=user_id,
                    updated_by=user_id,
                )
                db.add(config)
                created_count += 1

        await db.commit()
        logger.info(f"Seeded {created_count} default AI configurations")
        return created_count

    async def _get_config_from_db(
        self,
        db: AsyncSession,
        category: str,
        config_key: str,
        organization_id: UUID | None,
    ) -> AIConfig | None:
        """Internal method to get config from database."""
        if organization_id is None:
            stmt = select(AIConfig).where(
                and_(
                    AIConfig.category == category,
                    AIConfig.config_key == config_key,
                    AIConfig.organization_id.is_(None),
                    AIConfig.is_active.is_(True),
                )
            )
        else:
            stmt = select(AIConfig).where(
                and_(
                    AIConfig.category == category,
                    AIConfig.config_key == config_key,
                    AIConfig.organization_id == organization_id,
                    AIConfig.is_active.is_(True),
                )
            )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    def _get_default_config(
        self,
        category: str,
        config_key: str,
    ) -> dict[str, Any] | None:
        """Get default config value from hardcoded defaults."""
        try:
            cat_enum = AIConfigCategory(category)
            category_defaults = DEFAULT_AI_CONFIGS.get(cat_enum, {})
            config_data = category_defaults.get(config_key)
            if config_data:
                return config_data["config_value"]
        except ValueError:
            pass
        return None


# Singleton instance
ai_config_service = AIConfigService()
