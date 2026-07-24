"""Google Gemini provider."""

from __future__ import annotations

import os

from .base import ChatMessage, KeyMissingError, Provider


class GeminiProvider(Provider):
    name = "Google Gemini"

    def __init__(self, model: str, temperature: float = 0.2, max_tokens: int = 1024) -> None:
        self._model = self._extract_model_name(model)
        self._temperature = temperature
        self._max_tokens = max_tokens

    def _get_api_key(self) -> str:
        key = os.environ.get("GOOGLE_API_KEY")
        if not key:
            raise KeyMissingError("`GOOGLE_API_KEY` is missing in the environment.")
        return key

    def chat(self, messages: list[ChatMessage]) -> str:
        import google.generativeai as genai  # noqa: PLC0415

        api_key = self._get_api_key()
        genai.configure(api_key=api_key)
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE",
            },
        ]
        model_obj = genai.GenerativeModel(
            model_name=self._model, safety_settings=safety_settings
        )
        combined = "\n\n".join(m.content for m in messages if m.role != "system")
        response = model_obj.generate_content(combined)
        return getattr(response, "text", None) or ""


__all__ = ["GeminiProvider"]
