"""LLM response facade — delegates to the resolved provider.

Tests that patch ``core.llm.OpenAI`` or
``core.llm.Anthropic`` will work because every provider
lazy-looks up these classes from this module at call time.
"""

from __future__ import annotations

# --------------------------------------------------------------------------- #
# Re-exports — tests patch these names on this module                       #
# --------------------------------------------------------------------------- #
from anthropic import Anthropic  # noqa: F401
from openai import OpenAI  # noqa: F401


class ChatMessage:
    """Message for LLM chat interface.

    Also re-exported at module level so tests can patch ``core.llm.ChatMessage``.
    """

    def __init__(self, role: str, content: str) -> None:
        self.role = role  # "system" | "user" | "assistant"
        self.content = content

    def __repr__(self) -> str:
        return f"ChatMessage(role={self.role!r}, content=...)"


class KeyMissingError(Exception):
    """Raised when a required API key is not configured."""
    pass


class UnsupportedModelError(Exception):
    """Raised when the model string doesn't match any known provider."""
    pass


class RAGError(Exception):
    """Base exception for RAG-layer errors."""
    pass


def get_llm_response(
    query_context: str,
    user_query: str,
    llm_model: str,
    config_provider=None,  # noqa: ANN001
) -> str:
    """Query the selected LLM provider for a given context and model.

    Args:
        query_context: The retrieved context from vector store.
        llm_model: The model identifier (e.g., "gpt-4o-mini", "ollama:llama3").
        config_provider: Optional injected ConfigProvider to avoid import cycles.

    Returns:
        LLM-generated text or error message prefixed with ⚠️.
    """
    from ragapp.config_provider import get_config as _get_cfg
    cfg = config_provider or _get_cfg()
    temperature = cfg.llm_temperature  # type: ignore[union-attr]
    max_tokens = cfg.llm_max_tokens  # type: ignore[union-attr]

    from .providers.base import ChatMessage as CM
    from .providers.base import KeyMissingError as KME
    from .providers.base import UnsupportedModelError as UME
    from .providers.lm_studio import LMStudioProvider
    from .providers.ollama import OllamaProvider
    from .providers.openai import OpenAIProvider
    from .providers.routing import resolve_provider

    system_prompt = cfg.system_prompt  # type: ignore[union-attr]

    messages: list[CM] = [
        CM("system", system_prompt),
        CM(
            "user",
            f"=== PROVIDED CONTEXT ===\n{
                query_context}\n\n=== USER QUERY ===\n{user_query}\n\n",
        ),
    ]

    try:
        provider_class = resolve_provider(llm_model)
    except UME as exc:
        return f"\u26a0\ufe0f {exc}"

    # Determine which provider type we have and instantiate accordingly
    try:
        if provider_class == OpenAIProvider:
            api_key_env = "GROQ_API_KEY" if llm_model.startswith(
                "groq:") else "OPENAI_API_KEY"
            import os
            print(f"DEBUG: model={llm_model}, OPENAI_API_KEY={
                  os.environ.get("OPENAI_API_KEY", "NOT SET")}")
            instance = provider_class(
                model=llm_model, temperature=temperature, max_tokens=max_tokens, api_key_env=api_key_env)
            return instance.chat(messages)
        elif provider_class in (OllamaProvider, LMStudioProvider):
            # Local providers don't need explicit key env for initialization
            instance = provider_class(
                model=llm_model, temperature=temperature, max_tokens=max_tokens)
            return instance.chat(messages)
        else:
            # Other providers (Anthropic, Gemini, HuggingFace) take model param only
            instance = provider_class(
                model=llm_model, temperature=temperature, max_tokens=max_tokens)
            return instance.chat(messages)

    except KME as exc:
        return f"\u26a0\ufe0f Error: {exc}"
    except Exception as exc:
        return f"\u26a0\ufe0f {type(provider_class).__name__} API Error: {exc}"
