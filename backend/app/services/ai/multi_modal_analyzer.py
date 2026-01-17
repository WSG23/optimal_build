"""Phase 4.2: Multi-Modal Analysis.

Analyze floor plans, site images, and documents using vision AI.
"""

from __future__ import annotations

import base64
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


class ImageType(str, Enum):
    """Types of images for analysis."""

    FLOOR_PLAN = "floor_plan"
    SITE_PHOTO = "site_photo"
    AERIAL_VIEW = "aerial_view"
    BUILDING_FACADE = "building_facade"
    INTERIOR = "interior"
    DOCUMENT = "document"
    MAP = "map"


class AnalysisType(str, Enum):
    """Types of analysis to perform."""

    SPACE_ANALYSIS = "space_analysis"
    CONDITION_ASSESSMENT = "condition_assessment"
    LAYOUT_EXTRACTION = "layout_extraction"
    TEXT_EXTRACTION = "text_extraction"
    PROPERTY_VALUATION = "property_valuation"
    COMPLIANCE_CHECK = "compliance_check"


@dataclass
class SpaceMetrics:
    """Metrics extracted from floor plan analysis."""

    total_area_sqm: float | None = None
    usable_area_sqm: float | None = None
    room_count: int | None = None
    layout_type: str | None = None
    efficiency_ratio: float | None = None
    parking_spaces: int | None = None
    floors_detected: int | None = None


@dataclass
class ConditionAssessment:
    """Assessment of property condition from photos."""

    overall_condition: str  # excellent, good, fair, poor
    condition_score: int  # 1-10
    visible_issues: list[str]
    maintenance_recommendations: list[str]
    estimated_capex: str | None = None
    age_assessment: str | None = None


@dataclass
class ExtractedText:
    """Text extracted from documents/images."""

    raw_text: str
    structured_data: dict[str, Any]
    confidence: float
    document_type: str | None = None


@dataclass
class LayoutAnalysis:
    """Analysis of floor plan layout."""

    rooms: list[dict[str, Any]]
    circulation_paths: list[str]
    natural_light_assessment: str
    flexibility_score: int  # 1-10
    recommendations: list[str]


@dataclass
class MultiModalAnalysisResult:
    """Result from multi-modal analysis."""

    id: str
    image_type: ImageType
    analysis_type: AnalysisType
    space_metrics: SpaceMetrics | None = None
    condition: ConditionAssessment | None = None
    extracted_text: ExtractedText | None = None
    layout: LayoutAnalysis | None = None
    raw_analysis: str | None = None
    confidence: float = 0.0
    processing_time_ms: float = 0.0
    analyzed_at: datetime = field(default_factory=datetime.now)


@dataclass
class AnalysisRequest:
    """Request for multi-modal analysis."""

    image_data: bytes | None = None
    image_path: str | None = None
    image_url: str | None = None
    image_type: ImageType = ImageType.DOCUMENT
    analysis_types: list[AnalysisType] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)


