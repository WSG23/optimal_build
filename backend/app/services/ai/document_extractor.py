"""Phase 1.2: Document Intelligence - PDF/Contract Extraction.

Uses vision LLM + OCR to extract structured data from uploaded documents.
"""

from __future__ import annotations

import base64
import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Optional

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DocumentType(str, Enum):
    """Types of documents that can be processed."""

    TENANCY_AGREEMENT = "tenancy_agreement"
    SALE_PURCHASE_AGREEMENT = "spa"
    ZONING_LETTER = "zoning_letter"
    VALUATION_REPORT = "valuation_report"
    TITLE_DEED = "title_deed"
    BUILDING_PERMIT = "building_permit"
    REGULATORY_APPROVAL = "regulatory_approval"
    FLOOR_PLAN = "floor_plan"
    UNKNOWN = "unknown"


class ConfidenceLevel(str, Enum):
    """Confidence levels for extracted data."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Pydantic schemas for extraction
class TenancyAgreementSchema(BaseModel):
    """Extracted data from a tenancy agreement."""

    landlord_name: str | None = Field(None, description="Name of the landlord")
    tenant_name: str | None = Field(None, description="Name of the tenant")
    property_address: str | None = Field(None, description="Address of the property")
    monthly_rent: float | None = Field(None, description="Monthly rent amount")
    rent_currency: str = Field("SGD", description="Currency for rent")
    security_deposit: float | None = Field(None, description="Security deposit amount")
    lease_start_date: date | None = Field(None, description="Lease commencement date")
    lease_end_date: date | None = Field(None, description="Lease expiry date")
    lease_term_months: int | None = Field(None, description="Lease term in months")
    renewal_option: str | None = Field(None, description="Renewal option details")
    rent_escalation: str | None = Field(None, description="Rent escalation clause")
    permitted_use: str | None = Field(None, description="Permitted use of premises")
    fit_out_period: int | None = Field(None, description="Fit-out period in days")
    break_clause: str | None = Field(None, description="Break clause details")


class SalesPurchaseSchema(BaseModel):
    """Extracted data from a Sale & Purchase Agreement."""

    seller_name: str | None = Field(None, description="Name of the seller")
    buyer_name: str | None = Field(None, description="Name of the buyer")
    property_address: str | None = Field(None, description="Address of the property")
    purchase_price: float | None = Field(None, description="Purchase price")
    price_currency: str = Field("SGD", description="Currency for price")
    option_fee: float | None = Field(None, description="Option fee amount")
    exercise_date: date | None = Field(None, description="Option exercise date")
    completion_date: date | None = Field(None, description="Completion date")
    conditions_precedent: list[str] = Field(
        default_factory=list, description="Conditions precedent"
    )
    encumbrances: list[str] = Field(default_factory=list, description="Known encumbrances")
    special_conditions: list[str] = Field(default_factory=list, description="Special conditions")


class ZoningLetterSchema(BaseModel):
    """Extracted data from a zoning/planning letter."""

    property_address: str | None = Field(None, description="Property address")
    lot_number: str | None = Field(None, description="Lot number")
    zoning_code: str | None = Field(None, description="Zoning code")
    zoning_description: str | None = Field(None, description="Zoning description")
    plot_ratio: float | None = Field(None, description="Gross plot ratio")
    site_coverage: float | None = Field(None, description="Site coverage percentage")
    building_height: float | None = Field(None, description="Max building height in meters")
    setback_front: float | None = Field(None, description="Front setback in meters")
    setback_side: float | None = Field(None, description="Side setback in meters")
    setback_rear: float | None = Field(None, description="Rear setback in meters")
    permitted_uses: list[str] = Field(default_factory=list, description="Permitted uses")
    special_conditions: list[str] = Field(
        default_factory=list, description="Special planning conditions"
    )
    heritage_status: str | None = Field(None, description="Heritage/conservation status")
    effective_date: date | None = Field(None, description="Letter effective date")


class ValuationReportSchema(BaseModel):
    """Extracted data from a valuation report."""

    property_address: str | None = Field(None, description="Property address")
    valuation_date: date | None = Field(None, description="Valuation date")
    valuer_name: str | None = Field(None, description="Name of the valuer")
    valuer_company: str | None = Field(None, description="Valuation company")
    market_value: float | None = Field(None, description="Market value")
    value_currency: str = Field("SGD", description="Currency for value")
    value_per_sqft: float | None = Field(None, description="Value per square foot")
    land_area_sqft: float | None = Field(None, description="Land area in sqft")
    gross_floor_area_sqft: float | None = Field(None, description="GFA in sqft")
    property_type: str | None = Field(None, description="Property type")
    tenure: str | None = Field(None, description="Tenure type")
    cap_rate: float | None = Field(None, description="Capitalization rate")
    noi: float | None = Field(None, description="Net operating income")
    comparable_properties: list[dict[str, Any]] = Field(
        default_factory=list, description="Comparable properties used"
    )
    valuation_approach: str | None = Field(None, description="Valuation approach used")
    key_assumptions: list[str] = Field(default_factory=list, description="Key assumptions")


@dataclass
class ExtractedField:
    """A single extracted field with metadata."""

    name: str
    value: Any
    confidence: ConfidenceLevel
    source_page: int | None = None
    source_text: str | None = None


@dataclass
class ExtractionResult:
    """Result from document extraction."""

    success: bool
    document_type: DocumentType
    document_type_confidence: ConfidenceLevel
    extracted_data: dict[str, Any] = field(default_factory=dict)
    fields: list[ExtractedField] = field(default_factory=list)
    low_confidence_fields: list[str] = field(default_factory=list)
    processing_time_ms: float = 0.0
    page_count: int = 0
    error: str | None = None
    raw_text: str | None = None


EXTRACTION_PROMPTS = {
    DocumentType.TENANCY_AGREEMENT: """Extract the following information from this tenancy/lease agreement:
