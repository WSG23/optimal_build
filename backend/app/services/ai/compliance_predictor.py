"""Phase 2.4: Compliance Risk Predictor.

Predicts regulatory approval timelines and risks.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.regulatory import AuthoritySubmission
from app.models.property import Property

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """Risk levels for compliance items."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SubmissionType(str, Enum):
    """Types of regulatory submissions."""

    DC = "development_control"
    BP = "building_plan"
    TOP = "temporary_occupation_permit"
    CSC = "certificate_statutory_completion"
    WAIVER = "waiver"
    CONSULTATION = "consultation"


@dataclass
class RiskFactor:
    """A compliance risk factor."""

    name: str
    risk_level: RiskLevel
    description: str
    mitigation: str
    typical_delay_weeks: int = 0


@dataclass
class SimilarSubmission:
    """A similar historical submission for reference."""

    reference: str
    timeline_weeks: int
    rfi_count: int
    outcome: str
    notes: str | None = None


@dataclass
class TimelineEstimate:
    """Estimated timeline for approval."""

    min_weeks: int
    max_weeks: int
    most_likely_weeks: int
    vs_typical: str  # "faster", "typical", "slower"


@dataclass
class ComplianceAssessment:
    """Complete compliance risk assessment."""

    submission_type: str
    property_address: str
    assessed_at: datetime
    timeline_estimate: TimelineEstimate
    risk_factors: list[RiskFactor]
    similar_submissions: list[SimilarSubmission]
    overall_risk: RiskLevel
    recommendations: list[str]
    required_consultations: list[str]
    estimated_cost: float | None = None


@dataclass
class PredictionResult:
    """Result from compliance prediction."""

    success: bool
    assessment: ComplianceAssessment | None = None
    error: str | None = None


# Typical timelines by submission type (weeks)
TYPICAL_TIMELINES = {
    SubmissionType.DC: {"min": 10, "max": 16, "typical": 12},
    SubmissionType.BP: {"min": 6, "max": 12, "typical": 8},
    SubmissionType.TOP: {"min": 4, "max": 8, "typical": 6},
    SubmissionType.CSC: {"min": 2, "max": 6, "typical": 4},
    SubmissionType.WAIVER: {"min": 8, "max": 20, "typical": 14},
    SubmissionType.CONSULTATION: {"min": 2, "max": 6, "typical": 4},
}


