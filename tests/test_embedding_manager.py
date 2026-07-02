"""Tests for src/ragapp/core/embedding_manager.py."""

from unittest.mock import MagicMock, patch

from ragapp.core.embedding_manager import EmbeddingManager


class TestEmbeddingManager:
    """Tests for EmbeddingManager."""

    def test_init_default(self):
        manager = EmbeddingManager()
        assert manager._config is not None

    def test_init_custom_config(self):
        cfg = MagicMock()
        manager = EmbeddingManager(config_provider=cfg)
        assert manager._config == cfg

    def test_get_embedding_function_no_key(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        manager = EmbeddingManager()
        assert manager.get_embedding_function() is None
        assert not manager.is_openai

    def test_get_embedding_function_with_key(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
        cfg = MagicMock()
        cfg.embedding_model = "text-embedding-3-small"
        manager = EmbeddingManager(config_provider=cfg)

        with patch("chromadb.utils.embedding_functions.OpenAIEmbeddingFunction") as MockEF:
            mock_inst = MagicMock()
            MockEF.return_value = mock_inst

            ef = manager.get_embedding_function()
            assert ef == mock_inst
            MockEF.assert_called_once_with(
                api_key="test-key-123",
                model_name="text-embedding-3-small"
            )
            assert manager.is_openai
