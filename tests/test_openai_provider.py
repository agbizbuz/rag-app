"""Tests for src/ragapp/core/providers/openai.py."""

from unittest.mock import MagicMock, patch


class TestOpenAIProvider:
    """Tests for core.providers.openai.OpenAIProvider."""

    def test_init_sets_attributes(self):
        from core.providers.openai import OpenAIProvider

        p = OpenAIProvider("gpt-4o-mini", temperature=0.5, max_tokens=2048)
        assert p._model == "gpt-4o-mini"
        assert p.name == "OpenAI"
        assert p.api_key_env == "OPENAI_API_KEY"
        assert p._temperature == 0.5
        assert p._max_tokens == 2048

    def test_init_groq_model_resolves_key(self):
        from core.providers.openai import OpenAIProvider

        p = OpenAIProvider("groq:llama-3.1-8b-instant")
        assert p.api_key_env == "GROQ_API_KEY"

    def test_chat_with_key(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-123")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Hello world"))]

        with patch("core.providers.openai_compat.get_openai_client") as MockGetClient:
            mock_client_class = MagicMock(return_value=MagicMock(
                chat=MagicMock(completions=MagicMock(create=MagicMock(return_value=mock_response)))
            ))
            MockGetClient.return_value = mock_client_class

            from core.providers.openai import OpenAIProvider

            p = OpenAIProvider("gpt-4o-mini")
            msgs = [MagicMock(role="user", content="hello")]
            result = p.chat(msgs)
            assert result == "Hello world"
            assert mock_client_class.called
            call_kwargs = mock_client_class.call_args[1]
            assert call_kwargs["api_key"] == "sk-test-123"
            assert call_kwargs["base_url"] is not None

    def test_chat_returns_empty_on_none_content(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-123")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=None))]

        with patch("core.providers.openai_compat.get_openai_client") as MockGetClient:
            mock_client_class = MagicMock(return_value=MagicMock(
                chat=MagicMock(completions=MagicMock(create=MagicMock(return_value=mock_response)))
            ))
            MockGetClient.return_value = mock_client_class

            from core.providers.openai import OpenAIProvider

            p = OpenAIProvider("gpt-4o-mini")
            msgs = [MagicMock(role="user", content="hello")]
            result = p.chat(msgs)
            assert result == ""

    def test_chat_raises_key_missing(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        with patch("core.providers.openai_compat.get_openai_client"):
            from core.providers.openai import OpenAIProvider

            p = OpenAIProvider("gpt-4o-mini")
            msgs = [MagicMock(role="user", content="hello")]
            try:
                p.chat(msgs)
                assert False, "Should have raised KeyMissingError"
            except Exception as e:
                from core.providers.base import KeyMissingError

                assert isinstance(e, KeyMissingError)
                assert "OPENAI_API_KEY" in str(e)

    def test_chat_groq_variant(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "groq-test-key")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Groq reply"))]

        with patch("core.providers.openai_compat.get_openai_client") as MockGetClient:
            mock_client_class = MagicMock(return_value=MagicMock(
                chat=MagicMock(completions=MagicMock(create=MagicMock(return_value=mock_response)))
            ))
            MockGetClient.return_value = mock_client_class

            from core.providers.openai import OpenAIProvider

            p = OpenAIProvider("groq:llama-3.1-8b-instant")
            msgs = [MagicMock(role="user", content="hello")]
            result = p.chat(msgs)
            assert result == "Groq reply"
            call_kwargs = mock_client_class.call_args[1]
            assert call_kwargs["api_key"] == "groq-test-key"

    def test_get_openai_client_returns_class(self):
        """get_openai_client returns the OpenAI class."""
        from core.providers._openai_compat import get_openai_client

        result = get_openai_client()
        assert hasattr(result, "__name__") or callable(result)


class TestOpenAICompatProvider:
    """Tests for base OpenAI compat provider (used by Ollama/LM Studio)."""

    def test_default_chat_messages_passes_through(self):
        from core.providers.openai_compat import OpenAICompatProvider

        # Use a minimal concrete subclass to instantiate the abstract class indirectly
        class Fake(OpenAICompatProvider):
            name = "Fake"
            api_key_env = "FAKE_API_KEY"

            def __init__(self, model="fake"):
                super().__init__(model)
                self._base_url = "https://example.com/v1"

        p = Fake("gpt-4o-mini")
        msgs = [MagicMock(role="system", content="You are helpful"), MagicMock(role="user", content="hi")]
        result = p.chat_messages(msgs)
        # Default passes through ALL messages including system role (no stripping)
        assert len(result) == 2

    def test_chat_uses_get_openai_client(self, monkeypatch):
        """chat() calls get_openai_client which returns a class to instantiate."""
        from core.providers.openai_compat import OpenAICompatProvider

        class Fake(OpenAICompatProvider):
            name = "Fake"
            api_key_env = "FAKE_API_KEY"

            def __init__(self, model="fake"):
                super().__init__(model)
                self._base_url = "https://example.com/v1"

        monkeypatch.setenv("FAKE_API_KEY", "fake-key")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="ok"))]

        with patch("core.providers.openai_compat.get_openai_client") as MockGetClient:
            MockGetClient.return_value = MagicMock(return_value=MagicMock(
                chat=MagicMock(completions=MagicMock(create=MagicMock(return_value=mock_response)))
            ))

            p = Fake("fake-model")
            result = p.chat([MagicMock(role="user", content="hi")])
            assert result == "ok"


__all__ = ["TestOpenAIProvider"]
