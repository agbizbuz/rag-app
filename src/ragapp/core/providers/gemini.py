"""Google Gemini provider."""

from __future__ import annotations


class GeminiProvider:
    name = "Google Gemini"

    def __init__(self, model: str) -> None:
        self._model = model

    def chat(self, messages, temperature=0.0):  # noqa: ANN001
        import os

        from .base import KeyMissingError

        key = os.environ.get("GOOGLE_API_KEY")
        if not key:
            raise KeyMissingError("`GOOGLE_API_KEY` is missing in the environment.")

        import google.generativeai as genai

        genai.configure(api_key=key)
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        model_obj = genai.GenerativeModel(
            model_name=self._model, safety_settings=safety_settings
        )
        combined = "\n\n".join(m.content for m in messages if m.role != "system")
        response = model_obj.generate_content(combined)
        return response.text
