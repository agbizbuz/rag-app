"""Evaluation core classes to measure, store and grade RAG system performance.

Follows SOLID design principles:
- SRP: Separate classes for data mapping, persistence, and AI judging.
- DIP: Depends on ConfigProvider abstraction, not direct globals.
"""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ragapp.config_provider import ConfigProvider, get_config


class EvaluationRecord:
    """Represents a single query execution evaluation record."""

    def __init__(
        self,
        query: str,
        answer: str,
        model: str,
        latency: float,
        retrieval_mode: str,
        num_chunks: int,
        chunk_distances: List[float],
        timestamp: Optional[str] = None,
        record_id: Optional[str] = None,
        rating: Optional[str] = None,  # "thumbs_up", "thumbs_down", or None
        feedback_comment: Optional[str] = None,
        faithfulness_score: Optional[int] = None,
        faithfulness_reason: Optional[str] = None,
        relevance_score: Optional[int] = None,
        relevance_reason: Optional[str] = None,
    ) -> None:
        self.record_id = record_id or str(uuid.uuid4())
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()
        self.query = query
        self.answer = answer
        self.model = model
        self.latency = latency
        self.retrieval_mode = retrieval_mode
        self.num_chunks = num_chunks
        self.chunk_distances = chunk_distances
        self.rating = rating
        self.feedback_comment = feedback_comment
        self.faithfulness_score = faithfulness_score
        self.faithfulness_reason = faithfulness_reason
        self.relevance_score = relevance_score
        self.relevance_reason = relevance_reason

    @property
    def avg_distance(self) -> float:
        """Calculate average distance score of retrieved context chunks."""
        if not self.chunk_distances:
            return 0.0
        return sum(self.chunk_distances) / len(self.chunk_distances)

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to a JSON-serializable dictionary."""
        return {
            "record_id": self.record_id,
            "timestamp": self.timestamp,
            "query": self.query,
            "answer": self.answer,
            "model": self.model,
            "latency": self.latency,
            "retrieval_mode": self.retrieval_mode,
            "num_chunks": self.num_chunks,
            "chunk_distances": self.chunk_distances,
            "avg_distance": self.avg_distance,
            "rating": self.rating,
            "feedback_comment": self.feedback_comment,
            "faithfulness_score": self.faithfulness_score,
            "faithfulness_reason": self.faithfulness_reason,
            "relevance_score": self.relevance_score,
            "relevance_reason": self.relevance_reason,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> EvaluationRecord:
        """Create an EvaluationRecord from a dictionary."""
        return cls(
            query=d.get("query", ""),
            answer=d.get("answer", ""),
            model=d.get("model", ""),
            latency=d.get("latency", 0.0),
            retrieval_mode=d.get("retrieval_mode", "hybrid"),
            num_chunks=d.get("num_chunks", 0),
            chunk_distances=d.get("chunk_distances", []),
            timestamp=d.get("timestamp"),
            record_id=d.get("record_id"),
            rating=d.get("rating"),
            feedback_comment=d.get("feedback_comment"),
            faithfulness_score=d.get("faithfulness_score"),
            faithfulness_reason=d.get("faithfulness_reason"),
            relevance_score=d.get("relevance_score"),
            relevance_reason=d.get("relevance_reason"),
        )


class EvaluationManager:
    """Handles persistence of evaluation records to a local JSON file."""

    def __init__(self, config_provider: Optional[ConfigProvider] = None) -> None:
        self._config = config_provider or get_config()
        # Fallback if property is not defined
        self.log_path = getattr(self._config, "evaluation_log_path", "./evaluation_logs.json")

    def _load_logs(self) -> List[Dict[str, Any]]:
        """Load raw logs from disk."""
        if not os.path.exists(self.log_path):
            return []
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)  # type: ignore[no-any-return]
        except Exception:
            return []

    def _save_logs(self, logs: List[Dict[str, Any]]) -> None:
        """Save raw logs to disk."""
        dir_name = os.path.dirname(self.log_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        try:
            with open(self.log_path, "w", encoding="utf-8") as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def add_record(self, record: EvaluationRecord) -> None:
        """Append an evaluation record to log."""
        logs = self._load_logs()
        logs.append(record.to_dict())
        self._save_logs(logs)

    def get_records(self) -> List[EvaluationRecord]:
        """Retrieve all logged evaluation records."""
        logs = self._load_logs()
        return [EvaluationRecord.from_dict(d) for d in logs]

    def update_feedback(
        self, record_id: str, rating: Optional[str], feedback_comment: Optional[str] = None
    ) -> bool:
        """Update qualitative feedback (rating, comment) on an existing record."""
        logs = self._load_logs()
        updated = False
        for d in logs:
            if d.get("record_id") == record_id:
                if rating is not None:
                    d["rating"] = rating
                if feedback_comment is not None:
                    d["feedback_comment"] = feedback_comment
                updated = True
                break
        if updated:
            self._save_logs(logs)
        return updated

    def update_llm_judge(
        self,
        record_id: str,
        faithfulness_score: int,
        faithfulness_reason: str,
        relevance_score: int,
        relevance_reason: str,
    ) -> bool:
        """Update LLM Judge scores and reasons on an existing record."""
        logs = self._load_logs()
        updated = False
        for d in logs:
            if d.get("record_id") == record_id:
                d["faithfulness_score"] = faithfulness_score
                d["faithfulness_reason"] = faithfulness_reason
                d["relevance_score"] = relevance_score
                d["relevance_reason"] = relevance_reason
                updated = True
                break
        if updated:
            self._save_logs(logs)
        return updated

    def clear_logs(self) -> None:
        """Reset history by deleting the log file."""
        if os.path.exists(self.log_path):
            try:
                os.remove(self.log_path)
            except Exception:
                pass


class LLMJudge:
    """Performs LLM-as-a-judge qualitative evaluations."""

    @staticmethod
    def evaluate(
        query: str,
        context: str,
        answer: str,
        model: str,
        config_provider: Optional[ConfigProvider] = None,
    ) -> Dict[str, Any]:
        """Evaluate the quality (faithfulness and relevance) of a response.

        Args:
            query: The user query text.
            context: The RAG context text provided.
            answer: The generated answer text.
            model: The LLM model to use for the evaluation.
            config_provider: Configuration provider dependency.

        Returns:
            Dict containing scores and reasons, or error message.
        """
        from ragapp.config_provider import get_config as _get_cfg
        from ragapp.core.providers.base import ChatMessage as CM
        from ragapp.core.providers.routing import resolve_provider

        cfg = config_provider or _get_cfg()
        temperature = 0.0  # Determinisitic scoring
        max_tokens = cfg.llm_max_tokens

        prompt = """You are an AI judge evaluating a Retrieval-Augmented Generation (RAG) system.
