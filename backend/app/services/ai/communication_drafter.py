"""Phase 3.3: Email & Communication Drafting.

AI-powered drafting for professional communications.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from langchain_openai import ChatOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business_performance import AgentDeal
from app.models.property import Property

logger = logging.getLogger(__name__)


class CommunicationType(str, Enum):
    """Types of communications."""

    EMAIL = "email"
    LETTER = "letter"
    SMS = "sms"
    PROPOSAL = "proposal"
    MEMO = "memo"


class CommunicationTone(str, Enum):
    """Tone for communications."""

    FORMAL = "formal"
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    URGENT = "urgent"


class CommunicationPurpose(str, Enum):
    """Purpose of communication."""

    INTRODUCTION = "introduction"
    FOLLOW_UP = "follow_up"
    OFFER = "offer"
    COUNTER_OFFER = "counter_offer"
    NEGOTIATION = "negotiation"
    CLOSING = "closing"
    THANK_YOU = "thank_you"
    UPDATE = "update"
    REQUEST = "request"
    REJECTION = "rejection"


@dataclass
class CommunicationDraft:
    """A drafted communication."""

    id: str
    communication_type: CommunicationType
    purpose: CommunicationPurpose
    tone: CommunicationTone
    subject: str | None
    body: str
    recipient_context: dict[str, Any]
    deal_context: dict[str, Any] | None
    generated_at: datetime
    alternatives: list[str] = field(default_factory=list)


@dataclass
class DraftRequest:
    """Request for drafting a communication."""

    communication_type: CommunicationType
    purpose: CommunicationPurpose
    tone: CommunicationTone = CommunicationTone.PROFESSIONAL
    recipient_name: str | None = None
    recipient_company: str | None = None
    recipient_role: str | None = None
    deal_id: str | None = None
    property_id: str | None = None
    key_points: list[str] = field(default_factory=list)
    additional_context: str | None = None
    include_alternatives: bool = False


@dataclass
class DraftResult:
    """Result from communication drafting."""

    success: bool
    draft: CommunicationDraft | None = None
    error: str | None = None
    generation_time_ms: float = 0.0


class CommunicationDrafterService:
    """Service for AI-powered communication drafting."""

    llm: Optional[ChatOpenAI]

    def __init__(self) -> None:
        """Initialize the drafter service."""
        try:
            self.llm = ChatOpenAI(
                model="gpt-4-turbo",
                temperature=0.7,  # Slightly creative for natural language
            )
            self._initialized = True
        except Exception as e:
            logger.warning(f"Communication Drafter not initialized: {e}")
            self._initialized = False
            self.llm = None

    async def draft_communication(
        self,
        request: DraftRequest,
        db: AsyncSession | None = None,
    ) -> DraftResult:
        """Draft a communication based on the request.

        Args:
            request: Draft request with all parameters
            db: Optional database session for context

        Returns:
            DraftResult with generated draft
        """
        start_time = datetime.now()

        try:
            # Gather context
            deal_context = None
            property_context = None

            if db:
                if request.deal_id:
                    deal_query = select(AgentDeal).where(
                        AgentDeal.id == request.deal_id
                    )
                    result = await db.execute(deal_query)
                    deal = result.scalar_one_or_none()
                    if deal:
                        deal_context = {
                            "title": deal.title,
                            "deal_type": deal.deal_type.value,
                            "asset_type": deal.asset_type.value,
                            "pipeline_stage": deal.pipeline_stage.value,
                            "estimated_value": (
                                float(deal.estimated_value_amount)
                                if deal.estimated_value_amount
                                else None
                            ),
                            "description": deal.description,
                        }

                if request.property_id:
                    prop_query = select(Property).where(
                        Property.id == request.property_id
                    )
                    result = await db.execute(prop_query)
                    prop = result.scalar_one_or_none()
                    if prop:
                        property_context = {
                            "address": prop.address,
                            "district": prop.district,
                            "property_type": (
                                prop.property_type.value if prop.property_type else None
                            ),
                            "land_area_sqm": (
                                float(prop.land_area_sqm)
                                if prop.land_area_sqm
                                else None
                            ),
                        }

            # Generate draft
            if not self._initialized or not self.llm:
                draft = self._generate_template_draft(
                    request, deal_context, property_context
                )
            else:
                draft = await self._generate_ai_draft(
                    request, deal_context, property_context
                )

            generation_time = (datetime.now() - start_time).total_seconds() * 1000

            return DraftResult(
                success=True,
                draft=draft,
                generation_time_ms=generation_time,
            )

        except Exception as e:
            logger.error(f"Error drafting communication: {e}")
            return DraftResult(
                success=False,
                error=str(e),
            )

    async def _generate_ai_draft(
        self,
        request: DraftRequest,
        deal_context: dict[str, Any] | None,
        property_context: dict[str, Any] | None,
    ) -> CommunicationDraft:
        """Generate draft using AI."""
        assert self.llm is not None  # Caller ensures this
        prompt = self._build_prompt(request, deal_context, property_context)
        response = self.llm.invoke(prompt)
        content = response.content
        body = content if isinstance(content, str) else ""

        # Generate alternatives if requested
        alternatives: list[str] = []
        if request.include_alternatives:
            for variation in ["more concise", "more detailed"]:
                alt_prompt = f"{prompt}\n\nPlease make this version {variation}."
                alt_response = self.llm.invoke(alt_prompt)
                alt_content = alt_response.content
                if isinstance(alt_content, str):
                    alternatives.append(alt_content)

        # Generate subject line for emails
        subject: str | None = None
        if request.communication_type == CommunicationType.EMAIL:
            subject_prompt = f"Generate a professional email subject line for this email:\n{body}\n\nSubject line only, no quotes:"
            subject_response = self.llm.invoke(subject_prompt)
            subject_content = subject_response.content
            if isinstance(subject_content, str):
                subject = subject_content.strip()

        return CommunicationDraft(
            id=f"draft_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            communication_type=request.communication_type,
            purpose=request.purpose,
            tone=request.tone,
            subject=subject,
            body=body,
            recipient_context={
                "name": request.recipient_name,
                "company": request.recipient_company,
                "role": request.recipient_role,
            },
            deal_context=deal_context,
            generated_at=datetime.now(),
            alternatives=alternatives,
        )

    def _generate_template_draft(
        self,
        request: DraftRequest,
        deal_context: dict[str, Any] | None,
        property_context: dict[str, Any] | None,
    ) -> CommunicationDraft:
        """Generate draft using templates (fallback)."""
        templates = self._get_templates()
        template = templates.get(
            (request.purpose, request.communication_type),
            templates[(CommunicationPurpose.UPDATE, CommunicationType.EMAIL)],
        )

        # Fill in template
        recipient = request.recipient_name or "Sir/Madam"
        company = request.recipient_company or "your company"
        deal_title = deal_context["title"] if deal_context else "the opportunity"
        property_address = (
            property_context["address"] if property_context else "the property"
        )

        body = template.format(
            recipient=recipient,
            company=company,
            deal_title=deal_title,
            property_address=property_address,
            key_points=(
                "\n".join(f"- {p}" for p in request.key_points)
                if request.key_points
                else ""
            ),
        )

        subject = self._generate_template_subject(request, deal_context)

        return CommunicationDraft(
            id=f"draft_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            communication_type=request.communication_type,
            purpose=request.purpose,
            tone=request.tone,
            subject=subject,
            body=body,
            recipient_context={
                "name": request.recipient_name,
                "company": request.recipient_company,
                "role": request.recipient_role,
            },
            deal_context=deal_context,
            generated_at=datetime.now(),
        )

    def _build_prompt(
        self,
        request: DraftRequest,
        deal_context: dict[str, Any] | None,
        property_context: dict[str, Any] | None,
    ) -> str:
        """Build the LLM prompt for draft generation."""
        prompt_parts = [
            f"Draft a {request.tone.value} {request.communication_type.value} for the purpose of {request.purpose.value}.",
        ]

        if request.recipient_name:
            prompt_parts.append(f"\nRecipient: {request.recipient_name}")
        if request.recipient_company:
            prompt_parts.append(f"Company: {request.recipient_company}")
        if request.recipient_role:
            prompt_parts.append(f"Role: {request.recipient_role}")

        if deal_context:
            prompt_parts.append("\nDeal Context:")
            prompt_parts.append(f"- Deal: {deal_context['title']}")
            prompt_parts.append(f"- Type: {deal_context['deal_type']}")
            prompt_parts.append(f"- Asset: {deal_context['asset_type']}")
            prompt_parts.append(f"- Stage: {deal_context['pipeline_stage']}")
            if deal_context.get("estimated_value"):
                prompt_parts.append(f"- Value: ${deal_context['estimated_value']:,.0f}")

        if property_context:
            prompt_parts.append("\nProperty Context:")
            prompt_parts.append(f"- Address: {property_context['address']}")
            if property_context.get("district"):
                prompt_parts.append(f"- District: {property_context['district']}")
            if property_context.get("property_type"):
                prompt_parts.append(f"- Type: {property_context['property_type']}")

        if request.key_points:
            prompt_parts.append("\nKey points to include:")
            for point in request.key_points:
                prompt_parts.append(f"- {point}")

        if request.additional_context:
            prompt_parts.append(f"\nAdditional context: {request.additional_context}")

        prompt_parts.append(
            "\nGenerate only the body of the communication, no subject line."
        )
        prompt_parts.append(
            "Use professional real estate terminology appropriate for Singapore market."
        )

        return "\n".join(prompt_parts)

    def _get_templates(
        self,
    ) -> dict[tuple[CommunicationPurpose, CommunicationType], str]:
        """Get communication templates."""
        return {
            (
                CommunicationPurpose.INTRODUCTION,
                CommunicationType.EMAIL,
            ): """Dear {recipient},

