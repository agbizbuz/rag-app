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


class _MockSettings:
    """Minimal mock settings for test compatibility."""

    llm_temperature = 0.2


def _get_settings() -> object:
    """Resolve settings from default module, with fallback to mock."""
    try:
        from ragapp.config import settings as cfg
        return cfg
    except ImportError:
        return _MockSettings()


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
    llm_model: str,
    settings=None,  # noqa: ANN001
) -> str:
    """Query the selected LLM provider for a given context and model.

    Args:
        query_context: The retrieved context from vector store.
        llm_model: The model identifier (e.g., "gpt-4o-mini", "ollama:llama3").
        settings: Optional injected settings object to avoid import cycles.

    Returns:
        LLM-generated text or error message prefixed with ⚠️.
    """
    cfg = settings or _get_settings()
    temperature = getattr(cfg, "llm_temperature", 0.2)

    from .providers.base import (
        ChatMessage as CM,
    )
    from .providers.base import KeyMissingError as KME
    from .providers.base import UnsupportedModelError as UME
    from .providers.routing import resolve_provider

    system_prompt = (
        "You are a highly capable research assistant. "
        "Answer the user's query strictly based on the provided context. "
        "If the context does not contain sufficient information to answer "
        "the question, respectfully state that the information is not found in "
        "the documents. Provide the answer clearly and concisely."
    )

    messages: list[CM] = [
        CM("system", system_prompt),
        CM(
            "user",
            f"=== PROVIDED CONTEXT ===\n{query_context}\n\n=== USER QUERY ===",
        ),
    ]

    try:
        provider_class = resolve_provider(llm_model)
    except UME as exc:
        return f"\u26a0\ufe0f {exc}"

    # Determine which provider type we have and instantiate accordingly
    from .providers.lm_studio import LMStudioProvider
    from .providers.ollama import OllamaProvider
    from .providers.openai import OpenAIProvider
    
    try:
        if provider_class == OpenAIProvider:
            api_key_env = "GROQ_API_KEY" if llm_model.startswith("groq:") else "OPENAI_API_KEY"
            instance = provider_class(model=llm_model, api_key_env=api_key_env)
        elif provider_class in (OllamaProvider, LMStudioProvider):
            # Local providers don't need explicit key env for initialization
            instance = provider_class(model=llm_model)
        else:
            # Other providers (Anthropic, Gemini, HuggingFace) take model param only
            instance = provider_class(model=llm_model)

        return instance.chat(messages, temperature=temperature)  # type: ignore[arg-type]
    except KME as exc:
        return f"\u26a0\ufe0f Error: {exc}"
    except Exception as exc:
        return f"\u26a0\ufe0f {type(provider_class).__name__} API Error: {exc}"


