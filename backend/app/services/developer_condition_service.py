"""Developer property condition assessment heuristics."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, List, Optional
from uuid import UUID

from app.models.developer_checklists import ChecklistPriority, ChecklistStatus
from app.models.developer_condition import DeveloperConditionAssessmentRecord
from app.models.property import Property, PropertyType
from app.services.developer_checklist_service import DeveloperChecklistService
from sqlalchemy import desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(slots=True)
class ConditionSystem:
    """Represents the condition of a building subsystem."""

    name: str
    rating: str
    score: int
    notes: str
    recommended_actions: List[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "rating": self.rating,
            "score": self.score,
            "notes": self.notes,
            "recommended_actions": list(self.recommended_actions),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ConditionSystem":
        return cls(
            name=str(payload.get("name", "")),
            rating=str(payload.get("rating", "")),
            score=int(payload.get("score", 0)),
            notes=str(payload.get("notes", "")),
            recommended_actions=[
                str(item)
                for item in payload.get("recommended_actions", [])
                if isinstance(item, (str, int, float))
            ],
        )


@dataclass(slots=True)
class ConditionInsight:
    """Derived insight highlighting key risks or opportunities."""

    id: str
    severity: str
    title: str
    detail: str
    specialist: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "severity": self.severity,
            "title": self.title,
            "detail": self.detail,
            "specialist": self.specialist,
        }


@dataclass(slots=True)
class ConditionAssessment:
    """Aggregated condition assessment for a property."""

    property_id: UUID
    scenario: Optional[str]
    overall_score: int
    overall_rating: str
    risk_level: str
    summary: str
    scenario_context: Optional[str]
    systems: List[ConditionSystem]
    recommended_actions: List[str]
    inspector_name: Optional[str] = None
    recorded_by: Optional[UUID] = None
    recorded_at: Optional[datetime] = None
    attachments: List[dict[str, Any]] = field(default_factory=list)
    insights: List[ConditionInsight] = field(default_factory=list)


class DeveloperConditionService:
    """Provide developer-friendly property condition assessments."""

    @staticmethod
    async def generate_assessment(
        session: AsyncSession,
        property_id: UUID,
        scenario: Optional[str] = None,
    ) -> ConditionAssessment:
        """Generate a heuristic condition assessment for a property."""

        scenario_key = _normalise_scenario(scenario)
        stored = await DeveloperConditionService._get_latest_assessment(
            session=session,
            property_id=property_id,
            scenario=scenario_key,
        )

        property_record = await session.get(Property, property_id)

        if stored is not None:
            assessment = DeveloperConditionService._record_to_assessment(
                stored,
                property_record=property_record,
            )
        else:
            if property_record is None:
                raise ValueError("Property not found")

            age_score, age_band = _calculate_age_score(property_record)
            structure_score = _calculate_structure_score(property_record)
            systems_score = _calculate_systems_score(property_record)

            overall_score = round((age_score + structure_score + systems_score) / 3)
            overall_rating = _score_to_rating(overall_score)
            risk_level = _determine_risk_level(overall_rating)

            scenario_context = (
                _describe_scenario_context(property_record, scenario_key)
                if scenario_key
                else None
            )

            systems = [
                _build_structure_system(property_record, structure_score),
                _build_services_system(property_record, systems_score),
                _build_compliance_system(property_record, age_band),
            ]
            recommended_actions = _build_action_plan(
                property_record, overall_rating, scenario_key
            )

            summary = _build_summary(
                property_record, overall_rating, risk_level, scenario_context
            )

            assessment = ConditionAssessment(
                property_id=property_id,
                scenario=scenario_key,
                overall_score=overall_score,
                overall_rating=overall_rating,
                risk_level=risk_level,
                summary=summary,
                scenario_context=scenario_context,
                systems=systems,
                recommended_actions=recommended_actions,
                recorded_at=None,
            )

            assessment.insights = _generate_condition_insights(
                property_record=property_record,
                assessment=assessment,
            )

        specialist_insights = (
            await DeveloperConditionService._build_specialist_checklist_insights(
                session=session,
                property_id=property_id,
                scenario=scenario_key,
            )
        )
        if specialist_insights:
            assessment.insights = DeveloperConditionService._merge_insights(
                assessment.insights,
                specialist_insights,
            )

        return assessment

    @staticmethod
    async def record_assessment(
        session: AsyncSession,
        *,
        property_id: UUID,
        scenario: Optional[str],
        overall_rating: str,
        overall_score: int,
        risk_level: str,
        summary: str,
        scenario_context: Optional[str],
        systems: List[ConditionSystem],
        recommended_actions: List[str],
        inspector_name: Optional[str] = None,
        recorded_at: Optional[datetime] = None,
        attachments: Optional[List[dict[str, Any]]] = None,
        recorded_by: Optional[UUID] = None,
    ) -> ConditionAssessment:
        """Store a developer-provided condition assessment and return it."""

        scenario_key = _normalise_scenario(scenario)
        previous_record = await DeveloperConditionService._get_latest_assessment(
            session=session,
            property_id=property_id,
            scenario=scenario_key,
        )
        clean_attachments: List[dict[str, Any]] = []
        for item in attachments or []:
            if not isinstance(item, dict):
                continue
            label_raw = item.get("label")
            url_raw = item.get("url")
            label = str(label_raw).strip() if label_raw is not None else ""
            url = None
            if isinstance(url_raw, str):
                url_candidate = url_raw.strip()
                url = url_candidate or None
            if not label and not url:
                continue
            clean_attachments.append({"label": label or (url or ""), "url": url})
        record = DeveloperConditionAssessmentRecord(
            property_id=property_id,
            scenario=scenario_key,
            overall_rating=overall_rating,
            overall_score=overall_score,
            risk_level=risk_level,
            summary=summary,
            scenario_context=scenario_context,
            systems=[system.to_dict() for system in systems],
            recommended_actions=list(recommended_actions),
            inspector_name=inspector_name.strip() if inspector_name else None,
            attachments=clean_attachments,
            recorded_by=recorded_by,
        )
        if recorded_at is not None:
            record.recorded_at = recorded_at
        session.add(record)
        await session.flush()
        await session.refresh(record)

        property_record = await session.get(Property, property_id)
        previous_assessment = None
        if previous_record is not None and property_record is not None:
            previous_assessment = DeveloperConditionService._record_to_assessment(
                previous_record,
                property_record=property_record,
            )

        return DeveloperConditionService._record_to_assessment(
            record,
            property_record=property_record,
            previous=previous_assessment,
        )

    @staticmethod
    async def get_assessment_history(
        session: AsyncSession,
        *,
        property_id: UUID,
        scenario: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[ConditionAssessment]:
        """Return inspection history ordered from most recent to oldest."""

        scenario_key = _normalise_scenario(scenario)
        query = (
            select(DeveloperConditionAssessmentRecord)
            .where(DeveloperConditionAssessmentRecord.property_id == property_id)
            .order_by(desc(DeveloperConditionAssessmentRecord.recorded_at))
        )

        if scenario_key is not None:
            query = query.where(
                or_(
                    DeveloperConditionAssessmentRecord.scenario == scenario_key,
                    DeveloperConditionAssessmentRecord.scenario.is_(None),
                )
            )

        if limit:
            query = query.limit(limit)

        result = await session.execute(query)
        records_raw = list(result.scalars().all())
        property_record = await session.get(Property, property_id)
        assessments: List[ConditionAssessment] = []
        previous: Optional[ConditionAssessment] = None
        for record in records_raw:
            assessment = DeveloperConditionService._record_to_assessment(
                record,
                property_record=property_record,
                previous=previous,
            )
            assessments.append(assessment)
            previous = assessment
        return assessments

    @staticmethod
    async def get_latest_assessments_by_scenario(
        session: AsyncSession,
        *,
        property_id: UUID,
    ) -> List[ConditionAssessment]:
        """
        Return the most recent stored assessment for each scenario.

        Entries without a scenario (global overrides) are included with a `None` scenario
        key so the caller can decide whether to surface them.
        """

        query = (
            select(DeveloperConditionAssessmentRecord)
            .where(DeveloperConditionAssessmentRecord.property_id == property_id)
            .order_by(desc(DeveloperConditionAssessmentRecord.recorded_at))
        )
        result = await session.execute(query)
        records = []
        seen: set[Optional[str]] = set()
        property_record = await session.get(Property, property_id)
        for record in result.scalars():
            scenario_key = record.scenario
            if scenario_key in seen:
                continue
            seen.add(scenario_key)
            records.append(
                DeveloperConditionService._record_to_assessment(
                    record,
                    property_record=property_record,
                )
            )
        return records

    @staticmethod
    async def _get_latest_assessment(
        session: AsyncSession,
        property_id: UUID,
        scenario: Optional[str],
    ) -> Optional[DeveloperConditionAssessmentRecord]:
        filters = [DeveloperConditionAssessmentRecord.property_id == property_id]
        scenario_key = _normalise_scenario(scenario)
        query = (
            select(DeveloperConditionAssessmentRecord)
            .where(*filters)
            .order_by(desc(DeveloperConditionAssessmentRecord.recorded_at))
        )

        if scenario_key is not None:
            query = query.where(
                DeveloperConditionAssessmentRecord.scenario == scenario_key
            )
        result = await session.execute(query)
        record = result.scalars().first()

        if record is None and scenario_key is not None:
            fallback_query = (
                select(DeveloperConditionAssessmentRecord)
                .where(
                    DeveloperConditionAssessmentRecord.property_id == property_id,
                    DeveloperConditionAssessmentRecord.scenario.is_(None),
                )
                .order_by(desc(DeveloperConditionAssessmentRecord.recorded_at))
            )
            fallback_result = await session.execute(fallback_query)
            record = fallback_result.scalars().first()

        return record

    @staticmethod
    def _record_to_assessment(
        record: DeveloperConditionAssessmentRecord,
        property_record: Optional[Property] = None,
        previous: Optional[ConditionAssessment] = None,
    ) -> ConditionAssessment:
        systems_payload = record.systems if isinstance(record.systems, list) else []
        systems = [
            ConditionSystem.from_dict(item)
            for item in systems_payload
            if isinstance(item, dict)
        ]
        actions = [str(item) for item in record.recommended_actions or []]
        attachments_payload: List[dict[str, Any]] = []
        if isinstance(record.attachments, list):
            for raw in record.attachments:  # type: ignore[assignment]
                if not isinstance(raw, dict):
                    continue
                label = str(raw.get("label", "")).strip()
                url_raw = raw.get("url")
                url = str(url_raw).strip() if isinstance(url_raw, str) else None
                if not label and not url:
                    continue
                attachments_payload.append({"label": label or (url or ""), "url": url})

        assessment = ConditionAssessment(
            property_id=record.property_id,
            scenario=record.scenario,
            overall_score=record.overall_score,
            overall_rating=record.overall_rating,
            risk_level=record.risk_level,
            summary=record.summary,
            scenario_context=record.scenario_context,
            systems=systems,
            recommended_actions=actions,
            inspector_name=record.inspector_name,
            recorded_by=record.recorded_by,
            recorded_at=record.recorded_at,
            attachments=attachments_payload,
        )

        if property_record is not None:
            assessment.insights = _generate_condition_insights(
                property_record=property_record,
                assessment=assessment,
                previous=previous,
            )

        return assessment

    @staticmethod
    async def _build_specialist_checklist_insights(
        session: AsyncSession,
        property_id: UUID,
        scenario: Optional[str],
    ) -> List[ConditionInsight]:
        try:
            checklist_items = await DeveloperChecklistService.get_property_checklist(
                session,
                property_id,
            )
        except Exception:  # pragma: no cover - defensive fallback when table absent
            return []

        if not checklist_items:
            return []

        payloads = DeveloperChecklistService.format_property_checklist_items(
            checklist_items
        )
        scenario_filter = scenario
        insights: List[ConditionInsight] = []

        for payload in payloads:
            if not payload.get("requires_professional"):
                continue

            status_raw = str(payload.get("status") or ChecklistStatus.PENDING.value)
            try:
                status = ChecklistStatus(status_raw)
            except ValueError:  # pragma: no cover - defensive
                status = ChecklistStatus.PENDING

            if status not in _OPEN_CHECKLIST_STATUSES:
                continue

            item_scenario_raw = payload.get("development_scenario")
            item_scenario_key = _normalise_scenario(
                str(item_scenario_raw) if item_scenario_raw is not None else None
            )
            if scenario_filter is not None and item_scenario_key not in {
                scenario_filter,
                None,
            }:
                continue

            priority_raw = str(
                payload.get("priority") or ChecklistPriority.MEDIUM.value
            )
            try:
                priority = ChecklistPriority(priority_raw)
            except ValueError:  # pragma: no cover - defensive
                priority = ChecklistPriority.MEDIUM

            severity = _severity_from_priority(priority)
            if status == ChecklistStatus.IN_PROGRESS and severity == "critical":
                severity = "warning"

            detail_parts: List[str] = []
            if (
                item_scenario_key is not None
                and scenario_filter is None
                and isinstance(item_scenario_raw, str)
                and item_scenario_raw
            ):
                detail_parts.append(
                    f"Scenario: {_format_scenario_label(item_scenario_raw)}."
                )

            description = str(payload.get("item_description") or "").strip()
            if description:
                detail_parts.append(description)

            detail_parts.append(f"Status: {_format_status_label(status)}.")

            due_date = payload.get("due_date")
            if due_date:
                detail_parts.append(f"Due {due_date}.")

            notes = payload.get("notes")
            if notes:
                notes_str = str(notes).strip()
                if notes_str:
                    detail_parts.append(f"Notes: {notes_str}")

            detail = " ".join(detail_parts).strip()
            if not detail:
                detail = f"Status: {_format_status_label(status)}."

            specialist = payload.get("professional_type")
            insights.append(
                ConditionInsight(
                    id=f"checklist-{payload['id']}",
                    severity=severity,
                    title=str(
                        payload.get("item_title") or "Specialist follow-up required"
                    ),
                    detail=detail,
                    specialist=str(specialist) if specialist else None,
                )
            )

        return insights

    @staticmethod
    def _merge_insights(
        baseline: List[ConditionInsight],
        additional: List[ConditionInsight],
    ) -> List[ConditionInsight]:
        if not additional:
            return baseline

        merged = list(baseline)
        index_by_id = {insight.id: idx for idx, insight in enumerate(merged)}

        for insight in additional:
            existing_index = index_by_id.get(insight.id)
            if existing_index is not None:
                merged[existing_index] = insight
            else:
                index_by_id[insight.id] = len(merged)
                merged.append(insight)

        return merged


_OPEN_CHECKLIST_STATUSES = {
    ChecklistStatus.PENDING,
    ChecklistStatus.IN_PROGRESS,
}


def _severity_from_priority(priority: ChecklistPriority) -> str:
    if priority == ChecklistPriority.CRITICAL:
        return "critical"
    if priority == ChecklistPriority.HIGH:
        return "warning"
    if priority == ChecklistPriority.MEDIUM:
        return "info"
    return "info"


def _format_status_label(status: ChecklistStatus) -> str:
    return status.value.replace("_", " ").title()


def _format_scenario_label(raw: str) -> str:
    return raw.replace("_", " ").title()


def _calculate_age_score(property_record: Property) -> tuple[int, str]:
    """Score the building age and return score plus age band label."""
    current_year = date.today().year
    if property_record.year_built:
        age = max(current_year - int(property_record.year_built), 0)
    else:
        age = 25  # assume mid-life when unknown

    if age < 10:
        return 90, "new"
    if age < 25:
        return 80, "mid_life"
    if age < 40:
        return 65, "ageing"
    if age < 60:
        return 55, "late_life"
    return 45, "legacy"


def _calculate_structure_score(property_record: Property) -> int:
    """Approximate structural condition using property type + storeys."""
    floors = property_record.floors_above_ground or 0
    if property_record.property_type == PropertyType.OFFICE:
        baseline = 75
    elif property_record.property_type == PropertyType.MIXED_USE:
        baseline = 70
    else:
        baseline = 65

    if floors > 35:
        baseline -= 5
    if floors > 50:
        baseline -= 8

    if property_record.building_height_m and property_record.building_height_m > 200:
        baseline -= 5

    return max(40, min(90, baseline))


def _calculate_systems_score(property_record: Property) -> int:
    """Estimate M&E systems condition based on building age/usage."""
    _, age_band = _calculate_age_score(property_record)
    score_map = {
        "new": 88,
        "mid_life": 78,
        "ageing": 68,
        "late_life": 58,
        "legacy": 50,
    }
    score = score_map.get(age_band, 70)

    if property_record.status and property_record.status.name.lower() in {
        "existing",
        "occupied",
    }:
        score -= 2  # assume live load adds wear

    return max(45, score)


def _score_to_rating(score: int) -> str:
    """Convert numeric score into developer-friendly rating band."""
    if score >= 85:
        return "A"
    if score >= 75:
        return "B"
    if score >= 65:
        return "C"
    if score >= 55:
        return "D"
    return "E"


def _determine_risk_level(rating: str) -> str:
    """Translate rating into a simple risk label."""
    mapping = {
        "A": "low",
        "B": "moderate",
        "C": "elevated",
        "D": "high",
        "E": "critical",
    }
    return mapping.get(rating, "moderate")


def _describe_scenario_context(
    property_record: Property, scenario: Optional[str]
) -> Optional[str]:
    """Provide contextual messaging for the selected development scenario."""
    if not scenario:
        return None

    scenario = scenario.lower()
    if scenario == "existing_building":
        return "Focus on phased upgrade works while maintaining operations."
    if scenario == "heritage_property":
        return "Coordinate with conservation guidelines before intrusive works."
    if scenario == "underused_asset":
        return "Prioritise adaptive reuse strategies aligned with target tenants."
    if scenario == "mixed_use_redevelopment":
        return "Plan for full strip-out and structural strengthening for vertical expansion."
    if scenario == "raw_land":
        return "Existing condition insights inform demolition budgeting and site formation."
    return None


def _build_structure_system(
    property_record: Property, structure_score: int
) -> ConditionSystem:
    """Construct structural system assessment details."""
    rating = _score_to_rating(structure_score)
    notes = (
        "Reinforced concrete core with steel framing. Routine deflection monitoring "
        "recommended for spans exceeding 15m."
    )
    actions = [
        "Commission detailed structural survey and material testing",
        "Validate live load allowances against proposed programme",
    ]
    if property_record.floors_above_ground and property_record.floors_above_ground > 40:
        actions.append("Review lateral load resistance for high-rise retrofit")

    return ConditionSystem(
        name="Structural frame & envelope",
        rating=rating,
        score=structure_score,
        notes=notes,
        recommended_actions=actions,
    )


def _build_services_system(
    property_record: Property, systems_score: int
) -> ConditionSystem:
    """Construct M&E system assessment details."""
    rating = _score_to_rating(systems_score)
    actions = [
        "Undertake full M&E condition appraisal (HVAC, electrical, fire safety)",
        "Plan progressive replacement of aging chillers and switchgear",
    ]
    if property_record.status and property_record.status.name.lower() == "existing":
        actions.append("Coordinate upgrades with operations to minimise downtime")

    notes = (
        "Core plant sized for original specification. Efficiency upgrades required to "
        "meet current BCA Green Mark and tenant expectations."
    )
    return ConditionSystem(
        name="Mechanical & electrical systems",
        rating=rating,
        score=systems_score,
        notes=notes,
        recommended_actions=actions,
    )


def _build_compliance_system(
    property_record: Property, age_band: str
) -> ConditionSystem:
    """Construct regulatory/compliance view."""
    if age_band in {"new", "mid_life"}:
        score = 82
        rating = "B"
        notes = "Fire safety upgrades largely current; confirm latest SCDF submissions."
    else:
        score = 68
        rating = "C"
        notes = (
            "Legacy code compliance. Accessibility, façade inspections, and fire "
            "certifications require refresh."
        )

    return ConditionSystem(
        name="Compliance & envelope maintenance",
        rating=rating,
        score=score,
        notes=notes,
        recommended_actions=[
            "Update façade inspection records and sealant testing",
            "Refresh fire certification and evacuation strategy",
            "Verify accessibility provisions vs. 2024 BCA requirements",
        ],
    )


def _build_action_plan(
    property_record: Property, overall_rating: str, scenario: Optional[str]
) -> List[str]:
    """Provide a concise action plan list."""
    actions = [
        "Commission intrusive condition survey (structural + M&E)",
        "Develop capex phasing aligned with development programme",
        "Engage cost consultant for remediation budget with risk allowance",
    ]
    if overall_rating in {"D", "E"}:
        actions.insert(0, "Escalate risk to investment committee for budget approval")
    if scenario == "mixed_use_redevelopment":
        actions.append("Coordinate decant strategy and safe demolition methodology")
    if property_record.property_type == PropertyType.MIXED_USE:
        actions.append("Assess shared services segregation for mixed-use compliance")
    return actions


def _system_specialist_hint(name: str) -> Optional[str]:
    lower = name.lower()
    if "struct" in lower:
        return "Structural engineer"
    if "mechanical" in lower or "electrical" in lower or "m&e" in lower:
        return "M&E engineer"
    if "compliance" in lower or "regulatory" in lower or "envelope" in lower:
        return "Building surveyor"
    return None


def _estimate_property_age(property_record: Property) -> Optional[int]:
    if property_record.year_built:
        try:
            return max(date.today().year - int(property_record.year_built), 0)
        except (TypeError, ValueError):  # pragma: no cover - defensive
            return None
    return None


def _years_until_lease_expiry(property_record: Property) -> Optional[int]:
    if property_record.lease_expiry_date:
        delta = property_record.lease_expiry_date - date.today()
        return delta.days // 365
    return None


def _slugify_identifier(value: str) -> str:
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in value)
    slug = "-".join(part for part in slug.split("-") if part)
    return slug or "insight"


def _generate_condition_insights(
    property_record: Property,
    assessment: ConditionAssessment,
    previous: Optional[ConditionAssessment] = None,
) -> List[ConditionInsight]:
    insights: List[ConditionInsight] = []
    seen_ids: set[str] = set()

    def _add(insight: ConditionInsight) -> None:
        if insight.id in seen_ids:
            return
        insights.append(insight)
        seen_ids.add(insight.id)

    age_years = _estimate_property_age(property_record)
    if age_years is not None:
        if age_years >= 60:
            _add(
                ConditionInsight(
                    id="age-critical",
                    severity="critical",
                    title="Legacy structure nearing end-of-life",
                    detail=(
                        f"Primary structure is approximately {age_years} years old. "
                        "Plan intrusive testing and staged strengthening to reduce redevelopment risk."
                    ),
                    specialist="Structural engineer",
                )
            )
        elif age_years >= 40:
            _add(
                ConditionInsight(
                    id="age-watchlist",
                    severity="warning",
                    title="Ageing asset requires lifecycle planning",
                    detail=(
                        f"Structure is roughly {age_years} years old. Allow for higher contingency in structural refurbishment works."
                    ),
                    specialist="Structural engineer",
                )
            )
        elif age_years <= 10:
            _add(
                ConditionInsight(
                    id="age-positive",
                    severity="positive",
                    title="Recently built structure",
                    detail="Core structure remains relatively new with limited immediate lifecycle exposure.",
                )
            )

    if property_record.year_renovated:
        try:
            years_since = date.today().year - int(property_record.year_renovated)
        except (TypeError, ValueError):  # pragma: no cover - defensive
            years_since = None
        if years_since is not None and years_since <= 5:
            _add(
                ConditionInsight(
                    id="recent-renovation",
                    severity="positive",
                    title="Recent major renovation",
                    detail=(
                        "Significant refurbishment completed within the last five years "
                        "— leverage existing warranties and contractors."
                    ),
                )
            )

    lease_years = _years_until_lease_expiry(property_record)
    if lease_years is not None:
        expiry_str = (
            property_record.lease_expiry_date.isoformat()
            if property_record.lease_expiry_date
            else "lease expiry"
        )
        if lease_years <= 8:
            _add(
                ConditionInsight(
                    id="lease-critical",
                    severity="critical",
                    title="Lease tail creates financing pressure",
                    detail=(
                        f"Lease expires around {expiry_str}, leaving roughly {lease_years} years. "
                        "Engage legal counsel to map renewal or land replacement strategies."
                    ),
                    specialist="Conveyancing lawyer",
                )
            )
        elif lease_years <= 15:
            _add(
                ConditionInsight(
                    id="lease-watch",
                    severity="warning",
                    title="Lease term constrains redevelopment horizon",
                    detail=(
                        f"Lease expiry circa {expiry_str} (~{lease_years} years remaining). "
                        "Begin renewal negotiations alongside feasibility planning."
                    ),
                    specialist="Conveyancing lawyer",
                )
            )

    if property_record.is_conservation or property_record.conservation_status:
        conservation_note = (
            property_record.conservation_status or "Conservation controls apply"
        )
        _add(
            ConditionInsight(
                id="heritage-controls",
                severity="info",
                title="Conservation requirements impact works",
                detail=(
                    f"{conservation_note}. Coordinate with URA conservation team before design freeze."
                ),
                specialist="Heritage architect",
            )
        )

    if assessment.overall_rating in {"D", "E"}:
        _add(
            ConditionInsight(
                id="overall-rating",
                severity="critical",
                title="Condition rating below investment threshold",
                detail=(
                    f"Overall rating {assessment.overall_rating} indicates significant remediation before financing approval."
                ),
                specialist="Project QS",
            )
        )
    elif assessment.risk_level in {"high", "critical"}:
        _add(
            ConditionInsight(
                id="risk-level",
                severity="warning",
                title="Delivery risk flagged",
                detail=(
                    f"Risk level classified as {assessment.risk_level}. Align contingency and programme buffers."
                ),
            )
        )

    for system in assessment.systems:
        rating = system.rating.upper()
        severity: str
        if rating == "E" or system.score <= 50:
            severity = "critical"
        elif rating in {"D"} or system.score <= 60:
            severity = "warning"
        else:
            continue

        action_hint = (
            system.recommended_actions[0] if system.recommended_actions else None
        )
        detail = f"{system.name} rated {rating} ({system.score}/100)."
        if system.notes:
            detail = f"{detail} {system.notes.strip()}"
        if action_hint:
            detail = f"{detail} Recommended next step: {action_hint}."

        _add(
            ConditionInsight(
                id=f"system-{_slugify_identifier(system.name)}",
                severity=severity,
                title=f"{system.name} requires specialist intervention",
                detail=detail,
                specialist=_system_specialist_hint(system.name),
            )
        )

    if previous is not None:
        delta = assessment.overall_score - previous.overall_score
        if delta <= -8:
            reference = (
                previous.recorded_at.strftime("%d %b %Y")
                if previous.recorded_at
                else "previous inspection"
            )
            _add(
                ConditionInsight(
                    id="score-decline",
                    severity="warning",
                    title="Condition score deteriorated",
                    detail=(
                        f"Overall score dropped {abs(delta)} points since {reference} "
                        f"({previous.overall_score} → {assessment.overall_score})."
                    ),
                )
            )
        elif delta >= 8:
            reference = (
                previous.recorded_at.strftime("%d %b %Y")
                if previous.recorded_at
                else "previous inspection"
            )
            _add(
                ConditionInsight(
                    id="score-improvement",
                    severity="positive",
                    title="Condition score improved",
                    detail=(
                        f"Overall score improved by {delta} points since {reference} "
                        f"({previous.overall_score} → {assessment.overall_score})."
                    ),
                )
            )

    if not insights:
        _add(
            ConditionInsight(
                id="baseline-overview",
                severity="info",
                title="Baseline assessment recorded",
                detail="Condition profile captured. Use recommended actions to brief specialists for concept design freeze.",
            )
        )

    return insights


def _build_summary(
    property_record: Property,
    overall_rating: str,
    risk_level: str,
    scenario_context: Optional[str],
) -> str:
    """Compose a short summary string for the frontend."""
    property_name = property_record.name or "The property"
    summary = (
        f"{property_name} scores a {overall_rating} condition rating with {risk_level} "
        "delivery risk. Focus remediation on structural integrity, ageing M&E plant, "
        "and compliance uplift."
    )
    if scenario_context:
        summary = f"{summary} {scenario_context}"
    return summary


def _normalise_scenario(value: Optional[str]) -> Optional[str]:
    """Normalise scenario keys used for storage and comparisons."""

    if value is None:
        return None
    slug = value.strip().lower()
    if not slug or slug == "all":
        return None
    return slug


__all__ = [
    "ConditionAssessment",
    "ConditionInsight",
    "ConditionSystem",
    "DeveloperConditionService",
]
