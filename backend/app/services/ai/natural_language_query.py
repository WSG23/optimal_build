"""Phase 1.1: Natural Language Query Interface.

Translates natural language queries into structured database queries using LLM function calling.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from langchain_openai import ChatOpenAI
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business_performance import (
    AgentDeal,
    DealAssetType,
    DealStatus,
    DealType,
    PipelineStage,
)
from app.models.property import Property, PropertyType, MarketTransaction
from app.models.finance import FinScenario

logger = logging.getLogger(__name__)


class QueryType(str, Enum):
    """Types of queries supported by the NL interface."""

    SEARCH_PROPERTIES = "search_properties"
    SEARCH_DEALS = "search_deals"
    ANALYZE_PIPELINE = "analyze_pipeline"
    COMPARE_SCENARIOS = "compare_scenarios"
    MARKET_ANALYSIS = "market_analysis"
    PERFORMANCE_METRICS = "performance_metrics"
    GENERAL_QUESTION = "general_question"


@dataclass
class QueryResult:
    """Result from a natural language query."""

    success: bool
    query_type: QueryType
    natural_response: str
    data: list[dict[str, Any]] = field(default_factory=list)
    sql_executed: str | None = None
    execution_time_ms: float = 0.0
    suggestions: list[str] = field(default_factory=list)
    error: str | None = None


# OpenAI function definitions for structured query parsing
QUERY_FUNCTIONS = [
    {
        "name": "search_properties",
        "description": "Search for properties by various criteria like type, location, size, GPR",
        "parameters": {
            "type": "object",
            "properties": {
                "property_type": {
                    "type": "string",
                    "enum": [t.value for t in PropertyType],
                    "description": "Type of property (office, retail, industrial, etc.)",
                },
                "location": {
                    "type": "string",
                    "description": "Location, district, or planning area to search",
                },
                "min_gpr": {
                    "type": "number",
                    "description": "Minimum gross plot ratio",
                },
                "max_gpr": {
                    "type": "number",
                    "description": "Maximum gross plot ratio",
                },
                "min_land_area": {
                    "type": "number",
                    "description": "Minimum land area in sqm",
                },
                "max_land_area": {
                    "type": "number",
                    "description": "Maximum land area in sqm",
                },
                "tenure": {
                    "type": "string",
                    "description": "Tenure type (freehold, leasehold_99, etc.)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 10,
                },
            },
        },
    },
    {
        "name": "search_deals",
        "description": "Search for deals in the pipeline by status, type, value, or other criteria",
        "parameters": {
            "type": "object",
            "properties": {
                "deal_type": {
                    "type": "string",
                    "enum": [t.value for t in DealType],
                    "description": "Type of deal (buy_side, sell_side, lease, etc.)",
                },
                "asset_type": {
                    "type": "string",
                    "enum": [t.value for t in DealAssetType],
                    "description": "Asset type for the deal",
                },
                "status": {
                    "type": "string",
                    "enum": [s.value for s in DealStatus],
                    "description": "Deal status (open, closed_won, closed_lost)",
                },
                "pipeline_stage": {
                    "type": "string",
                    "enum": [s.value for s in PipelineStage],
                    "description": "Current pipeline stage",
                },
                "min_value": {
                    "type": "number",
                    "description": "Minimum deal value",
                },
                "max_value": {
                    "type": "number",
                    "description": "Maximum deal value",
                },
                "date_range": {
                    "type": "string",
                    "description": "Date range like 'last_month', 'this_quarter', 'last_year'",
                },
                "limit": {
                    "type": "integer",
                    "default": 10,
                },
            },
        },
    },
    {
        "name": "analyze_pipeline",
        "description": "Get pipeline analytics like total value, deal count, conversion rates",
        "parameters": {
            "type": "object",
            "properties": {
                "metric": {
                    "type": "string",
                    "enum": [
                        "total_value",
                        "deal_count",
                        "conversion_rate",
                        "avg_deal_size",
                        "stage_distribution",
                        "velocity",
                    ],
                    "description": "The metric to analyze",
                },
                "group_by": {
                    "type": "string",
                    "enum": ["asset_type", "deal_type", "stage", "month", "quarter"],
                    "description": "How to group the results",
                },
                "date_range": {
                    "type": "string",
                    "description": "Date range for analysis",
                },
            },
        },
    },
    {
        "name": "compare_scenarios",
        "description": "Compare financial scenarios for a project",
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "ID of the project to compare scenarios for",
                },
                "scenario_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of scenario IDs to compare",
                },
                "comparison_metric": {
                    "type": "string",
                    "enum": [
                        "irr",
                        "npv",
                        "equity_multiple",
                        "cash_on_cash",
                        "payback",
                    ],
                    "description": "Primary metric for comparison",
                },
            },
        },
    },
    {
        "name": "market_analysis",
        "description": "Analyze market data like transactions, cap rates, rental trends",
        "parameters": {
            "type": "object",
            "properties": {
                "analysis_type": {
                    "type": "string",
                    "enum": [
                        "recent_transactions",
                        "cap_rate_trends",
                        "rental_trends",
                        "supply_pipeline",
                        "absorption_rates",
                    ],
                    "description": "Type of market analysis",
                },
                "property_type": {
                    "type": "string",
                    "enum": [t.value for t in PropertyType],
                },
                "location": {
                    "type": "string",
                    "description": "Location or district to analyze",
                },
                "date_range": {
                    "type": "string",
                },
            },
        },
    },
    {
        "name": "performance_metrics",
        "description": "Get agent or team performance metrics",
        "parameters": {
            "type": "object",
            "properties": {
                "metric": {
                    "type": "string",
                    "enum": [
                        "commission_earned",
                        "deals_closed",
                        "pipeline_value",
                        "conversion_rate",
                        "avg_cycle_time",
                    ],
                },
                "agent_id": {
                    "type": "string",
                    "description": "Specific agent ID or 'all' for team",
                },
                "date_range": {
                    "type": "string",
                },
            },
        },
    },
]


class NaturalLanguageQueryService:
    """Service for processing natural language queries against the database."""

    def __init__(self) -> None:
        """Initialize the NL query service with LLM."""
        self.llm: Optional[ChatOpenAI] = None
        try:
            self.llm = ChatOpenAI(
                model="gpt-4-turbo",
                temperature=0,
            )
            self._initialized = True
        except Exception as e:
            logger.warning(f"NL Query Service not initialized: {e}")
            self._initialized = False

    async def process_query(
        self,
        query: str,
        user_id: str,
        db: AsyncSession,
    ) -> QueryResult:
        """Process a natural language query and return structured results.

        Args:
            query: The natural language query from the user
            user_id: The ID of the user making the query
            db: Database session for executing queries

        Returns:
            QueryResult with data and natural language response
        """
        start_time = datetime.now()

        if not self._initialized or not self.llm:
            return QueryResult(
                success=False,
                query_type=QueryType.GENERAL_QUESTION,
                natural_response="Natural language query service is not configured. Please set OPENAI_API_KEY.",
                error="Service not initialized",
            )

        try:
            # Use function calling to parse the query intent
            messages = [
                {
                    "role": "system",
                    "content": """You are a query parser for a real estate platform.
                    Analyze the user's question and call the appropriate function.
                    If the question doesn't match any function, respond naturally with what you know.""",
                },
                {"role": "user", "content": query},
            ]

            response = self.llm.invoke(
                messages,
                functions=QUERY_FUNCTIONS,
                function_call="auto",
            )

            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            # Check if a function was called
            if response.additional_kwargs.get("function_call"):
                func_call = response.additional_kwargs["function_call"]
                func_name = func_call["name"]
                func_args = json.loads(func_call["arguments"])

                # Execute the appropriate query
                result = await self._execute_function(func_name, func_args, user_id, db)
                result.execution_time_ms = execution_time
                return result

            # No function called - return general response
            content = response.content
            natural_response = (
                content
                if isinstance(content, str) and content
                else "I understand your question but need more context to provide specific data."
            )
            return QueryResult(
                success=True,
                query_type=QueryType.GENERAL_QUESTION,
                natural_response=natural_response,
                execution_time_ms=execution_time,
                suggestions=[
                    "Try asking about specific properties, deals, or metrics",
                    "Example: 'Show me industrial properties in Jurong'",
                    "Example: 'What's my pipeline value this quarter?'",
                ],
            )

        except Exception as e:
            logger.error(f"Error processing NL query: {e}")
            return QueryResult(
                success=False,
                query_type=QueryType.GENERAL_QUESTION,
                natural_response=f"I encountered an error processing your query: {str(e)}",
                error=str(e),
            )

    async def _execute_function(
        self,
        func_name: str,
        args: dict[str, Any],
        user_id: str,
        db: AsyncSession,
    ) -> QueryResult:
        """Execute the parsed function against the database."""
        handlers = {
            "search_properties": self._search_properties,
            "search_deals": self._search_deals,
            "analyze_pipeline": self._analyze_pipeline,
            "compare_scenarios": self._compare_scenarios,
            "market_analysis": self._market_analysis,
            "performance_metrics": self._performance_metrics,
        }

        handler = handlers.get(func_name)
        if not handler:
            return QueryResult(
                success=False,
                query_type=QueryType.GENERAL_QUESTION,
                natural_response=f"Unknown query type: {func_name}",
                error=f"No handler for {func_name}",
            )

        return await handler(args, user_id, db)

    async def _search_properties(
        self,
        args: dict[str, Any],
        user_id: str,
        db: AsyncSession,
    ) -> QueryResult:
        """Search for properties based on criteria."""
        conditions = []

        if args.get("property_type"):
            conditions.append(Property.property_type == args["property_type"])

        if args.get("location"):
            location = args["location"]
            conditions.append(
                or_(
                    Property.district.ilike(f"%{location}%"),
                    Property.planning_area.ilike(f"%{location}%"),
                    Property.address.ilike(f"%{location}%"),
                )
            )

        if args.get("min_gpr"):
            conditions.append(Property.plot_ratio >= args["min_gpr"])

        if args.get("max_gpr"):
            conditions.append(Property.plot_ratio <= args["max_gpr"])

        if args.get("min_land_area"):
            conditions.append(Property.land_area_sqm >= args["min_land_area"])

        if args.get("max_land_area"):
            conditions.append(Property.land_area_sqm <= args["max_land_area"])

        limit = args.get("limit", 10)

        query = select(Property)
        if conditions:
            query = query.where(and_(*conditions))
        query = query.limit(limit)

        result = await db.execute(query)
        properties = result.scalars().all()

        data = [
            {
                "id": str(p.id),
                "name": p.name,
                "address": p.address,
                "property_type": p.property_type.value if p.property_type else None,
                "district": p.district,
                "land_area_sqm": float(p.land_area_sqm) if p.land_area_sqm else None,
                "plot_ratio": float(p.plot_ratio) if p.plot_ratio else None,
                "tenure": p.tenure_type.value if p.tenure_type else None,
            }
            for p in properties
        ]

        count = len(data)
        response = f"Found {count} propert{'y' if count == 1 else 'ies'}"
        if args.get("property_type"):
            response += f" of type {args['property_type']}"
        if args.get("location"):
            response += f" in {args['location']}"
        response += "."

        return QueryResult(
            success=True,
            query_type=QueryType.SEARCH_PROPERTIES,
            natural_response=response,
            data=data,
        )

    async def _search_deals(
        self,
        args: dict[str, Any],
        user_id: str,
        db: AsyncSession,
    ) -> QueryResult:
        """Search for deals based on criteria."""
        conditions = [AgentDeal.agent_id == user_id]  # User can only see their deals

        if args.get("deal_type"):
            conditions.append(AgentDeal.deal_type == args["deal_type"])

        if args.get("asset_type"):
            conditions.append(AgentDeal.asset_type == args["asset_type"])

        if args.get("status"):
            conditions.append(AgentDeal.status == args["status"])

        if args.get("pipeline_stage"):
            conditions.append(AgentDeal.pipeline_stage == args["pipeline_stage"])

        if args.get("min_value"):
            conditions.append(AgentDeal.estimated_value_amount >= args["min_value"])

        if args.get("max_value"):
            conditions.append(AgentDeal.estimated_value_amount <= args["max_value"])

        limit = args.get("limit", 10)

        query = select(AgentDeal).where(and_(*conditions)).limit(limit)
        result = await db.execute(query)
        deals = result.scalars().all()

        data = [
            {
                "id": str(d.id),
                "title": d.title,
                "deal_type": d.deal_type.value,
                "asset_type": d.asset_type.value,
                "status": d.status.value,
                "pipeline_stage": d.pipeline_stage.value,
                "estimated_value": (
                    float(d.estimated_value_amount) if d.estimated_value_amount else None
                ),
                "currency": d.estimated_value_currency,
                "expected_close_date": (
                    d.expected_close_date.isoformat() if d.expected_close_date else None
                ),
            }
            for d in deals
        ]

        count = len(data)
        total_value = sum(d.get("estimated_value") or 0 for d in data)

        response = f"Found {count} deal{'s' if count != 1 else ''}"
        if args.get("status"):
            response += f" with status '{args['status']}'"
        if total_value:
            response += f" with total value ${total_value:,.0f}"
        response += "."

        return QueryResult(
            success=True,
            query_type=QueryType.SEARCH_DEALS,
            natural_response=response,
            data=data,
        )

    async def _analyze_pipeline(
        self,
        args: dict[str, Any],
        user_id: str,
        db: AsyncSession,
    ) -> QueryResult:
        """Analyze pipeline metrics."""
        metric = args.get("metric", "total_value")

        # Build base query for user's deals
        base_condition = and_(
            AgentDeal.agent_id == user_id,
            AgentDeal.status == DealStatus.OPEN,
        )

        if metric == "total_value":
            query = select(func.sum(AgentDeal.estimated_value_amount)).where(base_condition)
            result = await db.execute(query)
            total = result.scalar() or 0

            return QueryResult(
                success=True,
                query_type=QueryType.ANALYZE_PIPELINE,
                natural_response=f"Your total pipeline value is ${float(total):,.0f}",
                data=[{"metric": "total_value", "value": float(total)}],
            )

        elif metric == "deal_count":
            query = select(func.count(AgentDeal.id)).where(base_condition)
            result = await db.execute(query)
            count = result.scalar() or 0

            return QueryResult(
                success=True,
                query_type=QueryType.ANALYZE_PIPELINE,
                natural_response=f"You have {count} open deal{'s' if count != 1 else ''} in your pipeline",
                data=[{"metric": "deal_count", "value": count}],
            )

        elif metric == "stage_distribution":
            query = (
                select(
                    AgentDeal.pipeline_stage,
                    func.count(AgentDeal.id).label("count"),
                    func.sum(AgentDeal.estimated_value_amount).label("value"),
                )
                .where(base_condition)
                .group_by(AgentDeal.pipeline_stage)
            )
            result = await db.execute(query)
            rows = result.all()

            data = [
                {
                    "stage": row.pipeline_stage.value,
                    "count": row.count,
                    "value": float(row.value) if row.value else 0,
                }
                for row in rows
            ]

            response = "Pipeline distribution:\n" + "\n".join(
                f"- {d['stage']}: {d['count']} deals (${d['value']:,.0f})" for d in data
            )

            return QueryResult(
                success=True,
                query_type=QueryType.ANALYZE_PIPELINE,
                natural_response=response,
                data=data,
            )

        return QueryResult(
            success=True,
            query_type=QueryType.ANALYZE_PIPELINE,
            natural_response=f"Metric '{metric}' analysis not yet implemented",
            data=[],
        )

    async def _compare_scenarios(
        self,
        args: dict[str, Any],
        user_id: str,
        db: AsyncSession,
    ) -> QueryResult:
        """Compare financial scenarios."""
        scenario_ids = args.get("scenario_ids", [])

        if not scenario_ids:
            return QueryResult(
                success=False,
                query_type=QueryType.COMPARE_SCENARIOS,
                natural_response="Please specify which scenarios to compare",
                error="No scenario IDs provided",
            )

        query = select(FinScenario).where(FinScenario.id.in_(scenario_ids))
        result = await db.execute(query)
        scenarios = result.scalars().all()

        data = [
            {
                "id": str(s.id),
                "name": s.name,
                "description": s.description,
                "assumption_overrides": s.assumption_overrides,
            }
            for s in scenarios
        ]

        return QueryResult(
            success=True,
            query_type=QueryType.COMPARE_SCENARIOS,
            natural_response=f"Comparing {len(data)} scenarios",
            data=data,
        )

    async def _market_analysis(
        self,
        args: dict[str, Any],
        user_id: str,
        db: AsyncSession,
    ) -> QueryResult:
        """Perform market analysis."""
        analysis_type = args.get("analysis_type", "recent_transactions")

        if analysis_type == "recent_transactions":
            query = (
                select(MarketTransaction)
                .order_by(MarketTransaction.transaction_date.desc())
                .limit(20)
            )

            if args.get("property_type"):
                # Would need to join with Property table
                pass

            result = await db.execute(query)
            transactions = result.scalars().all()

            data = [
                {
                    "id": str(t.id),
                    "date": (t.transaction_date.isoformat() if t.transaction_date else None),
                    "price": float(t.sale_price) if t.sale_price else None,
                    "psf": float(t.psf_price) if t.psf_price else None,
                    "type": t.transaction_type,
                }
                for t in transactions
            ]

            return QueryResult(
                success=True,
                query_type=QueryType.MARKET_ANALYSIS,
                natural_response=f"Found {len(data)} recent transactions",
                data=data,
            )

        return QueryResult(
            success=True,
            query_type=QueryType.MARKET_ANALYSIS,
            natural_response=f"Analysis type '{analysis_type}' not yet implemented",
            data=[],
        )

    async def _performance_metrics(
        self,
        args: dict[str, Any],
        user_id: str,
        db: AsyncSession,
    ) -> QueryResult:
        """Get performance metrics."""
        metric = args.get("metric", "deals_closed")
        target_agent = args.get("agent_id", user_id)

        if metric == "deals_closed":
            query = select(func.count(AgentDeal.id)).where(
                and_(
                    AgentDeal.agent_id == target_agent,
                    AgentDeal.status == DealStatus.CLOSED_WON,
                )
            )
            result = await db.execute(query)
            count = result.scalar() or 0

            return QueryResult(
                success=True,
                query_type=QueryType.PERFORMANCE_METRICS,
                natural_response=f"You have closed {count} deal{'s' if count != 1 else ''}",
                data=[{"metric": "deals_closed", "value": count}],
            )

        elif metric == "pipeline_value":
            query = select(func.sum(AgentDeal.estimated_value_amount)).where(
                and_(
                    AgentDeal.agent_id == target_agent,
                    AgentDeal.status == DealStatus.OPEN,
                )
            )
            result = await db.execute(query)
            total = result.scalar() or 0

            return QueryResult(
                success=True,
                query_type=QueryType.PERFORMANCE_METRICS,
                natural_response=f"Your pipeline value is ${float(total):,.0f}",
                data=[{"metric": "pipeline_value", "value": float(total)}],
            )

        return QueryResult(
            success=True,
            query_type=QueryType.PERFORMANCE_METRICS,
            natural_response=f"Metric '{metric}' not yet implemented",
            data=[],
        )


# Singleton instance
nl_query_service = NaturalLanguageQueryService()