class CompliancePredictorService:
    """Service for predicting compliance risks and timelines."""

    def __init__(self) -> None:
        """Initialize the compliance predictor."""
        self._initialized = True

    async def predict_compliance_risk(
        self,
        property_id: str,
        submission_type: str,
        db: AsyncSession,
        context: dict[str, Any] | None = None,
    ) -> PredictionResult:
        """Predict compliance risks for a property submission.

        Args:
            property_id: ID of the property
            submission_type: Type of submission
            db: Database session
            context: Additional context about the submission

        Returns:
            PredictionResult with compliance assessment
        """
        context = context or {}

        try:
            # Fetch property data
            property_query = select(Property).where(Property.id == property_id)
            result = await db.execute(property_query)
            property_data = result.scalar_one_or_none()

            if not property_data:
                return PredictionResult(
                    success=False,
                    error="Property not found",
                )

            # Identify risk factors
            risk_factors = await self._identify_risk_factors(
                property_data, submission_type, context, db
            )

            # Estimate timeline
            timeline = self._estimate_timeline(submission_type, risk_factors)

            # Get similar submissions
            similar = await self._get_similar_submissions(
                submission_type, property_data, db
            )

            # Calculate overall risk
            overall_risk = self._calculate_overall_risk(risk_factors)

            # Generate recommendations
            recommendations = self._generate_recommendations(risk_factors, timeline)

            # Identify required consultations
            consultations = self._identify_required_consultations(
                property_data, submission_type, context
            )

            assessment = ComplianceAssessment(
                submission_type=submission_type,
                property_address=property_data.address,
                assessed_at=datetime.now(),
                timeline_estimate=timeline,
                risk_factors=risk_factors,
                similar_submissions=similar,
                overall_risk=overall_risk,
                recommendations=recommendations,
                required_consultations=consultations,
            )

            return PredictionResult(success=True, assessment=assessment)

        except Exception as e:
            logger.error(f"Error predicting compliance risk: {e}")
            return PredictionResult(success=False, error=str(e))

    async def _identify_risk_factors(
        self,
        property_data: Property,
        submission_type: str,
        context: dict[str, Any],
        db: AsyncSession,
    ) -> list[RiskFactor]:
        """Identify compliance risk factors for the property."""
        risk_factors = []

        # Check heritage/conservation status
        if property_data.is_conservation:
            risk_factors.append(
                RiskFactor(
                    name="Heritage Zone",
                    risk_level=RiskLevel.HIGH,
                    description="Property is in a conservation area requiring heritage referral",
                    mitigation="Engage heritage consultant early; pre-consult with URA",
                    typical_delay_weeks=4,
                )
            )

        # Check GPR
        if property_data.plot_ratio and float(property_data.plot_ratio) > 4.0:
            risk_factors.append(
                RiskFactor(
                    name="High GPR",
                    risk_level=RiskLevel.MEDIUM,
                    description="GPR above 4.0 requires traffic impact study",
                    mitigation="Commission traffic study in parallel with submission",
                    typical_delay_weeks=2,
                )
            )

        # Check proximity to MRT (from context or property data)
        mrt_distance = context.get("mrt_distance_meters", 500)
        if mrt_distance < 200:
            risk_factors.append(
                RiskFactor(
                    name="MRT Proximity",
                    risk_level=RiskLevel.MEDIUM,
                    description="Within 200m of MRT - requires LTA coordination and design review",
                    mitigation="Coordinate with LTA early; allocate time for design panel review",
                    typical_delay_weeks=3,
                )
            )

        # Check building age for structural concerns
        if property_data.year_built:
            building_age = datetime.now().year - property_data.year_built
            if building_age > 30:
                risk_factors.append(
                    RiskFactor(
                        name="Building Age",
                        risk_level=RiskLevel.MEDIUM,
                        description=f"Building is {building_age} years old - structural assessment may be required",
                        mitigation="Commission structural survey early",
                        typical_delay_weeks=2,
                    )
                )

        # Check for change of use
        if context.get("change_of_use"):
            risk_factors.append(
                RiskFactor(
                    name="Change of Use",
                    risk_level=RiskLevel.HIGH,
                    description="Proposed change of use requires planning approval",
                    mitigation="Submit change of use application before BP",
                    typical_delay_weeks=6,
                )
            )

        # Check industrial zoning for environmental concerns
        if (
            property_data.property_type
            and property_data.property_type.value == "industrial"
        ):
            risk_factors.append(
                RiskFactor(
                    name="Industrial Use",
                    risk_level=RiskLevel.MEDIUM,
                    description="Industrial zoning may require NEA environmental assessment",
                    mitigation="Engage environmental consultant for Phase I assessment",
                    typical_delay_weeks=3,
                )
            )

        # Check for greenfield development
        if context.get("is_greenfield"):
            risk_factors.append(
                RiskFactor(
                    name="Greenfield Site",
                    risk_level=RiskLevel.MEDIUM,
                    description="Greenfield site requires infrastructure planning",
                    mitigation="Coordinate with PUB, LTA for infrastructure requirements",
                    typical_delay_weeks=4,
                )
            )

        return risk_factors

    def _estimate_timeline(
        self,
        submission_type: str,
        risk_factors: list[RiskFactor],
    ) -> TimelineEstimate:
        """Estimate approval timeline based on submission type and risks."""
        # Get base timeline
        try:
            sub_type = SubmissionType(submission_type)
            base = TYPICAL_TIMELINES.get(sub_type, TYPICAL_TIMELINES[SubmissionType.DC])
        except ValueError:
            base = TYPICAL_TIMELINES[SubmissionType.DC]

        # Calculate risk-based delays
        total_delay = sum(rf.typical_delay_weeks for rf in risk_factors)

        min_weeks = base["min"] + (total_delay // 2)
        max_weeks = base["max"] + total_delay
        most_likely = base["typical"] + (total_delay * 2 // 3)

        # Determine vs typical
        if most_likely <= base["typical"]:
            vs_typical = "faster"
        elif most_likely >= base["max"]:
            vs_typical = "slower"
        else:
            vs_typical = "typical"

        return TimelineEstimate(
            min_weeks=min_weeks,
            max_weeks=max_weeks,
            most_likely_weeks=most_likely,
            vs_typical=vs_typical,
        )

    async def _get_similar_submissions(
        self,
        submission_type: str,
        property_data: Property,
        db: AsyncSession,
    ) -> list[SimilarSubmission]:
        """Get similar historical submissions for reference."""
        # Query for similar completed submissions
        two_years_ago = datetime.now() - timedelta(days=730)

        query = (
            select(AuthoritySubmission)
            .where(
                and_(
                    AuthoritySubmission.submission_type == submission_type,
                    AuthoritySubmission.submitted_at >= two_years_ago,
                    AuthoritySubmission.status.in_(
                        ["approved", "rejected", "completed"]
                    ),
                )
            )
            .order_by(AuthoritySubmission.submitted_at.desc())
            .limit(5)
        )

        result = await db.execute(query)
        submissions = result.scalars().all()

        similar = []
        for sub in submissions:
            # Calculate timeline
            if sub.approved_at and sub.submitted_at:
                timeline_days = (sub.approved_at - sub.submitted_at).days
                timeline_weeks = timeline_days // 7
            else:
                timeline_weeks = 12  # Default

            # Count RFIs from metadata
            metadata = sub.metadata_json or {}
            rfi_count = len(metadata.get("rfis", []))

            similar.append(
                SimilarSubmission(
                    reference=sub.reference_number,
                    timeline_weeks=timeline_weeks,
                    rfi_count=rfi_count,
                    outcome=sub.status,
                    notes=metadata.get("notes"),
                )
            )

        return similar

    def _calculate_overall_risk(
        self,
        risk_factors: list[RiskFactor],
    ) -> RiskLevel:
        """Calculate overall risk level from individual factors."""
        if not risk_factors:
            return RiskLevel.LOW

        # Check for any critical risks
        if any(rf.risk_level == RiskLevel.CRITICAL for rf in risk_factors):
            return RiskLevel.CRITICAL

        # Check for multiple high risks
        high_count = sum(1 for rf in risk_factors if rf.risk_level == RiskLevel.HIGH)
        if high_count >= 2:
            return RiskLevel.HIGH

        # Check for any high risks
        if high_count >= 1:
            return RiskLevel.MEDIUM

        # Multiple medium risks
        medium_count = sum(
            1 for rf in risk_factors if rf.risk_level == RiskLevel.MEDIUM
        )
        if medium_count >= 3:
            return RiskLevel.MEDIUM

        return RiskLevel.LOW

    def _generate_recommendations(
        self,
        risk_factors: list[RiskFactor],
        timeline: TimelineEstimate,
    ) -> list[str]:
        """Generate recommendations based on assessment."""
        recommendations = []

        # General recommendation based on timeline
        if timeline.vs_typical == "slower":
            recommendations.append(
                f"Allow for extended timeline of {timeline.max_weeks} weeks in project schedule"
            )

        # Specific recommendations from risk factors
        for rf in sorted(
            risk_factors, key=lambda x: x.typical_delay_weeks, reverse=True
        ):
            if rf.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                recommendations.append(rf.mitigation)

        # Generic recommendations
        recommendations.extend(
            [
                "Engage with agency officers early through pre-consultation",
                "Prepare comprehensive submission package to minimize RFI queries",
                "Monitor submission status weekly and respond to RFIs promptly",
            ]
        )

        return recommendations[:6]  # Limit to top 6

    def _identify_required_consultations(
        self,
        property_data: Property,
        submission_type: str,
        context: dict[str, Any],
    ) -> list[str]:
        """Identify required agency consultations."""
        consultations = []

        # URA is always required for DC
        if submission_type == "development_control":
            consultations.append("URA - Urban Redevelopment Authority")

        # BCA for building plan
        if submission_type in ["building_plan", "temporary_occupation_permit"]:
            consultations.append("BCA - Building and Construction Authority")

        # SCDF for fire safety
        consultations.append("SCDF - Singapore Civil Defence Force")

        # Conservation referral
        if property_data.is_conservation:
            consultations.append("URA Conservation - Heritage Assessment")

        # Traffic assessment
        if property_data.plot_ratio and float(property_data.plot_ratio) > 4.0:
            consultations.append("LTA - Land Transport Authority")

        # Environmental
        if (
            property_data.property_type
            and property_data.property_type.value == "industrial"
        ):
            consultations.append("NEA - National Environment Agency")

        return consultations


# Singleton instance
compliance_predictor_service = CompliancePredictorService()
