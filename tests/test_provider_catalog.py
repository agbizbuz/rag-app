"""Tests for src/ragapp/ui/components/provider_catalog.py."""

from unittest.mock import MagicMock, patch


class TestProviderInfo:
    """Tests for ProviderInfo dataclass."""

    def test_frozen(self):
        from ragapp.ui.components.provider_catalog import ProviderInfo

        info = ProviderInfo(
            name="OpenAI",
            key_env="OPENAI_API_KEY",
            model_options=["gpt-4o-mini"],
        )
        try:
            info.name = "Changed"
            assert False, "Should not allow mutation"
        except Exception:
            pass

    def test_defaults(self):
        from ragapp.ui.components.provider_catalog import ProviderInfo

        info = ProviderInfo(name="Test", key_env=None, model_options=[])
        assert info.discover_models is None
        assert info.base_url_key is None


class TestFetchFunctions:
    """Tests for fetch_ollama_models and fetch_lm_studio_models."""

    def test_fetch_ollama_models_success(self):
        from ragapp.ui.components.provider_catalog import fetch_ollama_models

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": [{"name": "llama3.1"}, {"name": "mistral"}]}

        with patch("requests.get", return_value=mock_response):
            result = fetch_ollama_models("http://localhost:11434")
            assert set(result) == {"llama3.1", "mistral"}

    def test_fetch_ollama_models_empty(self):
        from ragapp.ui.components.provider_catalog import fetch_ollama_models

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": []}

        with patch("requests.get", return_value=mock_response):
            result = fetch_ollama_models("http://localhost:11434")
            assert result == []

    def test_fetch_ollama_models_error(self):
        from ragapp.ui.components.provider_catalog import fetch_ollama_models

        with patch("requests.get", side_effect=Exception("connection error")):
            result = fetch_ollama_models("http://localhost:11434")
            assert result == []

    def test_fetch_lm_studio_models_success(self):
        from ragapp.ui.components.provider_catalog import fetch_lm_studio_models

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "llama-3.1-instruct"},
                {"id": "mistral-7b"},
            ]
        }

        with patch("requests.get", return_value=mock_response):
            result = fetch_lm_studio_models("http://localhost:1234/v1")
            # fetch adds 'lmstudio:' prefix to model IDs
            assert set(result) == {"lmstudio:llama-3.1-instruct", "lmstudio:mistral-7b"}


class TestProviderCatalogData:
    """Tests for the PROVIDERS list."""

    def test_providers_is_list(self):
        from ragapp.ui.components.provider_catalog import PROVIDERS

        assert isinstance(PROVIDERS, list)
        assert len(PROVIDERS) >= 4

    def test_providers_have_required_fields(self):
        from ragapp.ui.components.provider_catalog import PROVIDERS, ProviderInfo

        for p in PROVIDERS:
            assert isinstance(p, ProviderInfo)
            assert hasattr(p, "name")
            assert hasattr(p, "key_env")
            assert hasattr(p, "model_options")
            assert hasattr(p, "discover_models")
            assert hasattr(p, "base_url_key")

    def test_providers_names(self):
        from ragapp.ui.components.provider_catalog import PROVIDERS

        names = [p.name for p in PROVIDERS]
        assert "OpenAI" in names
        assert "Anthropic" in names
        assert "Google Gemini" in names
        assert "Groq" in names

    def test_ollama_in_providers(self):
        from ragapp.ui.components.provider_catalog import PROVIDERS

        ollama_entries = [p for p in PROVIDERS if p.name.startswith("Ollama")]
        assert len(ollama_entries) >= 1

    def test_lm_studio_in_providers(self):
        from ragapp.ui.components.provider_catalog import PROVIDERS

        lm_entries = [p for p in PROVIDERS if p.name.startswith("LM Studio")]
        assert len(lm_entries) >= 1


class TestOllamaBaseURL:
    """Tests for OLLAMA_BASE_URL env var handling."""

    def test_default_base_url(self):
        import os

        if "OLLAMA_BASE_URL" in os.environ:
            del os.environ["OLLAMA_BASE_URL"]
            from importlib import reload

            import ragapp.ui.components.provider_catalog as pc
            reload(pc)
            assert pc.OLLAMA_BASE_URL is None

class TestProviderStaticOptions:
    """Tests for static provider options (Gemini uses static)."""

    def test_gemini_has_static_options(self):
        from ragapp.ui.components.provider_catalog import PROVIDERS

        gemini_info = next(p for p in PROVIDERS if p.name == "Google Gemini")
        assert gemini_info.model_options is not None
        assert len(gemini_info.model_options) > 0
