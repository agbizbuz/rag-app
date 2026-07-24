"""HuggingFace Inference API provider (raw REST)."""

from __future__ import annotations

import os

from .base import ChatMessage, KeyMissingError, Provider


class HuggingFaceProvider(Provider):
    name = "HuggingFace"

    def __init__(self, model: str, temperature: float = 0.0, max_tokens: int = 1024) -> None:
        self._model = self._extract_model_name(model)
        self._temperature = temperature
        self._max_tokens = max_tokens

    def _get_api_key(self) -> str:
        key = os.environ.get("HUGGINGFACE_API_KEY")
        if not key:
            raise KeyMissingError("`HUGGINGFACE_API_KEY` is missing in the environment.")
        return key

    def chat(self, messages: list[ChatMessage]) -> str:
        import requests  # noqa: PLC0415

        api_key = self._get_api_key()
        combined = "\n\n".join(m.content for m in messages if m.role != "system")
        resp = requests.post(
            f"https://api-inference.huggingface.co/models/{self._model}",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "inputs": combined,
                "parameters": {"max_new_tokens": self._max_tokens},
            },
        )
        resp.raise_for_status()
        result = resp.json()

        if isinstance(result, list) and len(result) > 0:
            return result[0].get("generated_text", result[0])
        elif isinstance(result, str):
            return result
        else:
            raise RuntimeError(f"Unexpected HuggingFace response format: {result}")


__all__ = ["HuggingFaceProvider"]
