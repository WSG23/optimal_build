"""Phase 1.4: Enhanced RAG Knowledge Base.

Unified knowledge base with automatic ingestion and semantic search.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.property import Property
from app.models.business_performance import AgentDeal

logger = logging.getLogger(__name__)


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


@dataclass
class KnowledgeChunk:
    """A chunk of knowledge for embedding."""

    id: str
    source_type: KnowledgeSourceType
    source_id: str
    content: str
    metadata: dict[str, Any]
    embedding: list[float] | None = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class SearchResult:
    """A search result from the knowledge base."""

    chunk_id: str
    source_type: KnowledgeSourceType
    source_id: str
    content: str
    relevance_score: float
    metadata: dict[str, Any]


@dataclass
class KnowledgeSearchResponse:
    """Response from knowledge search."""

    query: str
    results: list[SearchResult]
    total_chunks_searched: int
    search_time_ms: float
    generated_answer: str | None = None


@dataclass
class IngestionResult:
    """Result from knowledge ingestion."""

    success: bool
    chunks_created: int
    source_type: KnowledgeSourceType
    source_id: str
    error: str | None = None


class RAGKnowledgeBaseService:
    """Service for managing the RAG knowledge base."""

    def __init__(self) -> None:
        """Initialize the knowledge base service."""
        self.embeddings: Optional[OpenAIEmbeddings] = None
        self.llm: Optional[ChatOpenAI] = None
        self._chunks: dict[str, KnowledgeChunk] = {}
        self._embeddings_cache: dict[str, list[float]] = {}
        try:
            self.embeddings = OpenAIEmbeddings()
            self.llm = ChatOpenAI(
                model="gpt-4-turbo",
                temperature=0.1,
            )
            self._initialized = True
            # In-memory store for demo (production would use ChromaDB/Pinecone)
        except Exception as e:
            logger.warning(f"RAG Knowledge Base not initialized: {e}")
            self._initialized = False

    async def ingest_property(
        self,
        property_id: str,
        db: AsyncSession,
    ) -> IngestionResult:
        """Ingest a property into the knowledge base.

        Args:
            property_id: ID of the property to ingest
            db: Database session

        Returns:
            IngestionResult with status
        """
        try:
            # Fetch property
            query = select(Property).where(Property.id == property_id)
            result = await db.execute(query)
            prop = result.scalar_one_or_none()

            if not prop:
                return IngestionResult(
                    success=False,
                    chunks_created=0,
                    source_type=KnowledgeSourceType.PROPERTY,
                    source_id=property_id,
                    error="Property not found",
                )

            # Create content for embedding
            content = self._property_to_text(prop)
            chunk = KnowledgeChunk(
                id=str(uuid4()),
                source_type=KnowledgeSourceType.PROPERTY,
                source_id=property_id,
                content=content,
                metadata={
                    "address": prop.address,
                    "district": prop.district,
                    "property_type": (prop.property_type.value if prop.property_type else None),
                    "land_area_sqm": (float(prop.land_area_sqm) if prop.land_area_sqm else None),
                },
            )

            # Generate embedding
            if self._initialized and self.embeddings:
                try:
                    embedding = await self._get_embedding(content)
                    chunk.embedding = embedding
                except Exception as e:
                    logger.warning(f"Failed to generate embedding: {e}")

            self._chunks[chunk.id] = chunk

            return IngestionResult(
                success=True,
                chunks_created=1,
                source_type=KnowledgeSourceType.PROPERTY,
                source_id=property_id,
            )

        except Exception as e:
            logger.error(f"Error ingesting property: {e}")
            return IngestionResult(
                success=False,
                chunks_created=0,
                source_type=KnowledgeSourceType.PROPERTY,
                source_id=property_id,
                error=str(e),
            )

    async def ingest_deal(
        self,
        deal_id: str,
        db: AsyncSession,
    ) -> IngestionResult:
        """Ingest a deal into the knowledge base.

        Args:
            deal_id: ID of the deal to ingest
            db: Database session

        Returns:
            IngestionResult with status
        """
        try:
            query = select(AgentDeal).where(AgentDeal.id == deal_id)
            result = await db.execute(query)
            deal = result.scalar_one_or_none()

            if not deal:
                return IngestionResult(
                    success=False,
                    chunks_created=0,
                    source_type=KnowledgeSourceType.DEAL,
                    source_id=deal_id,
                    error="Deal not found",
                )

            content = self._deal_to_text(deal)
            chunk = KnowledgeChunk(
                id=str(uuid4()),
                source_type=KnowledgeSourceType.DEAL,
                source_id=deal_id,
                content=content,
                metadata={
                    "title": deal.title,
                    "deal_type": deal.deal_type.value,
                    "asset_type": deal.asset_type.value,
                    "pipeline_stage": deal.pipeline_stage.value,
                    "estimated_value": (
                        float(deal.estimated_value_amount) if deal.estimated_value_amount else None
                    ),
                },
            )

            if self._initialized and self.embeddings:
                try:
                    embedding = await self._get_embedding(content)
                    chunk.embedding = embedding
                except Exception as e:
                    logger.warning(f"Failed to generate embedding: {e}")

            self._chunks[chunk.id] = chunk

            return IngestionResult(
                success=True,
                chunks_created=1,
                source_type=KnowledgeSourceType.DEAL,
                source_id=deal_id,
            )

        except Exception as e:
            logger.error(f"Error ingesting deal: {e}")
            return IngestionResult(
                success=False,
                chunks_created=0,
                source_type=KnowledgeSourceType.DEAL,
                source_id=deal_id,
                error=str(e),
            )

    async def ingest_document(
        self,
        document_id: str,
        content: str,
        metadata: dict[str, Any],
    ) -> IngestionResult:
        """Ingest a document into the knowledge base.

        Args:
            document_id: Unique ID for the document
            content: Document text content
            metadata: Document metadata

        Returns:
            IngestionResult with status
        """
        try:
            # Split into chunks if content is long
            chunks_created = 0
            chunk_size = 1000
            overlap = 100

            for i in range(0, len(content), chunk_size - overlap):
                chunk_content = content[i : i + chunk_size]
                chunk = KnowledgeChunk(
                    id=str(uuid4()),
                    source_type=KnowledgeSourceType.DOCUMENT,
                    source_id=document_id,
                    content=chunk_content,
                    metadata={
                        **metadata,
                        "chunk_index": i // (chunk_size - overlap),
                    },
                )

                if self._initialized and self.embeddings:
                    try:
                        embedding = await self._get_embedding(chunk_content)
                        chunk.embedding = embedding
                    except Exception as e:
                        logger.warning(f"Failed to generate embedding: {e}")

                self._chunks[chunk.id] = chunk
                chunks_created += 1

            return IngestionResult(
                success=True,
                chunks_created=chunks_created,
                source_type=KnowledgeSourceType.DOCUMENT,
                source_id=document_id,
            )

        except Exception as e:
            logger.error(f"Error ingesting document: {e}")
            return IngestionResult(
                success=False,
                chunks_created=0,
                source_type=KnowledgeSourceType.DOCUMENT,
                source_id=document_id,
                error=str(e),
            )

    async def search(
        self,
        query: str,
        mode: SearchMode = SearchMode.HYBRID,
        source_types: list[KnowledgeSourceType] | None = None,
        limit: int = 10,
        generate_answer: bool = True,
    ) -> KnowledgeSearchResponse:
        """Search the knowledge base.

        Args:
            query: Search query
            mode: Search mode (semantic, keyword, hybrid)
            source_types: Filter by source types
            limit: Maximum results to return
            generate_answer: Whether to generate an LLM answer

        Returns:
            KnowledgeSearchResponse with results
        """
        start_time = datetime.now()
        results: list[SearchResult] = []

        # Filter chunks by source type
        filtered_chunks = list(self._chunks.values())
        if source_types:
            filtered_chunks = [c for c in filtered_chunks if c.source_type in source_types]

        if mode in [SearchMode.SEMANTIC, SearchMode.HYBRID]:
            # Semantic search using embeddings
            if self._initialized and self.embeddings:
                try:
                    query_embedding = await self._get_embedding(query)
                    results = self._semantic_search(query_embedding, filtered_chunks, limit)
                except Exception as e:
                    logger.warning(f"Semantic search failed: {e}")
                    mode = SearchMode.KEYWORD

        if mode == SearchMode.KEYWORD or (mode == SearchMode.HYBRID and not results):
            # Keyword search fallback
            results = self._keyword_search(query, filtered_chunks, limit)

        # Generate answer using LLM
        generated_answer = None
        if generate_answer and results and self._initialized and self.llm:
            try:
                generated_answer = await self._generate_answer(query, results[:5])
            except Exception as e:
                logger.warning(f"Answer generation failed: {e}")

        search_time = (datetime.now() - start_time).total_seconds() * 1000

        return KnowledgeSearchResponse(
            query=query,
            results=results[:limit],
            total_chunks_searched=len(filtered_chunks),
            search_time_ms=search_time,
            generated_answer=generated_answer,
        )

    async def _get_embedding(self, text: str) -> list[float]:
        """Get embedding for text with caching."""
        cache_key = hashlib.md5(text.encode()).hexdigest()
        if cache_key in self._embeddings_cache:
            return self._embeddings_cache[cache_key]

        if self.embeddings is None:
            return []
        embedding: list[float] = self.embeddings.embed_query(text)
        self._embeddings_cache[cache_key] = embedding
        return embedding

    def _semantic_search(
        self,
        query_embedding: list[float],
        chunks: list[KnowledgeChunk],
        limit: int,
    ) -> list[SearchResult]:
        """Perform semantic search using cosine similarity."""
        import math

        scored_results = []
        for chunk in chunks:
            if chunk.embedding:
                # Cosine similarity
                dot_product = sum(
                    a * b for a, b in zip(query_embedding, chunk.embedding, strict=False)
                )
                norm_a = math.sqrt(sum(a * a for a in query_embedding))
                norm_b = math.sqrt(sum(b * b for b in chunk.embedding))
                similarity = dot_product / (norm_a * norm_b) if norm_a and norm_b else 0

                scored_results.append(
                    SearchResult(
                        chunk_id=chunk.id,
                        source_type=chunk.source_type,
                        source_id=chunk.source_id,
                        content=chunk.content,
                        relevance_score=similarity,
                        metadata=chunk.metadata,
                    )
                )

        scored_results.sort(key=lambda x: x.relevance_score, reverse=True)
        return scored_results[:limit]

    def _keyword_search(
        self,
        query: str,
        chunks: list[KnowledgeChunk],
        limit: int,
    ) -> list[SearchResult]:
        """Perform keyword search using term frequency."""
        query_terms = query.lower().split()
        scored_results = []

        for chunk in chunks:
            content_lower = chunk.content.lower()
            # Simple term frequency scoring
            score = sum(1 for term in query_terms if term in content_lower)
            if score > 0:
                scored_results.append(
                    SearchResult(
                        chunk_id=chunk.id,
                        source_type=chunk.source_type,
                        source_id=chunk.source_id,
                        content=chunk.content,
                        relevance_score=score / len(query_terms),
                        metadata=chunk.metadata,
                    )
                )

        scored_results.sort(key=lambda x: x.relevance_score, reverse=True)
        return scored_results[:limit]

    async def _generate_answer(
        self,
        query: str,
        results: list[SearchResult],
    ) -> str:
        """Generate an answer using LLM and search results."""
        context = "\n\n".join(f"Source ({r.source_type.value}): {r.content}" for r in results)

        prompt = f"""Based on the following context, answer the user's question.
