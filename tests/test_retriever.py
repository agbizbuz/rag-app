"""Tests for src/ragapp/core/retriever.py."""

from unittest.mock import MagicMock

from ragapp.core.retriever import RAGRetriever


class TestRAGRetriever:
    """Tests for RAGRetriever."""

    def test_init_and_routing(self):
        mock_vs = MagicMock()
        cfg = MagicMock()
        cfg.n_results = 5
        retriever = RAGRetriever(vector_store=mock_vs, config_provider=cfg)
        assert retriever.vector_store == mock_vs
        assert retriever._config == cfg

    def test_retrieve_uses_config_n_results(self):
        mock_vs = MagicMock()
        cfg = MagicMock()
        cfg.n_results = 5
        retriever = RAGRetriever(vector_store=mock_vs, config_provider=cfg)

        mock_vs.query.return_value = [{"text": "hello"}]

        res = retriever.retrieve("test query")
        assert res == [{"text": "hello"}]
        mock_vs.query.assert_called_once_with("test query", n_results=5)

    def test_retrieve_uses_override_n_results(self):
        mock_vs = MagicMock()
        cfg = MagicMock()
        cfg.n_results = 5
        retriever = RAGRetriever(vector_store=mock_vs, config_provider=cfg)

        mock_vs.query.return_value = []

        res = retriever.retrieve("test query", n_results=10)
        assert res == []
        mock_vs.query.assert_called_once_with("test query", n_results=10)

    def test_format_context(self):
        mock_vs = MagicMock()
        retriever = RAGRetriever(vector_store=mock_vs)

        results = [
            {"text": "chunk 1", "metadata": {}},
            {"text": "chunk 2", "metadata": {}},
        ]
        context = retriever.format_context(results)
        assert context == "chunk 1\n\n---\n\nchunk 2"

    def test_retrieve_formatted_context(self):
        mock_vs = MagicMock()
        retriever = RAGRetriever(vector_store=mock_vs)

        mock_vs.query.return_value = [
            {"text": "chunk 1", "metadata": {}},
            {"text": "chunk 2", "metadata": {}},
        ]

        context = retriever.retrieve_formatted_context("query text", n_results=2)
        assert context == "chunk 1\n\n---\n\nchunk 2"
        mock_vs.query.assert_called_once_with("query text", n_results=2)
