"""Tests for core/keyword_search.py."""

from __future__ import annotations

from ragapp.core.keyword_search import KeywordSearcher, _tokenize


def test_tokenize() -> None:
    """Test the basic regex tokenizer."""
    assert _tokenize("Hello, World!") == ["hello", "world"]
    assert _tokenize("RAG-app version 1.0.") == ["rag", "app", "version", "1", "0"]
    assert _tokenize("") == []


def test_keyword_searcher_empty_or_none() -> None:
    """Test KeywordSearcher with empty list or invalid corpus."""
    searcher = KeywordSearcher([])
    assert searcher.search("query") == []

    # Test query with no alphanumeric characters
    searcher = KeywordSearcher([{"id": "1", "text": "hello world"}])
    assert searcher.search("!!!") == []


def test_keyword_searcher_scoring_and_ranking() -> None:
    """Test KeywordSearcher ranking matches correctly and formatting return values."""
    docs = [
        {"id": "doc1", "text": "The quick brown fox jumps over the lazy dog"},
        {"id": "doc2", "text": "Python programming is fun and powerful"},
        {"id": "doc3", "text": "Quick brown foxes are fast animals"},
    ]

    searcher = KeywordSearcher(docs)

    # Search for "quick brown" - doc1 and doc3 have both words, doc2 has none
    results = searcher.search("quick brown", n_results=5)
    assert len(results) == 2
    assert results[0]["id"] in ["doc1", "doc3"]
    assert results[1]["id"] in ["doc1", "doc3"]
    assert results[0]["distance"] > 0
    assert results[0]["distance"] < 1.0

    # Verify return dict keys
    for r in results:
        assert "id" in r
        assert "text" in r
        assert "metadata" in r
        assert "distance" in r
