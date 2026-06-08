"""HuggingFace Inference API provider (raw REST)."""

from __future__ import annotations


class HuggingFaceProvider:
    name = "HuggingFace"

    def __init__(self, model: str) -> None:
        self._model = model

    def chat(self, messages, temperature=0.0):  # noqa: ANN001
        import os

        from .base import KeyMissingError as KME

        key = os.environ.get("HUGGINGFACE_API_KEY")
        if not key:
            raise KME("`HUGGINGFACE_API_KEY` is missing in the environment.")

        import requests

        combined = "\n\n".join(m.content for m in messages if m.role != "system")
        settings = _get_settings()
        resp = requests.post(
            f"https://api-inference.huggingface.co/models/{self._model}",
            headers={"Authorization": f"Bearer {key}"},
            json={
                "inputs": combined,
                "parameters": {"max_new_tokens": settings.llm_max_tokens},  # type: ignore[union-attr]
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


def _get_settings() -> object:
    """Resolve settings with fallback paths."""
    try:
        from config import settings as s
        return s
    except ImportError:
        pass
    from config import settings as s
    return s
