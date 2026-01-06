"""Pydantic schemas for AI service API endpoints."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ============================================================================
# Natural Language Query Schemas
# ============================================================================


class NLQueryRequest(BaseModel):
    """Request for natural language query processing."""

    query: str = Field(
        ..., min_length=1, max_length=2000, description="Natural language query"
    )
    user_id: str | None = Field(default=None, description="User ID for context")


class NLQueryResponse(BaseModel):
    """Response from natural language query processing."""

    query: str
    intent: str
    entities: dict[str, Any]
    structured_query: dict[str, Any] | None
    confidence: float
    suggested_action: str | None


# ============================================================================
# RAG Knowledge Base Schemas
# ============================================================================


class KnowledgeSourceType(str, Enum):
    """Types of knowledge sources."""

    PROPERTY = "property"
    DEAL = "deal"
    TRANSACTION = "transaction"
    REGULATORY = "regulatory"
    DOCUMENT = "document"
    MARKET_REPORT = "market_report"
    NEWS = "news"
    INTERNAL_NOTE = "internal_note"


class SearchMode(str, Enum):
    """Search modes for knowledge retrieval."""

    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"


class KnowledgeSearchRequest(BaseModel):
    """Request for knowledge base search."""

    query: str = Field(..., min_length=1, max_length=1000)
    mode: SearchMode = Field(default=SearchMode.HYBRID)
    source_types: list[KnowledgeSourceType] | None = None
    limit: int = Field(default=10, ge=1, le=50)
    generate_answer: bool = Field(default=True)


class SearchResultItem(BaseModel):
    """A single search result."""

    chunk_id: str
    source_type: str
    source_id: str
    content: str
    relevance_score: float
    metadata: dict[str, Any]


class KnowledgeSearchResponse(BaseModel):
    """Response from knowledge base search."""

    query: str
    results: list[SearchResultItem]
    total_chunks_searched: int
    search_time_ms: float
    generated_answer: str | None


class IngestPropertyRequest(BaseModel):
    """Request to ingest a property into knowledge base."""

    property_id: str


class IngestDealRequest(BaseModel):
    """Request to ingest a deal into knowledge base."""

    deal_id: str


class IngestDocumentRequest(BaseModel):
    """Request to ingest a document into knowledge base."""

    document_id: str
    content: str = Field(..., min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class IngestionResponse(BaseModel):
    """Response from knowledge ingestion."""

    success: bool
    chunks_created: int
    source_type: str
    source_id: str
    error: str | None = None


# ============================================================================
# Deal Scoring Schemas
# ============================================================================


class DealScoreRequest(BaseModel):
    """Request for deal scoring."""

    deal_id: str


class FactorScoreItem(BaseModel):
    """A single factor score."""

    factor: str
    score: float
    weight: float
    weighted_score: float
    rationale: str


class DealScoreResponse(BaseModel):
    """Response from deal scoring."""

    deal_id: str
    overall_score: float
    grade: str
    factor_scores: list[FactorScoreItem]
    recommendation: str
    confidence: float
    scored_at: datetime


# ============================================================================
# Scenario Optimizer Schemas
# ============================================================================


class FinancingType(str, Enum):
    """Types of financing scenarios."""

    CONVENTIONAL = "conventional"
    CONSTRUCTION = "construction"
    BRIDGE = "bridge"
    MEZZANINE = "mezzanine"


class ScenarioOptimizeRequest(BaseModel):
    """Request for scenario optimization."""

    project_id: str
    financing_types: list[FinancingType] | None = None
    target_irr: float | None = Field(default=None, ge=0, le=1)
    max_leverage: float | None = Field(default=None, ge=0, le=1)


class FinancingScenario(BaseModel):
    """A financing scenario option."""

    id: str
    financing_type: str
    loan_amount: float
    ltv_ratio: float
    interest_rate: float
    debt_service_coverage: float
    projected_irr: float
    projected_equity_multiple: float
    total_interest_cost: float
    recommendation_score: float


class ScenarioOptimizeResponse(BaseModel):
    """Response from scenario optimization."""

    project_id: str
    scenarios: list[FinancingScenario]
    recommended_scenario_id: str | None
    analysis_summary: str


# ============================================================================
# Market Predictor Schemas
# ============================================================================


class PredictionType(str, Enum):
    """Types of market predictions."""

    RENTAL = "rental"
    CAPITAL_VALUE = "capital_value"
    SUPPLY = "supply"
    DEMAND = "demand"


class MarketPredictionRequest(BaseModel):
    """Request for market prediction."""

    property_id: str | None = None
    district: str | None = None
    property_type: str | None = None
    prediction_types: list[PredictionType] | None = None
    forecast_months: int = Field(default=12, ge=1, le=60)


class PredictionItem(BaseModel):
    """A single prediction result."""

    prediction_type: str
    current_value: float | None
    predicted_value: float | None
    change_percentage: float | None
    confidence: float
    factors: list[str]


class MarketPredictionResponse(BaseModel):
    """Response from market prediction."""

    predictions: list[PredictionItem]
    forecast_months: int
    generated_at: datetime
    summary: str


# ============================================================================
# Compliance Predictor Schemas
# ============================================================================


class CompliancePredictionRequest(BaseModel):
    """Request for compliance prediction."""

    project_id: str
    submission_types: list[str] | None = None


class RegulatoryMilestone(BaseModel):
    """A regulatory milestone prediction."""

    milestone: str
    agency: str
    predicted_date: str | None
    confidence: float
    dependencies: list[str]
    risk_factors: list[str]


class CompliancePredictionResponse(BaseModel):
    """Response from compliance prediction."""

    project_id: str
    milestones: list[RegulatoryMilestone]
    critical_path_days: int
    risk_assessment: str
    recommendations: list[str]


# ============================================================================
# Due Diligence Generator Schemas
# ============================================================================


class DDGenerateRequest(BaseModel):
    """Request for due diligence checklist generation."""

    deal_id: str


class DDItemResponse(BaseModel):
    """A due diligence checklist item."""

    id: str
    category: str
    name: str
    description: str
    priority: str
    status: str
    requires_external: bool
    external_source: str | None
    assigned_to: str | None
    due_date: str | None
    notes: str | None


class DDRecommendationResponse(BaseModel):
    """A due diligence recommendation."""

    title: str
    description: str
    priority: str
    action_items: list[str]


class DDChecklistResponse(BaseModel):
    """Response from due diligence generation."""

    id: str
    deal_id: str
    deal_title: str
    items: list[DDItemResponse]
    recommendations: list[DDRecommendationResponse]
    completion_percentage: float
    estimated_days_to_complete: int


# ============================================================================
# Report Generator Schemas
# ============================================================================


class ReportType(str, Enum):
    """Types of reports that can be generated."""

    IC_MEMO = "ic_memo"
    PORTFOLIO_SUMMARY = "portfolio_summary"
    MARKET_REPORT = "market_report"
    DD_SUMMARY = "dd_summary"
    RISK_ASSESSMENT = "risk_assessment"


class ICMemoRequest(BaseModel):
    """Request for IC memo generation."""

    deal_id: str


class PortfolioReportRequest(BaseModel):
    """Request for portfolio report generation."""

    user_id: str


class ReportSectionResponse(BaseModel):
    """A report section."""

    title: str
    content: str
    order: int


class ReportResponse(BaseModel):
    """Response from report generation."""

    id: str
    report_type: str
    title: str
    subtitle: str | None
    generated_at: datetime
    sections: list[ReportSectionResponse]
    executive_summary: str | None
    recommendations: list[str]
    generation_time_ms: float


# ============================================================================
# Communication Drafter Schemas
# ============================================================================


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


class DraftCommunicationRequest(BaseModel):
    """Request for communication drafting."""

    communication_type: CommunicationType
    purpose: CommunicationPurpose
    tone: CommunicationTone = CommunicationTone.PROFESSIONAL
    recipient_name: str | None = None
    recipient_company: str | None = None
    recipient_role: str | None = None
    deal_id: str | None = None
    property_id: str | None = None
    key_points: list[str] = Field(default_factory=list)
    additional_context: str | None = None
    include_alternatives: bool = False


class CommunicationDraftResponse(BaseModel):
    """Response from communication drafting."""

    id: str
    communication_type: str
    purpose: str
    tone: str
    subject: str | None
    body: str
    alternatives: list[str]
    generation_time_ms: float


class RefineDraftRequest(BaseModel):
    """Request to refine a draft."""

    draft_id: str
    body: str
    feedback: str


# ============================================================================
# Conversational Assistant Schemas
# ============================================================================


class ChatMessageRequest(BaseModel):
    """Request for chat message processing."""

    message: str = Field(..., min_length=1, max_length=4000)
    conversation_id: str | None = None
    user_id: str | None = None


class SuggestedAction(BaseModel):
    """A suggested follow-up action."""

    action: str
    label: str


class ChatMessageResponse(BaseModel):
    """Response from chat message processing."""

    conversation_id: str
    message: str
    suggestions: list[str]
    actions_taken: list[dict[str, Any]]
    context_updates: dict[str, Any]


class ConversationListItem(BaseModel):
    """Summary of a conversation."""

    conversation_id: str
    user_id: str
    message_count: int
    created_at: datetime
    last_message_at: datetime


# ============================================================================
# Portfolio Optimizer Schemas
# ============================================================================


class OptimizationStrategy(str, Enum):
    """Portfolio optimization strategies."""

    MAXIMIZE_RETURNS = "maximize_returns"
    MINIMIZE_RISK = "minimize_risk"
    BALANCED = "balanced"
    INCOME_FOCUSED = "income_focused"
    GROWTH_FOCUSED = "growth_focused"


class RiskProfile(str, Enum):
    """Investor risk profiles."""

    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class PortfolioOptimizeRequest(BaseModel):
    """Request for portfolio optimization."""

    user_id: str
    strategy: OptimizationStrategy = OptimizationStrategy.BALANCED
    risk_profile: RiskProfile = RiskProfile.MODERATE
    max_concentration: float = Field(default=0.30, ge=0, le=1)
    min_liquidity: float = Field(default=0.10, ge=0, le=1)


class AssetAllocationItem(BaseModel):
    """Asset allocation details."""

    asset_type: str
    current_value: float
    current_percentage: float
    recommended_percentage: float
    variance: float
    action: str


class RebalancingRecommendation(BaseModel):
    """A rebalancing recommendation."""

    asset_id: str
    asset_name: str
    asset_type: str
    current_allocation: float
    recommended_action: str
    target_allocation: float
    rationale: str
    priority: str


class PortfolioMetricsResponse(BaseModel):
    """Portfolio metrics."""

    total_value: float
    total_assets: int
    weighted_yield: float
    portfolio_beta: float
    diversification_score: int
    concentration_risk: str
    liquidity_score: int


class PortfolioOptimizeResponse(BaseModel):
    """Response from portfolio optimization."""

    id: str
    user_id: str
    strategy: str
    risk_profile: str
    metrics: PortfolioMetricsResponse
    current_allocation: list[AssetAllocationItem]
    recommendations: list[RebalancingRecommendation]
    target_allocation: dict[str, float]
    expected_improvement: dict[str, float]
    analysis_summary: str


# ============================================================================
# Multi-Modal Analyzer Schemas
# ============================================================================


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


class ImageAnalysisRequest(BaseModel):
    """Request for image analysis."""

    image_base64: str | None = None
    image_url: str | None = None
    image_type: ImageType
    analysis_types: list[AnalysisType] | None = None
    property_id: str | None = None


class SpaceMetricsResponse(BaseModel):
    """Space metrics from analysis."""

    total_area_sqm: float | None = None
    usable_area_sqm: float | None = None
    room_count: int | None = None
    efficiency_ratio: float | None = None
    parking_spaces: int | None = None
    floors_detected: int | None = None


class ConditionAssessmentResponse(BaseModel):
    """Condition assessment from analysis."""

    overall_condition: str | None = None
    condition_score: int | None = None
    issues_detected: list[str] = Field(default_factory=list)
    maintenance_recommendations: list[str] = Field(default_factory=list)
    estimated_capex: str | None = None
    age_assessment: str | None = None


class ImageAnalysisResponse(BaseModel):
    """Response from image analysis."""

    id: str
    image_type: str
    analysis_type: str
    space_metrics: SpaceMetricsResponse | None = None
    condition: ConditionAssessmentResponse | None = None
    extracted_text: str | None = None
    confidence: float
    processing_time_ms: float


# ============================================================================
# Competitive Intelligence Schemas
# ============================================================================


class CompetitorTrackRequest(BaseModel):
    """Request to track a competitor."""

    name: str
    competitor_type: str
    focus_sectors: list[str] = Field(default_factory=list)
    focus_districts: list[str] = Field(default_factory=list)
    notes: str | None = None


class CompetitorResponse(BaseModel):
    """Competitor information."""

    id: str
    name: str
    competitor_type: str
    focus_sectors: list[str]
    focus_districts: list[str]
    tracked_since: datetime


class CompetitorActivityResponse(BaseModel):
    """Competitor activity."""

    id: str
    competitor_id: str
    competitor_name: str
    category: str
    title: str
    description: str
    location: str | None
    relevance_score: float
    detected_at: datetime


class CompetitiveAlertResponse(BaseModel):
    """Competitive alert."""

    id: str
    priority: str
    title: str
    description: str
    competitor_id: str
    competitor_name: str
    action_required: str
    expires_at: datetime


class CompetitiveIntelligenceRequest(BaseModel):
    """Request for competitive intelligence."""

    user_id: str


class CompetitiveIntelligenceResponse(BaseModel):
    """Response from competitive intelligence."""

    competitors: list[CompetitorResponse]
    activities: list[CompetitorActivityResponse]
    alerts: list[CompetitiveAlertResponse]
    summary: str


# ============================================================================
# Workflow Engine Schemas
# ============================================================================


class WorkflowTrigger(str, Enum):
    """Events that can trigger workflows."""

    DEAL_CREATED = "deal_created"
    DEAL_STAGE_CHANGED = "deal_stage_changed"
    DEADLINE_APPROACHING = "deadline_approaching"
    DOCUMENT_UPLOADED = "document_uploaded"
    APPROVAL_REQUIRED = "approval_required"
    COMPLIANCE_FLAG = "compliance_flag"
    MARKET_ALERT = "market_alert"


class TriggerWorkflowRequest(BaseModel):
    """Request to trigger a workflow."""

    trigger: WorkflowTrigger
    event_data: dict[str, Any]


class WorkflowStepResponse(BaseModel):
    """A workflow step result."""

    action_id: str
    action_type: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    result: dict[str, Any] | None
    error: str | None


class WorkflowResultResponse(BaseModel):
    """Response from workflow execution."""

    workflow_id: str
    workflow_name: str
    instance_id: str
    status: str
    started_at: datetime
    completed_at: datetime | None
    steps: list[WorkflowStepResponse]


class WorkflowDefinitionResponse(BaseModel):
    """Workflow definition."""

    id: str
    name: str
    description: str
    trigger: str
    is_active: bool
    action_count: int


# ============================================================================
# Anomaly Detection Schemas
# ============================================================================


class AnomalyDetectionRequest(BaseModel):
    """Request for anomaly detection."""

    deal_id: str | None = None
    property_id: str | None = None
    project_id: str | None = None


class AnomalyAlert(BaseModel):
    """An anomaly alert."""

    id: str
    alert_type: str
    severity: str
    title: str
    description: str
    entity_type: str
    entity_id: str
    detected_value: Any
    expected_range: dict[str, Any] | None
    recommendation: str
    detected_at: datetime


class AnomalyDetectionResponse(BaseModel):
    """Response from anomaly detection."""

    alerts: list[AnomalyAlert]
    entities_scanned: int
    scan_time_ms: float


# ============================================================================
# Document Extraction Schemas
# ============================================================================


class DocumentExtractionRequest(BaseModel):
    """Request for document extraction."""

    document_base64: str | None = None
    document_url: str | None = None
    document_type: str = "contract"
    extract_tables: bool = True
    extract_clauses: bool = True


class ExtractedClause(BaseModel):
    """An extracted contract clause."""

    clause_type: str
    text: str
    page_number: int | None
    confidence: float


class ExtractedTable(BaseModel):
    """An extracted table."""

    table_id: str
    headers: list[str]
    rows: list[list[str]]
    page_number: int | None


class DocumentExtractionResponse(BaseModel):
    """Response from document extraction."""

    document_type: str
    clauses: list[ExtractedClause]
    tables: list[ExtractedTable]
    key_dates: dict[str, str]
    parties: list[str]
    summary: str
    processing_time_ms: float


# ============================================================================
# AI Service Stats Schema
# ============================================================================


class AIServiceStatsResponse(BaseModel):
    """Statistics for AI services."""

    service_name: str
    initialized: bool
    stats: dict[str, Any]
