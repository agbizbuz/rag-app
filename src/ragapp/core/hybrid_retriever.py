"""Hybrid retriever combining semantic and keyword search with RRF."""

from __future__ import annotations

from typing import Optional

from ragapp.core.keyword_search import KeywordSearcher
from ragapp.core.retriever import RAGRetriever


class HybridRetriever(RAGRetriever):
    """Combines vector similarity and BM25 keyword search via Reciprocal Rank Fusion (RRF)."""

    def __init__(self, vector_store, config_provider=None, rrf_k: int = 60) -> None:
        super().__init__(vector_store, config_provider)
        self._rrf_k = rrf_k

    def retrieve(self, query: str, n_results: Optional[int] = None) -> list[dict]:
        """Retrieve relevant document chunks based on the configured mode.

        Args:
            query: The query string to search for.
            n_results: Number of results to return.

        Returns:
            List of result dicts sorted by relevance.
        """
        n_res = n_results if n_results is not None else self._config.n_results

        # Safely fetch mode from config, defaulting to hybrid if not set
        mode = getattr(self._config, "retrieval_mode", "hybrid")

        if mode == "semantic":
            return super().retrieve(query, n_results=n_res)

        # For keyword or hybrid, we need the database documents
        all_docs = self.vector_store.get_all_documents()
        if not all_docs:
            return []

        searcher = KeywordSearcher(all_docs)

        if mode == "keyword":
            return searcher.search(query, n_results=n_res)

        # Hybrid mode: get candidates from both, fuse them, and take top n_res
        # Retrieve slightly more candidates from each to ensure overlap and better reranking
        candidate_count = max(n_res * 2, 10)
        
        semantic_results = super().retrieve(query, n_results=candidate_count)
        keyword_results = searcher.search(query, n_results=candidate_count)

        fused = self._reciprocal_rank_fusion(
            semantic_results, keyword_results, k=self._rrf_k
        )
        return fused[:n_res]

    @staticmethod
    def _reciprocal_rank_fusion(
        semantic_results: list[dict],
        keyword_results: list[dict],
        k: int = 60,
    ) -> list[dict]:
        """Merge two ranked result lists using Reciprocal Rank Fusion (RRF)."""
        scores: dict[str, float] = {}
        docs_map: dict[str, dict] = {}

        # Rank starts at 1
        for rank, doc in enumerate(semantic_results, 1):
            doc_id = doc["id"]
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
            docs_map[doc_id] = doc

        for rank, doc in enumerate(keyword_results, 1):
            doc_id = doc["id"]
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
            if doc_id not in docs_map:
                docs_map[doc_id] = doc

        # Sort by score descending
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

        results = []
        for doc_id in sorted_ids:
            doc = docs_map[doc_id]
            results.append({
                "id": doc_id,
                "text": doc["text"],
                "metadata": doc.get("metadata", {}),
                "distance": 1.0 / (1.0 + scores[doc_id]),
            })

        return results
