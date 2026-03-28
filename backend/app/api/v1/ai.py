"""API endpoints for AI services.

This module exposes the 16 AI services implemented in Phase 1-4 of the AI rollout.
"""

from __future__ import annotations

import base64
import sys
from datetime import datetime, timedelta
from functools import lru_cache
from importlib import import_module
from typing import Any, cast
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend._compat.datetime import utcnow

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
    AIServiceStatsResponse,
)

router = APIRouter(prefix="/ai", tags=["AI Services"])

_AI_SERVICE_REGISTRY: dict[str, tuple[str, str, bool]] = {
    "natural_language_query": (
        "app.services.ai.natural_language_query",
        "nl_query_service",
        False,
    ),
    "knowledge_base": (
        "app.services.ai.rag_knowledge_base",
        "rag_knowledge_base_service",
        False,
    ),
    "deal_scoring": ("app.services.ai.deal_scoring", "deal_scoring_service", True),
    "scenario_optimizer": (
        "app.services.ai.scenario_optimizer",
        "scenario_optimizer_service",
        False,
    ),
    "market_predictor": (
        "app.services.ai.market_predictor",
        "market_predictor_service",
        True,
    ),
    "compliance_predictor": (
        "app.services.ai.compliance_predictor",
        "compliance_predictor_service",
        True,
    ),
    "due_diligence": (
        "app.services.ai.due_diligence_generator",
        "due_diligence_service",
        True,
    ),
    "report_generator": (
        "app.services.ai.report_generator",
        "ai_report_generator",
        False,
    ),
    "communication_drafter": (
        "app.services.ai.communication_drafter",
        "communication_drafter_service",
        False,
    ),
    "conversational_assistant": (
        "app.services.ai.conversational_assistant",
        "conversational_assistant_service",
        False,
    ),
    "portfolio_optimizer": (
        "app.services.ai.portfolio_optimizer",
        "portfolio_optimizer_service",
        False,
    ),
    "multi_modal_analyzer": (
        "app.services.ai.multi_modal_analyzer",
        "multi_modal_analyzer_service",
        False,
    ),
    "competitive_intelligence": (
        "app.services.ai.competitive_intelligence",
        "competitive_intelligence_service",
        False,
    ),
    "workflow_engine": (
        "app.services.ai.workflow_engine",
        "workflow_engine_service",
        True,
    ),
    "anomaly_detector": (
        "app.services.ai.anomaly_detector",
        "anomaly_detection_service",
        True,
    ),
    "document_extractor": (
        "app.services.ai.document_extractor",
        "document_extraction_service",
        False,
    ),
}


@lru_cache(maxsize=None)
def _load_service(module_name: str, attribute: str) -> Any:
    """Import and return a singleton AI service on first use."""

    module = import_module(module_name)
    return getattr(module, attribute)


def _service(service_name: str) -> Any:
    """Return the configured AI service singleton."""

    module_name, attribute, _ = _AI_SERVICE_REGISTRY[service_name]
    return _load_service(module_name, attribute)


def _service_initialized(service_name: str) -> bool:
    """Return the best-known initialization state without forcing imports."""

    module_name, attribute, fallback = _AI_SERVICE_REGISTRY[service_name]
    module = sys.modules.get(module_name)
    if module is None:
        return fallback
    service = getattr(module, attribute, None)
    if service is None:
        return fallback
    return bool(getattr(service, "_initialized", fallback))


def _natural_language_response(result: Any, request: NLQueryRequest) -> NLQueryResponse:
    """Normalise legacy and current NL query service payloads for the API contract."""

    query_type = getattr(result, "query_type", None)
    intent = getattr(result, "intent", None)
    if intent is None and query_type is not None:
        intent = getattr(query_type, "value", str(query_type))

    structured_query = getattr(result, "structured_query", None)
    if structured_query is None and query_type is not None:
        structured_query = {"query_type": getattr(query_type, "value", str(query_type))}
        sql_executed = getattr(result, "sql_executed", None)
        if sql_executed:
            structured_query["sql_executed"] = sql_executed

    confidence = getattr(result, "confidence", None)
    if confidence is None:
        confidence = 1.0 if getattr(result, "success", False) else 0.0

    suggested_action = getattr(result, "suggested_action", None)
    if suggested_action is None:
        suggestions = getattr(result, "suggestions", None) or []
        suggested_action = suggestions[0] if suggestions else None

    entities = getattr(result, "entities", None)
    if entities is None:
        entities = {}

    return NLQueryResponse(
        query=getattr(result, "original_query", request.query),
        intent=intent or "general_question",
        entities=entities,
        structured_query=structured_query,
        confidence=confidence,
        suggested_action=suggested_action,
    )


