"""OpenAI and Groq providers (Groq uses OpenAI-compatible API)."""

from __future__ import annotations

import os

from .base import KeyMissingError
from .openai_compat import OpenAICompatProvider, get_openai_client  # noqa: F401 re-export


class OpenAIProvider(OpenAICompatProvider):
    """Standard OpenAI provider that also handles Groq via the OpenAI SDK.

    Automatically resolves the correct API key env var based on model prefix:
      - ``groq:`` models -> ``GROQ_API_KEY``
      - everything else -> ``OPENAI_API_KEY``
    """

    name = "OpenAI"
    api_key_env = "OPENAI_API_KEY"  # may be overridden in __init__

    def __init__(self, model: str, temperature: float = 0.2, max_tokens: int = 1024) -> None:
        if model.lower().startswith("groq:"):
            self.api_key_env = "GROQ_API_KEY"
            self._base_url = "https://api.groq.com/openai/v1"
        else:
            self.api_key_env = "OPENAI_API_KEY"  # type: ignore[assignment]
            self._base_url = "https://api.openai.com/v1/"

        super().__init__(model, temperature=temperature, max_tokens=max_tokens)

    def _get_api_key(self) -> str:
        key = os.environ.get(self.api_key_env)
        if not key:
            raise KeyMissingError(
                f"`{self.api_key_env}` is missing in the environment."
            )
        return key


__all__ = ["OpenAIProvider", "get_openai_client"]
