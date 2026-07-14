"""Configuration provider for explicit dependency injection."""

from __future__ import annotations

import os
from typing import Any


class _MockSettings:
    """Minimal mock settings for test compatibility."""

    llm_temperature = 0.2
    db_path = "./chroma_db"
    collection_name = "my_rag_collection"
    default_llm = "gpt-4o-mini"
    llm_max_tokens = 1024
    chunk_size = 1000
    n_results = 3
    system_prompt = (
        "You are a highly capable research assistant. "
        "Answer the user's query strictly based on the provided context. "
        "If the context does not contain sufficient information to answer "
        "the question, respectfully state that the information is not found in "
        "the documents. Provide the answer clearly and concisely."
    )
    embedding_model = "text-embedding-3-small"
    discovery_timeout = 3
    retrieval_mode = "hybrid"
    evaluation_log_path = "./evaluation_logs.json"


class ConfigProvider:
    """Wrapper around Settings for explicit dependency injection.

    Exposes configuration via typed methods/properties to eliminate direct global access.
    Falls back to _MockSettings when actual Settings are unavailable (testing).
    """

    def __init__(self, settings=None):  # noqa: ANN001
        """Initialize with optional Settings instance.

        Args:
            settings: Optional Settings instance from config. Defaults to mock.
        """
        if settings is not None:
            self._settings = settings
        else:
            try:
                from config import Settings

                self._settings = Settings()
            except ImportError:
                self._settings = _MockSettings()

    def _get_session_value(self, key: str, default: Any) -> Any:
        """Safely fetch a value from Streamlit's session state if running."""
        try:
            import streamlit as st

            if st.runtime.exists() and key in st.session_state:
                val = st.session_state[key]
                if val is not None:
                    return val
        except Exception:
            pass
        return default

    @property
    def llm_temperature(self) -> float:
        """Return the configured temperature (default 0.2)."""
        val = self._settings.llm_temperature
        return self._get_session_value("_temp_slider", val)

    @property
    def db_path(self) -> str:
        """Return the ChromaDB persistence path."""
        return self._settings.db_path

    @property
    def collection_name(self) -> str:
        """Return the vector store collection name."""
        return self._settings.collection_name

    @property
    def default_llm(self) -> str:
        """Return the default model identifier."""
        return self._settings.default_llm

    @property
    def llm_max_tokens(self) -> int:
        """Return max tokens for LLM responses."""
        return self._settings.llm_max_tokens

    @property
    def chunk_size(self) -> int:
        """Return target chunk size in characters for document parsing."""
        val = self._settings.chunk_size
        return self._get_session_value("_chunk_size", val)

    @property
    def n_results(self) -> int:
        """Return default number of results for vector search queries."""
        val = self._settings.n_results
        return self._get_session_value("_n_results", val)

    @property
    def system_prompt(self) -> str:
        """Return the system prompt for LLM conversations."""
        _default = (
            "You are a highly capable research assistant. "
            "Answer the user's query strictly based on the provided context. "
            "If the context does not contain sufficient information to answer "
            "the question, respectfully state that the information is not found in "
            "the documents. Provide the answer clearly and concisely."
        )
        val = getattr(self._settings, "system_prompt", _default)
        return self._get_session_value("_system_prompt", val)

    @property
    def embedding_model(self) -> str:
        """Return the OpenAI embedding model name."""
        return self._settings.embedding_model

    @property
    def discovery_timeout(self) -> int:
        """Return HTTP timeout in seconds for model discovery calls."""
        return self._settings.discovery_timeout

    @property
    def retrieval_mode(self) -> str:
        """Return the configured retrieval mode ('semantic', 'keyword', or 'hybrid')."""
        val = self._settings.retrieval_mode
        return self._get_session_value("_retrieval_mode", val)

    @property
    def evaluation_log_path(self) -> str:
        """Return the path to save evaluation logs."""
        return self._settings.evaluation_log_path

    def get_openai_key(self) -> str | None:
        """Return OpenAI API key if set."""
        return os.environ.get("OPENAI_API_KEY")

    def get_anthropic_key(self) -> str | None:
        """Return Anthropic API key if set."""
        return os.environ.get("ANTHROPIC_API_KEY")

    def get_gemini_key(self) -> str | None:
        """Return Google Gemini API key if set."""
        return os.environ.get("GOOGLE_API_KEY")

    def get_groq_key(self) -> str | None:
        """Return Groq API key if set."""
        return os.environ.get("GROQ_API_KEY")


# Singleton instance for use as a module-level utility (optional global fallback)
_config_provider_instance: ConfigProvider | None = None


def get_config() -> ConfigProvider:
    """Return the singleton ConfigProvider instance.

    Creates on first call if needed. For tests, you can override with:
        from config import Settings
        config_provider_instance = ConfigProvider(Settings())
    """
    global _config_provider_instance
    if _config_provider_instance is None:
        _config_provider_instance = ConfigProvider()
    return _config_provider_instance
