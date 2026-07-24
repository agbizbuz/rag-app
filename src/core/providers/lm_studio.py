"""LM Studio provider (OpenAI-compatible local server)."""

from __future__ import annotations

import os

from .openai_compat import OpenAICompatProvider, get_openai_client  # noqa: F401 re-export


class LMStudioProvider(OpenAICompatProvider):
    """LM Studio provider — uses the "lm-studio" sentinel API key."""

    name = "LM Studio"

    def __init__(self, model: str, temperature: float = 0.2, max_tokens: int = 1024) -> None:
        self._base_url = os.environ.get("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
        super().__init__(model, temperature=temperature, max_tokens=max_tokens)

    def _get_api_key(self) -> str:
        # LM Studio uses a sentinel key "lm-studio", not an env var
        return "lm-studio"


__all__ = ["LMStudioProvider", "get_openai_client"]