- Landlord name
- Tenant name
- Property address
- Monthly rent amount and currency
- Security deposit
- Lease start and end dates
- Lease term in months
- Renewal options
- Rent escalation clauses
- Permitted use
- Fit-out period
- Break clause details

Return as JSON with field names matching: landlord_name, tenant_name, property_address, monthly_rent, rent_currency, security_deposit, lease_start_date, lease_end_date, lease_term_months, renewal_option, rent_escalation, permitted_use, fit_out_period, break_clause.

For dates, use YYYY-MM-DD format. For amounts, use numbers only without currency symbols.""",
    DocumentType.SALE_PURCHASE_AGREEMENT: """Extract the following from this Sale & Purchase Agreement:
- Seller name
- Buyer name
- Property address
- Purchase price and currency
- Option fee
- Option exercise date
- Completion date
- Conditions precedent (as list)
- Known encumbrances (as list)
- Special conditions (as list)

Return as JSON with field names: seller_name, buyer_name, property_address, purchase_price, price_currency, option_fee, exercise_date, completion_date, conditions_precedent, encumbrances, special_conditions.""",
    DocumentType.ZONING_LETTER: """Extract the following from this zoning/planning approval letter:
- Property address
- Lot number
- Zoning code
- Zoning description
- Gross plot ratio
- Site coverage percentage
- Maximum building height (meters)
- Setbacks (front, side, rear in meters)
- Permitted uses (as list)
- Special planning conditions (as list)
- Heritage/conservation status
- Letter effective date

Return as JSON with field names: property_address, lot_number, zoning_code, zoning_description, plot_ratio, site_coverage, building_height, setback_front, setback_side, setback_rear, permitted_uses, special_conditions, heritage_status, effective_date.""",
    DocumentType.VALUATION_REPORT: """Extract the following from this valuation report:
- Property address
- Valuation date
- Valuer name and company
- Market value and currency
- Value per square foot
- Land area (sqft)
- Gross floor area (sqft)
- Property type
- Tenure
- Capitalization rate
- Net operating income
- Valuation approach used
- Key assumptions (as list)
- Comparable properties (as list of objects with address, price, psf)

Return as JSON with field names: property_address, valuation_date, valuer_name, valuer_company, market_value, value_currency, value_per_sqft, land_area_sqft, gross_floor_area_sqft, property_type, tenure, cap_rate, noi, valuation_approach, key_assumptions, comparable_properties.""",
}


class DocumentExtractionService:
    """Service for extracting structured data from documents using AI."""

    llm: Optional[ChatOpenAI]
    vision_llm: Optional[ChatOpenAI]

    def __init__(self) -> None:
        """Initialize the document extraction service."""
        try:
            self.llm = ChatOpenAI(
                model="gpt-4-turbo",
                temperature=0,
            )
            self.vision_llm = ChatOpenAI(
                model="gpt-4-turbo",
                temperature=0,
                max_tokens=4096,
            )
            self._initialized = True
        except Exception as e:
            logger.warning(f"Document Extraction Service not initialized: {e}")
            self._initialized = False
            self.llm = None
            self.vision_llm = None

    async def detect_document_type(self, text_content: str) -> tuple[DocumentType, ConfidenceLevel]:
        """Detect the type of document from its content.

        Args:
            text_content: Text extracted from the document

        Returns:
            Tuple of (DocumentType, ConfidenceLevel)
        """
        if not self._initialized or not self.llm:
            return DocumentType.UNKNOWN, ConfidenceLevel.LOW

        prompt = f"""Analyze this document text and determine what type of document it is.

Document text (first 2000 chars):
{text_content[:2000]}

