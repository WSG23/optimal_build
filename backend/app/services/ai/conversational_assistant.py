"""Phase 4.1: Conversational AI Assistant.

Context-aware AI assistant with memory and tool usage.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from langchain_openai import ChatOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai.natural_language_query import NaturalLanguageQueryService
from app.services.ai.deal_scoring import DealScoringService
from app.services.ai.rag_knowledge_base import RAGKnowledgeBaseService

logger = logging.getLogger(__name__)


class MessageRole(str, Enum):
    """Role in conversation."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class AssistantCapability(str, Enum):
    """Capabilities the assistant can use."""

    SEARCH_PROPERTIES = "search_properties"
    SEARCH_DEALS = "search_deals"
    ANALYZE_DEAL = "analyze_deal"
    SCORE_DEAL = "score_deal"
    MARKET_ANALYSIS = "market_analysis"
    GENERATE_REPORT = "generate_report"
    CHECK_COMPLIANCE = "check_compliance"
    SCHEDULE_TASK = "schedule_task"
    KNOWLEDGE_SEARCH = "knowledge_search"


@dataclass
class Message:
    """A message in the conversation."""

    id: str
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    tool_calls: list[dict[str, Any]] | None = None
    tool_result: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class ConversationContext:
    """Context for the current conversation."""

    conversation_id: str
    user_id: str
    messages: list[Message]
    active_deal_id: str | None = None
    active_property_id: str | None = None
    preferences: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)


@dataclass
class AssistantResponse:
    """Response from the assistant."""

    message: str
    suggestions: list[str]
    actions_taken: list[dict[str, Any]]
    context_updates: dict[str, Any]
    confidence: float = 1.0


@dataclass
class ConversationResult:
    """Result from processing a user message."""

    success: bool
    response: AssistantResponse | None = None
    error: str | None = None


