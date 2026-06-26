"""Embedding manager component for RAG applications."""

from __future__ import annotations

import os
from typing import Optional

from ragapp.config_provider import get_config


class EmbeddingManager:
    """Manages embedding function configuration and instantiation.

    Encapsulates decision logic for selecting and creating embedding functions,
    separating these concerns from storage/persistence modules.
    """

    def __init__(self, config_provider=None) -> None:
        self._config = config_provider or get_config()

    def get_embedding_function(self) -> Optional[object]:
        """Return the configured embedding function, or None for ChromaDB default.

        - If `OPENAI_API_KEY` is set → returns an OpenAI embedding function.
        - Otherwise → None (ChromaDB falls back to SentenceTransformer locally).
        """
        if not os.environ.get("OPENAI_API_KEY"):
            return None

        from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

        return OpenAIEmbeddingFunction(
            api_key=os.environ["OPENAI_API_KEY"],
            model_name=self._config.embedding_model,
        )

    @property
    def is_openai(self) -> bool:
        """Return True if using OpenAI embedding function."""
        return bool(os.environ.get("OPENAI_API_KEY"))