Respond with ONLY one of these document types:
- tenancy_agreement (for lease agreements, tenancy contracts)
- spa (for sale & purchase agreements)
- zoning_letter (for zoning approvals, planning letters)
- valuation_report (for property valuations, appraisals)
- title_deed (for title documents, certificates of title)
- building_permit (for building permits, construction approvals)
- regulatory_approval (for other regulatory approvals)
- floor_plan (for architectural floor plans)
- unknown (if cannot determine)

Also provide confidence: high, medium, or low

Format: TYPE|CONFIDENCE"""

        try:
            response = self.llm.invoke(prompt)
            content = response.content
            if not isinstance(content, str):
                return DocumentType.UNKNOWN, ConfidenceLevel.LOW
            parts = content.strip().split("|")

            doc_type_str = parts[0].strip().lower()
            confidence_str = parts[1].strip().lower() if len(parts) > 1 else "medium"

            # Map to enum
            type_map = {
                "tenancy_agreement": DocumentType.TENANCY_AGREEMENT,
                "spa": DocumentType.SALE_PURCHASE_AGREEMENT,
                "zoning_letter": DocumentType.ZONING_LETTER,
                "valuation_report": DocumentType.VALUATION_REPORT,
                "title_deed": DocumentType.TITLE_DEED,
                "building_permit": DocumentType.BUILDING_PERMIT,
                "regulatory_approval": DocumentType.REGULATORY_APPROVAL,
                "floor_plan": DocumentType.FLOOR_PLAN,
            }
            doc_type = type_map.get(doc_type_str, DocumentType.UNKNOWN)

            confidence_map = {
                "high": ConfidenceLevel.HIGH,
                "medium": ConfidenceLevel.MEDIUM,
                "low": ConfidenceLevel.LOW,
            }
            confidence = confidence_map.get(confidence_str, ConfidenceLevel.MEDIUM)

            return doc_type, confidence

        except Exception as e:
            logger.error(f"Error detecting document type: {e}")
            return DocumentType.UNKNOWN, ConfidenceLevel.LOW

    async def extract_from_text(
        self,
        text_content: str,
        document_type: DocumentType | None = None,
    ) -> ExtractionResult:
        """Extract structured data from document text.

        Args:
            text_content: Text content of the document
            document_type: Optional document type (auto-detected if not provided)

        Returns:
            ExtractionResult with extracted data
        """
        start_time = datetime.now()

        if not self._initialized or not self.llm:
            return ExtractionResult(
                success=False,
                document_type=DocumentType.UNKNOWN,
                document_type_confidence=ConfidenceLevel.LOW,
                error="Document extraction service not initialized",
            )

        try:
            # Detect document type if not provided
            if document_type is None:
                document_type, type_confidence = await self.detect_document_type(text_content)
            else:
                type_confidence = ConfidenceLevel.HIGH

            if document_type == DocumentType.UNKNOWN:
                return ExtractionResult(
                    success=False,
                    document_type=document_type,
                    document_type_confidence=type_confidence,
                    error="Could not determine document type",
                    raw_text=text_content[:1000],
                )

            # Get extraction prompt
            extraction_prompt = EXTRACTION_PROMPTS.get(document_type)
            if not extraction_prompt:
                return ExtractionResult(
                    success=False,
                    document_type=document_type,
                    document_type_confidence=type_confidence,
                    error=f"No extraction template for document type: {document_type}",
                )

            # Extract data
            full_prompt = f"""{extraction_prompt}

Document content:
{text_content}

