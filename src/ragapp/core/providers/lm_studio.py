"""LM Studio provider (OpenAI-compatible local server)."""

from __future__ import annotations

import os


from ._openai_compat import get_openai_client
from .base import ChatMessage, Provider


class LMStudioProvider(Provider):
    name = "LM Studio"

    def __init__(self, model: str, temperature=0.2, max_tokens=1024) -> None:
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._base_url = os.environ.get("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")

    def chat(self, messages: list[ChatMessage]) -> str:
        OAI = get_openai_client()
        client = OAI(api_key="lm-studio", base_url=self._base_url)
        messages_dicts = [{"role": m.role, "content": m.content} for m in messages]
        resp = client.chat.completions.create(
            model=self._model,
            messages=messages_dicts,
            temperature=self._temperature,
        )
        return resp.choices[0].message.content or ""
