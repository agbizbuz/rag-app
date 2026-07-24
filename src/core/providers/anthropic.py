"""Anthropic (Claude) provider."""

from __future__ import annotations

import os

from .base import ChatMessage, KeyMissingError, Provider


class AnthropicProvider(Provider):
    name = "Anthropic"

    def __init__(self, model: str, temperature: float = 0.2, max_tokens: int = 1024) -> None:
        self._model = self._extract_model_name(model)
        self._temperature = temperature
        self._max_tokens = max_tokens

    def _get_api_key(self) -> str:
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise KeyMissingError("`ANTHROPIC_API_KEY` is missing in the environment.")
        return key

    def chat(self, messages: list[ChatMessage]) -> str:
        from anthropic import Anthropic  # noqa: PLC0415

        api_key = self._get_api_key()
        client = Anthropic(api_key=api_key)

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


__all__ = ["AnthropicProvider"]
