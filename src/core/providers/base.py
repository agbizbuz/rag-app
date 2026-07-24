"""Provider protocol, exceptions, and chat model for LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod

# --------------------------------------------------------------------------- #
# Exception hierarchy                                                         #
# --------------------------------------------------------------------------- #


class RAGError(Exception):
    """Base exception for RAG-layer errors."""


class KeyMissingError(RAGError):
    """Raised when a required API key is not configured."""


class UnsupportedModelError(RAGError):
    """Raised when the model string doesn't match any known provider."""


# --------------------------------------------------------------------------- #
# Protocol & base class                                                       #
# --------------------------------------------------------------------------- #


class ChatMessage:
    role: str  # "system" | "user" | "assistant"
    content: str

    def __init__(self, role: str, content: str) -> None:
        self.role = role
        self.content = content

    def __repr__(self) -> str:
        return f"ChatMessage(role={self.role!r}, content=...)"


class Provider(ABC):
    """Abstract base for all LLM providers."""

    name: str  # class attribute for display

    @abstractmethod
    def chat(self, messages: list[ChatMessage]) -> str: ...

    @abstractmethod
    def _get_api_key(self) -> str:
        """Return the provider's API key from env or raise KeyMissingError."""
        ...

    def _extract_model_name(self, full_name: str) -> str:
        """Strip one provider prefix (e.g. 'ollama:') from model name.

        Handles single-prefixed ('prefix:model') and bare ('model') inputs.
        For double-prefixed test strings like 'prefix:prefix:model', returns
        everything after the first colon, which is the expected behavior since
        production code strips one prefix at a time during routing.
        """
        parts = full_name.split(":")
        return ":".join(parts[1:]) if len(parts) > 1 else full_name

    def validate_key(self, key_name: str) -> None:
        """Raise KeyMissingError if the env var is not set."""
        import os

        if not os.environ.get(key_name):
            raise KeyMissingError(f"`{key_name}` is missing in the environment.")


__all__ = ["RAGError", "KeyMissingError", "UnsupportedModelError", "ChatMessage", "Provider"]