Important:
- If a field is not found, set it to null
- For dates, use YYYY-MM-DD format
- For monetary values, use numbers only
- Be precise and extract only what's explicitly stated"""

            response = self.llm.invoke(full_prompt)

            # Parse JSON response
            import json

            try:
                # Try to extract JSON from response
                content = response.content
                if not isinstance(content, str):
                    content = ""
                # Find JSON block if wrapped in markdown
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]

                extracted_data = json.loads(content.strip())
            except json.JSONDecodeError:
                # Try to parse as-is
                raw_content = response.content
                extracted_data = {
                    "raw_response": raw_content if isinstance(raw_content, str) else ""
                }

            # Identify low confidence fields (nulls or empty)
            low_confidence_fields = [
                key
                for key, value in extracted_data.items()
                if value is None or value == "" or value == []
            ]

            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            return ExtractionResult(
                success=True,
                document_type=document_type,
                document_type_confidence=type_confidence,
                extracted_data=extracted_data,
                low_confidence_fields=low_confidence_fields,
                processing_time_ms=processing_time,
                raw_text=text_content[:500],
            )

        except Exception as e:
            logger.error(f"Error extracting document data: {e}")
            return ExtractionResult(
                success=False,
                document_type=document_type or DocumentType.UNKNOWN,
                document_type_confidence=ConfidenceLevel.LOW,
                error=str(e),
            )

    async def extract_from_image(
        self,
        image_data: bytes,
        document_type: DocumentType | None = None,
    ) -> ExtractionResult:
        """Extract data from a document image using vision AI.

        Args:
            image_data: Raw image bytes (PNG, JPEG, etc.)
            document_type: Optional document type

        Returns:
            ExtractionResult with extracted data
        """
        start_time = datetime.now()

        if not self._initialized or not self.vision_llm:
            return ExtractionResult(
                success=False,
                document_type=DocumentType.UNKNOWN,
                document_type_confidence=ConfidenceLevel.LOW,
                error="Vision extraction service not initialized",
            )

        try:
            # Encode image to base64
            image_base64 = base64.b64encode(image_data).decode("utf-8")

            # First, detect document type if not provided
            if document_type is None:
                detect_prompt = """Look at this document image and determine what type of document it is.

Respond with ONLY one of:
- tenancy_agreement
- spa
- zoning_letter
- valuation_report
- title_deed
- building_permit
- regulatory_approval
- floor_plan
- unknown

Then pipe and confidence: high, medium, or low
Format: TYPE|CONFIDENCE"""

                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": detect_prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{image_base64}"},
                            },
                        ],
                    }
                ]

                response = self.vision_llm.invoke(messages)
                content = response.content
                if not isinstance(content, str):
                    content = "unknown|low"
                parts = content.strip().split("|")
                doc_type_str = parts[0].strip().lower()

                type_map = {
                    "tenancy_agreement": DocumentType.TENANCY_AGREEMENT,
                    "spa": DocumentType.SALE_PURCHASE_AGREEMENT,
                    "zoning_letter": DocumentType.ZONING_LETTER,
                    "valuation_report": DocumentType.VALUATION_REPORT,
                }
                document_type = type_map.get(doc_type_str, DocumentType.UNKNOWN)

            # Get extraction prompt
            extraction_prompt = EXTRACTION_PROMPTS.get(
                document_type,
                "Extract all relevant information from this document as JSON.",
            )

            # Extract data from image
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": extraction_prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{image_base64}"},
                        },
                    ],
                }
            ]

            response = self.vision_llm.invoke(messages)

            # Parse response
            import json

            try:
                content = response.content
                if not isinstance(content, str):
                    content = ""
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                extracted_data = json.loads(content.strip())
            except json.JSONDecodeError:
                raw_content = response.content
                extracted_data = {
                    "raw_response": raw_content if isinstance(raw_content, str) else ""
                }

            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            return ExtractionResult(
                success=True,
                document_type=document_type,
                document_type_confidence=ConfidenceLevel.MEDIUM,
                extracted_data=extracted_data,
                processing_time_ms=processing_time,
            )

        except Exception as e:
            logger.error(f"Error extracting from image: {e}")
            return ExtractionResult(
                success=False,
                document_type=document_type or DocumentType.UNKNOWN,
                document_type_confidence=ConfidenceLevel.LOW,
                error=str(e),
            )

    async def extract_from_pdf(
        self,
        pdf_data: bytes,
        document_type: DocumentType | None = None,
    ) -> ExtractionResult:
        """Extract data from a PDF document.

        Args:
            pdf_data: Raw PDF bytes
            document_type: Optional document type

        Returns:
            ExtractionResult with extracted data
        """
        try:
            # Try to extract text from PDF
            import fitz  # PyMuPDF

            pdf_doc = fitz.open(stream=pdf_data, filetype="pdf")
            page_count = len(pdf_doc)

            # Extract text from all pages
            text_content = ""
            for page in pdf_doc:
                text_content += page.get_text() + "\n\n"

            pdf_doc.close()

            if text_content.strip():
                # Use text extraction if we got meaningful text
                result = await self.extract_from_text(text_content, document_type)
                result.page_count = page_count
                return result
            else:
                # Fall back to image extraction for scanned PDFs
                # Convert first page to image
                pdf_doc = fitz.open(stream=pdf_data, filetype="pdf")
                first_page = pdf_doc[0]
                pix = first_page.get_pixmap(dpi=150)
                image_data = pix.tobytes("png")
                pdf_doc.close()

                result = await self.extract_from_image(image_data, document_type)
                result.page_count = page_count
                return result

        except ImportError:
            logger.warning("PyMuPDF not installed, cannot process PDFs")
            return ExtractionResult(
                success=False,
                document_type=document_type or DocumentType.UNKNOWN,
                document_type_confidence=ConfidenceLevel.LOW,
                error="PDF processing requires PyMuPDF (fitz) library",
            )
        except Exception as e:
            logger.error(f"Error extracting from PDF: {e}")
            return ExtractionResult(
                success=False,
                document_type=document_type or DocumentType.UNKNOWN,
                document_type_confidence=ConfidenceLevel.LOW,
                error=str(e),
            )


# Singleton instance
document_extraction_service = DocumentExtractionService()
