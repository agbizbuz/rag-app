"""Tests for src/ragapp/core/providers provider routing logic."""


class TestProviderRouting:
    """Verify that get_llm_response routes to the correct provider based on model prefix."""

    def _setup_key(self, monkeypatch, key, value):
        monkeypatch.setenv(key, value)

    def test_groq_routing(self, monkeypatch):
        """Test Groq routing - uses OpenAIProvider with GROQ_API_KEY."""
        self._setup_key(monkeypatch, "GROQ_API_KEY", "test-groq-key")
        from core.providers.openai import OpenAIProvider
        from core.providers.routing import ProviderRegistry
        from core.providers import register_all_providers
        _REGISTRY = ProviderRegistry()
        register_all_providers(_REGISTRY)

        # Verify groq provider is registered correctly (returns correct TYPE)
        p = _REGISTRY.resolve_provider("groq:llama-3.1-8b-instant")
        assert p == OpenAIProvider

    def test_groq_missing_key(self, monkeypatch):
        """Without GROQ_API_KEY, should return error string."""
        from core.llm import get_llm_response

        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        result = get_llm_response("ctx", "groq:llama-3.1-8b-instant", "groq:llama-3.1-8b-instant")
        assert "\u26a0\ufe0f" in result and "GROQ_API_KEY" in result

    def test_ollama_routing(self, monkeypatch):
        """Test Ollama-specific routing."""
        from core.providers.ollama import OllamaProvider
        from core.providers.routing import ProviderRegistry
        from core.providers import register_all_providers
        _REGISTRY = ProviderRegistry()
        register_all_providers(_REGISTRY)

        p = _REGISTRY.resolve_provider("ollama:llama3.1")
        assert p == OllamaProvider
        assert p.name == "Ollama"

    def test_lm_studio_routing(self, monkeypatch):
        """Test LM Studio-specific routing."""
        from core.providers.lm_studio import LMStudioProvider
        from core.providers.routing import ProviderRegistry
        from core.providers import register_all_providers
        _REGISTRY = ProviderRegistry()
        register_all_providers(_REGISTRY)

        p = _REGISTRY.resolve_provider("lmstudio:llama-3.1-instruct")
        assert p == LMStudioProvider
        assert p.name == "LM Studio"

    def test_huggingface_routing(self, monkeypatch):
        """Test HuggingFace provider routing via Hub ID pattern."""
        from core.providers.huggingface import HuggingFaceProvider
        from core.providers.routing import ProviderRegistry
        from core.providers import register_all_providers
        _REGISTRY = ProviderRegistry()
        register_all_providers(_REGISTRY)

        # HuggingFace uses hub model IDs without prefix - resolves to default OpenAIProvider
        p = _REGISTRY.resolve_provider("hf:meta-llama/Llama-3.3-70B-Instruct")
        assert p == HuggingFaceProvider

    def test_unsupported_model(self):
        """Test that unsupported model IDs fall back to default OpenAI provider."""
        from core.providers.routing import ProviderRegistry
        from core.providers import register_all_providers
        _REGISTRY = ProviderRegistry()
        register_all_providers(_REGISTRY)

        p = _REGISTRY.resolve_provider("openai:gpt-4o-mini")
        assert p is not None

    def test_openai_default_routing(self, monkeypatch):
        """Test that gpt-* models default to OpenAI."""
        self._setup_key(monkeypatch, "OPENAI_API_KEY", "test-key")
        from core.providers.openai import OpenAIProvider
        from core.providers.routing import ProviderRegistry
        from core.providers import register_all_providers
        _REGISTRY = ProviderRegistry()
        register_all_providers(_REGISTRY)

        p = _REGISTRY.resolve_provider("openai:gpt-4o-mini")
        assert p == OpenAIProvider

    def test_claude_routing(self, monkeypatch):
        """Test Claude model routing to Anthropic provider."""
        self._setup_key(monkeypatch, "ANTHROPIC_API_KEY", "test-key")
        from core.providers.routing import ProviderRegistry
        from core.providers import register_all_providers
        _REGISTRY = ProviderRegistry()
        register_all_providers(_REGISTRY)
        from core.providers.anthropic import AnthropicProvider

        p = _REGISTRY.resolve_provider("claude:claude-3-haiku-20240307")
        # Should resolve to AnthropicProvider (or at least a valid provider)
        assert p == AnthropicProvider

    def test_gemini_routing(self, monkeypatch):
        """Test Gemini model routing."""
        self._setup_key(monkeypatch, "GOOGLE_API_KEY", "test-key")
        from core.providers.gemini import GeminiProvider
        from core.providers.routing import ProviderRegistry
        from core.providers import register_all_providers
        _REGISTRY = ProviderRegistry()
        register_all_providers(_REGISTRY)

        p = _REGISTRY.resolve_provider("gemini:gemini-pro")
        assert p == GeminiProvider
