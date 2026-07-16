"""ChromaDB persistence layer — vector store operations only."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Optional

import chromadb
from collections import defaultdict
from config_provider import get_config

if TYPE_CHECKING:
    from .embedding_manager import EmbeddingManager
    from config_provider import ConfigProvider


# Type alias for embedding function creator callable
EmbeddingCreator = Callable[[], object | None]


class VectorStore:
    """Persistent ChromaDB client and collection wrapper.

    All dependencies are injected to avoid cross-directory imports.
    """

    def __init__(
        self,
        db_path: str | None = None,
        collection_name: str | None = None,
        embedding_creator: EmbeddingCreator | None = None,
        embedding_manager: EmbeddingManager | None = None,
        config_provider: ConfigProvider | None = None,
    ) -> None:
        cfg = config_provider or get_config()
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

        self.collection.add(
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

        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
        )

        if not results["ids"]:
            return []

        all_results = []
        for i, query_id in enumerate(results["ids"]):
            for j, doc_id in enumerate(query_id):
                all_results.append(
                    {
                        "id": doc_id,
                        "text": results["documents"][i][j],  # type: ignore[index]
                        # type: ignore[index]
                        "metadata": results["metadatas"][i][j] if results["metadatas"] else {},
                        # type: ignore[index]
                        "distance": results["distances"][i][j],
                    }
                )

        return all_results

    def get_collection_size(self) -> int:
        """Return the number of documents in the collection."""
        return self.collection.count()  # type: ignore[no-any-return]

    def get_all_documents(self) -> list[dict]:
        """Return all documents in the collection (for keyword search indexing).

        Returns:
            List of dicts with keys 'id', 'text', 'metadata'.
        """
        result = self.collection.get(include=["documents", "metadatas"])  # type: ignore[arg-type]

        if not result["ids"]:
            return []

        return [
            {
                "id": doc_id,
                "text": result["documents"][i] if result["documents"] else "",  # type: ignore[index]
                "metadata": result["metadatas"][i] if result["metadatas"] else {},  # type: ignore[index]
            }
            for i, doc_id in enumerate(result["ids"])
        ]

    def get_all_files(self) -> list[dict]:
        """Return all indexed files grouped by source.

        Returns:
            List of dicts with keys 'source', 'type', 'chunk_count',
            'page_range' (str), 'preview'.
        """
        result = self.collection.get(include=["documents", "metadatas"])
        if not result["ids"]:
            return []

        # Group documents by source filename
        groups: dict[str, list[dict]] = defaultdict(list)
        for i, doc_id in enumerate(result["ids"]):
            meta = result["metadatas"][i] if result["metadatas"] else {}  # type: ignore[index]
            docs_list = result["documents"]
            text = docs_list[i] if docs_list else ""  # type: ignore[index]
            source = meta.get("source", "unknown")
            groups[source].append({"meta": meta, "text": text, "id": doc_id})

        def _get_int_key(m: dict, k: str) -> int | None:
            v = m.get(k)
            if isinstance(v, int):
                return v
            try:
                return int(v)
            except (ValueError, TypeError):
                return None

        files: list[dict] = []
        for source, chunks in groups.items():
            chunk_count = len(chunks)
            type_labels: set[str] = set()
            page_nums: list[int] = []
            txt_chunks: list[int] = []
            docx_paras: list[int] = []
            for c in chunks:
                meta = c["meta"]

                if (page := _get_int_key(meta, "page")) is not None:
                    type_labels.add("PDF")
                    page_nums.append(page)
                elif _get_int_key(meta, "row") is not None:
                    type_labels.add("CSV")
                elif (para := _get_int_key(meta, "paragraph")) is not None:
                    type_labels.add("DOCX")
                    docx_paras.append(para)
                elif (chunk := _get_int_key(meta, "chunk")) is not None:
                    type_labels.add("TXT")
                    txt_chunks.append(chunk)

            # Single dominant type label
            if len(type_labels) == 1:
                type_label = next(iter(type_labels))
            else:
                type_label = "Mixed"

            # Page range
            if page_nums:
                page_range = f"{min(page_nums)}-{max(page_nums)}"
            elif txt_chunks:
                page_range = f"Chunk {min(txt_chunks)}-{max(txt_chunks)}"
            elif docx_paras:
                page_range = f"Para {min(docx_paras)}-{max(docx_paras)}"
            else:
                page_range = "-"

            # Preview from first chunk of this file
            preview = (chunks[0]["text"] or "").strip()[:80]

            files.append(
                {
                    "source": source,
                    "type": type_label,
                    "chunk_count": chunk_count,
                    "page_range": page_range,
                    "preview": preview,
                }
            )

        return files

    def delete_collection(self) -> None:
        """Delete the current collection (destructive)."""
        self._client.delete_collection(self.collection_name)
        self._collection = None  # invalidate lazy cache
