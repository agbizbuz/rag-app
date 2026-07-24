"""Ollama provider (OpenAI-compatible local server)."""

from __future__ import annotations

import os

from .openai_compat import OpenAICompatProvider, get_openai_client  # noqa: F401 re-export


class OllamaProvider(OpenAICompatProvider):
    """Ollama provider — uses the "ollama" sentinel API key."""

    name = "Ollama"

    def __init__(self, model: str, temperature: float = 0.2, max_tokens: int = 1024) -> None:
        self._base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        if not self._base_url.endswith("/v1"):
            self._base_url += "/v1"
        super().__init__(model, temperature=temperature, max_tokens=max_tokens)

    def _get_api_key(self) -> str:
        # Ollama uses a sentinel key "ollama", not an env var
        return "ollama"


__all__ = ["OllamaProvider", "get_openai_client"]
