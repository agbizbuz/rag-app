"""OpenAI and Groq providers (Groq uses OpenAI-compatible API)."""

from __future__ import annotations

from ._openai_compat import get_openai_client
from .base import ChatMessage, Provider


class OpenAIProvider(Provider):
    """Standard OpenAI provider (also handles Groq via OpenAI-compatible API).

    Automatically resolves the correct API key env var based on model prefix:
    - ``groq:`` models → ``GROQ_API_KEY``
    - everything else → ``OPENAI_API_KEY``
    """

    name = "OpenAI"

    def __init__(self, model: str, temperature: float = 0.2, max_tokens: int = 1024) -> None:
        self._model = self._get_model_name(model)
        # Groq models use GROQ_API_KEY; everything else uses OPENAI_API_KEY
        if model.lower().startswith("groq:"):
            self._base_url = "https://api.groq.com/openai/v1"
            self._api_key_env = "GROQ_API_KEY"
        else:
            self._api_key_env = "OPENAI_API_KEY"
            self._base_url = "https://api.openai.com/v1/"
        self._temperature = temperature
        self._max_tokens = max_tokens

    def chat(self, messages: list[ChatMessage]) -> str:
        import os

        from .base import KeyMissingError as KME

        key = os.environ.get(self._api_key_env)
        if not key:
            raise KME(f"`{self._api_key_env}` is missing in the environment.")

        OAI = get_openai_client()
        client = OAI(api_key=key, base_url=self._base_url)
        messages_dicts = [{"role": m.role, "content": m.content} for m in messages]
        resp = client.chat.completions.create(
            model=self._model,
            messages=messages_dicts,
            temperature=self._temperature,
        )
        return resp.choices[0].message.content or ""
