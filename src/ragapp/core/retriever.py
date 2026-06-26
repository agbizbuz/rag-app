"""Retriever component for RAG applications."""

from __future__ import annotations

from typing import Optional

from ragapp.config_provider import get_config
from ragapp.core.vector_store import VectorStore


class RAGRetriever:
    """Encapsulates retrieval functionalities for RAG applications.

    Separates the query/search mechanics from storage, session, and UI.
    """

    def __init__(self, vector_store: VectorStore, config_provider=None) -> None:
        self.vector_store = vector_store
        self._config = config_provider or get_config()

    def retrieve(self, query: str, n_results: Optional[int] = None) -> list[dict]:
        """Query the vector store for relevant document chunks.

        Args:
            query: The query text to search for.
            n_results: Number of results to return. Defaults to config value.

        Returns:
            List of result dicts with keys 'id', 'text', 'metadata', 'distance'.
        """
        n_res = n_results if n_results is not None else self._config.n_results
        return self.vector_store.query(query, n_results=n_res)

    def format_context(self, results: list[dict]) -> str:
        """Format a list of document chunks into a single context string."""
        return "\n\n---\n\n".join(r["text"] for r in results)

    def retrieve_formatted_context(self, query: str, n_results: Optional[int] = None) -> str:
        """Retrieve relevant document chunks and format them as a single context string."""
        results = self.retrieve(query, n_results=n_results)
        return self.format_context(results)