I hope this email finds you well. I am reaching out regarding {deal_title} at {property_address}.

{key_points}

I would welcome the opportunity to discuss this further at your convenience.

Best regards""",
            (
                CommunicationPurpose.FOLLOW_UP,
                CommunicationType.EMAIL,
            ): """Dear {recipient},

I am following up on our previous discussion regarding {deal_title}.

{key_points}

Please let me know if you require any additional information.

Best regards""",
            (
                CommunicationPurpose.OFFER,
                CommunicationType.EMAIL,
            ): """Dear {recipient},

Further to our discussions, I am pleased to present our offer for {deal_title} at {property_address}.

{key_points}

We look forward to your favorable response.

Best regards""",
            (
                CommunicationPurpose.COUNTER_OFFER,
                CommunicationType.EMAIL,
            ): """Dear {recipient},

Thank you for your proposal regarding {deal_title}. After careful consideration, we would like to present our counter-proposal.

{key_points}

We remain committed to reaching a mutually beneficial agreement.

Best regards""",
            (
                CommunicationPurpose.UPDATE,
                CommunicationType.EMAIL,
            ): """Dear {recipient},

I am writing to provide an update on {deal_title}.

{key_points}

Please do not hesitate to reach out if you have any questions.

Best regards""",
            (
                CommunicationPurpose.THANK_YOU,
                CommunicationType.EMAIL,
            ): """Dear {recipient},

