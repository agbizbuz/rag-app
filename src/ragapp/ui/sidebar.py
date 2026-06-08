"""Sidebar configuration widget group."""

from __future__ import annotations

import os

import streamlit as st

# Absolute imports for root-level packages (requires PYTHONPATH=src)
from ragapp.config import settings
from ragapp.core.vector_store import VectorStore
from ragapp.ui.components.provider_catalog import PROVIDERS


def render_sidebar(vs: VectorStore) -> str:
    """Render sidebar. Returns the selected model string."""

    with st.sidebar:
        st.header("Configuration")

        # Model selection
        model_options = [p.name for p in PROVIDERS] + ["gpt-4o-mini", "claude-3-haiku-20240307"]
        if settings.default_llm not in model_options:
            model_options.append(settings.default_llm)

        selected_model = st.selectbox(
            "Select Model", model_options, index=0, key="_selected_model"
        )

        # Temperature - use default from settings as initial value
        current_temp = st.session_state.get("_temp_slider", None)
        if current_temp is None:
            current_temp = settings.llm_temperature

        st.slider(
            "Temperature",
            0.0,
            1.0,
            current_temp,
            step=0.05,
            key="_temp_slider",
        )

        st.divider()

        # Database status + controls
        db_size = vs.get_collection_size()
        st.markdown(f"**Database Status**\n\nDocuments Index: `{db_size}`")

        if st.button("Clear Database", type="secondary"):
            vs.delete_collection()
            st.rerun()

        st.divider()
        if st.button("Quit App", type="primary"):
            _quit_session()

    return selected_model  # type: ignore[return-value]


def render_key_status(info) -> None:
    """Show a key / server health indicator for the selected provider."""
    
    if hasattr(info, 'key_env') and info.key_env:
        has_key = bool(os.environ.get(info.key_env))
        label = f"**{info.name} API Key:**"
        status = "✅" if has_key else "⚠️ Missing"

        st.write(f"{label} {status}")

    elif hasattr(info, 'discover_models') and info.discover_models and info.base_url_key:
        url = os.environ.get(info.base_url_key, "")
        if not url:
            return  # No URL set

        label = f"**{info.name} Server:**"
        reachable = _check_server_health(url, info.discover_models)

        status = "✅" if reachable else "⚠️ Unreachable"
        st.write(f"{label} {status}")


def _resolve_models(info):  # noqa: ANN001
    """Return dynamically-discovered models or empty list."""
    base_url = os.environ.get(info.base_url_key, "")
    if not info.discover_models or not base_url:
        return []

    try:
        func = info.discover_models
        return func(base_url)
    except Exception:
        # Server unreachable - let UI show a warning
        return []


def _check_server_health(base_url, discover_func):  # noqa: ANN001
    """Check if server is reachable by trying to list models."""
    try:
        from ragapp.ui.components.provider_catalog import fetch_lm_studio_models, fetch_ollama_models

        if discover_func == fetch_ollama_models:
            return len(fetch_ollama_models(base_url)) > 0
        elif discover_func == fetch_lm_studio_models:
            return len(fetch_lm_studio_models(base_url)) > 0
        else:
            # Generic fallback - try calling it directly
            discover_func(base_url)
            return True
    except Exception:
        return False


def _quit_session() -> None:
    st.session_state._quit_requested = True

    from ragapp.ui import components as _c  # noqa: F401

    # Trigger a refresh that closes the browser window/tab by executing JS
    body = "<script>window.close();</script>"
    _c.html(f"<script>try{{window.open('about:blank','_self').close()}}catch(e){{}}</script>{body}", height=0, width=0)

