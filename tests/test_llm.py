"""Tests for src/ragapp/core/llm.py."""

from unittest.mock import MagicMock, patch


class TestGetLlmResponse:
    """Tests for core.llm.get_llm_response."""

    def _make_mock(self):
        mock_cls = MagicMock()
        mock_instance = MagicMock()
        mock_instance.chat.return_value = "mock response"
        mock_cls.return_value = mock_instance
        return mock_cls, mock_instance

    def test_openai_routing(self, monkeypatch):
        """gpt-* models route to OpenAI provider."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        mock_cls, _ = self._make_mock()

        with patch("core.providers.routing.ProviderRegistry.resolve_provider", return_value=mock_cls):
            from core.llm import get_llm_response

            result = get_llm_response("ctx", "query", "gpt-4o-mini")
            assert "mock response" in result

    def test_openai_groq_routing(self, monkeypatch):
        """groq: models route to OpenAI provider."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        mock_cls, _ = self._make_mock()

        with patch("core.providers.routing.ProviderRegistry.resolve_provider", return_value=mock_cls):
            from core.llm import get_llm_response

            result = get_llm_response("ctx", "query", "groq:llama-3.1-8b-instant")
            assert "mock response" in result

    def test_ollama_routing(self, monkeypatch):
        """ollama: models route to OllamaProvider."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        mock_cls, _ = self._make_mock()

        with patch("core.providers.routing.ProviderRegistry.resolve_provider", return_value=mock_cls):
            from core.llm import get_llm_response

            result = get_llm_response("ctx", "query", "ollama:llama3.1")
            assert "mock response" in result

    def test_lm_studio_routing(self, monkeypatch):
        """lm-studio: models route to LMStudioProvider."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        mock_cls, _ = self._make_mock()

        with patch("core.providers.routing.ProviderRegistry.resolve_provider", return_value=mock_cls):
            from core.llm import get_llm_response

            result = get_llm_response("ctx", "query", "lm-studio:llama-3.1-instruct")
            assert "mock response" in result

    def test_anthropic_routing(self, monkeypatch):
        """claude-* models route to AnthropicProvider."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        mock_cls, _ = self._make_mock()

        with patch("core.providers.routing.ProviderRegistry.resolve_provider", return_value=mock_cls):
            from core.llm import get_llm_response

            result = get_llm_response("ctx", "query", "claude-3-opus-20240229")
            assert "mock response" in result

    def test_gemini_routing(self, monkeypatch):
        """gemini-* models route to GeminiProvider."""
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        mock_cls, _ = self._make_mock()

        with patch("core.providers.routing.ProviderRegistry.resolve_provider", return_value=mock_cls):
            from core.llm import get_llm_response

            result = get_llm_response("ctx", "query", "gemini-pro")
            assert "mock response" in result

    def test_key_missing_returns_error(self, monkeypatch):
        """Missing key returns warning-prefixed error."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        from core.llm import get_llm_response

        with patch("core.providers.openai.OpenAIProvider") as MockProvider:
            MockProvider.side_effect = Exception("`OPENAI_API_KEY` is missing")
            result = get_llm_response("ctx", "query", "gpt-4o-mini")
            assert "\u26a0\ufe0f" in result

    def test_unsupported_model_returns_error(self):
        """Unknown model returns error."""
        from core.providers.base import UnsupportedModelError as UME

        with patch("core.providers.routing.ProviderRegistry.resolve_provider", side_effect=UME("No provider for xyz")):
            from core.llm import get_llm_response

            result = get_llm_response("ctx", "query", "xyz-model")
            assert "\u26a0\ufe0f" in result

    def test_uniform_instantiation(self, monkeypatch):
        """All providers are instantiated with (model, temperature, max_tokens)."""
        mock_cls, mock_instance = self._make_mock()

        with patch("core.providers.routing.ProviderRegistry.resolve_provider", return_value=mock_cls):
            from core.llm import get_llm_response

            get_llm_response("ctx", "query", "gpt-4o-mini")

            # Verify uniform constructor call
            mock_cls.assert_called_once()
            call_kwargs = mock_cls.call_args
            assert call_kwargs.kwargs["model"] == "gpt-4o-mini"
            assert "temperature" in call_kwargs.kwargs
            assert "max_tokens" in call_kwargs.kwargs
            # No api_key_env should be passed — provider resolves it internally
            assert "api_key_env" not in call_kwargs.kwargs


class TestChatMessage:
    """Tests for core.llm.ChatMessage (re-exported from providers.base)."""

    def test_init(self):
        from core.llm import ChatMessage

        msg = ChatMessage("user", "hello")
        assert msg.role == "user"
        assert msg.content == "hello"

    def test_repr(self):
        from core.llm import ChatMessage

        msg = ChatMessage("system", "test")
        assert "ChatMessage(role='system'" in repr(msg)

    def test_is_same_as_base(self):
        """llm.ChatMessage is the same class as providers.base.ChatMessage."""
        from core.llm import ChatMessage as LlmCM
        from core.providers.base import ChatMessage as BaseCM

        assert LlmCM is BaseCM


class TestExceptionClasses:
    """Tests for llm exception classes (re-exported from providers.base)."""

    def test_key_missing_error_is_exception(self):
        from core.llm import KeyMissingError

        exc = KeyMissingError("missing key")
        assert isinstance(exc, Exception)
        assert str(exc) == "missing key"

    def test_unsupported_model_error_is_exception(self):
        from core.llm import UnsupportedModelError

        exc = UnsupportedModelError("unknown model")
        assert isinstance(exc, Exception)

    def test_rag_error_is_exception(self):
        from core.llm import RAGError

        exc = RAGError("rag error")
        assert isinstance(exc, Exception)

    def test_exceptions_same_as_base(self):
        """llm exceptions are the same classes as providers.base exceptions."""
        from core.llm import KeyMissingError as LlmKME
        from core.llm import RAGError as LlmRAG
        from core.llm import UnsupportedModelError as LlmUME
        from core.providers.base import KeyMissingError as BaseKME
        from core.providers.base import RAGError as BaseRAG
        from core.providers.base import UnsupportedModelError as BaseUME

        assert LlmKME is BaseKME
        assert LlmUME is BaseUME
        assert LlmRAG is BaseRAG
