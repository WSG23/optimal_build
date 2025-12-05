import logging

from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from app.core.rag import get_rag_engine

logger = logging.getLogger(__name__)


class IntelligenceService:
    """Service for Advanced Intelligence operations (RAG)."""

    def __init__(self):
        try:
            self.rag_engine = get_rag_engine()
            self.vector_store = self.rag_engine.get_vector_store()
            self.llm = ChatOpenAI(model_name="gpt-4-turbo", temperature=0)
        except Exception:
            logger.warning("RAG Engine not initialized (missing API key?)")
            self.rag_engine = None
            self.vector_store = None
            self.llm = None

    def ingest_text(self, text: str, source: str) -> bool:
        """Ingest text into the vector store."""
        if not self.vector_store:
            return False

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        texts = text_splitter.split_text(text)

        docs = [Document(page_content=t, metadata={"source": source}) for t in texts]

        self.vector_store.add_documents(docs)
        return True

    def query_agent(self, query: str) -> str:
        """Query the knowledge base using an LLM."""
        if not self.vector_store or not self.llm:
            return "Advanced Intelligence is not configured (missing OPENAI_API_KEY)."

        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever(search_kwargs={"k": 3}),
        )

        try:
            response = qa_chain.invoke(query)
            return response["result"]
        except Exception as e:
            logger.error(f"RAG Query failed: {e}")
            return "Unable to process query at this time."


# Singleton instance
intelligence_service = IntelligenceService()