If the answer cannot be found in the context, say so.

Context:
{context}

Question: {query}

Answer:"""

        if self.llm is None:
            return "Unable to generate answer."
        response = self.llm.invoke(prompt)
        content = response.content
        if isinstance(content, str):
            return content or "Unable to generate answer."
        return "Unable to generate answer."

    def _property_to_text(self, prop: Property) -> str:
        """Convert property to searchable text."""
        parts = [
            f"Property at {prop.address}",
            f"District: {prop.district}" if prop.district else None,
            f"Type: {prop.property_type.value}" if prop.property_type else None,
            f"Land area: {prop.land_area_sqm} sqm" if prop.land_area_sqm else None,
            (f"GFA: {prop.gross_floor_area_sqm} sqm" if prop.gross_floor_area_sqm else None),
            f"Plot ratio: {prop.plot_ratio}" if prop.plot_ratio else None,
            f"Tenure: {prop.tenure_type.value}" if prop.tenure_type else None,
            f"Year built: {prop.year_built}" if prop.year_built else None,
            "Conservation property" if prop.is_conservation else None,
        ]
        return " | ".join(p for p in parts if p)

    def _deal_to_text(self, deal: AgentDeal) -> str:
        """Convert deal to searchable text."""
        parts = [
            f"Deal: {deal.title}",
            f"Type: {deal.deal_type.value}",
            f"Asset: {deal.asset_type.value}",
            f"Stage: {deal.pipeline_stage.value}",
            (
                f"Value: ${float(deal.estimated_value_amount):,.0f}"
                if deal.estimated_value_amount
                else None
            ),
            f"Description: {deal.description}" if deal.description else None,
            f"Lead source: {deal.lead_source}" if deal.lead_source else None,
        ]
        return " | ".join(p for p in parts if p)

    def get_stats(self) -> dict[str, Any]:
        """Get knowledge base statistics."""
        by_type = {}
        for chunk in self._chunks.values():
            source_type = chunk.source_type.value
            by_type[source_type] = by_type.get(source_type, 0) + 1

        return {
            "total_chunks": len(self._chunks),
            "chunks_by_type": by_type,
            "embeddings_cached": len(self._embeddings_cache),
            "initialized": self._initialized,
        }


# Singleton instance
rag_knowledge_base_service = RAGKnowledgeBaseService()
