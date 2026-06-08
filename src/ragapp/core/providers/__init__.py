"""Provider protocol, exceptions, and chat model for LLM providers."""

from .base import ChatMessage as CM  # noqa: F401 re-export
from .base import (
    KeyMissingError,
    Provider,
    RAGError,
    UnsupportedModelError,
)
from .routing import _REGISTRY, Protocol, ProviderProtocol, register, resolve_provider


def _register_all():
    from .anthropic import AnthropicProvider  # noqa: TLE001
    register("claude-", AnthropicProvider)

    from .gemini import GeminiProvider  # noqa: TLE001
    register("gemini", GeminiProvider)

    from .lm_studio import LMStudioProvider  # noqa: TLE001
    register("lm-studio:", LMStudioProvider)

    from .ollama import OllamaProvider  # noqa: TLE001
    register("ollama:", OllamaProvider)

    from .openai import OpenAIProvider  # noqa: TLE001
    register("", OpenAIProvider)  # Default for gpt-* models
    register("groq:", OpenAIProvider)  # Groq uses same provider but with GROQ_API_KEY


_register_all()

__all__ = [
    "ChatMessage",
    "CM",
    "KeyMissingError",
    "Provider",
    "RAGError",
    "UnsupportedModelError",
    "Protocol",
    "ProviderProtocol",
    "_REGISTRY",
    "register",
    "resolve_provider",
]

