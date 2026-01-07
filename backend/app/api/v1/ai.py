"""API endpoints for AI services.

This module exposes the 16 AI services implemented in Phase 1-4 of the AI rollout.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import Role, require_reviewer, require_viewer, get_db
from app.schemas.ai import (
    # Natural Language Query
    NLQueryRequest,
    NLQueryResponse,
    # Knowledge Base
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    SearchResultItem,
    IngestPropertyRequest,
    IngestDealRequest,
    IngestDocumentRequest,
    IngestionResponse,
    # Deal Scoring
    DealScoreRequest,
    DealScoreResponse,
    FactorScoreItem,
    # Scenario Optimizer
    ScenarioOptimizeRequest,
    ScenarioOptimizeResponse,
    FinancingScenario,
    FinancingType,
    # Market Predictor
    MarketPredictionRequest,
    MarketPredictionResponse,
    PredictionItem,
    PredictionType,
    # Compliance Predictor
    CompliancePredictionRequest,
    CompliancePredictionResponse,
    RegulatoryMilestone,
    # Due Diligence
    DDGenerateRequest,
    DDChecklistResponse,
    DDItemResponse,
    DDRecommendationResponse,
    # Reports
    ICMemoRequest,
    PortfolioReportRequest,
    ReportResponse,
    ReportSectionResponse,
    # Communication
    DraftCommunicationRequest,
    CommunicationDraftResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    ConversationListItem,
    # Portfolio
    PortfolioOptimizeRequest,
    PortfolioOptimizeResponse,
    AssetAllocationItem,
    RebalancingRecommendation,
    PortfolioMetricsResponse,
    # Multi-Modal
    ImageAnalysisRequest,
    ImageAnalysisResponse,
    SpaceMetricsResponse,
    ConditionAssessmentResponse,
    # Competitive Intelligence
    CompetitorTrackRequest,
    CompetitorResponse,
    CompetitiveIntelligenceRequest,
    CompetitiveIntelligenceResponse,
    CompetitorActivityResponse,
    CompetitiveAlertResponse,
    # Workflow
    TriggerWorkflowRequest,
    WorkflowResultResponse,
    WorkflowStepResponse,
    WorkflowDefinitionResponse,
    # Anomaly Detection
    AnomalyDetectionRequest,
    AnomalyDetectionResponse,
    AnomalyAlert,
    # Document Extraction
    DocumentExtractionRequest,
    DocumentExtractionResponse,
    ExtractedClause,
    ExtractedTable,
    # Stats
    AIServiceStatsResponse,
)

# Import AI services
from app.services.ai.natural_language_query import nl_query_service
from app.services.ai.rag_knowledge_base import rag_knowledge_base_service
from app.services.ai.deal_scoring import deal_scoring_service
from app.services.ai.scenario_optimizer import scenario_optimizer_service
from app.services.ai.market_predictor import market_predictor_service
from app.services.ai.compliance_predictor import compliance_predictor_service
from app.services.ai.due_diligence_generator import due_diligence_service
from app.services.ai.report_generator import (
    ai_report_generator as report_generator_service,
)
from app.services.ai.communication_drafter import communication_drafter_service
from app.services.ai.conversational_assistant import conversational_assistant_service
from app.services.ai.portfolio_optimizer import portfolio_optimizer_service
from app.services.ai.multi_modal_analyzer import multi_modal_analyzer_service
from app.services.ai.competitive_intelligence import competitive_intelligence_service
from app.services.ai.workflow_engine import workflow_engine_service
from app.services.ai.anomaly_detector import (
    anomaly_detection_service as anomaly_detector_service,
)
from app.services.ai.document_extractor import (
    document_extraction_service as document_extractor_service,
)

router = APIRouter(prefix="/ai", tags=["AI Services"])


# ============================================================================
# Natural Language Query Endpoints
# ============================================================================


@router.post("/query", response_model=NLQueryResponse)
async def process_natural_language_query(
    request: NLQueryRequest,
    _: Role = Depends(require_viewer),
    db: AsyncSession = Depends(get_db),
) -> NLQueryResponse:
    """Process a natural language query and return structured results.

    Converts natural language questions into structured database queries
    and returns relevant information.
    """
    result = await nl_query_service.process_query(
        query=request.query,
        user_id=request.user_id,
        db=db,
    )
    return NLQueryResponse(
        query=result.original_query,
        intent=result.intent,
        entities=result.entities,
        structured_query=result.structured_query,
        confidence=result.confidence,
        suggested_action=result.suggested_action,
    )


# ============================================================================
# RAG Knowledge Base Endpoints
# ============================================================================


@router.post("/knowledge/search", response_model=KnowledgeSearchResponse)
async def search_knowledge_base(
    request: KnowledgeSearchRequest,
    _: Role = Depends(require_viewer),
) -> KnowledgeSearchResponse:
    """Search the knowledge base using semantic or keyword search.

    Returns relevant documents and optionally generates an AI answer.
    """
    from app.services.ai.rag_knowledge_base import SearchMode as ServiceSearchMode

    mode_map = {
        "semantic": ServiceSearchMode.SEMANTIC,
        "keyword": ServiceSearchMode.KEYWORD,
        "hybrid": ServiceSearchMode.HYBRID,
    }
    result = await rag_knowledge_base_service.search(
        query=request.query,
        mode=mode_map.get(request.mode.value, ServiceSearchMode.HYBRID),
        source_types=None,  # Would map from request.source_types
        limit=request.limit,
        generate_answer=request.generate_answer,
    )
    return KnowledgeSearchResponse(
        query=result.query,
        results=[
            SearchResultItem(
                chunk_id=r.chunk_id,
                source_type=r.source_type.value,
                source_id=r.source_id,
                content=r.content,
                relevance_score=r.relevance_score,
                metadata=r.metadata,
            )
            for r in result.results
        ],
        total_chunks_searched=result.total_chunks_searched,
        search_time_ms=result.search_time_ms,
        generated_answer=result.generated_answer,
    )


@router.post("/knowledge/ingest/property", response_model=IngestionResponse)
async def ingest_property(
    request: IngestPropertyRequest,
    _: Role = Depends(require_reviewer),
    db: AsyncSession = Depends(get_db),
) -> IngestionResponse:
    """Ingest a property into the knowledge base for semantic search."""
    result = await rag_knowledge_base_service.ingest_property(
        property_id=request.property_id,
        db=db,
    )
    return IngestionResponse(
        success=result.success,
        chunks_created=result.chunks_created,
        source_type=result.source_type.value,
        source_id=result.source_id,
        error=result.error,
    )


@router.post("/knowledge/ingest/deal", response_model=IngestionResponse)
async def ingest_deal(
    request: IngestDealRequest,
    _: Role = Depends(require_reviewer),
    db: AsyncSession = Depends(get_db),
) -> IngestionResponse:
    """Ingest a deal into the knowledge base for semantic search."""
    result = await rag_knowledge_base_service.ingest_deal(
        deal_id=request.deal_id,
        db=db,
    )
    return IngestionResponse(
        success=result.success,
        chunks_created=result.chunks_created,
        source_type=result.source_type.value,
        source_id=result.source_id,
        error=result.error,
    )


@router.post("/knowledge/ingest/document", response_model=IngestionResponse)
async def ingest_document(
    request: IngestDocumentRequest,
    _: Role = Depends(require_reviewer),
) -> IngestionResponse:
    """Ingest a document into the knowledge base for semantic search."""
    result = await rag_knowledge_base_service.ingest_document(
        document_id=request.document_id,
        content=request.content,
        metadata=request.metadata,
    )
    return IngestionResponse(
        success=result.success,
        chunks_created=result.chunks_created,
        source_type=result.source_type.value,
        source_id=result.source_id,
        error=result.error,
    )


@router.get("/knowledge/stats", response_model=AIServiceStatsResponse)
async def get_knowledge_stats(
    _: Role = Depends(require_viewer),
) -> AIServiceStatsResponse:
    """Get statistics about the knowledge base."""
    stats = rag_knowledge_base_service.get_stats()
    return AIServiceStatsResponse(
        service_name="RAGKnowledgeBase",
        initialized=stats.get("initialized", False),
        stats=stats,
    )


# ============================================================================
# Deal Scoring Endpoints
# ============================================================================


@router.post("/deals/score", response_model=DealScoreResponse)
async def score_deal(
    request: DealScoreRequest,
    _: Role = Depends(require_viewer),
    db: AsyncSession = Depends(get_db),
) -> DealScoreResponse:
    """Score a deal using AI-powered multi-factor analysis.

    Returns an overall score, grade, and breakdown by factors.
    """
    result = await deal_scoring_service.score_deal(
        deal_id=request.deal_id,
        db=db,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal not found or could not be scored",
        )
    return DealScoreResponse(
        deal_id=result.deal_id,
        overall_score=result.overall_score,
        grade=result.grade,
        factor_scores=[
            FactorScoreItem(
                factor=f.factor,
                score=f.score,
                weight=f.weight,
                weighted_score=f.weighted_score,
                rationale=f.rationale,
            )
            for f in result.factor_scores
        ],
        recommendation=result.recommendation,
        confidence=result.confidence,
        scored_at=result.scored_at,
    )


# ============================================================================
# Scenario Optimizer Endpoints
# ============================================================================


@router.post("/scenarios/optimize", response_model=ScenarioOptimizeResponse)
async def optimize_scenarios(
    request: ScenarioOptimizeRequest,
    _: Role = Depends(require_viewer),
    db: AsyncSession = Depends(get_db),
) -> ScenarioOptimizeResponse:
    """Generate and optimize financing scenarios for a project.

    Returns multiple financing options with recommendations.
    """
    from app.services.ai.scenario_optimizer import (
        FinancingType as ServiceFinancingType,
        OptimizationRequest,
    )

    type_map = {
        FinancingType.CONVENTIONAL: ServiceFinancingType.CONVENTIONAL,
        FinancingType.CONSTRUCTION: ServiceFinancingType.CONSTRUCTION,
        FinancingType.BRIDGE: ServiceFinancingType.BRIDGE,
        FinancingType.MEZZANINE: ServiceFinancingType.MEZZANINE,
    }
    financing_types = (
        [type_map[ft] for ft in request.financing_types]
        if request.financing_types
        else None
    )

    opt_request = OptimizationRequest(
        project_id=request.project_id,
        financing_types=financing_types,
        target_irr=request.target_irr,
        max_leverage=request.max_leverage,
    )
    result = await scenario_optimizer_service.optimize(opt_request, db)

    return ScenarioOptimizeResponse(
        project_id=result.project_id,
        scenarios=[
            FinancingScenario(
                id=s.id,
                financing_type=s.financing_type.value,
                loan_amount=s.loan_amount,
                ltv_ratio=s.ltv_ratio,
                interest_rate=s.interest_rate,
                debt_service_coverage=s.debt_service_coverage,
                projected_irr=s.projected_irr,
                projected_equity_multiple=s.projected_equity_multiple,
                total_interest_cost=s.total_interest_cost,
                recommendation_score=s.recommendation_score,
            )
            for s in result.scenarios
        ],
        recommended_scenario_id=result.recommended_scenario_id,
        analysis_summary=result.analysis_summary,
    )


# ============================================================================
# Market Predictor Endpoints
# ============================================================================


@router.post("/market/predict", response_model=MarketPredictionResponse)
async def predict_market(
    request: MarketPredictionRequest,
    _: Role = Depends(require_viewer),
    db: AsyncSession = Depends(get_db),
) -> MarketPredictionResponse:
    """Generate market predictions for rental rates, capital values, or supply.

    Returns forecasts with confidence levels and contributing factors.
    """
    from app.services.ai.market_predictor import (
        PredictionType as ServicePredictionType,
        PredictionRequest,
    )

    type_map = {
        PredictionType.RENTAL: ServicePredictionType.RENTAL,
        PredictionType.CAPITAL_VALUE: ServicePredictionType.CAPITAL_VALUE,
        PredictionType.SUPPLY: ServicePredictionType.SUPPLY,
        PredictionType.DEMAND: ServicePredictionType.DEMAND,
    }
    prediction_types = (
        [type_map[pt] for pt in request.prediction_types]
        if request.prediction_types
        else None
    )

    pred_request = PredictionRequest(
        property_id=request.property_id,
        district=request.district,
        property_type=request.property_type,
        prediction_types=prediction_types,
        forecast_months=request.forecast_months,
    )
    result = await market_predictor_service.predict(pred_request, db)

    return MarketPredictionResponse(
        predictions=[
            PredictionItem(
                prediction_type=p.prediction_type.value,
                current_value=p.current_value,
                predicted_value=p.predicted_value,
                change_percentage=p.change_percentage,
                confidence=p.confidence,
                factors=p.factors,
            )
            for p in result.predictions
        ],
        forecast_months=result.forecast_months,
        generated_at=result.generated_at,
        summary=result.summary,
    )


# ============================================================================
# Compliance Predictor Endpoints
# ============================================================================


@router.post("/compliance/predict", response_model=CompliancePredictionResponse)
async def predict_compliance(
    request: CompliancePredictionRequest,
    _: Role = Depends(require_viewer),
    db: AsyncSession = Depends(get_db),
) -> CompliancePredictionResponse:
    """Predict regulatory approval timelines and identify risks.

    Returns milestone predictions with confidence and risk factors.
    """
    from app.services.ai.compliance_predictor import PredictionRequest

    pred_request = PredictionRequest(
        project_id=request.project_id,
        submission_types=request.submission_types,
    )
    result = await compliance_predictor_service.predict(pred_request, db)

    return CompliancePredictionResponse(
        project_id=result.project_id,
        milestones=[
            RegulatoryMilestone(
                milestone=m.milestone,
                agency=m.agency,
                predicted_date=(
                    m.predicted_date.isoformat() if m.predicted_date else None
                ),
                confidence=m.confidence,
                dependencies=m.dependencies,
                risk_factors=m.risk_factors,
            )
            for m in result.milestones
        ],
        critical_path_days=result.critical_path_days,
        risk_assessment=result.risk_assessment,
        recommendations=result.recommendations,
    )


# ============================================================================
# Due Diligence Endpoints
# ============================================================================


@router.post("/due-diligence/generate", response_model=DDChecklistResponse)
async def generate_due_diligence(
    request: DDGenerateRequest,
    _: Role = Depends(require_viewer),
    db: AsyncSession = Depends(get_db),
) -> DDChecklistResponse:
    """Generate a due diligence checklist for a deal.

    Returns customized checklist items based on deal type and property.
    """
    result = await due_diligence_service.generate_checklist(
        deal_id=request.deal_id,
        db=db,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deal not found",
        )
    return DDChecklistResponse(
        id=result.id,
        deal_id=result.deal_id,
        deal_title=result.deal_title,
        items=[
            DDItemResponse(
                id=item.id,
                category=item.category.value,
                name=item.name,
                description=item.description,
                priority=item.priority.value,
                status=item.status.value,
                requires_external=item.requires_external,
                external_source=item.external_source,
                assigned_to=item.assigned_to,
                due_date=item.due_date.isoformat() if item.due_date else None,
                notes=item.notes,
            )
            for item in result.items
        ],
        recommendations=[
            DDRecommendationResponse(
                title=rec.title,
                description=rec.description,
                priority=rec.priority.value,
                action_items=rec.action_items,
            )
            for rec in result.recommendations
        ],
        completion_percentage=result.completion_percentage,
        estimated_days_to_complete=result.estimated_days_to_complete,
    )


# ============================================================================
# Report Generator Endpoints
# ============================================================================


@router.post("/reports/ic-memo", response_model=ReportResponse)
async def generate_ic_memo(
    request: ICMemoRequest,
    _: Role = Depends(require_viewer),
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    """Generate an Investment Committee memo for a deal.

    Returns a structured memo with executive summary, analysis, and recommendations.
    """
    result = await report_generator_service.generate_ic_memo(
        deal_id=request.deal_id,
        db=db,
    )
    if not result.success or result.report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.error or "Failed to generate IC memo",
        )
    report = result.report
    return ReportResponse(
        id=report.id,
        report_type=report.report_type.value,
        title=report.title,
        subtitle=report.subtitle,
        generated_at=report.generated_at,
        sections=[
            ReportSectionResponse(
                title=s.title,
                content=s.content,
                order=s.order,
            )
            for s in report.sections
        ],
        executive_summary=report.executive_summary,
        recommendations=report.recommendations,
        generation_time_ms=result.generation_time_ms,
    )


@router.post("/reports/portfolio", response_model=ReportResponse)
async def generate_portfolio_report(
    request: PortfolioReportRequest,
    _: Role = Depends(require_viewer),
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    """Generate a portfolio summary report for a user.

    Returns portfolio metrics, deal breakdown, and performance analysis.
    """
    result = await report_generator_service.generate_portfolio_report(
        user_id=request.user_id,
        db=db,
    )
    if not result.success or result.report is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error or "Failed to generate portfolio report",
        )
    report = result.report
    return ReportResponse(
        id=report.id,
        report_type=report.report_type.value,
        title=report.title,
        subtitle=report.subtitle,
        generated_at=report.generated_at,
        sections=[
            ReportSectionResponse(
                title=s.title,
                content=s.content,
                order=s.order,
            )
            for s in report.sections
        ],
        executive_summary=report.executive_summary,
        recommendations=report.recommendations,
        generation_time_ms=result.generation_time_ms,
    )


# ============================================================================
# Communication Drafter Endpoints
# ============================================================================


@router.post("/communications/draft", response_model=CommunicationDraftResponse)
async def draft_communication(
    request: DraftCommunicationRequest,
    _: Role = Depends(require_viewer),
    db: AsyncSession = Depends(get_db),
) -> CommunicationDraftResponse:
    """Draft a professional communication using AI.

    Supports emails, letters, proposals, and memos with various tones.
    """
    from app.services.ai.communication_drafter import (
        CommunicationType as ServiceCommunicationType,
        CommunicationTone as ServiceCommunicationTone,
        CommunicationPurpose as ServiceCommunicationPurpose,
        DraftRequest,
    )

    comm_type_map = {
        "email": ServiceCommunicationType.EMAIL,
        "letter": ServiceCommunicationType.LETTER,
        "sms": ServiceCommunicationType.SMS,
        "proposal": ServiceCommunicationType.PROPOSAL,
        "memo": ServiceCommunicationType.MEMO,
    }
    tone_map = {
        "formal": ServiceCommunicationTone.FORMAL,
        "professional": ServiceCommunicationTone.PROFESSIONAL,
        "friendly": ServiceCommunicationTone.FRIENDLY,
        "urgent": ServiceCommunicationTone.URGENT,
    }
    purpose_map = {
        "introduction": ServiceCommunicationPurpose.INTRODUCTION,
        "follow_up": ServiceCommunicationPurpose.FOLLOW_UP,
        "offer": ServiceCommunicationPurpose.OFFER,
        "counter_offer": ServiceCommunicationPurpose.COUNTER_OFFER,
        "negotiation": ServiceCommunicationPurpose.NEGOTIATION,
        "closing": ServiceCommunicationPurpose.CLOSING,
        "thank_you": ServiceCommunicationPurpose.THANK_YOU,
        "update": ServiceCommunicationPurpose.UPDATE,
        "request": ServiceCommunicationPurpose.REQUEST,
        "rejection": ServiceCommunicationPurpose.REJECTION,
    }

    draft_request = DraftRequest(
        communication_type=comm_type_map[request.communication_type.value],
        purpose=purpose_map[request.purpose.value],
        tone=tone_map[request.tone.value],
        recipient_name=request.recipient_name,
        recipient_company=request.recipient_company,
        recipient_role=request.recipient_role,
        deal_id=request.deal_id,
        property_id=request.property_id,
        key_points=request.key_points,
        additional_context=request.additional_context,
        include_alternatives=request.include_alternatives,
    )
    result = await communication_drafter_service.draft_communication(draft_request, db)

    if not result.success or result.draft is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error or "Failed to generate draft",
        )

    draft = result.draft
    return CommunicationDraftResponse(
        id=draft.id,
        communication_type=draft.communication_type.value,
        purpose=draft.purpose.value,
        tone=draft.tone.value,
        subject=draft.subject,
        body=draft.body,
        alternatives=draft.alternatives,
        generation_time_ms=result.generation_time_ms,
    )


# ============================================================================
# Conversational Assistant Endpoints
# ============================================================================


@router.post("/chat", response_model=ChatMessageResponse)
async def chat_message(
    request: ChatMessageRequest,
    _: Role = Depends(require_viewer),
    db: AsyncSession = Depends(get_db),
) -> ChatMessageResponse:
    """Send a message to the AI assistant.

    Maintains conversation context and can perform actions like searching
    and analyzing deals.
    """
    result = await conversational_assistant_service.process_message(
        message=request.message,
        conversation_id=request.conversation_id,
        user_id=request.user_id or "anonymous",
        db=db,
    )
    if not result.success or result.response is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message",
        )
    return ChatMessageResponse(
        conversation_id=result.response.conversation_id or "",
        message=result.response.message,
        suggestions=result.response.suggestions,
        actions_taken=result.response.actions_taken,
        context_updates=result.response.context_updates,
    )


@router.get("/chat/conversations", response_model=list[ConversationListItem])
async def list_conversations(
    user_id: str,
    _: Role = Depends(require_viewer),
) -> list[ConversationListItem]:
    """List all conversations for a user."""
    conversations = conversational_assistant_service.list_conversations(user_id)
    return [
        ConversationListItem(
            conversation_id=c.conversation_id,
            user_id=c.user_id,
            message_count=len(c.messages),
            created_at=c.created_at,
            last_message_at=c.messages[-1].timestamp if c.messages else c.created_at,
        )
        for c in conversations
    ]


@router.delete("/chat/conversations/{conversation_id}")
async def clear_conversation(
    conversation_id: str,
    _: Role = Depends(require_reviewer),
) -> dict[str, bool]:
    """Clear a conversation history."""
    success = conversational_assistant_service.clear_conversation(conversation_id)
    return {"success": success}


# ============================================================================
# Portfolio Optimizer Endpoints
# ============================================================================


@router.post("/portfolio/optimize", response_model=PortfolioOptimizeResponse)
async def optimize_portfolio(
    request: PortfolioOptimizeRequest,
    _: Role = Depends(require_viewer),
    db: AsyncSession = Depends(get_db),
) -> PortfolioOptimizeResponse:
    """Generate portfolio optimization recommendations.

    Analyzes current allocation and suggests rebalancing actions.
    """
    from app.services.ai.portfolio_optimizer import (
        OptimizationStrategy as ServiceStrategy,
        RiskProfile as ServiceRiskProfile,
        OptimizationRequest,
    )

    strategy_map = {
        "maximize_returns": ServiceStrategy.MAXIMIZE_RETURNS,
        "minimize_risk": ServiceStrategy.MINIMIZE_RISK,
        "balanced": ServiceStrategy.BALANCED,
        "income_focused": ServiceStrategy.INCOME_FOCUSED,
        "growth_focused": ServiceStrategy.GROWTH_FOCUSED,
    }
    risk_map = {
        "conservative": ServiceRiskProfile.CONSERVATIVE,
        "moderate": ServiceRiskProfile.MODERATE,
        "aggressive": ServiceRiskProfile.AGGRESSIVE,
    }

    opt_request = OptimizationRequest(
        user_id=request.user_id,
        strategy=strategy_map[request.strategy.value],
        risk_profile=risk_map[request.risk_profile.value],
        max_concentration=request.max_concentration,
        min_liquidity=request.min_liquidity,
    )
    result = await portfolio_optimizer_service.optimize(opt_request, db)

    return PortfolioOptimizeResponse(
        id=result.id,
        user_id=result.user_id,
        strategy=result.strategy.value,
        risk_profile=result.risk_profile.value,
        metrics=PortfolioMetricsResponse(
            total_value=result.metrics.total_value,
            total_assets=result.metrics.total_assets,
            weighted_yield=result.metrics.weighted_yield,
            portfolio_beta=result.metrics.portfolio_beta,
            diversification_score=result.metrics.diversification_score,
            concentration_risk=result.metrics.concentration_risk,
            liquidity_score=result.metrics.liquidity_score,
        ),
        current_allocation=[
            AssetAllocationItem(
                asset_type=a.asset_type,
                current_value=a.current_value,
                current_percentage=a.current_percentage,
                recommended_percentage=a.recommended_percentage,
                variance=a.variance,
                action=a.action,
            )
            for a in result.current_allocation
        ],
        recommendations=[
            RebalancingRecommendation(
                asset_id=r.asset_id,
                asset_name=r.asset_name,
                asset_type=r.asset_type,
                current_allocation=r.current_allocation,
                recommended_action=r.recommended_action,
                target_allocation=r.target_allocation,
                rationale=r.rationale,
                priority=r.priority,
            )
            for r in result.recommendations
        ],
        target_allocation=result.target_allocation,
        expected_improvement=result.expected_improvement,
        analysis_summary=result.analysis_summary,
    )


# ============================================================================
# Multi-Modal Analyzer Endpoints
# ============================================================================


@router.post("/images/analyze", response_model=ImageAnalysisResponse)
async def analyze_image(
    request: ImageAnalysisRequest,
    _: Role = Depends(require_viewer),
) -> ImageAnalysisResponse:
    """Analyze an image using AI vision capabilities.

    Supports floor plans, site photos, building facades, and documents.
    """
    from app.services.ai.multi_modal_analyzer import (
        ImageType as ServiceImageType,
        AnalysisType as ServiceAnalysisType,
        AnalysisRequest,
    )

    image_type_map = {
        "floor_plan": ServiceImageType.FLOOR_PLAN,
        "site_photo": ServiceImageType.SITE_PHOTO,
        "aerial_view": ServiceImageType.AERIAL_VIEW,
        "building_facade": ServiceImageType.BUILDING_FACADE,
        "interior": ServiceImageType.INTERIOR,
        "document": ServiceImageType.DOCUMENT,
        "map": ServiceImageType.MAP,
    }
    analysis_type_map = {
        "space_analysis": ServiceAnalysisType.SPACE_ANALYSIS,
        "condition_assessment": ServiceAnalysisType.CONDITION_ASSESSMENT,
        "layout_extraction": ServiceAnalysisType.LAYOUT_EXTRACTION,
        "text_extraction": ServiceAnalysisType.TEXT_EXTRACTION,
    }

    analysis_types = (
        [analysis_type_map[at.value] for at in request.analysis_types]
        if request.analysis_types
        else None
    )

    analysis_request = AnalysisRequest(
        image_base64=request.image_base64,
        image_url=request.image_url,
        image_type=image_type_map[request.image_type.value],
        analysis_types=analysis_types,
        property_id=request.property_id,
    )
    result = await multi_modal_analyzer_service.analyze(analysis_request)

    space_metrics = None
    if result.space_metrics:
        space_metrics = SpaceMetricsResponse(
            total_area_sqm=result.space_metrics.total_area_sqm,
            usable_area_sqm=result.space_metrics.usable_area_sqm,
            room_count=result.space_metrics.room_count,
            efficiency_ratio=result.space_metrics.efficiency_ratio,
            parking_spaces=result.space_metrics.parking_spaces,
            floors_detected=result.space_metrics.floors_detected,
        )

    condition = None
    if result.condition:
        condition = ConditionAssessmentResponse(
            overall_condition=result.condition.overall_condition,
            condition_score=result.condition.condition_score,
            issues_detected=result.condition.issues_detected,
            maintenance_recommendations=result.condition.maintenance_recommendations,
            estimated_capex=result.condition.estimated_capex,
            age_assessment=result.condition.age_assessment,
        )

    return ImageAnalysisResponse(
        id=result.id,
        image_type=result.image_type.value,
        analysis_type=result.analysis_type.value,
        space_metrics=space_metrics,
        condition=condition,
        extracted_text=(
            result.extracted_text.raw_text if result.extracted_text else None
        ),
        confidence=result.confidence,
        processing_time_ms=result.processing_time_ms,
    )


# ============================================================================
# Competitive Intelligence Endpoints
# ============================================================================


@router.post("/competitors/track", response_model=CompetitorResponse)
async def track_competitor(
    request: CompetitorTrackRequest,
    _: Role = Depends(require_reviewer),
) -> CompetitorResponse:
    """Start tracking a competitor."""
    from app.services.ai.competitive_intelligence import CompetitorType

    type_map = {
        "developer": CompetitorType.DEVELOPER,
        "investor": CompetitorType.INVESTOR,
        "reit": CompetitorType.REIT,
        "agency": CompetitorType.AGENCY,
        "fund": CompetitorType.FUND,
    }
    comp_type = type_map.get(request.competitor_type.lower(), CompetitorType.DEVELOPER)

    competitor = competitive_intelligence_service.track_competitor(
        name=request.name,
        competitor_type=comp_type,
        focus_sectors=request.focus_sectors,
        focus_districts=request.focus_districts,
        notes=request.notes,
    )
    return CompetitorResponse(
        id=competitor.id,
        name=competitor.name,
        competitor_type=competitor.competitor_type.value,
        focus_sectors=competitor.focus_sectors,
        focus_districts=competitor.focus_districts,
        tracked_since=competitor.tracked_since,
    )


@router.get("/competitors", response_model=list[CompetitorResponse])
async def list_competitors(
    _: Role = Depends(require_viewer),
) -> list[CompetitorResponse]:
    """List all tracked competitors."""
    competitors = competitive_intelligence_service.list_competitors()
    return [
        CompetitorResponse(
            id=c.id,
            name=c.name,
            competitor_type=c.competitor_type.value,
            focus_sectors=c.focus_sectors,
            focus_districts=c.focus_districts,
            tracked_since=c.tracked_since,
        )
        for c in competitors
    ]


@router.post("/intelligence/gather", response_model=CompetitiveIntelligenceResponse)
async def gather_intelligence(
    request: CompetitiveIntelligenceRequest,
    _: Role = Depends(require_viewer),
    db: AsyncSession = Depends(get_db),
) -> CompetitiveIntelligenceResponse:
    """Gather competitive intelligence for a user.

    Returns competitor activities, alerts, and market insights.
    """
    result = await competitive_intelligence_service.gather_intelligence(
        user_id=request.user_id,
        db=db,
    )
    return CompetitiveIntelligenceResponse(
        competitors=[
            CompetitorResponse(
                id=c.id,
                name=c.name,
                competitor_type=c.competitor_type.value,
                focus_sectors=c.focus_sectors,
                focus_districts=c.focus_districts,
                tracked_since=c.tracked_since,
            )
            for c in result.competitors
        ],
        activities=[
            CompetitorActivityResponse(
                id=a.id,
                competitor_id=a.competitor_id,
                competitor_name=a.competitor_name,
                category=a.category.value,
                title=a.title,
                description=a.description,
                location=a.location,
                relevance_score=a.relevance_score,
                detected_at=a.detected_at,
            )
            for a in result.activities
        ],
        alerts=[
            CompetitiveAlertResponse(
                id=a.id,
                priority=a.priority.value,
                title=a.title,
                description=a.description,
                competitor_id=a.competitor_id,
                competitor_name=a.competitor_name,
                action_required=a.action_required,
                expires_at=a.expires_at,
            )
            for a in result.alerts
        ],
        summary=result.summary,
    )


# ============================================================================
# Workflow Engine Endpoints
# ============================================================================


@router.post("/workflows/trigger", response_model=list[WorkflowResultResponse])
async def trigger_workflow(
    request: TriggerWorkflowRequest,
    _: Role = Depends(require_reviewer),
    db: AsyncSession = Depends(get_db),
) -> list[WorkflowResultResponse]:
    """Trigger workflows based on an event.

    Returns results from all matching workflows.
    """
    from app.services.ai.workflow_engine import WorkflowTrigger as ServiceTrigger

    trigger_map = {
        "deal_created": ServiceTrigger.DEAL_CREATED,
        "deal_stage_changed": ServiceTrigger.DEAL_STAGE_CHANGED,
        "deadline_approaching": ServiceTrigger.DEADLINE_APPROACHING,
        "document_uploaded": ServiceTrigger.DOCUMENT_UPLOADED,
        "approval_required": ServiceTrigger.APPROVAL_REQUIRED,
        "compliance_flag": ServiceTrigger.COMPLIANCE_FLAG,
        "market_alert": ServiceTrigger.MARKET_ALERT,
    }

    results = await workflow_engine_service.trigger_workflow(
        trigger=trigger_map[request.trigger.value],
        event_data=request.event_data,
        db=db,
    )
    return [
        WorkflowResultResponse(
            workflow_id=r.workflow_id,
            workflow_name=r.workflow_name,
            instance_id=r.instance_id,
            status=r.status.value,
            started_at=r.started_at,
            completed_at=r.completed_at,
            steps=[
                WorkflowStepResponse(
                    action_id=s.action_id,
                    action_type=s.action_type.value,
                    status=s.status.value,
                    started_at=s.started_at,
                    completed_at=s.completed_at,
                    result=s.result,
                    error=s.error,
                )
                for s in r.steps
            ],
        )
        for r in results
    ]


@router.get("/workflows", response_model=list[WorkflowDefinitionResponse])
async def list_workflows(
    _: Role = Depends(require_viewer),
) -> list[WorkflowDefinitionResponse]:
    """List all workflow definitions."""
    workflows = workflow_engine_service.list_workflows()
    return [
        WorkflowDefinitionResponse(
            id=w.id,
            name=w.name,
            description=w.description,
            trigger=w.trigger.value,
            is_active=w.is_active,
            action_count=len(w.actions),
        )
        for w in workflows
    ]


@router.post("/workflows/check-deadlines", response_model=list[WorkflowResultResponse])
async def check_deadlines(
    _: Role = Depends(require_reviewer),
    db: AsyncSession = Depends(get_db),
) -> list[WorkflowResultResponse]:
    """Check for approaching deadlines and trigger notifications."""
    results = await workflow_engine_service.check_deadlines(db)
    return [
        WorkflowResultResponse(
            workflow_id=r.workflow_id,
            workflow_name=r.workflow_name,
            instance_id=r.instance_id,
            status=r.status.value,
            started_at=r.started_at,
            completed_at=r.completed_at,
            steps=[
                WorkflowStepResponse(
                    action_id=s.action_id,
                    action_type=s.action_type.value,
                    status=s.status.value,
                    started_at=s.started_at,
                    completed_at=s.completed_at,
                    result=s.result,
                    error=s.error,
                )
                for s in r.steps
            ],
        )
        for r in results
    ]


# ============================================================================
# Anomaly Detection Endpoints
# ============================================================================


@router.post("/anomalies/detect", response_model=AnomalyDetectionResponse)
async def detect_anomalies(
    request: AnomalyDetectionRequest,
    _: Role = Depends(require_viewer),
    db: AsyncSession = Depends(get_db),
) -> AnomalyDetectionResponse:
    """Detect anomalies in deals, properties, or projects.

    Returns alerts for unusual patterns or values.
    """
    result = await anomaly_detector_service.detect_anomalies(
        deal_id=request.deal_id,
        property_id=request.property_id,
        project_id=request.project_id,
        db=db,
    )
    return AnomalyDetectionResponse(
        alerts=[
            AnomalyAlert(
                id=a.id,
                alert_type=a.alert_type.value,
                severity=a.severity.value,
                title=a.title,
                description=a.description,
                entity_type=a.entity_type,
                entity_id=a.entity_id,
                detected_value=a.detected_value,
                expected_range=a.expected_range,
                recommendation=a.recommendation,
                detected_at=a.detected_at,
            )
            for a in result.alerts
        ],
        entities_scanned=result.entities_scanned,
        scan_time_ms=result.scan_time_ms,
    )


# ============================================================================
# Document Extraction Endpoints
# ============================================================================


@router.post("/documents/extract", response_model=DocumentExtractionResponse)
async def extract_document(
    request: DocumentExtractionRequest,
    _: Role = Depends(require_viewer),
) -> DocumentExtractionResponse:
    """Extract structured information from documents.

    Supports contracts, leases, and legal documents.
    """
    from app.services.ai.document_extractor import ExtractionRequest

    extract_request = ExtractionRequest(
        document_base64=request.document_base64,
        document_url=request.document_url,
        document_type=request.document_type,
        extract_tables=request.extract_tables,
        extract_clauses=request.extract_clauses,
    )
    result = await document_extractor_service.extract(extract_request)

    return DocumentExtractionResponse(
        document_type=result.document_type,
        clauses=[
            ExtractedClause(
                clause_type=c.clause_type,
                text=c.text,
                page_number=c.page_number,
                confidence=c.confidence,
            )
            for c in result.clauses
        ],
        tables=[
            ExtractedTable(
                table_id=t.table_id,
                headers=t.headers,
                rows=t.rows,
                page_number=t.page_number,
            )
            for t in result.tables
        ],
        key_dates=result.key_dates,
        parties=result.parties,
        summary=result.summary,
        processing_time_ms=result.processing_time_ms,
    )


# ============================================================================
# Health Check
# ============================================================================


@router.get("/health")
async def ai_health_check() -> dict[str, Any]:
    """Check health status of AI services."""
    return {
        "status": "ok",
        "services": {
            "natural_language_query": nl_query_service._initialized,
            "knowledge_base": rag_knowledge_base_service._initialized,
            "deal_scoring": deal_scoring_service._initialized,
            "scenario_optimizer": scenario_optimizer_service._initialized,
            "market_predictor": market_predictor_service._initialized,
            "compliance_predictor": compliance_predictor_service._initialized,
            "due_diligence": True,  # No LLM dependency
            "report_generator": report_generator_service._initialized,
            "communication_drafter": communication_drafter_service._initialized,
            "conversational_assistant": conversational_assistant_service._initialized,
            "portfolio_optimizer": portfolio_optimizer_service._initialized,
            "multi_modal_analyzer": multi_modal_analyzer_service._initialized,
            "competitive_intelligence": competitive_intelligence_service._initialized,
            "workflow_engine": True,  # No LLM dependency
            "anomaly_detector": True,  # No LLM dependency
            "document_extractor": document_extractor_service._initialized,
        },
    }


__all__ = ["router"]
