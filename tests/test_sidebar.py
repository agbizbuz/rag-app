"""Tests for src/ragapp/ui/sidebar.py logic functions."""

import sys
from types import ModuleType
from unittest.mock import MagicMock, patch


class _AttrDict(dict):
    """dict that also supports attribute-style access (like real st.session_state)."""

    def __getattr__(self, key):  # noqa: D401
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        self[key] = value


def _unstub_streamlit():
    """Remove cached streamlit so our mocks take effect."""
    sys.modules.pop("streamlit", None)
    for mod in list(sys.modules):
        if mod.startswith("ragapp.ui.sidebar") or mod == "streamlit":
            del sys.modules[mod]


def _make_fake_streamlit():
    """Create a fully-stubbed fake streamlit module with all sidebar methods."""
    st = ModuleType("streamlit")

    class FakeExpander:
        def __init__(self, title):  # noqa: ARG002
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            pass

    st.sidebar = MagicMock()
    st.header = MagicMock()
    st.slider = MagicMock()
    st.divider = MagicMock()
    st.button = MagicMock(side_effect=[False, False, False])
    st.markdown = MagicMock()
    st.rerun = MagicMock()
    st.expander = FakeExpander
    st.number_input = MagicMock(return_value=1000)
    st.text_input = MagicMock(return_value="text-embedding-3-small")

    st.session_state = _AttrDict(
        {
            "_selected_provider_index": 0,
            "_selected_model": "gpt-4o-mini",
            "_temp_slider": None,
            "_chunk_size": 1000,
            "confirm_delete": False,
        }
    )

    def mock_selectbox(*args, **kwargs):
        idx = kwargs.get("index", 0)
        options = args[1] if len(args) > 1 else []
        return options[idx] if idx < len(options) else (options[0] if options else "placeholder")

    st.selectbox = mock_selectbox
    sys.modules["streamlit"] = st
    return st


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

        mock_result = MagicMock()
        mock_result.json.return_value = {"models": [{"name": "llama3"}]}

        with patch("requests.get", return_value=mock_result):
            result = _check_server_health(
                "http://localhost:11434", fetch_ollama_models
            )
            assert result is True


class TestResolveModels:
    """Tests for _resolve_models function."""

    def test_resolve_with_valid_url(self):
        from ragapp.ui.components.provider_catalog import ProviderInfo, fetch_ollama_models
        from ragapp.ui.sidebar import _resolve_models

        mock_result = MagicMock()
        mock_result.json.return_value = {
            "models": [
                {"name": "llama3"},
                {"name": "gpt-4"},
            ]
        }

        with patch.dict("os.environ", {"OLLAMA_BASE_URL": "http://localhost:11434"}):
            info = ProviderInfo(
                name="TestProvider",
                key_env=None,
                model_options=[],
                discover_models=fetch_ollama_models,
                base_url_key="OLLAMA_BASE_URL",
            )

            with patch("requests.get", return_value=mock_result):
                result = _resolve_models(info)

        # Both models returned from mock; set comparison is correct
        assert set(result) == {"llama3", "gpt-4"}


class TestRenderSidebar:
    """Tests for render_sidebar logic."""

    def test_returns_model_string(self):
        _unstub_streamlit()
        st = _make_fake_streamlit()

        from ragapp.config_provider import ConfigProvider
        from ragapp.core.vector_store import VectorStore
        from ragapp.ui.sidebar import render_sidebar

        mock_vs = MagicMock(spec=VectorStore)
        mock_vs.get_collection_size.return_value = 0

        cfg = ConfigProvider()
        result = render_sidebar(mock_vs, cfg)
        assert ":" in result
