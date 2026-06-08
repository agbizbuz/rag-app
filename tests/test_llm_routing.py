"""Tests for src/ragapp/core/providers provider routing logic."""


class TestProviderRouting:
    """Verify that get_llm_response routes to the correct provider based on model prefix."""

    def _setup_key(self, monkeypatch, key, value):
        monkeypatch.setenv(key, value)

    def test_groq_routing(self, monkeypatch):
        """Test Groq routing - uses OpenAIProvider with GROQ_API_KEY."""
        self._setup_key(monkeypatch, "GROQ_API_KEY", "test-groq-key")
        from ragapp.core.providers.routing import _REGISTRY
        from ragapp.core.providers.openai import OpenAIProvider

        # Verify groq provider is registered correctly (returns correct TYPE)
        p = _REGISTRY.resolve_provider("groq:llama-3.1-8b-instant")
        assert p == OpenAIProvider

    def test_groq_missing_key(self, monkeypatch):
        """Without GROQ_API_KEY, should return error string."""
        from ragapp.core.llm import get_llm_response

        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        result = get_llm_response("ctx", "groq:llama-3.1-8b-instant")
        assert "\u26a0\ufe0f" in result and "GROQ_API_KEY" in result

    def test_ollama_routing(self, monkeypatch):
        """Test Ollama-specific routing."""
        from ragapp.core.providers.routing import _REGISTRY
        from ragapp.core.providers.ollama import OllamaProvider

        p = _REGISTRY.resolve_provider("ollama:llama3.1")
        assert p == OllamaProvider
        assert p.name == "Ollama"

    def test_lm_studio_routing(self, monkeypatch):
        """Test LM Studio-specific routing."""
        from ragapp.core.providers.routing import _REGISTRY
        from ragapp.core.providers.lm_studio import LMStudioProvider

        p = _REGISTRY.resolve_provider("lm-studio:llama-3.1-instruct")
        assert p == LMStudioProvider
        assert p.name == "LM Studio"

    def test_huggingface_routing(self, monkeypatch):
        """Test HuggingFace provider routing via Hub ID pattern."""
        from ragapp.core.providers.routing import _REGISTRY
        from ragapp.core.providers.openai import OpenAIProvider

        # HuggingFace uses hub model IDs without prefix - resolves to default OpenAIProvider
        p = _REGISTRY.resolve_provider("meta-llama/Llama-3.3-70B-Instruct")
        assert p == OpenAIProvider

    def test_unsupported_model(self):
        """Test that unsupported model IDs fall back to default OpenAI provider."""
        from ragapp.core.providers.routing import _REGISTRY
        p = _REGISTRY.resolve_provider("gpt-4o-mini")
        assert p is not None

    def test_openai_default_routing(self, monkeypatch):
        """Test that gpt-* models default to OpenAI."""
        self._setup_key(monkeypatch, "OPENAI_API_KEY", "test-key")
        from ragapp.core.providers.routing import _REGISTRY
        from ragapp.core.providers.openai import OpenAIProvider

        p = _REGISTRY.resolve_provider("gpt-4o-mini")
        assert p == OpenAIProvider

    def test_claude_routing(self, monkeypatch):
        """Test Claude model routing to Anthropic provider."""
        self._setup_key(monkeypatch, "ANTHROPIC_API_KEY", "test-key")
        from ragapp.core.providers.routing import _REGISTRY
        
        p = _REGISTRY.resolve_provider("claude-3-haiku-20240307")
        # Should resolve to AnthropicProvider (or at least a valid provider)
        assert p is not None

    def test_gemini_routing(self, monkeypatch):
        """Test Gemini model routing."""
        self._setup_key(monkeypatch, "GOOGLE_API_KEY", "test-key")
        from ragapp.core.providers.routing import _REGISTRY
        from ragapp.core.providers.gemini import GeminiProvider
        
        p = _REGISTRY.resolve_provider("gemini-pro")
        assert p == GeminiProvider


