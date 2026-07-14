"""Anthropic (Claude) provider."""

from __future__ import annotations

from .base import ChatMessage, Provider


class AnthropicProvider(Provider):
    name = "Anthropic"

    def __init__(self, model: str, temperature: float = 0.2, max_tokens: int = 1024) -> None:
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens

    def chat(self, messages: list[ChatMessage]) -> str:
        import os

        from anthropic import Anthropic

        from .base import KeyMissingError as KME

        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise KME("`ANTHROPIC_API_KEY` is missing in the environment.")

        client = Anthropic(api_key=key)

        system_prompt = None
        chat_msgs = []
        for m in messages:
            if m.role == "system":
                system_prompt = m.content
            else:
                chat_msgs.append({"role": m.role, "content": m.content})

        kwargs_dict = {"model": self._model, "messages": chat_msgs}
        kwargs_dict["max_tokens"] = self._max_tokens
        kwargs_dict["temperature"] = self._temperature
        if system_prompt:
            kwargs_dict["system"] = system_prompt

        resp = client.messages.create(**kwargs_dict)
        content_block = resp.content[0]
        return getattr(content_block, "text", None) or ""
