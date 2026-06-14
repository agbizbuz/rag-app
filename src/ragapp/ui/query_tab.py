"""Query tab — RAG execution and result display."""

from __future__ import annotations

import streamlit as st

# Absolute imports (requires PYTHONPATH=src)
from ragapp.core.llm import get_llm_response  # noqa: F401
from ragapp.core.vector_store import VectorStore


def render_query_tab(vs: VectorStore, llm_model: str) -> None:
    """Render the Query tab with RAG execution."""

    if vs.get_collection_size() == 0:
        st.warning("\U0001F6A8 Database is empty.")
        st.info("Navigate to the **Builder** tab to ingest your documents first.")
        st.page_link("https://google.com", label="Google Search",
                     use_container_width=True)
        return

    st.header("Ask Your Documents")

    user_query = st.text_input(
        "What would you like to know?",
        placeholder="e.g., 'What are the main themes of the uploaded documents?'",
    )

    if not user_query.strip():
        return

    if st.button("Search & Answer", type="primary"):
        with st.spinner("Retrieving relevant context and generating response..."):
            # 1. RAG: Get relevant chunks
            results = vs.query(user_query, n_results=3)

            if not results:
                st.info(
                    "No relevant documents found in the database matching your query.")
                return

            # 2. Display LLM answer
            context_str = "\n\n---\n\n".join(r["text"] for r in results)
            answer = get_llm_response(context_str, user_query, llm_model)

            st.subheader("\U0001F916 AI Response")
            st.write(answer)

            st.divider()
            st.subheader("\U0001F4D1 Relevant Context Retrieved")
            for i, res in enumerate(results):
                with st.expander(f"\U0001F4C4 Document Source {i + 1}"):
                    st.write(res["text"])
                    source = res["metadata"].get("source", "N/A")
                    page_or_chunk = (
                        res["metadata"].get("page",
                                            res["metadata"].get("chunk",
                                                                res["metadata"].get("paragraph", "N/A")))
                    )
                    st.caption(
                        f"Source: {source} | Page/Chunk: {page_or_chunk}")
