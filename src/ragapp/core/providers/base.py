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
    def chat(self, messages: list[ChatMessage], temperature: float = 0.0) -> str: ...

    def validate_key(self, key_name: str) -> None:
        """Raise KeyMissingError if the env var is not set."""
        import os

        if not os.environ.get(key_name):
            raise KeyMissingError(f"`{key_name}` is missing in the environment.")


__all__ = ["RAGError", "KeyMissingError", "UnsupportedModelError", "ChatMessage", "Provider"]
