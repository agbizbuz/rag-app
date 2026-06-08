"""Anthropic (Claude) provider."""

from __future__ import annotations

# Re-export at module level for test patching
AnthropicClient = None  # type: ignore[assignment]
_setter_called = False


def _set_anthropic(cls):
    """Setter for Anthropic client - used by tests to inject mock."""
    global AnthropicClient, _setter_called
    AnthropicClient = cls
    _setter_called = True


def _get_anthropic_client_class():
    """Get Anthropic client class - supports test patching."""

    # First check if test has patched via this module
    global AnthropicClient
    if AnthropicClient is not None:
        return AnthropicClient

    import sys

    llm_mod = sys.modules.get("core.llm")
    if llm_mod is not None:
        result = getattr(llm_mod, "Anthropic", None)
        if result is not None:
            return result

    from anthropic import Anthropic
    return Anthropic


class AnthropicProvider:
    name = "Anthropic"

    def __init__(self, model: str) -> None:
        self._model = model

    def chat(self, messages, temperature=0.0):  # noqa: ANN001
        import os

        from .base import KeyMissingError as KME

        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise KME("`ANTHROPIC_API_KEY` is missing in the environment.")

        AnthropicClientClass = _get_anthropic_client_class()
        client = AnthropicClientClass(api_key=key)

        system_prompt = None
        chat_msgs = []
        for m in messages:
            if m.role == "system":
                system_prompt = m.content  # type: ignore[assignment]
            else:
                chat_msgs.append({"role": m.role, "content": m.content})

        settings = _get_settings()
        kwargs: dict = {"model": self._model, "messages": chat_msgs}
        kwargs["max_tokens"] = settings.llm_max_tokens  # type: ignore[union-attr]
        if system_prompt:
            kwargs["system"] = system_prompt  # type: ignore[arg-type]

        resp = client.messages.create(**kwargs)
        content_block = resp.content[0]
        return getattr(content_block, "text", None) or ""


def _get_settings() -> object:
    """Resolve settings with fallback paths."""
    try:
        from config import settings as s
        return s
    except ImportError:
        pass
    from config import settings as s
    return s
