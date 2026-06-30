"""LLM response facade — delegates to the resolved provider.

All types (ChatMessage, exceptions) are re-exported from
``providers.base`` so existing imports like ``from core.llm import ChatMessage``
continue to work.
"""

from __future__ import annotations

# --------------------------------------------------------------------------- #
# Re-exports for backward compatibility                                       #
# --------------------------------------------------------------------------- #
from .providers.base import (  # noqa: F401
    ChatMessage,
    KeyMissingError,
    RAGError,
    UnsupportedModelError,
)


def get_llm_response(
    query_context: str,
    user_query: str,
    llm_model: str,
    config_provider=None,  # noqa: ANN001
) -> str:
    """Query the selected LLM provider for a given context and model.

    Args:
        query_context: The retrieved context from vector store.
        user_query: The user's question.
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
    from .providers.routing import resolve_provider

    system_prompt = cfg.system_prompt  # type: ignore[union-attr]

    messages: list[CM] = [
        CM("system", system_prompt),
        CM(
            "user",
            f"=== PROVIDED CONTEXT ===\n{query_context}\n\n=== USER QUERY ===\n{user_query}\n\n",
        ),
    ]

    try:
        provider_class = resolve_provider(llm_model)
    except UME as exc:
        return f"\u26a0\ufe0f {exc}"

    # Uniform instantiation — every provider uses the same constructor contract
    try:
        instance = provider_class(
            model=llm_model, temperature=temperature, max_tokens=max_tokens)
        return instance.chat(messages)
    except KME as exc:
        return f"\u26a0\ufe0f Error: {exc}"
    except Exception as exc:
        return f"\u26a0\ufe0f {type(provider_class).__name__} API Error: {exc}"
