"""Tests for src/ragapp/core/llm.py provider routing logic."""

from unittest.mock import MagicMock, patch



class TestProviderRouting:
    """Verify that get_llm_response routes to the correct provider based on model prefix."""

    def _setup_key(self, monkeypatch, key, value):
        monkeypatch.setenv(key, value)

    def test_groq_routing(self, monkeypatch):
        self._setup_key(monkeypatch, "GROQ_API_KEY", "test-groq-key")
        from src.ragapp.core.llm import get_llm_response

        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock(message=MagicMock(content="groq answer"))]

        with patch("src.ragapp.core.llm.OpenAI") as MockOpenAI:
            MockOpenAI.return_value.chat.completions.create.return_value = mock_resp
            result = get_llm_response("ctx", "groq:llama-3.1-8b-instant")
            assert result == "groq answer"
            MockOpenAI.assert_called_once_with(
                api_key="test-groq-key",
                base_url="https://api.groq.com/openai/v1",
            )

    def test_groq_missing_key(self, monkeypatch):
        """Without GROQ_API_KEY, should return error string."""
        from src.ragapp.core.llm import get_llm_response
        monkeypatch.delenv("GROQ_API_KEY", raising=False)

        result = get_llm_response("ctx", "groq:llama-3.1-8b-instant")
        assert "missing" in result.lower() or result.startswith("\u26a0\ufe0f")

    def test_ollama_routing(self):
        from src.ragapp.core.llm import get_llm_response

        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock(message=MagicMock(content="ollama answer"))]

        with patch("src.ragapp.core.llm.OpenAI") as MockOpenAI:
            MockOpenAI.return_value.chat.completions.create.return_value = mock_resp
            result = get_llm_response("ctx", "ollama:llama3.1")
            assert result == "ollama answer"
            args, kwargs = MockOpenAI.call_args
            assert kwargs["api_key"] == "ollama"
            assert "localhost" in kwargs["base_url"]

    def test_lm_studio_routing(self):
        from src.ragapp.core.llm import get_llm_response

        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock(message=MagicMock(content="lmstudio answer"))]

        with patch("src.ragapp.core.llm.OpenAI") as MockOpenAI:
            MockOpenAI.return_value.chat.completions.create.return_value = mock_resp
            result = get_llm_response("ctx", "lmstudio:llama-3.1-instruct")
            assert result == "lmstudio answer"

    def test_lm_studio_alias_routing(self):
        from src.ragapp.core.llm import get_llm_response

        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock(message=MagicMock(content="lm-studio alias"))]

        with patch("src.ragapp.core.llm.OpenAI") as MockOpenAI:
            MockOpenAI.return_value.chat.completions.create.return_value = mock_resp
            result = get_llm_response("ctx", "lm-studio:llama-3.1-instruct")
            assert result == "lm-studio alias"

    def test_openai_routing(self, monkeypatch):
        self._setup_key(monkeypatch, "OPENAI_API_KEY", "test-openai-key")
        from src.ragapp.core.llm import get_llm_response

        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock(message=MagicMock(content="openai answer"))]

        with patch("src.ragapp.core.llm.OpenAI") as MockOpenAI:
            MockOpenAI.return_value.chat.completions.create.return_value = mock_resp
            result = get_llm_response("ctx", "gpt-4o-mini")
            assert result == "openai answer"

    def test_anthropic_routing(self, monkeypatch):
        self._setup_key(monkeypatch, "ANTHROPIC_API_KEY", "test-anthropic-key")
        from src.ragapp.core.llm import get_llm_response

        mock_resp = MagicMock()
        mock_resp.content = [MagicMock(text="claude answer")]

        with patch("src.ragapp.core.llm.Anthropic") as MockAnthropic:
            MockAnthropic.return_value.messages.create.return_value = mock_resp
            result = get_llm_response("ctx", "claude-3-haiku-20240307")
            assert result == "claude answer"

    def test_gemini_routing(self, monkeypatch):
        self._setup_key(monkeypatch, "GOOGLE_API_KEY", "test-gemini-key")
        # Patch google.generativeai globally so the import inside llm.py finds our mock
        mock_genai = MagicMock()
        mock_model_class = MagicMock()
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value = MagicMock(text="gemini answer")
        mock_model_class.return_value = mock_model_instance
        mock_genai.GenerativeModel = mock_model_class

        with patch.dict("sys.modules", {"google.generativeai": mock_genai}):
            from src.ragapp.core.llm import get_llm_response

            result = get_llm_response("ctx", "gemini-pro")
            assert result == "gemini answer"

    def test_huggingface_routing(self, monkeypatch):
        self._setup_key(monkeypatch, "HUGGINGFACE_API_KEY", "test-hf-key")
        # Patch requests globally so the import inside llm.py finds our mock
        mock_requests = MagicMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = [{"generated_text": "hf answer"}]
        mock_resp.raise_for_status = MagicMock()
        mock_requests.post.return_value = mock_resp

        with patch.dict("sys.modules", {"requests": mock_requests}):
            from src.ragapp.core.llm import get_llm_response

            result = get_llm_response("ctx", "meta-llama/Llama-3.3-70B-Instruct")
            assert result == "hf answer"

    def test_unsupported_model(self):
        from src.ragapp.core.llm import get_llm_response

        result = get_llm_response("ctx", "unsupported-model")
        assert "Unsupported" in result or result.startswith("\u26a0\ufe0f")
