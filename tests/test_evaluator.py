"""Tests for core evaluator module."""

from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

import pytest
from ragapp.config_provider import ConfigProvider
from ragapp.core.evaluator import EvaluationManager, EvaluationRecord, LLMJudge


@pytest.fixture
def temp_log_path(tmp_path) -> str:
    """Create a temporary log path for testing EvaluationManager."""
    return str(tmp_path / "test_evaluation_logs.json")


@pytest.fixture
def mock_config(temp_log_path) -> ConfigProvider:
    """Create a mock ConfigProvider pointing to the temp log path."""
    cfg = MagicMock(spec=ConfigProvider)
    cfg.evaluation_log_path = temp_log_path
    cfg.llm_max_tokens = 512
    return cfg


def test_evaluation_record_init():
    """Test EvaluationRecord field mapping and properties."""
    record = EvaluationRecord(
        query="test query",
        answer="test answer",
        model="gpt-4o-mini",
        latency=1.23,
        retrieval_mode="hybrid",
        num_chunks=2,
        chunk_distances=[0.1, 0.3],
    )

    assert record.query == "test query"
    assert record.answer == "test answer"
    assert record.model == "gpt-4o-mini"
    assert record.latency == 1.23
    assert record.retrieval_mode == "hybrid"
    assert record.num_chunks == 2
    assert record.chunk_distances == [0.1, 0.3]
    assert record.avg_distance == 0.2
    assert record.rating is None
    assert record.feedback_comment is None
    assert record.faithfulness_score is None
    assert record.relevance_score is None


def test_evaluation_record_serialization():
    """Test serialization/deserialization to/from dict."""
    record = EvaluationRecord(
        query="test",
        answer="test response",
        model="gemini",
        latency=0.5,
        retrieval_mode="semantic",
        num_chunks=1,
        chunk_distances=[0.15],
        rating="thumbs_up",
        feedback_comment="Nice job",
        faithfulness_score=5,
        faithfulness_reason="good grounding",
        relevance_score=4,
        relevance_reason="minor detail missing",
    )

    d = record.to_dict()
    assert d["query"] == "test"
    assert d["rating"] == "thumbs_up"
    assert d["faithfulness_score"] == 5

    restored = EvaluationRecord.from_dict(d)
    assert restored.record_id == record.record_id
    assert restored.query == "test"
    assert restored.rating == "thumbs_up"
    assert restored.avg_distance == 0.15
    assert restored.faithfulness_score == 5
    assert restored.faithfulness_reason == "good grounding"
    assert restored.relevance_score == 4
    assert restored.relevance_reason == "minor detail missing"


def test_evaluation_manager_lifecycle(mock_config, temp_log_path):
    """Test EvaluationManager log adding, getting, updating, and clearing."""
    manager = EvaluationManager(config_provider=mock_config)
    assert manager.get_records() == []

    # Add a record
    record = EvaluationRecord(
        query="query 1",
        answer="answer 1",
        model="gpt",
        latency=1.0,
        retrieval_mode="hybrid",
        num_chunks=1,
        chunk_distances=[0.2],
    )
    manager.add_record(record)

    records = manager.get_records()
    assert len(records) == 1
    assert records[0].query == "query 1"
    assert records[0].record_id == record.record_id

    # Update feedback
    success = manager.update_feedback(
        record_id=record.record_id, rating="thumbs_down", feedback_comment="wrong"
    )
    assert success is True

    records = manager.get_records()
    assert records[0].rating == "thumbs_down"
    assert records[0].feedback_comment == "wrong"

    # Update LLM judge
    success_judge = manager.update_llm_judge(
        record_id=record.record_id,
        faithfulness_score=3,
        faithfulness_reason="partially faithful",
        relevance_score=5,
        relevance_reason="highly relevant",
    )
    assert success_judge is True

    records = manager.get_records()
    assert records[0].faithfulness_score == 3
    assert records[0].relevance_score == 5

    # Update non-existent record
    fail = manager.update_feedback("non-existent-id", rating="thumbs_up")
    assert fail is False

    # Clear logs
    manager.clear_logs()
    assert manager.get_records() == []
    assert not os.path.exists(temp_log_path)


@patch("ragapp.core.providers.routing.resolve_provider")
def test_llm_judge_evaluate_success(mock_resolve, mock_config):
    """Test LLMJudge successful evaluation parsing."""
    mock_provider_cls = MagicMock()
    mock_instance = MagicMock()
    # Mock LLM returns a json string inside tags
    mock_instance.chat.return_value = """
    ```json
    {
      "faithfulness_score": 5,
      "faithfulness_reason": "Fully grounded in the text provided.",
      "relevance_score": 4,
      "relevance_reason": "Directly answers the query, but is missing details."
    }
    ```
    """
    mock_provider_cls.return_value = mock_instance
    mock_resolve.return_value = mock_provider_cls

    res = LLMJudge.evaluate(
        query="test query",
        context="test context",
        answer="test answer",
        model="gpt-4o-mini",
        config_provider=mock_config,
    )

    assert res["faithfulness_score"] == 5
    assert res["relevance_score"] == 4
    assert "Fully grounded" in res["faithfulness_reason"]
    assert "Directly answers" in res["relevance_reason"]


@patch("ragapp.core.providers.routing.resolve_provider")
def test_llm_judge_evaluate_failure(mock_resolve, mock_config):
    """Test LLMJudge graceful failure handling on malformed JSON response."""
    mock_provider_cls = MagicMock()
    mock_instance = MagicMock()
    mock_instance.chat.return_value = "not a json string"
    mock_provider_cls.return_value = mock_instance
    mock_resolve.return_value = mock_provider_cls

    res = LLMJudge.evaluate(
        query="test query",
        context="test context",
        answer="test answer",
        model="gpt-4o-mini",
        config_provider=mock_config,
    )

    assert "error" in res
    assert res["faithfulness_score"] == 0
    assert "Evaluation error" in res["faithfulness_reason"]
