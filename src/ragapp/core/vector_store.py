"""ChromaDB persistence layer — vector store operations only."""

from __future__ import annotations

from typing import Callable, Optional

import chromadb
from ragapp.config_provider import ConfigProvider, get_config


class _MockConfigProvider:
    """Minimal mock for test compatibility.

    Provides a fallback when actual ConfigProvider is unavailable.
    """

    @property
    def db_path(self) -> str:
        return "./chroma_db"

    @property
    def collection_name(self) -> str:
        return "my_rag_collection"

    @property
    def n_results(self) -> int:
        return 3


# Type alias for embedding function creator callable
EmbeddingCreator = Callable[[], Optional[object]]


class VectorStore:
    """Persistent ChromaDB client and collection wrapper.

    All dependencies are injected to avoid cross-directory imports.
    """

    def __init__(
        self,
        db_path: str | None = None,
        collection_name: str | None = None,
        embedding_creator: Optional[EmbeddingCreator] = None,
        embedding_manager: Optional[EmbeddingManager] = None,
        config_provider=None,  # noqa: ANN001
    ) -> None:
        cfg = config_provider or _MockConfigProvider()
        self._config = cfg
        self.db_path = db_path or cfg.db_path
        self.collection_name = collection_name or cfg.collection_name

        self._client = chromadb.PersistentClient(path=self.db_path)
        self._collection: chromadb.Collection | None = None

        self._embedding_creator = embedding_creator

        from .embedding_manager import EmbeddingManager

        self._embedding_manager = embedding_manager or EmbeddingManager(config_provider=cfg)

    @property
    def collection(self) -> chromadb.Collection:
        if self._collection is None:
            ef = self._get_embedding_function()
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=ef,  # type: ignore[arg-type]
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def _get_embedding_function(self) -> Optional[object]:
        """Get or create the embedding function via injected manager or creator."""
        if self._embedding_creator is not None:
            return self._embedding_creator()

        return self._embedding_manager.get_embedding_function()

    def _ensure_collection(self) -> None:
        """Re-fetch collection if it may have been deleted externally."""

        _ = self.collection  # triggers lazy init via property accessor

    def add_documents(self, chunks: list[dict]) -> int:
        """Add document chunks to the collection.

        Args:
            chunks: List of document chunk dicts with keys 'id', 'text', 'metadata'.

        Returns:
            Number of documents added.
        """
        self._ensure_collection()

        if not chunks:
            return 0

        ids = [chunk["id"] for chunk in chunks]
        documents = [chunk["text"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]

        self._collection.add(
            ids=ids,
            embeddings=None,  # Use server-side embedding if configured
            documents=documents,
            metadatas=metadatas,
        )

        return len(ids)

    def query(self, query_text: str, n_results: int | None = None) -> list[dict]:
        """Query the collection for relevant document chunks.

        Args:
            query_text: The query string to search for.
            n_results: Number of results to return. Defaults to config value.

        Returns:
            List of result dicts with keys 'id', 'text', 'metadata', 'distance'.
        """
        if n_results is None:
            n_results = self._config.n_results

        self._ensure_collection()

        results = self._collection.query(
            query_texts=[query_text],
            n_results=n_results,
            # include=["documents", "metadatas", "distances"],  # type: ignore
        )

        if not results["ids"]:
            return []

        all_results = []
        for i in range(len(results["ids"])):
            query_id = results["ids"][i]
            for j, doc_id in enumerate(query_id):
                all_results.append({
                    "id": doc_id,
                    "text": results["documents"][i][j],  # type: ignore[index]
                    # type: ignore[index]
                    "metadata": results["metadatas"][i][j] if results["metadatas"] else {},
                    # type: ignore[index]
                    "distance": results["distances"][i][j],
                })

        return all_results

    def get_collection_size(self) -> int:
        """Return the number of documents in the collection."""
        self._ensure_collection()
        return self._collection.count()  # type: ignore[no-any-return]

    def delete_collection(self) -> None:
        """Delete the current collection (destructive)."""
        self._client.delete_collection(self.collection_name)
        self._collection = None  # invalidate lazy cache
