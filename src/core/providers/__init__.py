"""Provider protocol, exceptions, and chat model for LLM providers."""

from .base import ChatMessage as CM  # noqa: F401 re-export
from .base import (
    KeyMissingError,
    Provider,
    RAGError,
    UnsupportedModelError,
)
from .routing import ProviderRegistry


def register_all_providers(registry: ProviderRegistry) -> None:
    """Register all available providers to the given registry instance."""
    from .anthropic import AnthropicProvider  # noqa: TLE001
    registry.register("claude:", AnthropicProvider)

    from .gemini import GeminiProvider  # noqa: TLE001
    registry.register("gemini:", GeminiProvider)

    from .huggingface import HuggingFaceProvider  # noqa: TLE001
    registry.register("hf:", HuggingFaceProvider)

    from .lm_studio import LMStudioProvider  # noqa: TLE001
    registry.register("lmstudio:", LMStudioProvider)  # alias used by provider_catalog UI

    from .ollama import OllamaProvider  # noqa: TLE001
    registry.register("ollama:", OllamaProvider)

    from .openai import OpenAIProvider  # noqa: TLE001
    registry.register("openai:", OpenAIProvider)  # Default for gpt-* models
    registry.register("groq:", OpenAIProvider)  # Groq uses same provider but with GROQ_API_KEY


__all__ = [
    "ChatMessage",
    "CM",
    "KeyMissingError",
    "Provider",
    "RAGError",
    "UnsupportedModelError",
    "ProviderRegistry",
    "register_all_providers",
]
