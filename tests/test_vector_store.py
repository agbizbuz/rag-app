"""Tests for src/ragapp/core/vector_store.py."""

import uuid
from unittest.mock import MagicMock, patch


class TestVectorStore:
    """Tests for ragapp.core.vector_store.VectorStore."""

    def _make_vs(self):
        """Create a VectorStore with mocked ChromaDB internals."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        type(mock_client).get_or_create_collection = MagicMock(return_value=mock_collection)
        mock_cfg = MagicMock()
        mock_cfg.db_path = "./chroma_db"
        mock_cfg.collection_name = "test_collection"
        mock_cfg.n_results = 3

        from ragapp.core.vector_store import VectorStore

        vs = VectorStore(config_provider=mock_cfg)
        # Replace the lazy-initialized client with our mock
        vs._client = mock_client
        vs._collection = mock_collection
        return vs, mock_client, mock_collection

    def test_init_default_config(self):
        from ragapp.core.vector_store import VectorStore

        with patch("ragapp.core.vector_store.chromadb.PersistentClient") as MockClient:
            MockClient.return_value = MagicMock()
            vs = VectorStore()
            assert isinstance(vs, VectorStore)

    def test_init_with_custom_config(self):
        from ragapp.core.vector_store import VectorStore

        with patch("ragapp.core.vector_store.chromadb.PersistentClient"):
            cfg = MagicMock()
            cfg.db_path = "/custom/path"
            cfg.collection_name = "custom_name"

            vs = VectorStore(config_provider=cfg)
            assert vs._client is not None

    def test_add_documents(self):
        vs, mock_client, mock_collection = self._make_vs()
        chunks = [
            {"id": str(uuid.uuid4()), "text": "Hello world", "metadata": {"source": "test.txt"}},
            {"id": str(uuid.uuid4()), "text": "Second doc", "metadata": {"source": "test2.txt"}},
        ]
        result = vs.add_documents(chunks)
        assert result == 2

        # Verify chromaDB was called with correct arguments
        add_call = mock_collection.add.call_args
        assert len(add_call[1]["ids"]) == 2
        assert add_call[1]["documents"][0] == "Hello world"

    def test_add_documents_empty(self):
        vs, _, _ = self._make_vs()
        result = vs.add_documents([])
        assert result == 0

    def test_query_returns_results(self):
        vs, mock_client, mock_collection = self._make_vs()
        mock_collection.query.return_value = {
            "ids": [["doc1", "doc2"]],
            "distances": [[0.1, 0.3]],
            "metadatas": [[{"source": "a.txt"}, {"source": "b.txt"}]],
            "documents": [["Text A", "Text B"]],
        }

        results = vs.query("test query", n_results=2)
        assert len(results) == 2
        assert results[0]["text"] == "Text A"
        assert results[0]["distance"] == 0.1
        assert results[0]["metadata"]["source"] == "a.txt"

    def test_query_with_default_n_results(self):
        vs, mock_client, mock_collection = self._make_vs()
        mock_collection.query.return_value = {
            "ids": [["doc1"]],
            "distances": [[0.2]],
            "metadatas": [[{"source": "x.txt"}]],
            "documents": [["Some text"]],
        }

        vs.query("test")  # default n_results=3
        mock_collection.query.assert_called_once()
        call_kwargs = mock_collection.query.call_args[1]
        assert call_kwargs["query_texts"] == ["test"]
        assert call_kwargs["n_results"] == 3

    def test_get_collection_size(self):
        vs, _, mock_collection = self._make_vs()
        mock_collection.count.return_value = 42

        size = vs.get_collection_size()
        assert size == 42
        mock_collection.count.assert_called_once()

    def test_delete_collection(self):
        vs, _, mock_collection = self._make_vs()
        vs.delete_collection()
        vs._client.delete_collection.assert_called_once_with("test_collection")
        assert vs._collection is None  # invalidated

    def test_get_all_documents(self):
        vs, _, mock_collection = self._make_vs()
        mock_collection.get.return_value = {
            "ids": ["doc1", "doc2"],
            "documents": ["doc1 text", "doc2 text"],
            "metadatas": [{"src": "a"}, {"src": "b"}],
        }

        docs = vs.get_all_documents()
        assert len(docs) == 2
        assert docs[0]["id"] == "doc1"
        assert docs[0]["text"] == "doc1 text"
        assert docs[0]["metadata"]["src"] == "a"
        mock_collection.get.assert_called_once_with(include=["documents", "metadatas"])

    def test_get_all_documents_empty(self):
        vs, _, mock_collection = self._make_vs()
        mock_collection.get.return_value = {
            "ids": [],
            "documents": [],
            "metadatas": [],
        }

        docs = vs.get_all_documents()
        assert docs == []

    def test_collection_property_lazy_init(self):
        """Test that collection property triggers lazy init."""
        with patch("ragapp.core.vector_store.chromadb.PersistentClient") as MockClient:
            mock_inst = MagicMock()
            MockClient.return_value = mock_inst

            from ragapp.core.vector_store import VectorStore

            vs = VectorStore()
            _ = vs.collection  # triggers lazy init
            mock_inst.get_or_create_collection.assert_called_once()

    def test_ensure_collection_invalidates_on_delete(self):
        """After delete_collection, _collection is None and re-initialises."""
        vs, _, mock_collection = self._make_vs()
        vs.delete_collection()
        assert vs._collection is None

        # Accessing collection triggers re-init
        _ = vs.collection  # Should work without error (mock returns itself)


class TestMockConfigProvider:
    """Tests for the internal _MockConfigProvider."""

    def test_db_path(self):
        from ragapp.core.vector_store import _MockConfigProvider

        mock_cfg = _MockConfigProvider()
        assert mock_cfg.db_path == "./chroma_db"

    def test_collection_name(self):
        from ragapp.core.vector_store import _MockConfigProvider

        mock_cfg = _MockConfigProvider()
        assert mock_cfg.collection_name == "my_rag_collection"


class TestVectorStoreEmbeddingFunction:
    """Tests for VectorStore embedding function configuration."""

    def test_no_openai_key_returns_none(self, monkeypatch):
        """Without OPENAI_API_KEY, create_embedding_function returns None."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with patch("ragapp.core.vector_store.chromadb.PersistentClient"):
            from ragapp.core.embedding_function import create_embedding_function

            assert create_embedding_function() is None

    def test_embedding_creator_injected(self):
        """Test that an injected embedding creator is used."""
        with patch("ragapp.core.vector_store.chromadb.PersistentClient"):
            from ragapp.core.vector_store import VectorStore

            mock_ef = MagicMock()
            mock_cfg = MagicMock()
            mock_cfg.db_path = "./chroma_db"
            mock_cfg.collection_name = "test"

            def creator():
                return mock_ef

            vs = VectorStore(config_provider=mock_cfg, embedding_creator=creator)
            assert vs._embedding_creator is not None
