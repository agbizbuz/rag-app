"""Tests for src/ragapp/core/providers/openai.py."""

from unittest.mock import MagicMock, patch


class TestOpenAIProvider:
    """Tests for ragapp.core.providers.openai.OpenAIProvider."""

    def test_init_sets_attributes(self):
        from ragapp.core.providers.openai import OpenAIProvider

        p = OpenAIProvider("gpt-4o", temperature=0.5, max_tokens=2048)
        assert p._model == "gpt-4o"
        assert p.name == "OpenAI"
        assert p._api_key_env == "OPENAI_API_KEY"
        assert p._temperature == 0.5
        assert p._max_tokens == 2048

    def test_init_groq_model_resolves_key(self):
        from ragapp.core.providers.openai import OpenAIProvider

        p = OpenAIProvider("groq:llama-3.1-8b-instant")
        assert p._api_key_env == "GROQ_API_KEY"

    def test_chat_with_key(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-123")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Hello world"))]

        with patch(
            "ragapp.core.providers.openai._get_openai_client"
        ) as MockGetClient:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            MockGetClient.return_value = MagicMock(return_value=mock_client)

            from ragapp.core.providers.openai import OpenAIProvider

            p = OpenAIProvider("gpt-4o-mini")
            msgs = [MagicMock(role="user", content="hello")]
            result = p.chat(msgs)
            assert result == "Hello world"
            mock_client.chat.completions.create.assert_called_once()
            call_kwargs = mock_client.chat.completions.create.call_args[1]
            assert call_kwargs["model"] == "gpt-4o-mini"

    def test_chat_returns_empty_on_none_content(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-123")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=None))]

        with patch(
            "ragapp.core.providers.openai._get_openai_client"
        ) as MockGetClient:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            MockGetClient.return_value = MagicMock(return_value=mock_client)

            from ragapp.core.providers.openai import OpenAIProvider

            p = OpenAIProvider("gpt-4o-mini")
            msgs = [MagicMock(role="user", content="hello")]
            result = p.chat(msgs)
            assert result == ""

    def test_chat_raises_key_missing(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        from ragapp.core.providers.base import KeyMissingError as KME
        from ragapp.core.providers.openai import OpenAIProvider

        p = OpenAIProvider("gpt-4o-mini")
        msgs = [MagicMock(role="user", content="hello")]
        try:
            p.chat(msgs)
            assert False, "Should have raised KeyMissingError"
        except KME as e:
            assert "OPENAI_API_KEY" in str(e)

    def test_chat_groq_variant(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "groq-test-key")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Groq reply"))]

        with patch(
            "ragapp.core.providers.openai._get_openai_client"
        ) as MockGetClient:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            MockGetClient.return_value = MagicMock(return_value=mock_client)

            from ragapp.core.providers.openai import OpenAIProvider

            p = OpenAIProvider("groq:llama-3.1")
            msgs = [MagicMock(role="user", content="hello")]
            result = p.chat(msgs)
            assert result == "Groq reply"

    def test_get_openai_client_returns_class(self):
        """_get_openai_client returns the OpenAI class."""
        from ragapp.core.providers.openai import _get_openai_client

        result = _get_openai_client()
        assert hasattr(result, "__name__") or callable(result)


class TestOpenAISetter:
    """Tests for the test-only _set_openai setter."""

    def test_setter_patches_class(self):
        from ragapp.core.providers import openai as openai_mod

        MockClass = MagicMock()
        openai_mod._set_openai(MockClass)
        assert openai_mod.OpenAI is MockClass
        assert openai_mod._setter_called is True