def _identity_user_id(identity: Any) -> str:
    return str(getattr(identity, "user_id", None) or "anonymous")


def _confidence_score(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)

    name = getattr(value, "value", value)
    if isinstance(name, str):
        normalized = name.lower()
        return {
            "high": 0.9,
            "medium": 0.6,
            "low": 0.3,
            "critical": 0.2,
        }.get(normalized, 0.5)

    return 0.5


def _score_grade(score: float) -> str:
    if score >= 85:
        return "A"
    if score >= 70:
        return "B"
    if score >= 55:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def _tracked_since(competitor: Any) -> datetime:
    tracked_since = getattr(competitor, "tracked_since", None)
    if tracked_since is None:
        tracked_since = utcnow()
        try:
            competitor.tracked_since = tracked_since
        except Exception:
            pass
    return cast(datetime, tracked_since)


def _workflow_response(result: Any) -> WorkflowResultResponse | None:
    instance = getattr(result, "instance", None)
    if instance is None:
        return None

    return WorkflowResultResponse(
        workflow_id=instance.workflow_id,
        workflow_name=instance.workflow_name,
        instance_id=instance.id,
        status=instance.status.value,
        started_at=instance.started_at,
        completed_at=instance.completed_at,
        steps=[
            WorkflowStepResponse(
                action_id=step.action_id,
                action_type=step.action_type.value,
                status=step.status.value,
                started_at=step.started_at,
                completed_at=step.completed_at,
                result=step.result,
                error=step.error,
            )
            for step in instance.steps
        ],
    )


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
    result = await _service("natural_language_query").process_query(
        query=request.query,
        user_id=request.user_id,
        db=db,
    )
    return _natural_language_response(result, request)


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
    result = await _service("knowledge_base").search(
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
    result = await _service("knowledge_base").ingest_property(
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
    result = await _service("knowledge_base").ingest_deal(
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
    result = await _service("knowledge_base").ingest_document(
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
    stats = _service("knowledge_base").get_stats()
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
    identity: Role = Depends(require_viewer),
    db: AsyncSession = Depends(get_db),
) -> DealScoreResponse:
    """Score a deal using AI-powered multi-factor analysis.

    Returns an overall score, grade, and breakdown by factors.
    """
    try:
        result = await _service("deal_scoring").score_deal(
            deal_id=request.deal_id,
            db=db,
            user_id=_identity_user_id(identity),
        )
        if result is None or (
            getattr(result, "score", 0) <= 0
            and "not found" in (getattr(result, "recommendation", "") or "").lower()
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deal not found or could not be scored",
            )

        raw_factors = (
            list(getattr(result, "positive_factors", []))
            + list(getattr(result, "neutral_factors", []))
            + list(getattr(result, "risk_factors", []))
        )
        total_factors = len(raw_factors) or 1
        factor_scores = [
            FactorScoreItem(
                factor=f.name,
                score=abs(float(f.impact_score)) * 100,
                weight=1 / total_factors,
                weighted_score=float(f.impact_score) * 100 / total_factors,
                rationale=f.evidence or f.description,
            )
            for f in raw_factors
        ]

        return DealScoreResponse(
            deal_id=request.deal_id,
            overall_score=float(result.score),
            grade=_score_grade(float(result.score)),
            factor_scores=factor_scores,
            recommendation=result.recommendation,
            confidence=_confidence_score(result.confidence),
            scored_at=result.scored_at,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


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
    try:
        from app.services.ai.scenario_optimizer import (
            OptimizationConstraints,
            RiskTolerance,
        )

        constraints = OptimizationConstraints()
        if request.target_irr is not None:
            constraints.target_irr = request.target_irr
        if request.max_leverage is not None:
            constraints.max_ltv = request.max_leverage
            constraints.max_leverage_ratio = request.max_leverage
        if request.financing_types and (
            FinancingType.BRIDGE in request.financing_types
            or FinancingType.MEZZANINE in request.financing_types
        ):
            constraints.risk_tolerance = RiskTolerance.AGGRESSIVE

        result = await _service("scenario_optimizer").optimize(
            project_id=request.project_id,
            constraints=constraints,
            db=db,
        )
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.error or "Failed to optimize scenarios",
            )

        recommended_id = None
        scenarios: list[FinancingScenario] = []
        for index, scenario in enumerate(result.scenarios, start=1):
            debt_components = [
                component
                for component in scenario.financing_structure
                if component.interest_rate is not None
            ]
            loan_amount = sum(component.amount for component in debt_components)
            total_cost = scenario.total_project_cost or 1.0
            ltv_ratio = loan_amount / total_cost
            weighted_rate = (
                sum(
                    component.amount * float(component.interest_rate or 0.0)
                    for component in debt_components
                )
                / loan_amount
                if loan_amount
                else 0.0
            )
            total_interest_cost = sum(
                component.amount
                * float(component.interest_rate or 0.0)
                * float(component.term_years or 0)
                for component in debt_components
            )
            scenario_id = f"scenario_{index}"
            if scenario.name == result.recommended_scenario:
                recommended_id = scenario_id

            scenarios.append(
                FinancingScenario(
                    id=scenario_id,
                    financing_type=scenario.scenario_type.value,
                    loan_amount=loan_amount,
                    ltv_ratio=ltv_ratio,
                    interest_rate=weighted_rate,
                    debt_service_coverage=constraints.min_dscr,
                    projected_irr=scenario.projected_returns.equity_irr,
                    projected_equity_multiple=(
                        scenario.projected_returns.equity_multiple
                    ),
                    total_interest_cost=total_interest_cost,
                    recommendation_score=max(0.0, 1 - (scenario.risk_score / 10)),
                )
            )

        return ScenarioOptimizeResponse(
            project_id=request.project_id,
            scenarios=scenarios,
            recommended_scenario_id=recommended_id,
            analysis_summary=result.optimization_notes,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


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
    try:
        from app.models.property import Property, PropertyType

        property_type = request.property_type
        location = request.district

        if request.property_id and (property_type is None or location is None):
            property_row = (
                await db.execute(
                    select(Property).where(Property.id == request.property_id)
                )
            ).scalar_one_or_none()
            if property_row is not None:
                if property_type is None and property_row.property_type is not None:
                    property_type = property_row.property_type.value
                if location is None:
                    location = property_row.address

        if not property_type or not location:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Market prediction requires a district and property_type",
            )

        try:
            property_type_enum = next(
                item for item in PropertyType if item.value == property_type
            )
        except StopIteration as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unsupported property type: {property_type}",
            ) from exc

        result = await _service("market_predictor").predict_market(
            property_type=property_type_enum,
            location=location,
            db=db,
        )
        if not result.success or result.forecast is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.error or "Failed to generate market prediction",
            )

        forecast = result.forecast
        prediction_types = request.prediction_types or [PredictionType.RENTAL]
        factors = [driver.name for driver in forecast.key_drivers[:3]]
        predictions: list[PredictionItem] = []

        for prediction_type in prediction_types:
            if prediction_type == PredictionType.RENTAL:
                predictions.append(
                    PredictionItem(
                        prediction_type=prediction_type.value,
                        current_value=forecast.rental_forecast.current_psf,
                        predicted_value=forecast.rental_forecast.forecast_12m_psf,
                        change_percentage=forecast.rental_forecast.change_12m_percent,
                        confidence=_confidence_score(
                            forecast.rental_forecast.confidence
                        ),
                        factors=factors,
                    )
                )
            elif prediction_type == PredictionType.CAPITAL_VALUE:
                predictions.append(
                    PredictionItem(
                        prediction_type=prediction_type.value,
                        current_value=forecast.rental_forecast.current_psf,
                        predicted_value=forecast.rental_forecast.forecast_12m_psf,
                        change_percentage=forecast.rental_forecast.change_12m_percent,
                        confidence=_confidence_score(forecast.confidence),
                        factors=factors,
                    )
                )
            elif prediction_type == PredictionType.SUPPLY:
                predictions.append(
                    PredictionItem(
                        prediction_type=prediction_type.value,
                        current_value=forecast.supply_demand.pipeline_sqft,
                        predicted_value=forecast.supply_demand.projected_absorption_sqft,
                        change_percentage=None,
                        confidence=_confidence_score(forecast.confidence),
                        factors=factors,
                    )
                )
            elif prediction_type == PredictionType.DEMAND:
                predictions.append(
                    PredictionItem(
                        prediction_type=prediction_type.value,
                        current_value=forecast.supply_demand.current_vacancy,
                        predicted_value=forecast.supply_demand.projected_vacancy,
                        change_percentage=(
                            (
                                forecast.supply_demand.projected_vacancy
                                - forecast.supply_demand.current_vacancy
                            )
                            * 100
                        ),
                        confidence=_confidence_score(forecast.confidence),
                        factors=factors,
                    )
                )

        return MarketPredictionResponse(
            predictions=predictions,
            forecast_months=request.forecast_months,
            generated_at=forecast.as_of_date,
            summary=forecast.recommendation,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


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
    try:
        submission_type_map = {
            "planning": "development_control",
            "building": "building_plan",
        }
        submission_types = request.submission_types or ["development_control"]
        primary_submission = submission_type_map.get(
            submission_types[0], submission_types[0]
        )

        result = await _service("compliance_predictor").predict_compliance_risk(
            property_id=request.project_id,
            submission_type=primary_submission,
            db=db,
            context={},
        )
        if not result.success or result.assessment is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.error or "Failed to predict compliance risk",
            )

        assessment = result.assessment
        predicted_date = (
            utcnow() + timedelta(weeks=assessment.timeline_estimate.most_likely_weeks)
        ).date()
        milestone = RegulatoryMilestone(
            milestone=assessment.submission_type,
            agency=(
                assessment.required_consultations[0]
                if assessment.required_consultations
                else "URA"
            ),
            predicted_date=predicted_date.isoformat(),
            confidence=_confidence_score(assessment.overall_risk),
            dependencies=assessment.required_consultations,
            risk_factors=[factor.name for factor in assessment.risk_factors],
        )

        return CompliancePredictionResponse(
            project_id=request.project_id,
            milestones=[milestone],
            critical_path_days=assessment.timeline_estimate.most_likely_weeks * 7,
            risk_assessment=assessment.overall_risk.value,
            recommendations=assessment.recommendations,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


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
    result = await _service("due_diligence").generate_checklist(
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
    result = await _service("report_generator").generate_ic_memo(
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
    result = await _service("report_generator").generate_portfolio_report(
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
    result = await _service("communication_drafter").draft_communication(
        draft_request,
        db,
    )

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
    try:
        service = _service("conversational_assistant")
        user_id = request.user_id or "anonymous"
        result = await service.process_message(
            message=request.message,
            conversation_id=request.conversation_id,
            user_id=user_id,
            db=db,
        )
        if not result.success or result.response is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.error or "Failed to process message",
            )

        conversation_id = request.conversation_id or ""
        if not conversation_id:
            conversations = getattr(service, "_conversations", {}).values()
            matching = [ctx for ctx in conversations if ctx.user_id == user_id]
            if matching:
                conversation_id = max(
                    matching, key=lambda ctx: ctx.last_activity
                ).conversation_id

        return ChatMessageResponse(
            conversation_id=conversation_id,
            message=result.response.message,
            suggestions=result.response.suggestions,
            actions_taken=result.response.actions_taken,
            context_updates=result.response.context_updates,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.get("/chat/conversations", response_model=list[ConversationListItem])
async def list_conversations(
    user_id: str,
    _: Role = Depends(require_viewer),
) -> list[ConversationListItem]:
    """List all conversations for a user."""
    conversations = _service("conversational_assistant").list_conversations(user_id)
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
    success = _service("conversational_assistant").clear_conversation(conversation_id)
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
    result = await _service("portfolio_optimizer").optimize(opt_request, db)

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
    try:
        from app.services.ai.multi_modal_analyzer import (
            AnalysisRequest,
            AnalysisType as ServiceAnalysisType,
            ImageType as ServiceImageType,
        )

        analysis_types = (
            [ServiceAnalysisType(item.value) for item in request.analysis_types]
            if request.analysis_types
            else []
        )
        image_data = (
            base64.b64decode(request.image_base64)
            if request.image_base64 is not None
            else None
        )
        analysis_request = AnalysisRequest(
            image_data=image_data,
            image_url=request.image_url,
            image_type=ServiceImageType(request.image_type.value),
            analysis_types=analysis_types,
            context=(
                {"property_id": request.property_id}
                if request.property_id is not None
                else {}
            ),
        )
        result = await _service("multi_modal_analyzer").analyze(analysis_request)

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
                issues_detected=result.condition.visible_issues,
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
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


# ============================================================================
# Competitive Intelligence Endpoints
# ============================================================================


@router.post("/competitors/track", response_model=CompetitorResponse)
async def track_competitor(
    request: CompetitorTrackRequest,
    _: Role = Depends(require_reviewer),
) -> CompetitorResponse:
    """Start tracking a competitor."""
    try:
        from app.services.ai.competitive_intelligence import Competitor, CompetitorType

        type_map = {
            "developer": CompetitorType.DEVELOPER,
            "investor": CompetitorType.INVESTOR,
            "reit": CompetitorType.REIT,
            "fund": CompetitorType.FUND,
            "family_office": CompetitorType.FAMILY_OFFICE,
        }
        competitor = Competitor(
            id=str(uuid4()),
            name=request.name,
            competitor_type=type_map.get(
                request.competitor_type.lower(), CompetitorType.DEVELOPER
            ),
            focus_sectors=request.focus_sectors,
            focus_districts=request.focus_districts,
        )
        competitor.tracked_since = utcnow()
        _service("competitive_intelligence").track_competitor(competitor)
        return CompetitorResponse(
            id=competitor.id,
            name=competitor.name,
            competitor_type=competitor.competitor_type.value,
            focus_sectors=competitor.focus_sectors,
            focus_districts=competitor.focus_districts,
            tracked_since=_tracked_since(competitor),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.get("/competitors", response_model=list[CompetitorResponse])
async def list_competitors(
    _: Role = Depends(require_viewer),
) -> list[CompetitorResponse]:
    """List all tracked competitors."""
    competitors = _service("competitive_intelligence").list_competitors()
    return [
        CompetitorResponse(
            id=c.id,
            name=c.name,
            competitor_type=c.competitor_type.value,
            focus_sectors=c.focus_sectors,
            focus_districts=c.focus_districts,
            tracked_since=_tracked_since(c),
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
    try:
        dashboard = await _service("competitive_intelligence").get_dashboard(
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
                    tracked_since=_tracked_since(c),
                )
                for c in dashboard.competitors
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
                for a in dashboard.recent_activities
            ],
            alerts=[
                CompetitiveAlertResponse(
                    id=a.id,
                    priority=a.priority.value,
                    title=a.title,
                    description=a.description,
                    competitor_id=a.competitor_id or "",
                    competitor_name=a.competitor_name or "",
                    action_required=a.action_required or "",
                    expires_at=a.expires_at or utcnow(),
                )
                for a in dashboard.alerts
            ],
            summary=dashboard.summary,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


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
    try:
        from app.services.ai.workflow_engine import WorkflowTrigger as ServiceTrigger

        trigger_map = {
            "deal_created": ServiceTrigger.DEAL_CREATED,
            "deal_stage_changed": ServiceTrigger.DEAL_STAGE_CHANGED,
            "deadline_approaching": ServiceTrigger.DEADLINE_APPROACHING,
            "document_uploaded": ServiceTrigger.DOCUMENT_UPLOADED,
            "approval_required": ServiceTrigger.MANUAL,
            "compliance_flag": ServiceTrigger.MANUAL,
            "market_alert": ServiceTrigger.MANUAL,
        }

        results = await _service("workflow_engine").trigger_workflow(
            trigger=trigger_map[request.trigger.value],
            event_data=request.event_data,
            db=db,
        )
        return [
            response
            for response in (_workflow_response(result) for result in results)
            if response is not None
        ]
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.get("/workflows", response_model=list[WorkflowDefinitionResponse])
async def list_workflows(
    _: Role = Depends(require_viewer),
) -> list[WorkflowDefinitionResponse]:
    """List all workflow definitions."""
    workflows = _service("workflow_engine").list_workflows()
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
    try:
        results = await _service("workflow_engine").check_deadlines(db)
        return [
            response
            for response in (_workflow_response(result) for result in results)
            if response is not None
        ]
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


# ============================================================================
# Anomaly Detection Endpoints
# ============================================================================


@router.post("/anomalies/detect", response_model=AnomalyDetectionResponse)
async def detect_anomalies(
    request: AnomalyDetectionRequest,
    identity: Role = Depends(require_viewer),
    db: AsyncSession = Depends(get_db),
) -> AnomalyDetectionResponse:
    """Detect anomalies in deals, properties, or projects.

    Returns alerts for unusual patterns or values.
    """
    try:
        alerts = await _service("anomaly_detector").run_detection_cycle(
            db=db,
            user_id=_identity_user_id(identity),
            context={
                "deal_id": request.deal_id,
                "property_id": request.property_id,
                "project_id": request.project_id,
            },
        )
        return AnomalyDetectionResponse(
            alerts=[
                AnomalyAlert(
                    id=alert.id,
                    alert_type=alert.category.value,
                    severity=alert.priority.value,
                    title=alert.title,
                    description=alert.message,
                    entity_type=alert.entity_type or "unknown",
                    entity_id=alert.entity_id or "",
                    detected_value=alert.data,
                    expected_range=None,
                    recommendation=(
                        alert.suggested_actions[0] if alert.suggested_actions else ""
                    ),
                    detected_at=alert.created_at,
                )
                for alert in alerts
            ],
            entities_scanned=(
                sum(
                    1
                    for value in (
                        request.deal_id,
                        request.property_id,
                        request.project_id,
                    )
                    if value
                )
                or 1
            ),
            scan_time_ms=0.0,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


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
    try:
        from app.services.ai.document_extractor import DocumentType

        document_type_map = {
            "contract": DocumentType.SALE_PURCHASE_AGREEMENT,
            "lease": DocumentType.TENANCY_AGREEMENT,
        }
        service = _service("document_extractor")
        document_type = document_type_map.get(
            request.document_type.lower(), DocumentType.UNKNOWN
        )

        if request.document_base64:
            raw_bytes = base64.b64decode(request.document_base64)
            if raw_bytes.startswith(b"%PDF"):
                result = await service.extract_from_pdf(raw_bytes, document_type)
            else:
                try:
                    text = raw_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    result = await service.extract_from_image(raw_bytes, document_type)
                else:
                    result = await service.extract_from_text(text, document_type)
        elif request.document_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Remote document fetching is unavailable in this environment",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Document source is required",
            )

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.error or "Failed to extract document",
            )

        extracted_data = result.extracted_data or {}
        parties = [
            value
            for key, value in extracted_data.items()
            if key.endswith("_name") and isinstance(value, str) and value
        ]
        key_dates = {
            key: str(value)
            for key, value in extracted_data.items()
            if "date" in key and value is not None
        }
        summary = (
            result.raw_text
            or extracted_data.get("raw_response")
            or "Document processed successfully."
        )

        return DocumentExtractionResponse(
            document_type=result.document_type.value,
            clauses=[],
            tables=[],
            key_dates=key_dates,
            parties=parties,
            summary=str(summary),
            processing_time_ms=result.processing_time_ms,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


# ============================================================================
# Health Check
# ============================================================================


@router.get("/health")
async def ai_health_check() -> dict[str, Any]:
    """Check health status of AI services."""
    return {
        "status": "ok",
        "services": {name: _service_initialized(name) for name in _AI_SERVICE_REGISTRY},
    }


__all__ = ["router"]
