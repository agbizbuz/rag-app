"""Base class for providers using the OpenAI Python SDK.

Also provides ``get_openai_client()`` which tests can patch to inject a fake
OpenAI client, keeping tests free of network calls.  This function is called by
:meth:`chat` so patches at ``core.providers.openai_compat.get_openai_client``
intercept the OpenAI import for all subclass providers (Ollama, LM Studio,
OpenAI / Groq).

Backwards-compat shim: :mod:`_openai_compat` re-exports this same function.
Older test patches that target ``core.providers._openai_compat.get_openai_client``
resolve to the same object and keep working.
"""

from __future__ import annotations

import os
from typing import ClassVar

from .base import ChatMessage, KeyMissingError, Provider


def get_openai_client():
    """Return the OpenAI client class. Tests can patch this function."""
    from openai import OpenAI  # noqa: PLC0415

    return OpenAI


class OpenAICompatProvider(Provider):
    """Base for providers that use the OpenAI chat.completions API.

    Subclasses only need to define ``api_key_env``, set ``_base_url`` in
    :meth:`__init__`, and optionally override :meth:`chat_messages`.  The base
    class provides default implementations of ``_extract_model_name``,
    ``_get_api_key``, and the full OpenAI SDK call chain.

    For backwards-compat, subclass providers re-export ``get_openai_client`` so
    older test patches (targeting e.g. ``core.providers.openai.get_openai_client``)
    still work even though they don't intercept in practice -- only the base
    class's patch location is authoritative for new tests.
    """

    api_key_env: ClassVar[str] = ""  # noqa: E701 — abstract by convention
    _base_url: str | None = None
    display_name: ClassVar[str] = ""  # noqa: UP035

    def __init__(
        self, model: str, temperature: float = 0.2, max_tokens: int = 1024
    ) -> None:
        self._model = self._extract_model_name(model)
        self._temperature = temperature
        self._max_tokens = max_tokens

    def _get_api_key(self) -> str:
        key = os.environ.get(self.api_key_env)
        if not key:
            raise KeyMissingError(
                f"`{self.api_key_env}` is missing in the environment."
            )
        return key

    def chat_messages(self, messages):  # type: ignore[type-arg]
        """Convert ChatMessage objects to OpenAI SDK message dicts.

        Subclasses can override to customize (e.g., strip ``system`` roles).
        Default passes every message through unchanged.
        """
        return [{"role": m.role, "content": m.content} for m in messages]

    def chat(self, messages: list[ChatMessage]) -> str:
        OAI = get_openai_client()  # type: ignore[misc]
        api_key = self._get_api_key()
        client = OAI(api_key=api_key, base_url=self._base_url)

        msgs_dicts = self.chat_messages(messages)

        resp = client.chat.completions.create(
            model=self._model,
            messages=msgs_dicts,
            temperature=self._temperature,
        )
        return resp.choices[0].message.content or ""


__all__ = ["get_openai_client", "OpenAICompatProvider"]
