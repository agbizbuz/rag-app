"""Sidebar configuration widget group."""

from __future__ import annotations

import os

import streamlit as st

from ragapp.config_provider import ConfigProvider
from ragapp.core.vector_store import VectorStore
from ragapp.ui.components.provider_catalog import PROVIDERS


def _get_provider_models(provider_info):
    """Return list of model identifiers for a provider with appropriate prefix."""
    if provider_info.discover_models and provider_info.base_url_key:
        discovered = _resolve_models(provider_info)
        if discovered:
            return discovered
        return []

    opts = provider_info.model_options.copy() if provider_info.model_options else []

    # Apply prefixes matching providers/__init__.py registration patterns
    if provider_info.name == "Groq":
        return opts  # Already prefixed with groq:
    elif provider_info.name.startswith("LM Studio"):
        return [f"lm-studio:{m}" for m in opts] if opts else []
    elif provider_info.name == "Ollama":
        return [f"ollama:{m}" for m in opts] if opts else []
    elif provider_info.name.startswith("Google Gemini"):
        # Just use the model name directly - it routes via 'gemini' prefix
        # gemini-pro -> gemini-pro (matches 'gemini' registration)
        return opts  # Already correct format
    elif provider_info.name == "Anthropic":
        # model_options like claude-3-haiku don't need extra prefix
        return opts
    elif provider_info.name == "OpenAI":
        return opts  # Default (empty prefix)
    elif provider_info.name == "HuggingFace":
        return [f"hf-{m}" for m in opts]  # Add hf- prefix for clarity
    return opts


def _get_sorted_providers() -> list[tuple[str, object]]:
    """Return sorted list of (display_name, provider_info) tuples."""
    results = []
    for info in PROVIDERS:
        if info.discover_models and info.base_url_key:
            # Dynamic discovery - always show even if server is down
            results.append((info.name, info))
        elif info.model_options:
            results.append((info.name, info))
    return sorted(results, key=lambda x: x[0])


def render_sidebar(vs: VectorStore, config: ConfigProvider) -> str:
    """Render sidebar. Returns the selected model string."""

    with st.sidebar:
        st.header("Configuration")

        # Provider selection - dropdown to choose provider category
        provider_options = [(name, info)
                            for name, info in _get_sorted_providers()]

        if "_selected_provider_index" not in st.session_state:
            st.session_state._selected_provider_index = 0

        selected_provider_name = st.selectbox(
            "Select Provider",
            [name for name, _ in provider_options],
            index=st.session_state._selected_provider_index,
            key="_selected_provider_name"
        )

        # Update index on selection (will persist to next render)
        selected_idx = next((i for i, (name, _) in enumerate(
            provider_options) if name == selected_provider_name), 0)

        # Find selected provider info
        selected_provider_info = next(
            info for name, info in provider_options if name == selected_provider_name)

        # Model selection - shows models for the currently selected provider
        provider_models = _get_provider_models(selected_provider_info)

        if not provider_models:
            st.info("🔄 Discovering available models...")
            # Force discovery by checking server health
            if selected_provider_info.discover_models and selected_provider_info.base_url_key:
                base_url = os.environ.get(
                    selected_provider_info.base_url_key, "")
                discovered = _resolve_models(selected_provider_info)
                if discovered:
                    provider_models = [
                        f"{selected_provider_name}:{m}" for m in discovered]
                else:
                    st.warning(
                        "⚠️ Server appears offline. Check URL settings.")
                    provider_models = []

        # Remove duplicates while preserving order
        seen = set()
        unique_options = []
        for m in provider_models:
            if m not in seen:
                seen.add(m)
                unique_options.append(m)

        if unique_options:
            selected_model = st.selectbox(
                "Select Model",
                unique_options,
                index=next((i for i, model in enumerate(unique_options)
                            if model == st.session_state.get("_selected_model")), 0),
                key="_selected_model"
            )
        else:
            # No models available - show placeholder with guidance
            st.selectbox("Select Model", [
                         "⚠️ Add API key or check server"], index=0)
            selected_model = None

        # Temperature - use default from settings as initial value
        current_temp = st.session_state.get("_temp_slider", None)
        if current_temp is None:
            current_temp = config.llm_temperature

        st.slider(
            "Temperature",
            0.0,
            1.0,
            current_temp,
            step=0.05,
            key="_temp_slider",
        )

        # Advanced Settings — collapsible to keep default view clean
        with st.expander("⚙️ Advanced Settings"):
            # Chunk Size
            current_chunk = st.session_state.get("_chunk_size", None)
            if current_chunk is None:
                current_chunk = config.chunk_size

            st.number_input(
                "Chunk Size (characters)",
                min_value=200,
                max_value=5000,
                value=current_chunk,
                step=100,
                key="_chunk_size",
                help="Target size for document chunks during ingestion. "
                     "Smaller = more precise retrieval, larger = more context per chunk.",
            )

            # Retrieved Results (n_results)
            current_n = st.session_state.get("_n_results", None)
            if current_n is None:
                current_n = config.n_results

            st.slider(
                "Retrieved Results",
                min_value=1,
                max_value=20,
                value=current_n,
                key="_n_results",
                help="Number of document chunks retrieved per query.",
            )

            # Embedding Model (read-only display, env-only config)
            st.text_input(
                "Embedding Model",
                value=config.embedding_model,
                disabled=True,
                help="⚠️ Set via EMBEDDING_MODEL env var. "
                     "Changing requires re-indexing all documents.",
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

    # type: ignore[return-value]
    return selected_provider_name + ":" + selected_model


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

    # Trigger a refresh that closes the browser window/tab by executing JS
    body = "<script>window.close();</script>"
    st.html(
        f"<script>try{{window.open('about:blank','_self').close()}}catch(e){{}}</script>{body}", height=0, width=0)
