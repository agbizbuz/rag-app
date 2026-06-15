"""Tests for src/ragapp/core/providers/ollama.py."""

from unittest.mock import MagicMock, patch


class TestOllamaProvider:
    """Tests for ragapp.core.providers.ollama.OllamaProvider."""

    def test_init_strips_ollama_prefix(self):
        from ragapp.core.providers.ollama import OllamaProvider

        p = OllamaProvider("ollama:llama3.1")
        assert p._model == "llama3.1"

    def test_init_case_insensitive_strip(self):
        from ragapp.core.providers.ollama import OllamaProvider

        p = OllamaProvider("OLLAMA:Llama-3")
        assert p._model == "Llama-3"

    def test_init_uses_default_base_url(self, monkeypatch):
        monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
        from ragapp.core.providers.ollama import OllamaProvider

        p = OllamaProvider("ollama:llama3.1")
        assert p._base_url == "http://localhost:11434/v1"

    def test_init_appends_v1_to_base_url(self, monkeypatch):
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://custom:11434")
        from ragapp.core.providers.ollama import OllamaProvider

        p = OllamaProvider("ollama:llama3.1")
        assert p._base_url == "http://custom:11434/v1"

    def test_init_base_url_already_has_v1(self, monkeypatch):
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        from ragapp.core.providers.ollama import OllamaProvider

        p = OllamaProvider("ollama:llama3.1")
        assert p._base_url == "http://localhost:11434/v1"

    def test_chat_with_mock(self):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Ollama reply"))]

        with patch(
            "ragapp.core.providers.ollama._get_openai_client"
        ) as MockGetClient:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            MockGetClient.return_value = MagicMock(return_value=mock_client)

            from ragapp.core.providers.ollama import OllamaProvider

            p = OllamaProvider("ollama:llama3.1")
            msgs = [MagicMock(role="user", content="hello")]
            result = p.chat(msgs)
            assert result == "Ollama reply"


class TestOllamaStripPattern:
    """Tests for the strip_pattern regex."""

    def test_replaces_ollama_prefix(self):
        from ragapp.core.providers.ollama import strip_pattern

        result = strip_pattern.sub("", "ollama:test-model")
        assert result == "test-model"

    def test_case_insensitive_strip(self):
        from ragapp.core.providers.ollama import strip_pattern

        result = strip_pattern.sub("", "OLLAMA:model")
        assert result == "model"


class TestOllamaGetClient:
    """Tests for _get_openai_client function."""

    def test_caching(self):
        from ragapp.core.providers.ollama import _get_openai_client

        c1 = _get_openai_client()
        c2 = _get_openai_client()
        assert hasattr(_get_openai_client, "_cached")
