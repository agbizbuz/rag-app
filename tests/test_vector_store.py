"""Tests for src/ragapp/core/vector_store.py."""

import uuid
from unittest.mock import MagicMock, patch


class TestVectorStore:
    """Tests for core.vector_store.VectorStore."""

    def _make_vs(self):
        """Create a VectorStore with mocked ChromaDB internals."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        type(mock_client).get_or_create_collection = MagicMock(return_value=mock_collection)
        mock_cfg = MagicMock()
        mock_cfg.db_path = "./chroma_db"
        mock_cfg.collection_name = "test_collection"
        mock_cfg.n_results = 3

        from core.vector_store import VectorStore
        from config_provider import ConfigProvider
        from unittest.mock import MagicMock

        vs = VectorStore(config_provider=mock_cfg)
        # Replace the lazy-initialized client with our mock
        vs._client = mock_client
        vs._collection = mock_collection
        return vs, mock_client, mock_collection

    def test_init_default_config(self):
        from core.vector_store import VectorStore
        from config_provider import ConfigProvider
        from unittest.mock import MagicMock

        with patch("core.vector_store.chromadb.PersistentClient") as MockClient:
            MockClient.return_value = MagicMock()
            vs = VectorStore(ConfigProvider(MagicMock()))
            assert isinstance(vs, VectorStore)

    def test_init_with_custom_config(self):
        from core.vector_store import VectorStore
        from config_provider import ConfigProvider
        from unittest.mock import MagicMock

        with patch("core.vector_store.chromadb.PersistentClient"):
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

    def test_get_all_files_groups_by_source(self):
        vs, _, mock_collection = self._make_vs()
        mock_collection.get.return_value = {
            "ids": ["doc1", "doc2", "doc3"],
            "documents": ["text1", "text2", "text3"],
            "metadatas": [
                {"source": "report.pdf", "page": 1},
                {"source": "report.pdf", "page": 2},
                {"source": "other.txt", "chunk": 0},
            ],
        }
        files = vs.get_all_files()
        assert len(files) == 2
        sources = {f["source"] for f in files}
        assert "report.pdf" in sources
        assert "other.txt" in sources
        # report.pdf has 2 chunks
        report = [f for f in files if f["source"] == "report.pdf"][0]
        assert report["chunk_count"] == 2
        assert report["page_range"] == "1-2"

    def test_get_all_files_empty(self):
        vs, _, mock_collection = self._make_vs()
        mock_collection.get.return_value = {
            "ids": [],
            "documents": [],
            "metadatas": [],
        }
        files = vs.get_all_files()
        assert files == []

    def test_get_all_files_type_detection(self):
        vs, _, mock_collection = self._make_vs()
        mock_collection.get.return_value = {
            "ids": ["d1", "d2", "d3", "d4"],
            "documents": ["a", "b", "c", "d"],
            "metadatas": [
                {"source": "f.pdf", "page": 3},
                {"source": "g.csv", "row": 10},
                {"source": "h.docx", "paragraph": 7},
                {"source": "i.txt", "chunk": 2},
            ],
        }
        files = vs.get_all_files()
        assert len(files) == 4
        for f in files:
            if f["source"] == "f.pdf":
                assert f["type"] == "PDF"
                assert f["page_range"] == "3-3"
            elif f["source"] == "g.csv":
                assert f["type"] == "CSV"
                assert f["page_range"] == "-"
            elif f["source"] == "h.docx":
                assert f["type"] == "DOCX"
                assert f["page_range"] == "Para 7-7"
            elif f["source"] == "i.txt":
                assert f["type"] == "TXT"
                assert f["page_range"] == "Chunk 2-2"

    def test_get_all_files_mixed_type(self):
        vs, _, mock_collection = self._make_vs()
        # Edge case: a weird source with mixed metadata types
        mock_collection.get.return_value = {
            "ids": ["d1", "d2"],
            "documents": ["a", "b"],
            "metadatas": [
                {"source": "weird.pdf", "page": 1},
                {"source": "weird.pdf", "chunk": 0},  # mixed: PDF + TXT
            ],
        }
        files = vs.get_all_files()
        assert len(files) == 1
        assert files[0]["type"] == "Mixed"

    def test_get_all_files_single_file(self):
        vs, _, mock_collection = self._make_vs()
        mock_collection.get.return_value = {
            "ids": ["d1", "d2"],
            "documents": ["first paragraph of the report...", "page 2 content"],
            "metadatas": [
                {"source": "report.pdf", "page": 1},
                {"source": "report.pdf", "page": 2},
            ],
        }
        files = vs.get_all_files()
        assert len(files) == 1
        f = files[0]
        assert f["source"] == "report.pdf"
        assert f["type"] == "PDF"
        assert f["chunk_count"] == 2
        assert f["page_range"] == "1-2"
        assert f["preview"] == "first paragraph of the report..."

    def test_collection_property_lazy_init(self):
        """Test that collection property triggers lazy init."""
        with patch("core.vector_store.chromadb.PersistentClient") as MockClient:
            mock_inst = MagicMock()
            MockClient.return_value = mock_inst

            from core.vector_store import VectorStore
        from config_provider import ConfigProvider
        from unittest.mock import MagicMock

            vs = VectorStore(ConfigProvider(MagicMock()))
            _ = vs.collection  # triggers lazy init
            mock_inst.get_or_create_collection.assert_called_once()

    def test_ensure_collection_invalidates_on_delete(self):
        """After delete_collection, _collection is None and re-initialises."""
        vs, _, mock_collection = self._make_vs()
        vs.delete_collection()
        assert vs._collection is None

        # Accessing collection triggers re-init
        _ = vs.collection  # Should work without error (mock returns itself)





class TestVectorStoreEmbeddingFunction:
    """Tests for VectorStore embedding function configuration."""

    def test_no_openai_key_returns_none(self, monkeypatch):
        """Without OPENAI_API_KEY, create_embedding_function returns None."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with patch("core.vector_store.chromadb.PersistentClient"):
            from core.embedding_function import create_embedding_function
            from config_provider import ConfigProvider
            from unittest.mock import MagicMock

            assert create_embedding_function(ConfigProvider(MagicMock())) is None

    def test_embedding_creator_injected(self):
        """Test that an injected embedding creator is used."""
        with patch("core.vector_store.chromadb.PersistentClient"):
            from core.vector_store import VectorStore
        from config_provider import ConfigProvider
        from unittest.mock import MagicMock

            mock_ef = MagicMock()
            mock_cfg = MagicMock()
            mock_cfg.db_path = "./chroma_db"
            mock_cfg.collection_name = "test"

            def creator():
                return mock_ef

            vs = VectorStore(config_provider=mock_cfg, embedding_creator=creator)
            assert vs._embedding_creator is not None
