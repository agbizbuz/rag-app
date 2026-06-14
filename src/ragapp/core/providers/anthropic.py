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

    def __init__(self, model: str, temperature: float = 0.2, max_tokens: int = 1024) -> None:
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens

    def chat(self, messages, **kwargs):
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
                system_prompt = m.content
            else:
                chat_msgs.append({"role": m.role, "content": m.content})

        kwargs_dict = {"model": self._model, "messages": chat_msgs}
        kwargs_dict["max_tokens"] = self._max_tokens
        if system_prompt:
            kwargs_dict["system"] = system_prompt

        resp = client.messages.create(**kwargs_dict)
        content_block = resp.content[0]
        return getattr(content_block, "text", None) or ""


