"""Tests for core/hybrid_retriever.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from ragapp.core.hybrid_retriever import HybridRetriever


class TestHybridRetriever:
    """Tests for HybridRetriever."""

    def test_init(self) -> None:
        mock_vs = MagicMock()
        cfg = MagicMock()
        cfg.n_results = 3
        cfg.retrieval_mode = "hybrid"

        retriever = HybridRetriever(vector_store=mock_vs, config_provider=cfg)
        assert retriever.vector_store == mock_vs
        assert retriever._config == cfg
        assert retriever._rrf_k == 60

    def test_retrieve_semantic_mode(self) -> None:
        """Semantic mode should delegate directly to vector store query."""
        mock_vs = MagicMock()
        mock_vs.query.return_value = [{"id": "1", "text": "sem result", "metadata": {}, "distance": 0.1}]

        cfg = MagicMock()
        cfg.n_results = 2
        cfg.retrieval_mode = "semantic"

        retriever = HybridRetriever(vector_store=mock_vs, config_provider=cfg)
        results = retriever.retrieve("query text")

        assert len(results) == 1
        assert results[0]["text"] == "sem result"
        mock_vs.query.assert_called_once_with("query text", n_results=2)
        mock_vs.get_all_documents.assert_not_called()

    def test_retrieve_keyword_mode(self) -> None:
        """Keyword mode should get all docs and search via KeywordSearcher."""
        mock_vs = MagicMock()
        mock_vs.get_all_documents.return_value = [
            {"id": "doc1", "text": "apple banana", "metadata": {}},
            {"id": "doc2", "text": "orange grape", "metadata": {}},
        ]

        cfg = MagicMock()
        cfg.n_results = 2
        cfg.retrieval_mode = "keyword"

        retriever = HybridRetriever(vector_store=mock_vs, config_provider=cfg)

        with patch("ragapp.core.hybrid_retriever.KeywordSearcher") as MockSearcher:
            mock_instance = MagicMock()
            mock_instance.search.return_value = [{"id": "doc1", "text": "apple banana", "metadata": {}, "distance": 0.5}]
            MockSearcher.return_value = mock_instance

            results = retriever.retrieve("apple")

            assert len(results) == 1
            assert results[0]["id"] == "doc1"
            mock_vs.get_all_documents.assert_called_once()
            mock_instance.search.assert_called_once_with("apple", n_results=2)
            mock_vs.query.assert_not_called()

    def test_retrieve_hybrid_mode(self) -> None:
        """Hybrid mode fetches from both sources and fuses results."""
        mock_vs = MagicMock()
        mock_vs.get_all_documents.return_value = [
            {"id": "doc1", "text": "apple", "metadata": {}},
            {"id": "doc2", "text": "banana", "metadata": {}},
        ]
        # Semantic results
        mock_vs.query.return_value = [
            {"id": "doc1", "text": "apple", "metadata": {}, "distance": 0.1},
            {"id": "doc2", "text": "banana", "metadata": {}, "distance": 0.2},
        ]

        cfg = MagicMock()
        cfg.n_results = 2
        cfg.retrieval_mode = "hybrid"

        retriever = HybridRetriever(vector_store=mock_vs, config_provider=cfg)

        with patch("ragapp.core.hybrid_retriever.KeywordSearcher") as MockSearcher:
            mock_searcher_instance = MagicMock()
            # Keyword results return reversed rank order to see fusion effect
            mock_searcher_instance.search.return_value = [
                {"id": "doc2", "text": "banana", "metadata": {}, "distance": 0.3},
                {"id": "doc1", "text": "apple", "metadata": {}, "distance": 0.4},
            ]
            MockSearcher.return_value = mock_searcher_instance

            # We fetch candidate_count = max(n_res * 2, 10) = 10
            results = retriever.retrieve("query")

            assert len(results) == 2
            mock_vs.query.assert_called_once_with("query", n_results=10)
            mock_searcher_instance.search.assert_called_once_with("query", n_results=10)

    def test_reciprocal_rank_fusion(self) -> None:
        """Directly verify RRF ranking mathematics."""
        sem = [
            {"id": "docA", "text": "A", "metadata": {}},
            {"id": "docB", "text": "B", "metadata": {}},
        ]
        key = [
            {"id": "docB", "text": "B", "metadata": {}},
            {"id": "docC", "text": "C", "metadata": {}},
        ]

        # docB rank: 2 in sem, 1 in key
        # docA rank: 1 in sem, inf in key
        # docC rank: inf in sem, 1 in key
        # Using k=60:
        # Score docB = 1/(60+2) + 1/(60+1) = 1/62 + 1/61 = 0.016129 + 0.016393 = 0.032522
        # Score docA = 1/(60+1) = 0.016393
        # Score docC = 1/(60+1) = 0.016393
        # So docB must be ranked 1st.
        fused = HybridRetriever._reciprocal_rank_fusion(sem, key, k=60)
        assert len(fused) == 3
        assert fused[0]["id"] == "docB"
        # docA and docC have same score, order depends on sorting stability or dictionary order
        assert {fused[1]["id"], fused[2]["id"]} == {"docA", "docC"}
