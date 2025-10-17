"""Developer due diligence checklist service."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.developer_checklists import (
    ChecklistCategory,
    ChecklistPriority,
    ChecklistStatus,
    DeveloperChecklistTemplate,
    DeveloperPropertyChecklist,
)

ChecklistTemplateInput = Mapping[str, object]


DEFAULT_TEMPLATE_DEFINITIONS: Tuple[ChecklistTemplateInput, ...] = (
    {
        "development_scenario": "raw_land",
        "category": "title_verification",
        "item_title": "Confirm land ownership and title status",
        "item_description": "Retrieve SLA title extracts and confirm that there are no caveats or encumbrances on the parcel.",
        "priority": "critical",
        "typical_duration_days": 5,
        "requires_professional": True,
        "professional_type": "Conveyancing lawyer",
        "display_order": 10,
    },
    {
        "development_scenario": "raw_land",
        "category": "zoning_compliance",
        "item_title": "Validate URA master plan parameters",
        "item_description": "Cross-check zoning, plot ratio, and allowable uses against intended development outcomes.",
        "priority": "critical",
        "typical_duration_days": 4,
        "requires_professional": False,
        "professional_type": None,
        "display_order": 20,
    },
    {
        "development_scenario": "raw_land",
        "category": "environmental_assessment",
        "item_title": "Screen for environmental and soil constraints",
        "item_description": "Review PUB drainage, flood susceptibility, soil conditions, and adjacent environmental protections.",
        "priority": "high",
        "typical_duration_days": 7,
        "requires_professional": True,
        "professional_type": "Geotechnical engineer",
        "display_order": 30,
    },
    {
        "development_scenario": "raw_land",
        "category": "access_rights",
        "item_title": "Confirm legal site access and right-of-way",
        "item_description": "Validate ingress/egress arrangements with LTA and adjacent land owners for temporary works.",
        "priority": "medium",
        "typical_duration_days": 6,
        "requires_professional": True,
        "professional_type": "Traffic consultant",
        "display_order": 40,
    },
    {
        "development_scenario": "existing_building",
        "category": "structural_survey",
        "item_title": "Commission structural integrity assessment",
        "item_description": "Carry out intrusive and non-intrusive inspections to determine retrofitting effort.",
        "priority": "critical",
        "typical_duration_days": 14,
        "requires_professional": True,
        "professional_type": "Structural engineer",
        "display_order": 10,
    },
    {
        "development_scenario": "existing_building",
        "category": "utility_capacity",
        "item_title": "Benchmark utility upgrade requirements",
        "item_description": "Review existing electrical, water, and gas supply against target load profiles.",
        "priority": "high",
        "typical_duration_days": 5,
        "requires_professional": True,
        "professional_type": "M&E engineer",
        "display_order": 20,
    },
    {
        "development_scenario": "existing_building",
        "category": "zoning_compliance",
        "item_title": "Validate change-of-use requirements",
        "item_description": "Confirm URA and BCA approvals required for intended repositioning program.",
        "priority": "high",
        "typical_duration_days": 3,
        "requires_professional": False,
        "professional_type": None,
        "display_order": 30,
    },
    {
        "development_scenario": "existing_building",
        "category": "environmental_assessment",
        "item_title": "Assess asbestos and hazardous material presence",
        "item_description": "Undertake sampling programme before any strip-out or demolition work proceeds.",
        "priority": "medium",
        "typical_duration_days": 10,
        "requires_professional": True,
        "professional_type": "Environmental consultant",
        "display_order": 40,
    },
    {
        "development_scenario": "heritage_property",
        "category": "heritage_constraints",
        "item_title": "Confirm conservation requirements with URA",
        "item_description": "Document façade retention, material preservation, and permissible alteration scope.",
        "priority": "critical",
        "typical_duration_days": 7,
        "requires_professional": True,
        "professional_type": "Heritage architect",
        "display_order": 10,
    },
    {
        "development_scenario": "heritage_property",
        "category": "structural_survey",
        "item_title": "Heritage structural reinforcement study",
        "item_description": "Evaluate load paths and necessary strengthening to achieve code compliance without damaging heritage elements.",
        "priority": "high",
        "typical_duration_days": 12,
        "requires_professional": True,
        "professional_type": "Structural engineer",
        "display_order": 20,
    },
    {
        "development_scenario": "heritage_property",
        "category": "zoning_compliance",
        "item_title": "Assess conservation overlay with planning parameters",
        "item_description": "Check whether conservation overlays restrict development intensity or allowable uses.",
        "priority": "high",
        "typical_duration_days": 5,
        "requires_professional": False,
        "professional_type": None,
        "display_order": 30,
    },
    {
        "development_scenario": "heritage_property",
        "category": "access_rights",
        "item_title": "Coordinate logistics with surrounding stakeholders",
        "item_description": "Identify staging areas, hoarding approvals, and historic streetscape protection measures.",
        "priority": "medium",
        "typical_duration_days": 4,
        "requires_professional": False,
        "professional_type": None,
        "display_order": 40,
    },
    {
        "development_scenario": "underused_asset",
        "category": "utility_capacity",
        "item_title": "Determine retrofit M&E upgrade scope",
        "item_description": "Right-size mechanical plant, vertical transportation, and ICT backbone for the new programme.",
        "priority": "high",
        "typical_duration_days": 8,
        "requires_professional": True,
        "professional_type": "Building services engineer",
        "display_order": 10,
    },
    {
        "development_scenario": "underused_asset",
        "category": "environmental_assessment",
        "item_title": "Perform indoor environmental quality audit",
        "item_description": "Quantify remediation required for mould, humidity, and ventilation gaps from prolonged underuse.",
        "priority": "medium",
        "typical_duration_days": 6,
        "requires_professional": True,
        "professional_type": "Environmental specialist",
        "display_order": 20,
    },
    {
        "development_scenario": "underused_asset",
        "category": "access_rights",
        "item_title": "Validate access control and fire egress updates",
        "item_description": "Ensure adaptive reuse complies with SCDF requirements and workplace safety codes.",
        "priority": "high",
        "typical_duration_days": 5,
        "requires_professional": True,
        "professional_type": "Fire engineer",
        "display_order": 30,
    },
    {
        "development_scenario": "mixed_use_redevelopment",
        "category": "zoning_compliance",
        "item_title": "Confirm mixed-use allowable combination",
        "item_description": "Reconcile residential, commercial, and retail programme with masterplan mix and strata limitations.",
        "priority": "critical",
        "typical_duration_days": 6,
        "requires_professional": False,
        "professional_type": None,
        "display_order": 10,
    },
    {
        "development_scenario": "mixed_use_redevelopment",
        "category": "utility_capacity",
        "item_title": "Integrate district cooling and energy sharing options",
        "item_description": "Assess utility providers' capacity and incentives for precinct-scale systems.",
        "priority": "high",
        "typical_duration_days": 9,
        "requires_professional": True,
        "professional_type": "Energy consultant",
        "display_order": 20,
    },
    {
        "development_scenario": "mixed_use_redevelopment",
        "category": "structural_survey",
        "item_title": "Phase-by-phase structural staging plan",
        "item_description": "Evaluate demolition, retention, and staging needed to keep operations running during redevelopment.",
        "priority": "high",
        "typical_duration_days": 15,
        "requires_professional": True,
        "professional_type": "Structural engineer",
        "display_order": 30,
    },
    {
        "development_scenario": "mixed_use_redevelopment",
        "category": "heritage_constraints",
        "item_title": "Coordinate heritage façade integration",
        "item_description": "Identify conserved elements that must be retained and methods to blend with new podium.",
        "priority": "medium",
        "typical_duration_days": 10,
        "requires_professional": True,
        "professional_type": "Conservation architect",
        "display_order": 40,
    },
)


def _coerce_category(value: object) -> ChecklistCategory:
    if isinstance(value, ChecklistCategory):
        return value
    if isinstance(value, str):
        return ChecklistCategory(value)
    raise ValueError(f"Unsupported checklist category value: {value!r}")


def _coerce_priority(value: object) -> ChecklistPriority:
    if isinstance(value, ChecklistPriority):
        return value
    if isinstance(value, str):
        return ChecklistPriority(value)
    raise ValueError(f"Unsupported checklist priority value: {value!r}")


def _normalise_definition(definition: ChecklistTemplateInput) -> Dict[str, object]:
    scenario = str(definition.get("development_scenario", "")).strip()
    if not scenario:
        raise ValueError("development_scenario is required")

    item_title = str(definition.get("item_title", "")).strip()
    if not item_title:
        raise ValueError("item_title is required")

    category = _coerce_category(definition.get("category"))
    priority = _coerce_priority(definition.get("priority"))
    item_description_value = definition.get("item_description")
    typical_duration_value = definition.get("typical_duration_days")
    professional_type_value = definition.get("professional_type")
    requires_professional_value = definition.get("requires_professional")
    display_order_value = definition.get("display_order")

    item_description = (
        str(item_description_value).strip()
        if item_description_value is not None
        else None
    )
    if item_description == "":
        item_description = None

    if typical_duration_value is None or typical_duration_value == "":
        typical_duration = None
    else:
        typical_duration = int(typical_duration_value)

    requires_professional = bool(requires_professional_value)

    professional_type = (
        str(professional_type_value).strip()
        if professional_type_value is not None
        else None
    )
    if professional_type == "":
        professional_type = None
    if not requires_professional:
        professional_type = None

    display_order = None
    if display_order_value is not None and display_order_value != "":
        display_order = int(display_order_value)

    return {
        "development_scenario": scenario,
        "category": category,
        "item_title": item_title,
        "item_description": item_description,
        "priority": priority,
        "typical_duration_days": typical_duration,
        "requires_professional": requires_professional,
        "professional_type": professional_type,
        "display_order": display_order,
    }


class DeveloperChecklistService:
    """Service for managing developer due diligence checklists."""

    _BOOTSTRAPPED_DIALECTS: set[str] = set()

    @staticmethod
    async def _ensure_tables(session: AsyncSession) -> None:
        """Create checklist tables if the current database has not yet bootstrapped them."""

        connection = await session.connection()
        dialect_name = connection.dialect.name

        if dialect_name in DeveloperChecklistService._BOOTSTRAPPED_DIALECTS:
            return

        if dialect_name == "sqlite":
            await connection.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS developer_checklist_templates (
                        id TEXT PRIMARY KEY,
                        development_scenario TEXT NOT NULL,
                        category TEXT NOT NULL,
                        item_title TEXT NOT NULL,
                        item_description TEXT,
                        priority TEXT NOT NULL,
                        typical_duration_days INTEGER,
                        requires_professional INTEGER NOT NULL DEFAULT 0,
                        professional_type TEXT,
                        display_order INTEGER DEFAULT 0,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
            )
            await connection.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS developer_property_checklists (
                        id TEXT PRIMARY KEY,
                        property_id TEXT NOT NULL,
                        template_id TEXT,
                        development_scenario TEXT NOT NULL,
                        category TEXT NOT NULL,
                        item_title TEXT NOT NULL,
                        item_description TEXT,
                        priority TEXT NOT NULL,
                        status TEXT NOT NULL,
                        assigned_to TEXT,
                        due_date TEXT,
                        completed_date TEXT,
                        completed_by TEXT,
                        notes TEXT,
                        metadata TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
            )
        else:

            def _create(connection_) -> None:
                DeveloperChecklistTemplate.__table__.create(
                    connection_, checkfirst=True
                )
                DeveloperPropertyChecklist.__table__.create(
                    connection_, checkfirst=True
                )

            try:
                await connection.run_sync(_create)
            except Exception:  # pragma: no cover - align with metadata bootstrap
                pass

        DeveloperChecklistService._BOOTSTRAPPED_DIALECTS.add(dialect_name)

    @staticmethod
    async def list_templates(
        session: AsyncSession, development_scenario: Optional[str] = None
    ) -> List[DeveloperChecklistTemplate]:
        await DeveloperChecklistService._ensure_tables(session)
        query = select(DeveloperChecklistTemplate)
        if development_scenario:
            query = query.where(
                DeveloperChecklistTemplate.development_scenario == development_scenario
            )
        query = query.order_by(
            DeveloperChecklistTemplate.development_scenario,
            DeveloperChecklistTemplate.display_order,
            DeveloperChecklistTemplate.item_title,
        )
        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def _next_display_order(
        session: AsyncSession, development_scenario: str
    ) -> int:
        result = await session.execute(
            select(DeveloperChecklistTemplate.display_order)
            .where(
                DeveloperChecklistTemplate.development_scenario == development_scenario
            )
            .order_by(DeveloperChecklistTemplate.display_order.desc())
            .limit(1)
        )
        current_max = result.scalar_one_or_none() or 0
        # Leave a bit of spacing so manual inserts can slot in between defaults.
        return current_max + 10

    @staticmethod
    async def _template_exists(
        session: AsyncSession,
        development_scenario: str,
        item_title: str,
        exclude_id: Optional[UUID] = None,
    ) -> bool:
        query = select(DeveloperChecklistTemplate.id).where(
            DeveloperChecklistTemplate.development_scenario == development_scenario,
            func.lower(DeveloperChecklistTemplate.item_title) == item_title.lower(),
        )
        if exclude_id:
            query = query.where(DeveloperChecklistTemplate.id != exclude_id)
        result = await session.execute(query)
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def create_template(
        session: AsyncSession, payload: ChecklistTemplateInput
    ) -> DeveloperChecklistTemplate:
        await DeveloperChecklistService._ensure_tables(session)
        definition = _normalise_definition(payload)
        scenario = definition["development_scenario"]
        title = definition["item_title"]

        if await DeveloperChecklistService._template_exists(session, scenario, title):
            raise ValueError(
                f"Template '{title}' already exists for scenario '{scenario}'."
            )

        display_order = definition.get("display_order")
        if display_order is None:
            display_order = await DeveloperChecklistService._next_display_order(
                session, scenario
            )
            definition["display_order"] = display_order

        template = DeveloperChecklistTemplate(**definition)  # type: ignore[arg-type]
        session.add(template)
        await session.flush()
        return template

    @staticmethod
    async def update_template(
        session: AsyncSession, template_id: UUID, payload: ChecklistTemplateInput
    ) -> Optional[DeveloperChecklistTemplate]:
        await DeveloperChecklistService._ensure_tables(session)
        result = await session.execute(
            select(DeveloperChecklistTemplate).where(
                DeveloperChecklistTemplate.id == template_id
            )
        )
        template = result.scalar_one_or_none()
        if not template:
            return None

        current_state: Dict[str, object] = {
            "development_scenario": template.development_scenario,
            "category": template.category,
            "item_title": template.item_title,
            "item_description": template.item_description,
            "priority": template.priority,
            "typical_duration_days": template.typical_duration_days,
            "requires_professional": template.requires_professional,
            "professional_type": template.professional_type,
            "display_order": template.display_order,
        }
        merged: Dict[str, object] = {**current_state, **dict(payload)}
        definition = _normalise_definition(merged)

        scenario = definition["development_scenario"]
        title = definition["item_title"]

        if await DeveloperChecklistService._template_exists(
            session, scenario, title, exclude_id=template_id
        ):
            raise ValueError(
                f"Template '{title}' already exists for scenario '{scenario}'."
            )

        for field, value in definition.items():
            if field == "display_order" and value is None:
                continue
            setattr(template, field, value)

        if definition.get("display_order") is None:
            template.display_order = (
                await DeveloperChecklistService._next_display_order(session, scenario)
            )

        await session.flush()
        return template

    @staticmethod
    async def delete_template(session: AsyncSession, template_id: UUID) -> bool:
        await DeveloperChecklistService._ensure_tables(session)
        result = await session.execute(
            select(DeveloperChecklistTemplate).where(
                DeveloperChecklistTemplate.id == template_id
            )
        )
        template = result.scalar_one_or_none()
        if not template:
            return False
        await session.delete(template)
        await session.flush()
        return True

    @staticmethod
    async def bulk_upsert_templates(
        session: AsyncSession,
        definitions: Sequence[ChecklistTemplateInput],
        *,
        replace_existing: bool = False,
    ) -> Dict[str, int]:
        if not definitions:
            return {"created": 0, "updated": 0, "deleted": 0}

        await DeveloperChecklistService._ensure_tables(session)
        existing_result = await session.execute(select(DeveloperChecklistTemplate))
        existing_templates = list(existing_result.scalars().all())
        existing_index: Dict[Tuple[str, str], DeveloperChecklistTemplate] = {
            (
                template.development_scenario,
                template.item_title.strip().lower(),
            ): template
            for template in existing_templates
        }
        max_display_order: Dict[str, int] = defaultdict(int)
        for template in existing_templates:
            display_order = template.display_order or 0
            if display_order > max_display_order[template.development_scenario]:
                max_display_order[template.development_scenario] = display_order

        created = 0
        updated = 0
        scenarios_in_payload: set[str] = set()
        incoming_keys: set[Tuple[str, str]] = set()

        for raw_definition in definitions:
            definition = _normalise_definition(raw_definition)
            scenario = definition["development_scenario"]
            title_key = definition["item_title"].lower()

            key = (scenario, title_key)
            incoming_keys.add(key)
            scenarios_in_payload.add(scenario)

            display_order = definition.get("display_order")
            if display_order is None or display_order <= 0:
                next_order = max_display_order[scenario] + 10
                max_display_order[scenario] = next_order
                definition["display_order"] = next_order
            else:
                if display_order > max_display_order[scenario]:
                    max_display_order[scenario] = int(display_order)

            existing = existing_index.get(key)
            if existing:
                changed = False
                for field, value in definition.items():
                    if getattr(existing, field) != value:
                        setattr(existing, field, value)
                        changed = True
                if changed:
                    updated += 1
            else:
                template = DeveloperChecklistTemplate(
                    **definition  # type: ignore[arg-type]
                )
                session.add(template)
                created += 1
                existing_index[key] = template

        deleted = 0
        if replace_existing and scenarios_in_payload:
            for template in existing_templates:
                scenario = template.development_scenario
                key = (scenario, template.item_title.strip().lower())
                if scenario in scenarios_in_payload and key not in incoming_keys:
                    await session.delete(template)
                    deleted += 1

        if created or updated or deleted:
            await session.flush()

        return {"created": created, "updated": updated, "deleted": deleted}

    @staticmethod
    async def ensure_templates_seeded(session: AsyncSession) -> bool:
        await DeveloperChecklistService._ensure_tables(session)
        result = await DeveloperChecklistService.bulk_upsert_templates(
            session, DEFAULT_TEMPLATE_DEFINITIONS, replace_existing=False
        )
        return bool(result["created"] or result["updated"])

    @staticmethod
    async def get_templates_for_scenario(
        session: AsyncSession,
        development_scenario: str,
    ) -> List[DeveloperChecklistTemplate]:
        """Get all checklist templates for a development scenario."""
        result = await session.execute(
            select(DeveloperChecklistTemplate)
            .where(
                DeveloperChecklistTemplate.development_scenario == development_scenario
            )
            .order_by(DeveloperChecklistTemplate.display_order)
        )
        return list(result.scalars().all())

    @staticmethod
    async def auto_populate_checklist(
        session: AsyncSession,
        property_id: UUID,
        development_scenarios: List[str],
        assigned_to: Optional[UUID] = None,
    ) -> List[DeveloperPropertyChecklist]:
        """
        Auto-populate checklist items for a property based on development scenarios.

        Creates property-specific checklist items from templates for each selected scenario.
        """
        created_items: List[DeveloperPropertyChecklist] = []

        await DeveloperChecklistService._ensure_tables(session)
        existing_items_result = await session.execute(
            select(DeveloperPropertyChecklist).where(
                DeveloperPropertyChecklist.property_id == property_id
            )
        )
        existing_items = list(existing_items_result.scalars().all())
        existing_template_ids = {
            item.template_id for item in existing_items if item.template_id is not None
        }
        existing_titles = {
            (item.development_scenario, item.item_title.strip().lower())
            for item in existing_items
        }

        for scenario in development_scenarios:
            templates = await DeveloperChecklistService.get_templates_for_scenario(
                session, scenario
            )

            for template in templates:
                key = (template.development_scenario, template.item_title.lower())
                if template.id in existing_template_ids or key in existing_titles:
                    continue

                due_date = None
                if template.typical_duration_days:
                    due_date = (
                        datetime.utcnow()
                        + timedelta(days=template.typical_duration_days)
                    ).date()

                checklist_item = DeveloperPropertyChecklist(
                    property_id=property_id,
                    template_id=template.id,
                    development_scenario=template.development_scenario,
                    category=template.category,
                    item_title=template.item_title,
                    item_description=template.item_description,
                    priority=template.priority,
                    status=ChecklistStatus.PENDING,
                    assigned_to=assigned_to,
                    due_date=due_date,
                    metadata={
                        "requires_professional": template.requires_professional,
                        "professional_type": template.professional_type,
                        "typical_duration_days": template.typical_duration_days,
                        "display_order": template.display_order,
                    },
                )
                session.add(checklist_item)
                created_items.append(checklist_item)

                existing_template_ids.add(template.id)
                existing_titles.add(key)

        if created_items:
            await session.flush()
        return created_items

    @staticmethod
    async def get_property_checklist(
        session: AsyncSession,
        property_id: UUID,
        development_scenario: Optional[str] = None,
        status: Optional[ChecklistStatus] = None,
    ) -> List[DeveloperPropertyChecklist]:
        """Get checklist items for a property, optionally filtered by scenario and status."""
        await DeveloperChecklistService._ensure_tables(session)
        query = (
            select(DeveloperPropertyChecklist)
            .options(selectinload(DeveloperPropertyChecklist.template))
            .where(DeveloperPropertyChecklist.property_id == property_id)
        )

        if development_scenario:
            query = query.where(
                DeveloperPropertyChecklist.development_scenario == development_scenario
            )

        if status:
            query = query.where(DeveloperPropertyChecklist.status == status)

        query = query.order_by(
            DeveloperPropertyChecklist.development_scenario,
            DeveloperPropertyChecklist.category,
            DeveloperPropertyChecklist.created_at,
        )

        result = await session.execute(query)
        items = list(result.scalars().all())

        def _display_order_for(item: DeveloperPropertyChecklist) -> int:
            metadata = item.metadata or {}
            template_order = getattr(item.template, "display_order", None)
            metadata_order = metadata.get("display_order")

            for value in (template_order, metadata_order):
                if value is None:
                    continue
                if isinstance(value, int):
                    return value
                if isinstance(value, float) and value.is_integer():
                    return int(value)
                if isinstance(value, str):
                    try:
                        return int(value)
                    except ValueError:
                        continue
            return 0

        items.sort(
            key=lambda item: (
                item.development_scenario or "",
                _display_order_for(item),
                item.item_title.lower(),
                item.created_at or datetime.min,
            )
        )
        return items

    @staticmethod
    def format_property_checklist_items(
        items: Iterable[DeveloperPropertyChecklist],
    ) -> List[dict[str, object]]:
        """Serialise checklist records with template-aware fallbacks."""

        formatted: List[dict[str, object]] = []
        for item in items:
            payload = item.to_dict()
            metadata = payload.get("metadata") or {}

            requires_professional = metadata.get("requires_professional")
            professional_type = metadata.get("professional_type")
            typical_duration_days = metadata.get("typical_duration_days")
            display_order = metadata.get("display_order")

            template = getattr(item, "template", None)
            if requires_professional is None and template is not None:
                requires_professional = template.requires_professional
            if professional_type is None and template is not None:
                professional_type = template.professional_type
            if typical_duration_days is None and template is not None:
                typical_duration_days = template.typical_duration_days
            if display_order is None and template is not None:
                display_order = template.display_order

            payload["requires_professional"] = bool(requires_professional)
            payload["professional_type"] = professional_type
            payload["typical_duration_days"] = typical_duration_days
            payload["display_order"] = display_order

            if not payload["requires_professional"]:
                payload["professional_type"] = None

            formatted.append(payload)

        return formatted

    @staticmethod
    async def update_checklist_status(
        session: AsyncSession,
        checklist_id: UUID,
        status: ChecklistStatus,
        completed_by: Optional[UUID] = None,
        notes: Optional[str] = None,
    ) -> Optional[DeveloperPropertyChecklist]:
        """Update the status of a checklist item."""
        await DeveloperChecklistService._ensure_tables(session)
        result = await session.execute(
            select(DeveloperPropertyChecklist).where(
                DeveloperPropertyChecklist.id == checklist_id
            )
        )
        checklist_item = result.scalar_one_or_none()

        if not checklist_item:
            return None

        checklist_item.status = status

        if status == ChecklistStatus.COMPLETED:
            checklist_item.completed_date = datetime.utcnow().date()
            if completed_by:
                checklist_item.completed_by = completed_by

        if notes:
            checklist_item.notes = notes

        await session.flush()
        return checklist_item

    @staticmethod
    async def get_checklist_summary(
        session: AsyncSession,
        property_id: UUID,
    ) -> dict:
        """Get a summary of checklist completion status for a property."""
        await DeveloperChecklistService._ensure_tables(session)
        items = await DeveloperChecklistService.get_property_checklist(
            session, property_id
        )

        totals = {
            "total": len(items),
            "completed": 0,
            "in_progress": 0,
            "pending": 0,
            "not_applicable": 0,
        }

        by_category: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {
                "total": 0,
                "completed": 0,
                "in_progress": 0,
                "pending": 0,
                "not_applicable": 0,
            }
        )

        for item in items:
            status = item.status
            if status == ChecklistStatus.COMPLETED:
                totals["completed"] += 1
            elif status == ChecklistStatus.IN_PROGRESS:
                totals["in_progress"] += 1
            elif status == ChecklistStatus.NOT_APPLICABLE:
                totals["not_applicable"] += 1
            else:
                totals["pending"] += 1

            category_key = item.category.value
            by_category[category_key]["total"] += 1
            if status == ChecklistStatus.COMPLETED:
                by_category[category_key]["completed"] += 1
            elif status == ChecklistStatus.IN_PROGRESS:
                by_category[category_key]["in_progress"] += 1
            elif status == ChecklistStatus.NOT_APPLICABLE:
                by_category[category_key]["not_applicable"] += 1
            else:
                by_category[category_key]["pending"] += 1

        completion_percentage = (
            int((totals["completed"] / totals["total"]) * 100)
            if totals["total"] > 0
            else 0
        )

        by_category_serialised = {
            category: dict(stats) for category, stats in by_category.items()
        }

        return {
            "property_id": str(property_id),
            "total": totals["total"],
            "completed": totals["completed"],
            "in_progress": totals["in_progress"],
            "pending": totals["pending"],
            "not_applicable": totals["not_applicable"],
            "completion_percentage": completion_percentage,
            "by_category_status": by_category_serialised,
        }


__all__ = [
    "DEFAULT_TEMPLATE_DEFINITIONS",
    "DeveloperChecklistService",
]