I wanted to extend my sincere thanks for your time and consideration regarding {deal_title}.

{key_points}

I look forward to our continued collaboration.

Best regards""",
        }

    def _generate_template_subject(
        self,
        request: DraftRequest,
        deal_context: dict[str, Any] | None,
    ) -> str:
        """Generate subject line from template."""
        deal_title = deal_context["title"] if deal_context else "Property Opportunity"

        subjects = {
            CommunicationPurpose.INTRODUCTION: f"Introduction - {deal_title}",
            CommunicationPurpose.FOLLOW_UP: f"Following Up - {deal_title}",
            CommunicationPurpose.OFFER: f"Offer for {deal_title}",
            CommunicationPurpose.COUNTER_OFFER: f"Counter Proposal - {deal_title}",
            CommunicationPurpose.UPDATE: f"Update on {deal_title}",
            CommunicationPurpose.THANK_YOU: f"Thank You - {deal_title}",
            CommunicationPurpose.NEGOTIATION: f"Regarding {deal_title}",
            CommunicationPurpose.CLOSING: f"Closing - {deal_title}",
            CommunicationPurpose.REQUEST: f"Request - {deal_title}",
            CommunicationPurpose.REJECTION: f"Re: {deal_title}",
        }

        return subjects.get(request.purpose, f"Re: {deal_title}")

    async def refine_draft(
        self,
        draft: CommunicationDraft,
        feedback: str,
    ) -> DraftResult:
        """Refine a draft based on feedback.

        Args:
            draft: Original draft to refine
            feedback: User feedback for refinement

        Returns:
            DraftResult with refined draft
        """
        start_time = datetime.now()

        if not self._initialized or not self.llm:
            return DraftResult(
                success=False,
                error="AI service not available for refinement",
            )

        try:
            assert self.llm is not None  # Caller ensures this
            prompt = f"""Please refine the following {draft.communication_type.value} based on this feedback:

Feedback: {feedback}

Original:
{draft.body}

Provide only the refined version, maintaining the same format and purpose."""

            response = self.llm.invoke(prompt)
            refined_content = response.content
            refined_body = (
                refined_content if isinstance(refined_content, str) else draft.body
            )

            refined_draft = CommunicationDraft(
                id=f"draft_{datetime.now().strftime('%Y%m%d%H%M%S')}_refined",
                communication_type=draft.communication_type,
                purpose=draft.purpose,
                tone=draft.tone,
                subject=draft.subject,
                body=refined_body,
                recipient_context=draft.recipient_context,
                deal_context=draft.deal_context,
                generated_at=datetime.now(),
            )

            generation_time = (datetime.now() - start_time).total_seconds() * 1000

            return DraftResult(
                success=True,
                draft=refined_draft,
                generation_time_ms=generation_time,
            )

        except Exception as e:
            logger.error(f"Error refining draft: {e}")
            return DraftResult(
                success=False,
                error=str(e),
            )


# Singleton instance
communication_drafter_service = CommunicationDrafterService()
