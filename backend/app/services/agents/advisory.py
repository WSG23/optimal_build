"""Agent advisory analytics and feedback helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_advisory import AgentAdvisoryFeedback
from app.models.property import Property, PropertyType


@dataclass(slots=True)
class AdvisorySummary:
    """Structured advisory results returned to the API layer."""

    asset_mix: dict[str, Any]
    market_positioning: dict[str, Any]
    absorption_forecast: dict[str, Any]
    feedback: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable representation."""
        return {
            "asset_mix": self.asset_mix,
            "market_positioning": self.market_positioning,
            "absorption_forecast": self.absorption_forecast,
            "feedback": self.feedback,
        }


class AgentAdvisoryService:
    """Provide lightweight advisory insights derived from property context."""

    def __init__(self) -> None:
        self._default_mix_profiles: dict[str, list[tuple[str, float, str]]] = {
            "mixed_use": [
                ("residential", 0.42, "Meet CBD demand for live-work-play stacks."),
                ("office", 0.36, "Maintain prime office yield exposure."),
                ("retail", 0.22, "Activate ground plane and podium traffic."),
            ],
            "office": [
                ("office", 0.7, "Preserve premium office positioning."),
                ("flex workspace", 0.2, "Capture hybrid demand."),
                ("amenities", 0.1, "Support tenant experience."),
            ],
            "retail": [
                ("anchor retail", 0.5, "Secure destination tenant."),
                ("specialty retail", 0.3, "Differentiate merchandising."),
                ("experience/food", 0.2, "Drive repeat footfall."),
            ],
            "residential": [
                ("residential", 0.8, "Maximise saleable units."),
                ("serviced living", 0.1, "Provide yield buffer."),
                ("community amenities", 0.1, "Strengthen positioning."),
            ],
            "industrial": [
                ("production", 0.55, "Core industrial utilisation."),
                ("high-spec logistics", 0.25, "Support e-commerce uplift."),
                ("support services", 0.2, "House value-add services."),
            ],
        }

    async def build_summary(
        self, *, property_id: UUID, session: AsyncSession
    ) -> AdvisorySummary:
        """Return advisory calculations for a property."""

        property_record = await self._get_property(session, property_id)
        asset_mix = self._build_asset_mix(property_record)
        market_positioning = self._build_market_positioning(property_record)
        absorption_forecast = self._build_absorption(property_record)
        feedback_items = await self._list_feedback(session, property_id)

        return AdvisorySummary(
            asset_mix=asset_mix,
            market_positioning=market_positioning,
            absorption_forecast=absorption_forecast,
            feedback=feedback_items,
        )

    async def record_feedback(
        self,
        *,
        property_id: UUID,
        session: AsyncSession,
        submitted_by: str | None,
        sentiment: str,
        notes: str,
        channel: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Persist agent feedback for the specified property."""

        await self._ensure_property_exists(session, property_id)

        feedback = AgentAdvisoryFeedback(
            id=str(uuid4()),
            property_id=str(property_id),
            submitted_by=submitted_by,
            channel=channel,
            sentiment=sentiment,
            notes=notes,
            context=metadata or {},
        )

        session.add(feedback)
        await session.commit()
        await session.refresh(feedback)
        return self._map_feedback(feedback)

    async def list_feedback(
        self, *, property_id: UUID, session: AsyncSession
    ) -> list[dict[str, Any]]:
        """Return feedback entries associated with the property."""

        return await self._list_feedback(session, property_id)

    async def _get_property(self, session: AsyncSession, property_id: UUID) -> Property:
        result = await session.execute(
            select(Property).where(Property.id == property_id)
        )
        property_record = result.scalar_one_or_none()
        if property_record is None:
            raise ValueError(f"Property {property_id} not found")
        return property_record

    async def _ensure_property_exists(
        self, session: AsyncSession, property_id: UUID
    ) -> None:
        result = await session.execute(
            select(Property.id).where(Property.id == property_id)
        )
        if result.scalar_one_or_none() is None:
            raise ValueError(f"Property {property_id} not found")

    async def _list_feedback(
        self, session: AsyncSession, property_id: UUID
    ) -> list[dict[str, Any]]:
        result = await session.execute(
            select(AgentAdvisoryFeedback)
            .where(AgentAdvisoryFeedback.property_id == str(property_id))
            .order_by(AgentAdvisoryFeedback.created_at.desc())
        )
        return [self._map_feedback(row[0]) for row in result.all()]

    def _build_asset_mix(self, property_record: Property) -> dict[str, Any]:
        property_type = (
            property_record.property_type.value
            if isinstance(property_record.property_type, PropertyType)
            else str(property_record.property_type or "mixed_use")
        )
        mix_profile = self._default_mix_profiles.get(
            property_type, self._default_mix_profiles["mixed_use"]
        )
        total_gfa = self._calculate_total_gfa(property_record)
        mix_segments = []
        for use, allocation, rationale in mix_profile:
            target_area = total_gfa * allocation if total_gfa is not None else None
            mix_segments.append(
                {
                    "use": use,
                    "allocation_pct": round(allocation * 100, 2),
                    "target_gfa_sqm": (
                        round(target_area, 2) if target_area is not None else None
                    ),
                    "rationale": rationale,
                }
            )

        notes: list[str] = []
        if property_record.plot_ratio:
            notes.append(
                f"Plot ratio of {property_record.plot_ratio} allows repricing of mix if URA guides change."
            )
        if property_record.is_conservation:
            notes.append(
                "Heritage status limits facade intervention—allocate more area to uses requiring minimal exterior change."
            )

        return {
            "property_id": str(property_record.id),
            "total_programmable_gfa_sqm": (
                round(total_gfa, 2) if total_gfa is not None else None
            ),
            "mix_recommendations": mix_segments,
            "notes": notes,
        }

    def _build_market_positioning(self, property_record: Property) -> dict[str, Any]:
        market_tier = self._determine_market_tier(property_record.district)
        pricing = self._baseline_pricing(property_record.property_type, market_tier)
        anchors = self._suggest_anchor_segments(property_record.property_type)

        messaging = [
            f"Position as a {market_tier.lower()} {self._describe_property_type(property_record.property_type)} in {property_record.district or 'core Singapore'}",
            "Leverage existing quick analysis scenarios to support investor conversations.",
        ]
        if property_record.is_conservation:
            messaging.append(
                "Emphasise conservation credentials and adaptive reuse potential to differentiate inventory."
            )

        return {
            "market_tier": market_tier,
            "pricing_guidance": {
                "sale_psf": {
                    "target_min": pricing["sale_psf"] * 0.97,
                    "target_max": pricing["sale_psf"] * 1.05,
                },
                "rent_psm_monthly": {
                    "target_min": pricing["rent_psm_monthly"] * 0.95,
                    "target_max": pricing["rent_psm_monthly"] * 1.05,
                },
            },
            "target_segments": anchors,
            "messaging": messaging,
        }

    def _build_absorption(self, property_record: Property) -> dict[str, Any]:
        units_total = property_record.units_total or 20
        base_velocity = self._velocity_baseline(property_record.property_type)
        projected_months = (
            max(6, int(units_total / base_velocity)) if units_total else 6
        )
        timeline = self._build_absorption_timeline(projected_months)

        return {
            "expected_months_to_stabilize": projected_months,
            "monthly_velocity_target": base_velocity,
            "confidence": "medium",
            "timeline": timeline,
        }

    def _calculate_total_gfa(self, property_record: Property) -> float | None:
        if property_record.gross_floor_area_sqm:
            return float(property_record.gross_floor_area_sqm)
        if property_record.land_area_sqm and property_record.plot_ratio:
            return float(property_record.land_area_sqm) * float(
                property_record.plot_ratio
            )
        return None

    def _determine_market_tier(self, district: str | None) -> str:
        if not district:
            return "Core CBD"
        if district.upper() in {"D01", "D02", "D06"}:
            return "Prime CBD"
        if district.upper() in {"D09", "D10", "D11"}:
            return "Core Central Region"
        if district.upper().startswith("D") and district[1:].isdigit():
            return "Rest of Central Region"
        return "Singapore Island-wide"

    def _baseline_pricing(
        self, property_type: PropertyType | str | None, market_tier: str
    ) -> dict[str, float]:
        property_key = (
            property_type.value
            if isinstance(property_type, PropertyType)
            else str(property_type or "office")
        )
        base_sale = {
            "office": 2850,
            "retail": 3200,
            "mixed_use": 2950,
            "residential": 3100,
            "industrial": 1400,
        }.get(property_key, 2600)
        base_rent = {
            "office": 12.5,
            "retail": 18.0,
            "mixed_use": 14.0,
            "residential": 7.8,
            "industrial": 4.5,
        }.get(property_key, 10.0)

        tier_multiplier = {
            "Prime CBD": 1.12,
            "Core CBD": 1.08,
            "Core Central Region": 1.05,
            "Rest of Central Region": 0.95,
            "Singapore Island-wide": 0.9,
        }.get(market_tier, 1.0)

        return {
            "sale_psf": round(base_sale * tier_multiplier, 2),
            "rent_psm_monthly": round(base_rent * tier_multiplier, 2),
        }

    def _suggest_anchor_segments(
        self, property_type: PropertyType | str | None
    ) -> list[dict[str, Any]]:
        property_key = (
            property_type.value
            if isinstance(property_type, PropertyType)
            else str(property_type or "office")
        )
        default_segments: dict[str, Iterable[dict[str, Any]]] = {
            "office": [
                {"segment": "Regional HQ", "weight": 0.4},
                {"segment": "Tech/Innovation", "weight": 0.35},
                {"segment": "Financial Services", "weight": 0.25},
            ],
            "retail": [
                {"segment": "Experiential Retail", "weight": 0.4},
                {"segment": "F&B Flagships", "weight": 0.35},
                {"segment": "Luxury Boutiques", "weight": 0.25},
            ],
            "mixed_use": [
                {"segment": "Premium Residential Buyers", "weight": 0.3},
                {"segment": "Blue-chip Office Tenants", "weight": 0.4},
                {"segment": "Destination Retail", "weight": 0.3},
            ],
            "residential": [
                {"segment": "Core Central Family Buyers", "weight": 0.35},
                {"segment": "Global Investors", "weight": 0.3},
                {"segment": "Young Professionals", "weight": 0.35},
            ],
            "industrial": [
                {"segment": "Advanced Manufacturing", "weight": 0.4},
                {"segment": "E-commerce Logistics", "weight": 0.35},
                {"segment": "Data/Cold Storage", "weight": 0.25},
            ],
        }
        segments = default_segments.get(property_key, default_segments["mixed_use"])
        return [
            {**segment, "weight_pct": round(segment["weight"] * 100, 1)}
            for segment in segments
        ]

    def _velocity_baseline(
        self, property_type: PropertyType | str | None
    ) -> int:  # units per month
        property_key = (
            property_type.value
            if isinstance(property_type, PropertyType)
            else str(property_type or "office")
        )
        return {
            "office": 3,
            "retail": 4,
            "mixed_use": 5,
            "residential": 8,
            "industrial": 2,
        }.get(property_key, 4)

    def _build_absorption_timeline(self, projected_months: int) -> list[dict[str, Any]]:
        milestones = [
            ("Launch preparation", 0.1),
            ("Initial release", 0.35),
            ("Mid-cycle momentum", 0.65),
            ("Stabilisation", 1.0),
        ]
        step = max(projected_months // len(milestones), 3)
        timeline = []
        for index, (label, pct) in enumerate(milestones):
            month = min(projected_months, (index + 1) * step)
            timeline.append(
                {
                    "milestone": label,
                    "month": month,
                    "expected_absorption_pct": round(pct * 100, 1),
                }
            )
        return timeline

    def _map_feedback(self, feedback: AgentAdvisoryFeedback) -> dict[str, Any]:
        return {
            "id": feedback.id,
            "property_id": feedback.property_id,
            "submitted_by": feedback.submitted_by,
            "channel": feedback.channel,
            "sentiment": feedback.sentiment,
            "notes": feedback.notes,
            "context": feedback.context,
            "created_at": (
                feedback.created_at.isoformat()
                if isinstance(feedback.created_at, datetime)
                else str(feedback.created_at)
            ),
        }

    def _describe_property_type(self, property_type: PropertyType | str | None) -> str:
        if isinstance(property_type, PropertyType):
            return property_type.value.replace("_", " ")
        return str(property_type or "commercial property").replace("_", " ")


__all__ = ["AgentAdvisoryService", "AdvisorySummary"]
