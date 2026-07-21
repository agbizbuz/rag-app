"""Streamlit entry point -- thin glue between UI components and core."""

from __future__ import annotations

import streamlit as st
from config_provider import ConfigProvider
from core.vector_store import VectorStore


st.set_page_config(page_title="Local RAG Assistant", page_icon="📚", layout="wide")

# Main title banner (restored from pre-refactor version)
st.title("📚 Local Research RAG")
st.caption("A persistent, local, and secure Question Answering system powered by ChromaDB.")

# Lazy init components once per session
if "config_provider" not in st.session_state:
    from config import Settings
    st.session_state.config_provider = ConfigProvider(Settings())

if "provider_registry" not in st.session_state:
    from core.providers.routing import ProviderRegistry
    from core.providers import register_all_providers
    
    registry = ProviderRegistry()
    register_all_providers(registry)
    st.session_state.provider_registry = registry
    
if "parser_registry" not in st.session_state:
    from core.parser import ParserRegistry
    
    st.session_state.parser_registry = ParserRegistry()

if "vector_store" not in st.session_state:
    from core.embedding_manager import EmbeddingManager

    _config = st.session_state.config_provider
    st.session_state.embedding_manager = EmbeddingManager(config_provider=_config)
    st.session_state.vector_store = VectorStore(
        config_provider=_config,
        embedding_manager=st.session_state.embedding_manager,
    )

if "retriever" not in st.session_state:
    from core.hybrid_retriever import HybridRetriever

    st.session_state.retriever = HybridRetriever(
        vector_store=st.session_state.vector_store,
        config_provider=st.session_state.config_provider,
    )


def _main() -> None:
    if st.session_state.get("_quit_requested"):
        import sys
        sys.exit(0)

    vs = st.session_state.vector_store
    retriever = st.session_state.retriever
    cfg = st.session_state.config_provider
    provider_registry = st.session_state.provider_registry
    parser_registry = st.session_state.parser_registry
    selected_model = st.session_state.get("_selected_model", cfg.default_llm)

    # Sidebar handles its own state via session keys
    from ui.sidebar import render_sidebar

    sidebar_model = render_sidebar(vs, cfg)
    if sidebar_model:
        selected_model = sidebar_model

    # Tab navigation
    (tab1, tab2, tab3, tab4) = st.tabs(
        [
            "📝 **Builder**",
            "❓ **Query**",
            "📊 **Evaluation**",
            "🗃️ **Database Info**",
        ]
    )

    with tab1:
        from ui.builder_tab import render_builder
        render_builder(vs, parser_registry=parser_registry, config_provider=cfg)

    with tab2:
        from ui.query_tab import render_query_tab
        render_query_tab(retriever, selected_model, config_provider=cfg, provider_registry=provider_registry)

    with tab3:
        from ui.evaluation_tab import render_evaluation_tab
        render_evaluation_tab(config_provider=cfg, provider_registry=provider_registry)

    with tab4:
        from ui.db_tab import render_db_tab
        render_db_tab(vs)


_main()
