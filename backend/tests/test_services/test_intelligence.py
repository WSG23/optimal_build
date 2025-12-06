import pytest

langchain = pytest.importorskip("langchain")

from unittest.mock import MagicMock, patch
from app.services.intelligence import IntelligenceService


@pytest.fixture
def mock_rag_engine():
    with patch("app.services.intelligence.get_rag_engine") as mock:
        engine_mock = MagicMock()
        vector_store_mock = MagicMock()
        engine_mock.get_vector_store.return_value = vector_store_mock
        mock.return_value = engine_mock
        yield mock, vector_store_mock


@pytest.fixture
def mock_openai():
    with patch("app.services.intelligence.ChatOpenAI") as mock:
        yield mock


@pytest.fixture
def intelligence_service(mock_rag_engine, mock_openai):
    # Initialize service with mocks injected via patch
    return IntelligenceService()


def test_initialization_failure():
    """Test safe handling when RAG engine fails to load."""
    with patch(
        "app.services.intelligence.get_rag_engine", side_effect=Exception("DB Error")
    ):
        service = IntelligenceService()
        assert service.rag_engine is None
        assert (
            service.query_agent("test")
            == "Advanced Intelligence is not configured (missing OPENAI_API_KEY)."
        )


def test_ingest_text(intelligence_service, mock_rag_engine):
    _, vector_store = mock_rag_engine

    success = intelligence_service.ingest_text(
        "This is some sample knowledge.", "test_source"
    )

    assert success is True
    vector_store.add_documents.assert_called_once()
    docs = vector_store.add_documents.call_args[0][0]
    assert len(docs) > 0
    assert docs[0].page_content == "This is some sample knowledge."
    assert docs[0].metadata["source"] == "test_source"


def test_query_agent(intelligence_service, mock_rag_engine):
    service = intelligence_service
    _, vector_store = mock_rag_engine

    # Mock the chain invocation
    with patch("app.services.intelligence.RetrievalQA") as mock_chain_cls:
        chain_instance = MagicMock()
        chain_instance.invoke.return_value = {"result": "The answer is 42."}
        mock_chain_cls.from_chain_type.return_value = chain_instance

        response = service.query_agent("What is the answer?")

        assert response == "The answer is 42."
        vector_store.as_retriever.assert_called()
