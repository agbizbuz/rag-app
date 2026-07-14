"""Ollama provider (OpenAI-compatible local server)."""

from __future__ import annotations

import os
import re

strip_pattern = re.compile("ollama:", re.IGNORECASE)


from ._openai_compat import get_openai_client
from .base import ChatMessage, Provider


class OllamaProvider(Provider):
    name = "Ollama"

    def __init__(self, model: str, temperature=0.2, max_tokens=1024) -> None:
        self._model = strip_pattern.sub("", model)
        self._temperature = temperature
        self._max_tokens = max_tokens
        base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        if not base_url.endswith("/v1"):
            base_url = base_url + "/v1"
        self._base_url = base_url

    def chat(self, messages: list[ChatMessage]) -> str:
        OAI = get_openai_client()
        client = OAI(api_key="ollama", base_url=self._base_url)
        messages_dicts = [{"role": m.role, "content": m.content} for m in messages]
        resp = client.chat.completions.create(
            model=self._model,
            messages=messages_dicts,
            temperature=self._temperature,
        )
        return resp.choices[0].message.content or ""
