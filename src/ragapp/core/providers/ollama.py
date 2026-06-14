"""Ollama provider (OpenAI-compatible local server)."""

from __future__ import annotations

import os
import re

strip_pattern = re.compile("ollama:", re.IGNORECASE)


def _get_openai_client():
    """Get OpenAI client class - supports test patching via core.llm module."""

    # First check if test has patched this function directly
    result = getattr(_get_openai_client, "_cached", None)
    if result is not None:
        return result

    import sys

    llm_mod = sys.modules.get("core.llm")
    if llm_mod is not None:
        result = getattr(llm_mod, "OpenAI", None)
        if result is not None:
            _get_openai_client._cached = result  # type: ignore[attr-defined]
            return result

    from openai import OpenAI as OAI
    _get_openai_client._cached = OAI  # type: ignore[attr-defined]
    return OAI


class OllamaProvider:
    name = "Ollama"

    def __init__(self, model: str, temperature=0.2, max_tokens=1024) -> None:
        self._model = strip_pattern.sub('', model)
        base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        if not base_url.endswith("/v1"):
            base_url = base_url + "/v1"
        self._base_url = base_url
        
    def chat(self, messages, temperature=0.0):  # noqa: ANN001
        OAI = _get_openai_client()
        client = OAI(api_key="ollama", base_url=self._base_url)
        messages_dicts = [{"role": m.role, "content": m.content} for m in messages]
        resp = client.chat.completions.create(
            model=self._model,
            messages=messages_dicts,
            temperature=temperature,
        )
        return (resp.choices[0].message.content) or ""