Given a user query, the retrieved context, and the generated answer, evaluate:
1. Faithfulness (1-5): Is the answer grounded ONLY in the context? (1 = completely unsupported, 5 = fully grounded)
2. Relevance (1-5): Does the answer directly address the query? (1 = irrelevant, 5 = fully relevant)

=== Context ===
{context}

=== User Query ===
{query}

=== Generated Answer ===
{answer}

Respond ONLY with a valid JSON object matching the following structure:
{{
  "faithfulness_score": int,
  "faithfulness_reason": "string describing the faithfulness rating",
  "relevance_score": int,
  "relevance_reason": "string describing the relevance rating"
}}
Do not include any other markdown formatting (like ```json), introduction, or trailing text.
"""
        messages = [CM("user", prompt.format(context=context, query=query, answer=answer))]
        try:
            provider_class = resolve_provider(model)
            instance = provider_class(model=model, temperature=temperature, max_tokens=max_tokens)
            response = instance.chat(messages)

            # Extract outermost JSON object
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                response_clean = json_match.group(0)
                data = json.loads(response_clean)
                return {
                    "faithfulness_score": int(data.get("faithfulness_score", 0)),
                    "faithfulness_reason": str(data.get("faithfulness_reason", "")),
                    "relevance_score": int(data.get("relevance_score", 0)),
                    "relevance_reason": str(data.get("relevance_reason", "")),
                }
            else:
                raise ValueError("Could not parse JSON from model response: {response}")
        except Exception:
            return {
                "error": "Failed to run LLM Judge: {e}",
                "faithfulness_score": 0,
                "faithfulness_reason": "Evaluation error: {e}",
                "relevance_score": 0,
                "relevance_reason": "Evaluation error: {e}",
            }
