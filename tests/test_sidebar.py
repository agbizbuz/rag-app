"""Tests for src/ragapp/ui/sidebar.py logic functions."""

from unittest.mock import MagicMock, patch


class TestGetSortedProviders:
    """Tests for _get_sorted_providers function."""

    def test_returns_sorted_list(self):
        from ragapp.ui.sidebar import _get_sorted_providers

        providers = _get_sorted_providers()
        assert isinstance(providers, list)
        names = [name for name, _ in providers]
        assert names == sorted(names)


class TestGetProviderModels:
    """Tests for _get_provider_models helper."""

    def test_openai_no_prefix(self):
        from ragapp.ui.components.provider_catalog import PROVIDERS
        from ragapp.ui.sidebar import _get_provider_models

        openai_info = next(p for p in PROVIDERS if p.name == "OpenAI")
        models = _get_provider_models(openai_info)
        assert "gpt-4o-mini" in models


class TestCheckServerHealth:
    """Tests for _check_server_health function."""

    def test_ollama_reachable(self):
        from ragapp.ui.components.provider_catalog import fetch_ollama_models
        from ragapp.ui.sidebar import _check_server_health

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": [{"name": "test"}]}

        with patch("requests.get", return_value=mock_response):
            result = _check_server_health("http://localhost:11434", fetch_ollama_models)
            assert result is True


class TestResolveModels:
    """Tests for _resolve_models function."""

    def test_resolve_with_valid_url(self):
        from ragapp.ui.components.provider_catalog import ProviderInfo, fetch_ollama_models
        from ragapp.ui.sidebar import _resolve_models

        info = ProviderInfo(
            name="Ollama", key_env=None, model_options=[],
            discover_models=fetch_ollama_models, base_url_key="OLLAMA_BASE_URL",
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": [{"name": "llama3"}]}

        with patch("requests.get", return_value=mock_response):
            import os
            with patch.dict(os.environ, {"OLLAMA_BASE_URL": "http://localhost:11434"}):
                result = _resolve_models(info)
                assert set(result) == {"llama3"}


class TestRenderSidebar:
    """Tests for render_sidebar logic."""

    def test_returns_model_string(self):
        import sys
        from types import ModuleType

        st = ModuleType("streamlit")
        st.sidebar = MagicMock()
        st.header = MagicMock()
        st.slider = MagicMock()
        st.divider = MagicMock()
        st.button = MagicMock(side_effect=[False, False, False])
        st.markdown = MagicMock()
        st.rerun = MagicMock()
        st.session_state = {
            "_selected_provider_index": 0,
            "_selected_model": "gpt-4o-mini",
            "_temp_slider": None,
        }

        def mock_selectbox(*args, **kwargs):
            return args[1][0] if len(args) > 1 else "placeholder"

        st.selectbox = mock_selectbox
        sys.modules["streamlit"] = st

        from ragapp.core.vector_store import VectorStore
        from ragapp.config_provider import ConfigProvider
        from ragapp.ui.sidebar import render_sidebar

        mock_vs = MagicMock(spec=VectorStore)
        mock_vs.get_collection_size.return_value = 0

        cfg = ConfigProvider()
        result = render_sidebar(mock_vs, cfg)
        assert ":" in result