class MultiModalAnalyzerService:
    """Service for multi-modal AI analysis."""

    llm: Optional[ChatOpenAI]

    def __init__(self) -> None:
        """Initialize the analyzer."""
        try:
            self.llm = ChatOpenAI(
                model="gpt-4o",  # Vision-capable model
                temperature=0.1,
            )
            self._initialized = True
        except Exception as e:
            logger.warning(f"Multi-Modal Analyzer not initialized: {e}")
            self._initialized = False
            self.llm = None

    async def analyze(
        self,
        request: AnalysisRequest,
    ) -> MultiModalAnalysisResult:
        """Analyze an image using vision AI.

        Args:
            request: Analysis request with image and type

        Returns:
            MultiModalAnalysisResult with analysis
        """
        start_time = datetime.now()

        try:
            # Get image data
            image_base64 = await self._get_image_base64(request)
            if not image_base64:
                return self._empty_result(request.image_type, request.analysis_types)

            # Determine analysis types
            analysis_types = request.analysis_types or self._default_analysis_types(
                request.image_type
            )

            # Perform analysis
            result = MultiModalAnalysisResult(
                id=str(uuid4()),
                image_type=request.image_type,
                analysis_type=(
                    analysis_types[0] if analysis_types else AnalysisType.SPACE_ANALYSIS
                ),
            )

            for analysis_type in analysis_types:
                if analysis_type == AnalysisType.SPACE_ANALYSIS:
                    result.space_metrics = await self._analyze_space(image_base64, request)
                elif analysis_type == AnalysisType.CONDITION_ASSESSMENT:
                    result.condition = await self._assess_condition(image_base64, request)
                elif analysis_type == AnalysisType.LAYOUT_EXTRACTION:
                    result.layout = await self._extract_layout(image_base64, request)
                elif analysis_type == AnalysisType.TEXT_EXTRACTION:
                    result.extracted_text = await self._extract_text(image_base64, request)

            result.processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            result.confidence = 0.85 if self._initialized else 0.3

            return result

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return self._empty_result(request.image_type, request.analysis_types)

    async def _get_image_base64(self, request: AnalysisRequest) -> str | None:
        """Get base64 encoded image data."""
        if request.image_data:
            return base64.b64encode(request.image_data).decode("utf-8")

        if request.image_path:
            path = Path(request.image_path)
            if path.exists():
                return base64.b64encode(path.read_bytes()).decode("utf-8")

        if request.image_url:
            # In production, would fetch from URL
            return None

        return None

    def _default_analysis_types(self, image_type: ImageType) -> list[AnalysisType]:
        """Get default analysis types for an image type."""
        defaults = {
            ImageType.FLOOR_PLAN: [
                AnalysisType.SPACE_ANALYSIS,
                AnalysisType.LAYOUT_EXTRACTION,
            ],
            ImageType.SITE_PHOTO: [AnalysisType.CONDITION_ASSESSMENT],
            ImageType.AERIAL_VIEW: [AnalysisType.SPACE_ANALYSIS],
            ImageType.BUILDING_FACADE: [AnalysisType.CONDITION_ASSESSMENT],
            ImageType.INTERIOR: [AnalysisType.CONDITION_ASSESSMENT],
            ImageType.DOCUMENT: [AnalysisType.TEXT_EXTRACTION],
            ImageType.MAP: [AnalysisType.SPACE_ANALYSIS],
        }
        return defaults.get(image_type, [AnalysisType.SPACE_ANALYSIS])

    async def _analyze_space(
        self,
        image_base64: str,
        request: AnalysisRequest,
    ) -> SpaceMetrics:
        """Analyze space metrics from floor plan."""
        if not self._initialized or not self.llm:
            return SpaceMetrics()

        prompt = """Analyze this floor plan image and extract the following metrics in JSON format:
{
    "total_area_sqm": <estimated total area in sqm or null>,
    "usable_area_sqm": <estimated usable area in sqm or null>,
    "room_count": <number of distinct rooms or null>,
    "layout_type": <"open plan", "cellular", "hybrid", or null>,
    "efficiency_ratio": <usable/total ratio as decimal or null>,
    "parking_spaces": <number of parking spaces visible or null>,
    "floors_detected": <number of floors shown or null>
}

Only return valid JSON."""

        try:
            response = self.llm.invoke(
                [
                    {
                        "type": "text",
                        "text": prompt,
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                    },
                ]
            )

            import json

            content = response.content
            if not isinstance(content, str):
                content = "{}"
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(content[start:end])
                return SpaceMetrics(**data)
        except Exception as e:
            logger.warning(f"Space analysis failed: {e}")

        return SpaceMetrics()

    async def _assess_condition(
        self,
        image_base64: str,
        request: AnalysisRequest,
    ) -> ConditionAssessment:
        """Assess property condition from photos."""
        if not self._initialized or not self.llm:
            return ConditionAssessment(
                overall_condition="unknown",
                condition_score=5,
                visible_issues=[],
                maintenance_recommendations=[],
            )

        prompt = """Analyze this property photo and assess its condition in JSON format:
{
    "overall_condition": <"excellent", "good", "fair", or "poor">,
    "condition_score": <1-10 score>,
    "visible_issues": [<list of visible issues or defects>],
    "maintenance_recommendations": [<list of recommended maintenance>],
    "estimated_capex": <"minimal", "moderate", "significant", or "major" or null>,
    "age_assessment": <estimated building age description or null>
}

Only return valid JSON."""

        try:
            response = self.llm.invoke(
                [
                    {
                        "type": "text",
                        "text": prompt,
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                    },
                ]
            )

            import json

            content = response.content
            if not isinstance(content, str):
                content = "{}"
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(content[start:end])
                return ConditionAssessment(**data)
        except Exception as e:
            logger.warning(f"Condition assessment failed: {e}")

        return ConditionAssessment(
            overall_condition="unknown",
            condition_score=5,
            visible_issues=[],
            maintenance_recommendations=[],
        )

    async def _extract_layout(
        self,
        image_base64: str,
        request: AnalysisRequest,
    ) -> LayoutAnalysis:
        """Extract layout information from floor plan."""
        if not self._initialized or not self.llm:
            return LayoutAnalysis(
                rooms=[],
                circulation_paths=[],
                natural_light_assessment="Unknown",
                flexibility_score=5,
                recommendations=[],
            )

        prompt = """Analyze this floor plan and extract layout information in JSON format:
{
    "rooms": [{"name": "room name", "approximate_size": "small/medium/large", "has_windows": true/false}],
    "circulation_paths": ["description of main circulation/corridors"],
    "natural_light_assessment": "description of natural lighting",
    "flexibility_score": <1-10 how flexible/adaptable the layout is>,
    "recommendations": ["layout improvement suggestions"]
}

Only return valid JSON."""

        try:
            response = self.llm.invoke(
                [
                    {
                        "type": "text",
                        "text": prompt,
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                    },
                ]
            )

            import json

            content = response.content
            if not isinstance(content, str):
                content = "{}"
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(content[start:end])
                return LayoutAnalysis(**data)
        except Exception as e:
            logger.warning(f"Layout extraction failed: {e}")

        return LayoutAnalysis(
            rooms=[],
            circulation_paths=[],
            natural_light_assessment="Unknown",
            flexibility_score=5,
            recommendations=[],
        )

    async def _extract_text(
        self,
        image_base64: str,
        request: AnalysisRequest,
    ) -> ExtractedText:
        """Extract text from documents/images."""
        if not self._initialized or not self.llm:
            return ExtractedText(
                raw_text="",
                structured_data={},
                confidence=0.0,
            )

        prompt = """Extract all text from this document image and structure it in JSON format:
{
    "raw_text": "all visible text transcribed",
    "structured_data": {
        "title": "document title if visible",
        "date": "any dates found",
        "parties": ["names of parties mentioned"],
        "key_values": {"label": "value"},
        "document_type": "type of document"
    },
    "document_type": "contract/letter/form/report/other"
}

Only return valid JSON."""

        try:
            response = self.llm.invoke(
                [
                    {
                        "type": "text",
                        "text": prompt,
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                    },
                ]
            )

            import json

            content = response.content
            if not isinstance(content, str):
                content = "{}"
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(content[start:end])
                return ExtractedText(
                    raw_text=data.get("raw_text", ""),
                    structured_data=data.get("structured_data", {}),
                    confidence=0.85,
                    document_type=data.get("document_type"),
                )
        except Exception as e:
            logger.warning(f"Text extraction failed: {e}")

        return ExtractedText(
            raw_text="",
            structured_data={},
            confidence=0.0,
        )

    def _empty_result(
        self,
        image_type: ImageType,
        analysis_types: list[AnalysisType],
    ) -> MultiModalAnalysisResult:
        """Create an empty result for failed analysis."""
        return MultiModalAnalysisResult(
            id=str(uuid4()),
            image_type=image_type,
            analysis_type=(analysis_types[0] if analysis_types else AnalysisType.SPACE_ANALYSIS),
            confidence=0.0,
        )

    async def compare_floor_plans(
        self,
        plan1_base64: str,
        plan2_base64: str,
    ) -> dict[str, Any]:
        """Compare two floor plans.

        Args:
            plan1_base64: First floor plan as base64
            plan2_base64: Second floor plan as base64

        Returns:
            Comparison results
        """
        if not self._initialized or not self.llm:
            return {"error": "Service not available"}

        prompt = """Compare these two floor plans and provide analysis in JSON format:
{
    "similarities": ["list of similarities"],
    "differences": ["list of key differences"],
    "size_comparison": "which appears larger and by how much",
    "layout_comparison": "comparison of layouts",
    "recommendation": "which is better and why"
}

Only return valid JSON."""

        try:
            response = self.llm.invoke(
                [
                    {
                        "type": "text",
                        "text": prompt,
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{plan1_base64}"},
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{plan2_base64}"},
                    },
                ]
            )

            import json

            content = response.content
            if not isinstance(content, str):
                content = "{}"
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                parsed: dict[str, Any] = json.loads(content[start:end])
                return parsed
        except Exception as e:
            logger.warning(f"Floor plan comparison failed: {e}")

        return {"error": "Comparison failed"}


# Singleton instance
multi_modal_analyzer_service = MultiModalAnalyzerService()
