"""Streamlit entry point — thin glue between UI components and core."""

from __future__ import annotations

import streamlit as st
from ragapp.config_provider import get_config, ConfigProvider
from ragapp.core.vector_store import VectorStore


def _get_config() -> ConfigProvider:
    """Lazy load config provider."""
    return get_config()


st.set_page_config(
    page_title="Local RAG Assistant", page_icon="\U0001F4DA", layout="wide"
)

# Main title banner (restored from pre-refactor version)
st.title("📚 Local Research RAG")
st.caption(
    "A persistent, local, and secure Question Answering system powered by ChromaDB.")

# Lazy init the vector store once per session
if "vector_store" not in st.session_state:
    _config = get_config()
    st.session_state.vector_store = VectorStore(config_provider=_config)


def _main(config: ConfigProvider | None = None) -> None:
    if st.session_state.get("_quit_requested"):
        import sys
        sys.exit(0)

    vs = st.session_state.vector_store
    cfg = config or _get_config()
    selected_model = st.session_state.get("_selected_model", cfg.default_llm)

    # Sidebar handles its own state via session keys
    from ragapp.ui.sidebar import render_sidebar

    selected_model = render_sidebar(vs, cfg) or selected_model

    # Tab navigation
    tab1, tab2 = st.tabs(["📝 **Builder**", "❓ **Query**"])

    with tab1:
        from ragapp.ui.builder_tab import render_builder
        _ = render_builder(vs)  # noqa: F841

    with tab2:
        # current_model = st.session_state.get("_selected_model", cfg.default_llm)
        from ragapp.ui.query_tab import render_query_tab as _render_query_tab
        # _render_query_tab(vs, current_model)  # noqa: F841
        _render_query_tab(vs, selected_model)  # noqa: F841


_main()
