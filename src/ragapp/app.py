"""Streamlit entry point — thin glue between UI components and core."""

from __future__ import annotations

import streamlit as st

# Absolute imports - works when PYTHONPATH=src is set (standard for Python projects)
from config import settings


st.set_page_config(
    page_title="Local RAG Assistant", page_icon="\U0001F4DA", layout="wide"
)


# Main title banner (restored from pre-refactor version)
st.title("📚 Local Research RAG")
st.caption("A persistent, local, and secure Question Answering system powered by ChromaDB.")

# Lazy init the vector store once per session
if "vector_store" not in st.session_state:
    from core.vector_store import VectorStore

    st.session_state.vector_store = VectorStore()


def _main() -> None:
    if st.session_state.get("_quit_requested"):
        import sys

        sys.exit(0)

    vs = st.session_state.vector_store

    selected_model = st.session_state.get("_selected_model", settings.default_llm)

    # Sidebar handles its own state via session keys
    from ui.sidebar import render_sidebar

    selected_model = render_sidebar(vs) or selected_model

    tab_build, tab_query = st.tabs(["Builder (Create DB)", "Query (Ask Questions)"])

    with tab_build:
        from ui.builder_tab import render_builder

        render_builder(vs)

    with tab_query:
        from ui.query_tab import render_query_tab

        render_query_tab(vs, selected_model)


_main()
