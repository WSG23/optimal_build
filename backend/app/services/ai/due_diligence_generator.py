"""Phase 3.1: Automated Due Diligence Checklist.

Generates context-aware DD checklists and automates where possible.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business_performance import AgentDeal, DealType
from app.models.property import Property

logger = logging.getLogger(__name__)


class DDItemStatus(str, Enum):
    """Status of a DD checklist item."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    NOT_APPLICABLE = "not_applicable"
    BLOCKED = "blocked"


class DDItemPriority(str, Enum):
    """Priority of a DD item."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DDCategory(str, Enum):
    """Categories of due diligence."""

    LEGAL = "legal"
    TECHNICAL = "technical"
    FINANCIAL = "financial"
    REGULATORY = "regulatory"
    ENVIRONMENTAL = "environmental"
    COMMERCIAL = "commercial"


@dataclass
class DDItem:
    """A single due diligence item."""

    id: str
    category: DDCategory
    name: str
    description: str
    status: DDItemStatus = DDItemStatus.PENDING
    priority: DDItemPriority = DDItemPriority.MEDIUM
    is_auto_completable: bool = False
    auto_complete_source: str | None = None
    completed_data: dict[str, Any] | None = None
    notes: str | None = None
    assignee: str | None = None
    due_date: datetime | None = None
    dependencies: list[str] = field(default_factory=list)


@dataclass
class DDRecommendation:
    """An AI-generated recommendation for DD."""

    title: str
    description: str
    priority: DDItemPriority
    action_items: list[str]


@dataclass
class DDChecklist:
    """Complete due diligence checklist."""

    id: str
    deal_id: str
    deal_title: str
    deal_type: str
    asset_type: str
    created_at: datetime
    items: list[DDItem]
    recommendations: list[DDRecommendation]
    completion_percentage: float
    estimated_days_to_complete: int


# Base checklist templates by deal type
DD_TEMPLATES = {
    DealType.BUY_SIDE: {
        DDCategory.LEGAL: [
            (
                "Title Search",
                "Verify clean title with no encumbrances",
                DDItemPriority.CRITICAL,
                True,
                "SLA",
            ),
            (
                "Encumbrance Check",
                "Check for mortgages, charges, caveats",
                DDItemPriority.CRITICAL,
                True,
                "SLA",
            ),
            (
                "Lease Review",
                "Review all tenancy agreements",
                DDItemPriority.HIGH,
                False,
                None,
            ),
            (
                "Legal Opinion",
                "Obtain legal opinion on title",
                DDItemPriority.CRITICAL,
                False,
                None,
            ),
            (
                "Power of Attorney",
                "Verify seller's authority to sell",
                DDItemPriority.HIGH,
                False,
                None,
            ),
            (
                "Strata Title Status",
                "Verify strata subdivision if applicable",
                DDItemPriority.MEDIUM,
                False,
                None,
            ),
            (
                "IRAS Tax Clearance",
                "Obtain property tax clearance",
                DDItemPriority.HIGH,
                True,
                "IRAS",
            ),
            (
                "Pending Litigation",
                "Check for any pending legal matters",
                DDItemPriority.HIGH,
                False,
                None,
            ),
        ],
        DDCategory.TECHNICAL: [
            (
                "Building Inspection",
                "Conduct physical building inspection",
                DDItemPriority.CRITICAL,
                False,
                None,
            ),
            (
                "M&E Assessment",
                "Assess mechanical and electrical systems",
                DDItemPriority.HIGH,
                False,
                None,
            ),
            (
                "Structural Survey",
                "Structural integrity assessment",
                DDItemPriority.HIGH,
                False,
                None,
            ),
            (
                "As-Built Plans Review",
                "Review approved plans vs as-built",
                DDItemPriority.MEDIUM,
                False,
                None,
            ),
            (
                "Fire Safety Compliance",
                "Verify FSC and fire systems",
                DDItemPriority.HIGH,
                False,
                None,
            ),
            (
                "Lift Assessment",
                "Assess lift condition and compliance",
                DDItemPriority.MEDIUM,
                False,
                None,
            ),
        ],
        DDCategory.FINANCIAL: [
            (
                "Tenancy Schedule",
                "Verify rent roll and lease terms",
                DDItemPriority.CRITICAL,
                False,
                None,
            ),
            (
                "Operating Expenses",
                "Analyze historical operating costs",
                DDItemPriority.HIGH,
                False,
                None,
            ),
            (
                "Service Charges",
                "Verify service charge budgets",
                DDItemPriority.MEDIUM,
                False,
                None,
            ),
            (
                "Arrears Analysis",
                "Check for tenant arrears",
                DDItemPriority.HIGH,
                False,
                None,
            ),
            (
                "Income Verification",
                "Verify historical income statements",
                DDItemPriority.HIGH,
                False,
                None,
            ),
            (
                "Capex History",
                "Review historical capital expenditure",
                DDItemPriority.MEDIUM,
                False,
                None,
            ),
        ],
        DDCategory.REGULATORY: [
            (
                "Zoning Confirmation",
                "Confirm URA zoning and permitted use",
                DDItemPriority.CRITICAL,
                True,
                "URA",
            ),
            (
                "Planning Approvals",
                "Review all planning approvals",
                DDItemPriority.HIGH,
                True,
                "URA",
            ),
            (
                "Outstanding Applications",
                "Check for pending applications",
                DDItemPriority.HIGH,
                True,
                "URA",
            ),
            (
                "GFA Compliance",
                "Verify approved vs built GFA",
                DDItemPriority.HIGH,
                False,
                None,
            ),
            (
                "DC/BP Compliance",
                "Review DC and BP approvals",
                DDItemPriority.MEDIUM,
                False,
                None,
            ),
            (
                "TOP/CSC Status",
                "Verify TOP and CSC status",
                DDItemPriority.HIGH,
                True,
                "BCA",
            ),
        ],
        DDCategory.ENVIRONMENTAL: [
            (
                "Phase I ESA",
                "Environmental site assessment",
                DDItemPriority.MEDIUM,
                False,
                None,
            ),
            (
                "Contamination Check",
                "Check for soil/groundwater contamination",
                DDItemPriority.MEDIUM,
                False,
                None,
            ),
            (
                "Asbestos Survey",
                "Check for asbestos-containing materials",
                DDItemPriority.HIGH,
                False,
                None,
            ),
            (
                "Hazardous Materials",
                "Identify hazardous materials",
                DDItemPriority.MEDIUM,
                False,
                None,
            ),
        ],
        DDCategory.COMMERCIAL: [
            (
                "Market Comparable Analysis",
                "Analyze comparable transactions",
                DDItemPriority.HIGH,
                False,
                None,
            ),
            (
                "Tenant Credit Analysis",
                "Assess tenant creditworthiness",
                DDItemPriority.HIGH,
                False,
                None,
            ),
            (
                "Competition Assessment",
                "Analyze competing properties",
                DDItemPriority.MEDIUM,
                False,
                None,
            ),
            (
                "Vacancy Analysis",
                "Assess market vacancy trends",
                DDItemPriority.MEDIUM,
                False,
                None,
            ),
        ],
    },
    DealType.LEASE: {
        DDCategory.LEGAL: [
            (
                "Landlord Title",
                "Verify landlord's title to property",
                DDItemPriority.HIGH,
                True,
                "SLA",
            ),
            (
                "Lease Template Review",
                "Review standard lease terms",
                DDItemPriority.HIGH,
                False,
                None,
            ),
            (
                "Negotiated Terms",
                "Document negotiated variations",
                DDItemPriority.MEDIUM,
                False,
                None,
            ),
        ],
        DDCategory.TECHNICAL: [
            (
                "Premises Inspection",
                "Inspect premises condition",
                DDItemPriority.HIGH,
                False,
                None,
            ),
            (
                "Fit-out Assessment",
                "Assess fit-out requirements",
                DDItemPriority.MEDIUM,
                False,
                None,
            ),
            (
                "M&E Capacity",
                "Verify M&E capacity for intended use",
                DDItemPriority.MEDIUM,
                False,
                None,
            ),
        ],
        DDCategory.COMMERCIAL: [
            (
                "Rent Benchmark",
                "Compare rent to market rates",
                DDItemPriority.HIGH,
                False,
                None,
            ),
            (
                "Operating Cost Analysis",
                "Analyze service charges and costs",
                DDItemPriority.MEDIUM,
                False,
                None,
            ),
        ],
    },
}


class DueDiligenceService:
    """Service for generating and managing DD checklists."""

    def __init__(self) -> None:
        """Initialize the DD service."""
        self._initialized = True

    async def generate_checklist(
        self,
        deal_id: str,
        db: AsyncSession,
    ) -> DDChecklist:
        """Generate a context-aware DD checklist for a deal.

        Args:
            deal_id: ID of the deal
            db: Database session

        Returns:
            Generated DDChecklist
        """
        # Fetch deal data
        deal_query = select(AgentDeal).where(AgentDeal.id == deal_id)
        result = await db.execute(deal_query)
        deal = result.scalar_one_or_none()

        if not deal:
            return self._empty_checklist(deal_id)

        # Fetch property data if available
        property_data = None
        if deal.property_id:
            prop_query = select(Property).where(Property.id == deal.property_id)
            prop_result = await db.execute(prop_query)
            property_data = prop_result.scalar_one_or_none()

        # Get base template for deal type
        template = DD_TEMPLATES.get(deal.deal_type, DD_TEMPLATES[DealType.BUY_SIDE])

        # Generate items from template
        items = []
        for category, category_items in template.items():
            for item_tuple in category_items:
                name, description, priority, auto_complete, source = item_tuple
                items.append(
                    DDItem(
                        id=str(uuid4()),
                        category=category,
                        name=name,
                        description=description,
                        priority=priority,
                        is_auto_completable=auto_complete,
                        auto_complete_source=source,
                    )
                )

        # Add conditional items based on property attributes
        conditional_items = self._generate_conditional_items(deal, property_data)
        items.extend(conditional_items)

        # Generate AI recommendations
        recommendations = self._generate_recommendations(deal, property_data, items)

        # Calculate completion
        completed = sum(1 for i in items if i.status == DDItemStatus.COMPLETED)
        completion_pct = (completed / len(items) * 100) if items else 0

        # Estimate days to complete (1 day per critical, 0.5 per high, 0.25 per medium)
        days = sum(
            (
                1
                if i.priority == DDItemPriority.CRITICAL
                else 0.5 if i.priority == DDItemPriority.HIGH else 0.25
            )
            for i in items
            if i.status != DDItemStatus.COMPLETED
        )

        return DDChecklist(
            id=str(uuid4()),
            deal_id=deal_id,
            deal_title=deal.title,
            deal_type=deal.deal_type.value,
            asset_type=deal.asset_type.value,
            created_at=datetime.now(),
            items=items,
            recommendations=recommendations,
            completion_percentage=completion_pct,
            estimated_days_to_complete=int(days + 1),
        )

    def _empty_checklist(self, deal_id: str) -> DDChecklist:
        """Return an empty checklist for missing deal."""
        return DDChecklist(
            id=str(uuid4()),
            deal_id=deal_id,
            deal_title="Unknown",
            deal_type="unknown",
            asset_type="unknown",
            created_at=datetime.now(),
            items=[],
            recommendations=[],
            completion_percentage=0,
            estimated_days_to_complete=0,
        )

    def _generate_conditional_items(
        self,
        deal: AgentDeal,
        property_data: Property | None,
    ) -> list[DDItem]:
        """Generate conditional DD items based on property attributes."""
        items = []

        if property_data:
            # Heritage property
            if property_data.is_conservation:
                items.append(
                    DDItem(
                        id=str(uuid4()),
                        category=DDCategory.REGULATORY,
                        name="Heritage Assessment",
                        description="Heritage impact assessment required for conservation property",
                        priority=DDItemPriority.CRITICAL,
                    )
                )

            # Old building
            if (
                property_data.year_built
                and (datetime.now().year - property_data.year_built) > 20
            ):
                items.append(
                    DDItem(
                        id=str(uuid4()),
                        category=DDCategory.TECHNICAL,
                        name="Structural Survey",
                        description=f"Building is {datetime.now().year - property_data.year_built} years old - structural survey recommended",
                        priority=DDItemPriority.HIGH,
                    )
                )

            # Industrial property
            if (
                property_data.property_type
                and property_data.property_type.value == "industrial"
            ):
                items.append(
                    DDItem(
                        id=str(uuid4()),
                        category=DDCategory.ENVIRONMENTAL,
                        name="Phase I ESA Required",
                        description="Industrial zoning requires environmental site assessment",
                        priority=DDItemPriority.HIGH,
                    )
                )

        # Large deal value (metadata available for future enhanced checks)
        _ = deal.metadata_json or {}
        if (
            deal.estimated_value_amount
            and float(deal.estimated_value_amount) > 50000000
        ):
            items.append(
                DDItem(
                    id=str(uuid4()),
                    category=DDCategory.FINANCIAL,
                    name="Independent Valuation",
                    description="High-value transaction requires independent valuation",
                    priority=DDItemPriority.CRITICAL,
                )
            )

        return items

    def _generate_recommendations(
        self,
        deal: AgentDeal,
        property_data: Property | None,
        items: list[DDItem],
    ) -> list[DDRecommendation]:
        """Generate AI-powered DD recommendations."""
        recommendations = []

        # Count critical items
        critical_count = sum(1 for i in items if i.priority == DDItemPriority.CRITICAL)

        if critical_count > 5:
            recommendations.append(
                DDRecommendation(
                    title="High Priority DD",
                    description=f"This deal has {critical_count} critical DD items. Prioritize parallel workstreams.",
                    priority=DDItemPriority.CRITICAL,
                    action_items=[
                        "Engage legal counsel immediately",
                        "Schedule building inspection within 5 days",
                        "Order title search from SLA",
                    ],
                )
            )

        # Property-specific recommendations
        if property_data:
            if (
                property_data.year_built
                and (datetime.now().year - property_data.year_built) > 25
            ):
                recommendations.append(
                    DDRecommendation(
                        title="Aging Building Assessment",
                        description=f"Building is {datetime.now().year - property_data.year_built} years old. Plan for enhanced technical DD.",
                        priority=DDItemPriority.HIGH,
                        action_items=[
                            "Commission comprehensive structural survey",
                            "Assess M&E remaining useful life",
                            "Review historical capex spending",
                            "Budget for potential renovation costs",
                        ],
                    )
                )

            if property_data.is_conservation:
                recommendations.append(
                    DDRecommendation(
                        title="Heritage Property Considerations",
                        description="Conservation status will impact renovation options and timelines.",
                        priority=DDItemPriority.HIGH,
                        action_items=[
                            "Engage heritage consultant early",
                            "Pre-consult with URA on any proposed changes",
                            "Review conservation guidelines",
                        ],
                    )
                )

        return recommendations

    async def auto_complete_items(
        self,
        checklist_id: str,
        db: AsyncSession,
    ) -> list[str]:
        """Attempt to auto-complete items where data is available.

        Args:
            checklist_id: ID of the checklist
            db: Database session

        Returns:
            List of auto-completed item IDs
        """
        completed_ids = []

        # In production, this would:
        # 1. Call URA API for zoning/planning data
        # 2. Call SLA for title information
        # 3. Call BCA for TOP/CSC status
        # 4. Populate items with fetched data

        return completed_ids


# Singleton instance
due_diligence_service = DueDiligenceService()
