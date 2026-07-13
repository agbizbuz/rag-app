"""Tests for src/ragapp/config_provider.py and config."""


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
    """Tests for config.Settings."""

    def test_settings_defaults(self, monkeypatch):
        _clear_all_keys(monkeypatch)
        from config import Settings

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
        assert s.chunk_size == 1000
        assert s.n_results == 3
        assert "research assistant" in s.system_prompt
        assert s.embedding_model == "text-embedding-3-small"
        assert s.discovery_timeout == 3

    def test_settings_from_env(self, monkeypatch):
        _clear_all_keys(monkeypatch)
        monkeypatch.setenv("CHROMA_DB_PATH", "/custom/path")
        monkeypatch.setenv("COLLECTION_NAME", "my_custom_collection")
        monkeypatch.setenv("DEFAULT_LLM", "claude-3-opus-20240229")
        monkeypatch.setenv("LLM_TEMPERATURE", "0.7")
        monkeypatch.setenv("LLM_MAX_TOKENS", "2048")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")

        from config import Settings

        s = Settings()
        assert s.db_path == "/custom/path"
        assert s.collection_name == "my_custom_collection"
        assert s.default_llm == "claude-3-opus-20240229"
        assert s.llm_temperature == 0.7
        assert s.llm_max_tokens == 2048
        assert s.openai_api_key == "sk-test"


class TestConfigProvider:
    """Tests for config_provider.ConfigProvider."""

    def test_singleton_returns_instance(self):
        from config_provider import ConfigProvider, get_config

        cfg = get_config()
        assert isinstance(cfg, ConfigProvider)

    def test_singleton_reuses_instance(self):
        from config_provider import get_config

        cfg1 = get_config()
        cfg2 = get_config()
        assert cfg1 is cfg2

    def test_default_values_via_config_provider(self):
        from config_provider import ConfigProvider

        cfg = ConfigProvider()
        assert cfg.llm_temperature == 0.2
        assert cfg.db_path == "./chroma_db"
        assert cfg.collection_name == "my_rag_collection"
        assert cfg.default_llm == "gpt-4o-mini"
        assert cfg.llm_max_tokens == 1024

    def test_key_getters_openai(self, monkeypatch):
        _set_all_keys(monkeypatch)
        from config_provider import ConfigProvider

        cfg = ConfigProvider()
        assert cfg.get_openai_key() == "sk-openai-123"

    def test_key_getters_anthropic(self, monkeypatch):
        _set_all_keys(monkeypatch)
        from config_provider import ConfigProvider

        cfg = ConfigProvider()
        assert cfg.get_anthropic_key() == "sk-ant-456"

    def test_key_getters_gemini(self, monkeypatch):
        _set_all_keys(monkeypatch)
        from config_provider import ConfigProvider

        cfg = ConfigProvider()
        assert cfg.get_gemini_key() == "goo-gle-789"

    def test_key_getters_groq(self, monkeypatch):
        _set_all_keys(monkeypatch)
        from config_provider import ConfigProvider

        cfg = ConfigProvider()
        assert cfg.get_groq_key() == "groq-key-012"

    def test_key_getters_missing(self, monkeypatch):
        _clear_all_keys(monkeypatch)
        from config_provider import ConfigProvider

        cfg = ConfigProvider()
        assert cfg.get_openai_key() is None
        assert cfg.get_anthropic_key() is None
        assert cfg.get_gemini_key() is None
        assert cfg.get_groq_key() is None

    def test_config_provider_with_mock_settings(self):
        """ConfigProvider accepts a mock settings object."""
        from config_provider import ConfigProvider, _MockSettings

        cfg = ConfigProvider(_MockSettings())
        assert cfg.db_path == "./chroma_db"
        assert cfg.llm_temperature == 0.2

    def test_system_prompt_returns_default_without_session_key(self):
        """ConfigProvider.system_prompt returns Settings default when no session override."""
        from config_provider import ConfigProvider, _MockSettings

        cfg = ConfigProvider(_MockSettings())
        expected = (
            "You are a highly capable research assistant. Answer the user's query "
            "strictly based on the provided context. If the context does not contain "
            "sufficient information to answer the question, respectfully state that "
            "the information is not found in the documents. Provide the answer clearly "
            "and concisely."
        )
        assert cfg.system_prompt == expected

    def test_system_prompt_session_override(self):
        """Session-state override beats Settings default for system_prompt."""
        from config_provider import ConfigProvider, _MockSettings

        # Stub out session state with a custom prompt value
        fake_state = {"_system_prompt": "Be concise and answer in one sentence."}

        def mock_get_session_value(self, key: str, default):
            if key in fake_state and fake_state[key] is not None:
                return fake_state[key]
            return default

        real_method = ConfigProvider._get_session_value
        try:
            ConfigProvider._get_session_value = mock_get_session_value
            cfg = ConfigProvider(_MockSettings())
            assert cfg.system_prompt == "Be concise and answer in one sentence.", (
                f"Session-state override failed: got {cfg.system_prompt!r}"
            )
        finally:
            ConfigProvider._get_session_value = real_method

    def test_system_prompt_session_none_falls_to_default(self):
        """None session value falls back to Settings default."""
        from config_provider import ConfigProvider, _MockSettings

        fake_state = {"_system_prompt": None}  # key present but None should fall through

        def mock_get_session_value(self, key: str, default):
            if key in fake_state and fake_state[key] is not None:
                return fake_state[key]
            return default

        real_method = ConfigProvider._get_session_value
        try:
            ConfigProvider._get_session_value = mock_get_session_value
            cfg = ConfigProvider(_MockSettings())
            expected = (
                "You are a highly capable research assistant. Answer the user's query "
                "strictly based on the provided context. If the context does not contain "
                "sufficient information to answer the question, respectfully state that "
                "the information is not found in the documents. Provide the answer clearly "
                "and concisely."
            )
            assert cfg.system_prompt == expected, f"Expected default when session-state None: got {cfg.system_prompt!r}"
        finally:
            ConfigProvider._get_session_value = real_method


class TestEmbeddingFunction:
    """Tests for core.embedding_function.create_embedding_function."""

    def test_no_openai_key_returns_none(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        from core.embedding_function import create_embedding_function

        result = create_embedding_function()
        assert result is None

    def test_with_openai_key_calls_factory(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
        from unittest.mock import patch

        with patch("chromadb.utils.embedding_functions.OpenAIEmbeddingFunction") as MockEF:
            MockEF.return_value = "mock_ef"
            from core.embedding_function import create_embedding_function

            result = create_embedding_function()
            assert result == "mock_ef"
            MockEF.assert_called_once_with(api_key="sk-test-key", model_name="text-embedding-3-small")
