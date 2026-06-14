"""OpenAI and Groq providers (Groq uses OpenAI-compatible API)."""

from __future__ import annotations

# Re-export at module level so tests can patch via "core.providers.openai.OpenAI"
# This enables test mocks to be applied via "patch('ragapp.core.providers.openai.OpenAI')"
OpenAI = None  # type: ignore[assignment]
_setter_called = False


def _set_openai(cls):
    """Setter for OpenAI class - used by tests to inject mock."""
    global OpenAI, _setter_called
    OpenAI = cls
    _setter_called = True


# Default behavior if not patched by tests: try core.llm first, then import directly
def _get_openai_client():
    """Get OpenAI client class - supports test patching via core.llm module."""

    # First check if test has patched via this module
    global OpenAI, _setter_called
    if OpenAI is not None:
        return OpenAI

    import sys

    llm_mod = sys.modules.get("core.llm")
    if llm_mod is not None:
        result = getattr(llm_mod, "OpenAI", None)
        if result is not None:
            return result

    from openai import OpenAI as OAI
    return OAI


class OpenAIProvider:
    """Standard OpenAI provider."""

    name = "OpenAI"

    def __init__(self, model: str, api_key_env: str = "OPENAI_API_KEY", base_url=None, temperature=0.2, max_tokens=1024):  # noqa: ANN001
        self._model = model
        self._api_key_env = api_key_env
        self._base_url = base_url
        self._temperature = temperature
        self._max_tokens = max_tokens

    def chat(self, messages, temperature=0.0):  # noqa: ANN001
        import os

        from .base import KeyMissingError as KME

        key = os.environ.get(self._api_key_env)
        if not key:
            raise KME(f"`{self._api_key_env}` is missing in the environment.")

        OAI = _get_openai_client()
        client = OAI(api_key=key, base_url=self._base_url)
        messages_dicts = [{"role": m.role, "content": m.content} for m in messages]
        resp = client.chat.completions.create(
            model=self._model,
            messages=messages_dicts,
            temperature=temperature,
        )
        return (resp.choices[0].message.content) or ""
