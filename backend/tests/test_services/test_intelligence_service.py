"""Tests for intelligence_service with mocked LLM dependencies.

Tests focus on IntelligenceService methods with mocked langchain components.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

# Skip entire module if langchain is not installed
langchain = pytest.importorskip("langchain")
langchain_openai = pytest.importorskip("langchain_openai")


class TestIntelligenceServiceInit:
    """Test IntelligenceService initialization."""

    def test_init_handles_missing_api_key_gracefully(self):
        """Test IntelligenceService handles missing API key without crashing."""
        with patch("app.services.intelligence.get_rag_engine") as mock_rag:
            mock_rag.side_effect = Exception("Missing API key")

            from app.services.intelligence import IntelligenceService

            service = IntelligenceService()

            assert service.rag_engine is None
            assert service.vector_store is None
            assert service.llm is None

    def test_init_with_successful_rag_engine(self):
        """Test IntelligenceService initializes with working RAG engine."""
        mock_vector_store = MagicMock()
        mock_rag_engine = MagicMock()
        mock_rag_engine.get_vector_store.return_value = mock_vector_store

        with (
            patch("app.services.intelligence.get_rag_engine") as mock_get_rag,
            patch("app.services.intelligence.ChatOpenAI") as mock_chat,
        ):
            mock_get_rag.return_value = mock_rag_engine
            mock_chat.return_value = MagicMock()

            from app.services.intelligence import IntelligenceService

            service = IntelligenceService()

            assert service.rag_engine is not None
            assert service.vector_store == mock_vector_store
            assert service.llm is not None


class TestIngestText:
    """Test IntelligenceService.ingest_text."""

    def test_ingest_text_returns_false_when_no_vector_store(self):
        """Test ingest_text returns False when vector store not configured."""
        with patch("app.services.intelligence.get_rag_engine") as mock_rag:
            mock_rag.side_effect = Exception("Not configured")

            from app.services.intelligence import IntelligenceService

            service = IntelligenceService()

            result = service.ingest_text("Some text content", "test_source")

            assert result is False

    def test_ingest_text_splits_and_adds_documents(self):
        """Test ingest_text splits text and adds to vector store."""
        mock_vector_store = MagicMock()
        mock_rag_engine = MagicMock()
        mock_rag_engine.get_vector_store.return_value = mock_vector_store

        with (
            patch("app.services.intelligence.get_rag_engine") as mock_get_rag,
            patch("app.services.intelligence.ChatOpenAI"),
        ):
            mock_get_rag.return_value = mock_rag_engine

            from app.services.intelligence import IntelligenceService

            service = IntelligenceService()

            result = service.ingest_text(
                "This is a test document with some content.", "test_source"
            )

            assert result is True
            mock_vector_store.add_documents.assert_called_once()

            # Verify documents have correct metadata
            call_args = mock_vector_store.add_documents.call_args
            docs = call_args[0][0]
            assert len(docs) > 0
            assert all(d.metadata["source"] == "test_source" for d in docs)

    def test_ingest_text_handles_long_text(self):
        """Test ingest_text splits long text into chunks."""
        mock_vector_store = MagicMock()
        mock_rag_engine = MagicMock()
        mock_rag_engine.get_vector_store.return_value = mock_vector_store

        with (
            patch("app.services.intelligence.get_rag_engine") as mock_get_rag,
            patch("app.services.intelligence.ChatOpenAI"),
        ):
            mock_get_rag.return_value = mock_rag_engine

            from app.services.intelligence import IntelligenceService

            service = IntelligenceService()

            # Create text longer than chunk_size (1000)
            long_text = "This is a paragraph. " * 200  # ~4200 chars

            result = service.ingest_text(long_text, "long_document")

            assert result is True
            call_args = mock_vector_store.add_documents.call_args
            docs = call_args[0][0]
            # Should have multiple chunks
            assert len(docs) > 1


class TestQueryAgent:
    """Test IntelligenceService.query_agent."""

    def test_query_agent_returns_message_when_not_configured(self):
        """Test query_agent returns helpful message when not configured."""
        with patch("app.services.intelligence.get_rag_engine") as mock_rag:
            mock_rag.side_effect = Exception("Not configured")

            from app.services.intelligence import IntelligenceService

            service = IntelligenceService()

            result = service.query_agent("What is the building height limit?")

            assert "not configured" in result.lower()
            assert "OPENAI_API_KEY" in result

    def test_query_agent_returns_llm_response(self):
        """Test query_agent returns LLM response on success."""
        mock_vector_store = MagicMock()
        mock_rag_engine = MagicMock()
        mock_rag_engine.get_vector_store.return_value = mock_vector_store
        mock_llm = MagicMock()

        with (
            patch("app.services.intelligence.get_rag_engine") as mock_get_rag,
            patch("app.services.intelligence.ChatOpenAI") as mock_chat,
            patch("app.services.intelligence.RetrievalQA") as mock_retrieval_qa,
        ):
            mock_get_rag.return_value = mock_rag_engine
            mock_chat.return_value = mock_llm

            mock_qa_chain = MagicMock()
            mock_qa_chain.invoke.return_value = {
                "result": "The building height limit is 50 meters."
            }
            mock_retrieval_qa.from_chain_type.return_value = mock_qa_chain

            from app.services.intelligence import IntelligenceService

            service = IntelligenceService()

            result = service.query_agent("What is the building height limit?")

            assert result == "The building height limit is 50 meters."
            mock_qa_chain.invoke.assert_called_once_with(
                "What is the building height limit?"
            )

    def test_query_agent_handles_llm_error(self):
        """Test query_agent returns error message on LLM failure."""
        mock_vector_store = MagicMock()
        mock_rag_engine = MagicMock()
        mock_rag_engine.get_vector_store.return_value = mock_vector_store
        mock_llm = MagicMock()

        with (
            patch("app.services.intelligence.get_rag_engine") as mock_get_rag,
            patch("app.services.intelligence.ChatOpenAI") as mock_chat,
            patch("app.services.intelligence.RetrievalQA") as mock_retrieval_qa,
        ):
            mock_get_rag.return_value = mock_rag_engine
            mock_chat.return_value = mock_llm

            mock_qa_chain = MagicMock()
            mock_qa_chain.invoke.side_effect = Exception("LLM API error")
            mock_retrieval_qa.from_chain_type.return_value = mock_qa_chain

            from app.services.intelligence import IntelligenceService

            service = IntelligenceService()

            result = service.query_agent("What is the building height limit?")

            assert "Unable to process query" in result

    def test_query_agent_uses_correct_retriever_settings(self):
        """Test query_agent configures retriever with k=3."""
        mock_vector_store = MagicMock()
        mock_retriever = MagicMock()
        mock_vector_store.as_retriever.return_value = mock_retriever
        mock_rag_engine = MagicMock()
        mock_rag_engine.get_vector_store.return_value = mock_vector_store
        mock_llm = MagicMock()

        with (
            patch("app.services.intelligence.get_rag_engine") as mock_get_rag,
            patch("app.services.intelligence.ChatOpenAI") as mock_chat,
            patch("app.services.intelligence.RetrievalQA") as mock_retrieval_qa,
        ):
            mock_get_rag.return_value = mock_rag_engine
            mock_chat.return_value = mock_llm

            mock_qa_chain = MagicMock()
            mock_qa_chain.invoke.return_value = {"result": "Answer"}
            mock_retrieval_qa.from_chain_type.return_value = mock_qa_chain

            from app.services.intelligence import IntelligenceService

            service = IntelligenceService()
            service.query_agent("Test query")

            # Verify retriever was created with k=3
            mock_vector_store.as_retriever.assert_called_once_with(
                search_kwargs={"k": 3}
            )

            # Verify QA chain was created with correct settings
            mock_retrieval_qa.from_chain_type.assert_called_once()
            call_kwargs = mock_retrieval_qa.from_chain_type.call_args[1]
            assert call_kwargs["llm"] == mock_llm
            assert call_kwargs["chain_type"] == "stuff"
            assert call_kwargs["retriever"] == mock_retriever
