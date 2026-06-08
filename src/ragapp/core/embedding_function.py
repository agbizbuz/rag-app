"""Embedding function factory."""

from __future__ import annotations


def create_embedding_function() -> object | None:
    """Return the configured embedding function, or ``None`` for ChromaDB default.

    - If ``OPENAI_API_KEY`` is set → returns an OpenAI embedding function.
    - Otherwise → ``None`` (ChromaDB falls back to SentenceTransformer locally).
    """
    import os

    if not os.environ.get("OPENAI_API_KEY"):
        return None

    from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

    return OpenAIEmbeddingFunction(
        api_key=os.environ["OPENAI_API_KEY"],
        model_name="text-embedding-3-small",
    )