class ConversationalAssistantService:
    """AI-powered conversational assistant."""

    def __init__(self) -> None:
        """Initialize the assistant."""
        try:
            self.llm = ChatOpenAI(
                model_name="gpt-4-turbo",
                temperature=0.7,
            )
            self.nl_query_service = NaturalLanguageQueryService()
            self.deal_scoring_service = DealScoringService()
            self.knowledge_service = RAGKnowledgeBaseService()
            self._initialized = True
            self._conversations: dict[str, ConversationContext] = {}
        except Exception as e:
            logger.warning(f"Conversational Assistant not initialized: {e}")
            self._initialized = False
            self.llm = None
            self._conversations = {}

    async def process_message(
        self,
        user_id: str,
        message: str,
        conversation_id: str | None = None,
        db: AsyncSession | None = None,
    ) -> ConversationResult:
        """Process a user message and generate a response.

        Args:
            user_id: ID of the user
            message: User's message
            conversation_id: Optional existing conversation ID
            db: Database session

        Returns:
            ConversationResult with response
        """
        try:
            # Get or create conversation context
            if conversation_id and conversation_id in self._conversations:
                context = self._conversations[conversation_id]
            else:
                context = ConversationContext(
                    conversation_id=str(uuid4()),
                    user_id=user_id,
                    messages=[],
                )
                self._conversations[context.conversation_id] = context

            # Add user message
            user_msg = Message(
                id=str(uuid4()),
                role=MessageRole.USER,
                content=message,
            )
            context.messages.append(user_msg)
            context.last_activity = datetime.now()

            # Process the message
            response = await self._generate_response(context, db)

            # Add assistant message
            assistant_msg = Message(
                id=str(uuid4()),
                role=MessageRole.ASSISTANT,
                content=response.message,
                metadata={"actions": response.actions_taken},
            )
            context.messages.append(assistant_msg)

            # Update context
            if response.context_updates:
                if "active_deal_id" in response.context_updates:
                    context.active_deal_id = response.context_updates["active_deal_id"]
                if "active_property_id" in response.context_updates:
                    context.active_property_id = response.context_updates[
                        "active_property_id"
                    ]

            return ConversationResult(
                success=True,
                response=response,
            )

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return ConversationResult(
                success=False,
                error=str(e),
            )

    async def _generate_response(
        self,
        context: ConversationContext,
        db: AsyncSession | None,
    ) -> AssistantResponse:
        """Generate a response using the LLM and tools."""
        if not self._initialized or not self.llm:
            return self._generate_fallback_response(context)

        # Analyze intent
        latest_message = context.messages[-1].content
        intent = await self._analyze_intent(latest_message)

        actions_taken = []
        context_updates = {}
        tool_results = []

        # Execute relevant tools based on intent
        if intent.get("needs_search"):
            search_result = await self._execute_search(
                intent.get("search_query", latest_message),
                intent.get("search_type", "general"),
                db,
            )
            tool_results.append(search_result)
            actions_taken.append(
                {
                    "action": "search",
                    "query": intent.get("search_query"),
                    "type": intent.get("search_type"),
                }
            )

        if intent.get("needs_deal_analysis") and context.active_deal_id:
            score_result = await self._analyze_deal(context.active_deal_id, db)
            tool_results.append(score_result)
            actions_taken.append(
                {
                    "action": "deal_analysis",
                    "deal_id": context.active_deal_id,
                }
            )

        if intent.get("needs_knowledge"):
            kb_result = await self._search_knowledge(
                intent.get("knowledge_query", latest_message),
            )
            tool_results.append(kb_result)
            actions_taken.append(
                {
                    "action": "knowledge_search",
                    "query": intent.get("knowledge_query"),
                }
            )

        # Generate final response
        response_text = await self._compose_response(
            context,
            intent,
            tool_results,
        )

        # Generate suggestions
        suggestions = self._generate_suggestions(context, intent)

        return AssistantResponse(
            message=response_text,
            suggestions=suggestions,
            actions_taken=actions_taken,
            context_updates=context_updates,
            confidence=intent.get("confidence", 0.8),
        )

    async def _analyze_intent(self, message: str) -> dict[str, Any]:
        """Analyze the intent of a user message."""
        if not self.llm:
            return {"intent": "general", "confidence": 0.5}

        prompt = f"""Analyze the following user message and determine the intent.
Return a JSON object with these fields:
- intent: The primary intent (search, analyze, compare, report, question, action)
- needs_search: boolean, whether we need to search for data
- search_type: if needs_search, what type (properties, deals, transactions)
- search_query: if needs_search, the search query
- needs_deal_analysis: boolean, whether to analyze a specific deal
- needs_knowledge: boolean, whether to search the knowledge base
- knowledge_query: if needs_knowledge, the query
- confidence: float 0-1

Message: "{message}"

Return only valid JSON:"""

        try:
            response = self.llm.invoke(prompt)
            content = response.content or "{}"
            # Simple JSON extraction
            import json

            # Find JSON in response
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
            return {"intent": "general", "confidence": 0.5}
        except Exception as e:
            logger.warning(f"Intent analysis failed: {e}")
            return {"intent": "general", "confidence": 0.5}

    async def _execute_search(
        self,
        query: str,
        search_type: str,
        db: AsyncSession | None,
    ) -> dict[str, Any]:
        """Execute a search using the NL query service."""
        if not db:
            return {"error": "No database connection"}

        result = await self.nl_query_service.process_query(query, db)
        return {
            "type": "search",
            "query": query,
            "results": result.results if result else [],
            "summary": result.summary if result else "No results found",
        }

    async def _analyze_deal(
        self,
        deal_id: str,
        db: AsyncSession | None,
    ) -> dict[str, Any]:
        """Analyze a deal using the scoring service."""
        if not db:
            return {"error": "No database connection"}

        score = await self.deal_scoring_service.score_deal(deal_id, db)
        return {
            "type": "deal_analysis",
            "deal_id": deal_id,
            "score": score.overall_score if score else None,
            "factors": (
                {f.factor: f.score for f in score.factor_scores} if score else {}
            ),
            "recommendation": score.recommendation if score else "Unable to analyze",
        }

    async def _search_knowledge(self, query: str) -> dict[str, Any]:
        """Search the knowledge base."""
        result = await self.knowledge_service.search(query)
        return {
            "type": "knowledge",
            "query": query,
            "results": (
                [
                    {"content": r.content, "score": r.relevance_score}
                    for r in result.results[:5]
                ]
                if result
                else []
            ),
            "answer": result.generated_answer if result else None,
        }

    async def _compose_response(
        self,
        context: ConversationContext,
        intent: dict[str, Any],
        tool_results: list[dict[str, Any]],
    ) -> str:
        """Compose the final response."""
        if not self.llm:
            return self._compose_fallback_response(context, tool_results)

        # Build conversation history
        history = "\n".join(
            f"{msg.role.value}: {msg.content}"
            for msg in context.messages[-5:]  # Last 5 messages
        )

        # Build tool results summary
        results_summary = "\n".join(
            f"- {r.get('type', 'result')}: {r.get('summary', str(r))}"
            for r in tool_results
        )

        prompt = f"""You are a helpful real estate investment assistant for Singapore property market.
Generate a natural, helpful response based on the conversation and any tool results.

Conversation:
{history}

Tool Results:
{results_summary or "No tool results"}

Current Context:
- Active Deal: {context.active_deal_id or 'None'}
- Active Property: {context.active_property_id or 'None'}

Generate a helpful, conversational response. Be specific with any data from the tool results.
If you don't have enough information, ask clarifying questions.

Response:"""

        try:
            response = self.llm.invoke(prompt)
            return (
                response.content
                or "I apologize, I'm having trouble generating a response."
            )
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return self._compose_fallback_response(context, tool_results)

    def _compose_fallback_response(
        self,
        context: ConversationContext,
        tool_results: list[dict[str, Any]],
    ) -> str:
        """Compose a fallback response without LLM."""
        if tool_results:
            for result in tool_results:
                if result.get("type") == "search" and result.get("summary"):
                    return f"Based on your search: {result['summary']}"
                if result.get("type") == "deal_analysis" and result.get("score"):
                    return f"The deal has a score of {result['score']}/100. {result.get('recommendation', '')}"
                if result.get("type") == "knowledge" and result.get("answer"):
                    return result["answer"]

        return "I'm here to help with your real estate investment questions. What would you like to know?"

    def _generate_fallback_response(
        self, context: ConversationContext
    ) -> AssistantResponse:
        """Generate a fallback response when LLM is unavailable."""
        return AssistantResponse(
            message="I'm currently operating in limited mode. How can I assist you with your real estate needs?",
            suggestions=[
                "Search for properties in a specific district",
                "Review your active deals",
                "Check regulatory submission status",
            ],
            actions_taken=[],
            context_updates={},
            confidence=0.3,
        )

    def _generate_suggestions(
        self,
        context: ConversationContext,
        intent: dict[str, Any],
    ) -> list[str]:
        """Generate contextual suggestions for next actions."""
        suggestions = []

        if context.active_deal_id:
            suggestions.extend(
                [
                    "Analyze this deal's risk factors",
                    "Generate an IC memo for this deal",
                    "Check compliance status",
                ]
            )
        else:
            suggestions.extend(
                [
                    "Show me my active deals",
                    "Search for industrial properties in Jurong",
                    "What's the market outlook for office space?",
                ]
            )

        if intent.get("intent") == "search":
            suggestions.append("Refine the search with additional filters")

        if not suggestions:
            suggestions = [
                "What properties are available?",
                "How's my pipeline performing?",
                "Any deadlines coming up?",
            ]

        return suggestions[:3]

    def get_conversation(self, conversation_id: str) -> ConversationContext | None:
        """Get a conversation by ID.

        Args:
            conversation_id: ID of the conversation

        Returns:
            ConversationContext or None
        """
        return self._conversations.get(conversation_id)

    def list_conversations(self, user_id: str) -> list[ConversationContext]:
        """List all conversations for a user.

        Args:
            user_id: ID of the user

        Returns:
            List of conversations
        """
        return [c for c in self._conversations.values() if c.user_id == user_id]

    def clear_conversation(self, conversation_id: str) -> bool:
        """Clear a conversation history.

        Args:
            conversation_id: ID of the conversation

        Returns:
            True if cleared, False if not found
        """
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            return True
        return False


# Singleton instance
conversational_assistant_service = ConversationalAssistantService()
