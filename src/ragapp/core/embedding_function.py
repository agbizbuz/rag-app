"""Embedding function factory."""

from __future__ import annotations


def create_embedding_function() -> object | None:
    """Return the configured embedding function, or ``None`` for ChromaDB default.

    - If ``OPENAI_API_KEY`` is set → returns an OpenAI embedding function.
    - Otherwise → ``None`` (ChromaDB falls back to SentenceTransformer locally).
    """
    from ragapp.core.embedding_manager import EmbeddingManager

    return EmbeddingManager().get_embedding_function()
