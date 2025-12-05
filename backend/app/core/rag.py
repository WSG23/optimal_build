import os
from functools import lru_cache

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
import chromadb


class RagEngine:
    """Core RAG Engine utilizing ChromaDB and OpenAI Embeddings."""

    def __init__(self):
        self._persist_directory = os.path.join(os.getcwd(), ".storage", "chroma_db")
        self._collection_name = "optimal_build_knowledge"

        # Ensure storage directory exists
        os.makedirs(self._persist_directory, exist_ok=True)

        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

        # Initialize Chroma Client
        self.chroma_client = chromadb.PersistentClient(path=self._persist_directory)

    def get_vector_store(self) -> Chroma:
        """Get the LangChain Chroma vector store instance."""
        return Chroma(
            client=self.chroma_client,
            collection_name=self._collection_name,
            embedding_function=self.embeddings,
        )


@lru_cache()
def get_rag_engine() -> RagEngine:
    """Singleton accessor for the RAG Engine."""
    return RagEngine()
