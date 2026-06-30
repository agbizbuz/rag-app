"""BM25 keyword search over document chunks."""

from __future__ import annotations

import re


def _tokenize(text: str) -> list[str]:
    """Simple whitespace + punctuation tokenizer with lowercasing."""
    return re.findall(r"[a-z0-9]+", text.lower())


class KeywordSearcher:
    """BM25 keyword search over a corpus of document chunks.

    Builds an in-memory BM25 index at construction time.
    Results are returned in the same ``{"id", "text", "metadata", "distance"}``
    dict format as ``VectorStore.query()`` for drop-in compatibility.
    """

    def __init__(self, documents: list[dict]) -> None:
        """Build BM25 index from document chunk dicts.

        Args:
            documents: List of dicts with keys ``id``, ``text``, ``metadata``.
        """
        from rank_bm25 import BM25Okapi

        self._documents = documents
        corpus = [_tokenize(doc["text"]) for doc in documents]
        self._bm25 = BM25Okapi(corpus) if corpus else None

    def search(self, query: str, n_results: int = 5) -> list[dict]:
        """Return top-n keyword matches with BM25 scores.

        Args:
            query: The search query string.
            n_results: Maximum number of results to return.

        Returns:
            List of result dicts sorted by BM25 score (highest first).
            Each dict has keys ``id``, ``text``, ``metadata``, ``distance``
            where ``distance`` is ``1 / (1 + bm25_score)`` (lower = better match,
            matching the vector store convention).
        """
        if not self._documents or self._bm25 is None:
            return []

        tokenized_query = _tokenize(query)
        if not tokenized_query:
            return []

        scores = self._bm25.get_scores(tokenized_query)

        # Pair scores with document indices and sort descending
        scored_indices = sorted(
            enumerate(scores), key=lambda x: x[1], reverse=True
        )

        results: list[dict] = []
        for idx, score in scored_indices[:n_results]:
            if score <= 0:
                break  # No point returning zero-score documents
            doc = self._documents[idx]
            results.append({
                "id": doc["id"],
                "text": doc["text"],
                "metadata": doc.get("metadata", {}),
                # Convert BM25 score to a "distance" (lower = better) for
                # compatibility with vector store results
                "distance": 1.0 / (1.0 + score),
            })

        return results
