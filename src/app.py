"""Streamlit entry point -- thin glue between UI components and core."""

from __future__ import annotations

import streamlit as st
from config_provider import get_config, ConfigProvider
from core.vector_store import VectorStore


def _get_config() -> ConfigProvider:
    """Lazy load config provider."""
    return get_config()


st.set_page_config(page_title="Local RAG Assistant", page_icon="\U0001f4da", layout="wide")

# Main title banner (restored from pre-refactor version)
st.title("\U0001f4da Local Research RAG")
st.caption("A persistent, local, and secure Question Answering system powered by ChromaDB.")

# Lazy init components once per session
if "vector_store" not in st.session_state:
    from core.embedding_manager import EmbeddingManager

    _config = get_config()
    st.session_state.embedding_manager = EmbeddingManager(config_provider=_config)
    st.session_state.vector_store = VectorStore(
        config_provider=_config,
        embedding_manager=st.session_state.embedding_manager,
    )

if "retriever" not in st.session_state:
    from core.hybrid_retriever import HybridRetriever

    st.session_state.retriever = HybridRetriever(
        vector_store=st.session_state.vector_store,
        config_provider=get_config(),
    )


def _main(config: ConfigProvider | None = None) -> None:
    if st.session_state.get("_quit_requested"):
        import sys

        sys.exit(0)

    vs = st.session_state.vector_store
    retriever = st.session_state.retriever
    cfg = config or _get_config()
    selected_model = st.session_state.get("_selected_model", cfg.default_llm)

    # Sidebar handles its own state via session keys
    from ui.sidebar import render_sidebar

    sidebar_model = render_sidebar(vs, cfg)
    if sidebar_model:
        selected_model = sidebar_model

    # Tab navigation
    (tab1, tab2, tab3, tab4) = st.tabs(
        [
            "\U0001f4dd **Builder**",
            "\u2753 **Query**",
            "\U0001f4ca **Evaluation**",
            "\U0001f5c3\ufe0f **Database Info**",
        ]
    )

    with tab1:
        from ui.builder_tab import render_builder

        render_builder(vs)

    with tab2:
        from ui.query_tab import render_query_tab

        render_query_tab(retriever, selected_model)

    with tab3:
        from ui.evaluation_tab import render_evaluation_tab

        render_evaluation_tab()

    with tab4:
        from ui.db_tab import render_db_tab

        render_db_tab(vs)


_main()
