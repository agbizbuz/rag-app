"""Tests for src/ragapp/config_provider.py and ragapp.config."""

import os

import pytest


def _set_all_keys(monkeypatch):
    """Set all known API keys."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-123")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-456")
    monkeypatch.setenv("GOOGLE_API_KEY", "goo-gle-789")
    monkeypatch.setenv("GROQ_API_KEY", "groq-key-012")
    monkeypatch.setenv("HUGGINGFACE_API_KEY", "hf-key-345")


def _clear_all_keys(monkeypatch):
    """Clear all known API keys."""
    for key in (
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GOOGLE_API_KEY",
        "GROQ_API_KEY",
        "HUGGINGFACE_API_KEY",
    ):
        monkeypatch.delenv(key, raising=False)


class TestSettings:
    """Tests for ragapp.config.Settings."""

    def test_settings_defaults(self, monkeypatch):
        _clear_all_keys(monkeypatch)
        from ragapp.config import Settings

        s = Settings()
        assert s.openai_api_key == ""
        assert s.anthropic_api_key == ""
        assert s.google_api_key == ""
        assert s.groq_api_key == ""
        assert s.huggingface_api_key == ""
        assert s.db_path == "./chroma_db"
        assert s.collection_name == "my_rag_collection"
        assert s.default_llm == "gpt-4o-mini"
        assert s.ollama_base_url == "http://localhost:11434"
        assert s.lm_studio_base_url == "http://localhost:1234"
        assert s.llm_temperature == 0.2
        assert s.llm_max_tokens == 1024
        assert s.max_file_size_bytes == 50 * 1024 * 1024

    def test_settings_from_env(self, monkeypatch):
        _clear_all_keys(monkeypatch)
        monkeypatch.setenv("CHROMA_DB_PATH", "/custom/path")
        monkeypatch.setenv("COLLECTION_NAME", "my_custom_collection")
        monkeypatch.setenv("DEFAULT_LLM", "claude-3-opus-20240229")
        monkeypatch.setenv("LLM_TEMPERATURE", "0.7")
        monkeypatch.setenv("LLM_MAX_TOKENS", "2048")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")

        from ragapp.config import Settings

        s = Settings()
        assert s.db_path == "/custom/path"
        assert s.collection_name == "my_custom_collection"
        assert s.default_llm == "claude-3-opus-20240229"
        assert s.llm_temperature == 0.7
        assert s.llm_max_tokens == 2048
        assert s.openai_api_key == "sk-test"


class TestConfigProvider:
    """Tests for ragapp.config_provider.ConfigProvider."""

    def test_singleton_returns_instance(self):
        from ragapp.config_provider import get_config, ConfigProvider

        cfg = get_config()
        assert isinstance(cfg, ConfigProvider)

    def test_singleton_reuses_instance(self):
        from ragapp.config_provider import get_config

        cfg1 = get_config()
        cfg2 = get_config()
        assert cfg1 is cfg2

    def test_default_values_via_config_provider(self):
        from ragapp.config_provider import ConfigProvider

        cfg = ConfigProvider()
        assert cfg.llm_temperature == 0.2
        assert cfg.db_path == "./chroma_db"
        assert cfg.collection_name == "my_rag_collection"
        assert cfg.default_llm == "gpt-4o-mini"
        assert cfg.llm_max_tokens == 1024

    def test_key_getters_openai(self, monkeypatch):
        _set_all_keys(monkeypatch)
        from ragapp.config_provider import ConfigProvider

        cfg = ConfigProvider()
        assert cfg.get_openai_key() == "sk-openai-123"

    def test_key_getters_anthropic(self, monkeypatch):
        _set_all_keys(monkeypatch)
        from ragapp.config_provider import ConfigProvider

        cfg = ConfigProvider()
        assert cfg.get_anthropic_key() == "sk-ant-456"

    def test_key_getters_gemini(self, monkeypatch):
        _set_all_keys(monkeypatch)
        from ragapp.config_provider import ConfigProvider

        cfg = ConfigProvider()
        assert cfg.get_gemini_key() == "goo-gle-789"

    def test_key_getters_groq(self, monkeypatch):
        _set_all_keys(monkeypatch)
        from ragapp.config_provider import ConfigProvider

        cfg = ConfigProvider()
        assert cfg.get_groq_key() == "groq-key-012"

    def test_key_getters_missing(self, monkeypatch):
        _clear_all_keys(monkeypatch)
        from ragapp.config_provider import ConfigProvider

        cfg = ConfigProvider()
        assert cfg.get_openai_key() is None
        assert cfg.get_anthropic_key() is None
        assert cfg.get_gemini_key() is None
        assert cfg.get_groq_key() is None

    def test_config_provider_with_mock_settings(self):
        """ConfigProvider accepts a mock settings object."""
        from ragapp.config_provider import ConfigProvider, _MockSettings

        cfg = ConfigProvider(_MockSettings())
        assert cfg.db_path == "./chroma_db"
        assert cfg.llm_temperature == 0.2


class TestEmbeddingFunction:
    """Tests for ragapp.core.embedding_function.create_embedding_function."""

    def test_no_openai_key_returns_none(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        from ragapp.core.embedding_function import create_embedding_function

        result = create_embedding_function()
        assert result is None

    def test_with_openai_key_calls_factory(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
        from unittest.mock import patch

        with patch(
            "chromadb.utils.embedding_functions.OpenAIEmbeddingFunction"
        ) as MockEF:
            MockEF.return_value = "mock_ef"
            from ragapp.core.embedding_function import create_embedding_function

            result = create_embedding_function()
            assert result == "mock_ef"
            MockEF.assert_called_once_with(
                api_key="sk-test-key", model_name="text-embedding-3-small"
            )
