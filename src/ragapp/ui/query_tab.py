"""Query tab — RAG execution and result display."""

from __future__ import annotations

import re
from datetime import datetime

import streamlit as st

# Absolute imports (requires PYTHONPATH=src)
from ragapp.core.llm import get_llm_response  # noqa: F401
from ragapp.core.retriever import RAGRetriever


def _build_export_markdown(
    query: str,
    answer: str,
    model: str,
    results: list[dict],
) -> str:
    """Build a markdown string suitable for file export."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# RAG Query Export",
        "",
        f"**Date:** {timestamp}  ",
        f"**Model:** `{model}`",
        "",
        "---",
        "",
        "## Query",
        "",
        query,
        "",
        "---",
        "",
        "## AI Response",
        "",
        answer,
        "",
        "---",
        "",
        "## Retrieved Sources",
        "",
    ]
    for i, res in enumerate(results, 1):
        source = res["metadata"].get("source", "N/A")
        page_or_chunk = res["metadata"].get(
            "page",
            res["metadata"].get(
                "chunk", res["metadata"].get("paragraph", "N/A")
            ),
        )
        lines.append(f"### Source {i}")
        lines.append("")
        lines.append(f"- **File:** {source}")
        lines.append(f"- **Page / Chunk:** {page_or_chunk}")
        lines.append("")
        lines.append(res["text"])
        lines.append("")

    return "\n".join(lines)


def _safe_filename(query: str, max_len: int = 40) -> str:
    """Derive a filesystem-safe filename from the user query."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", query).strip("_").lower()
    return slug[:max_len] if slug else "rag_export"


def render_query_tab(retriever: RAGRetriever, llm_model: str) -> None:
    """Render the Query tab with RAG execution."""

    if retriever.vector_store.get_collection_size() == 0:
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
            n_results = st.session_state.get("_n_results", 3)
            results = retriever.retrieve(user_query, n_results=n_results)

            if not results:
                st.info(
                    "No relevant documents found in the database matching your query.")
                return

            # 2. Display LLM answer
            context_str = retriever.format_context(results)
            answer = get_llm_response(context_str, user_query, llm_model)

            st.subheader("\U0001F916 AI Response")
            st.write(answer)

            # 3. Export to Markdown
            md_content = _build_export_markdown(
                user_query, answer, llm_model, results
            )
            filename = f"{_safe_filename(user_query)}.md"
            st.download_button(
                label="📥 Export Response to Markdown",
                data=md_content,
                file_name=filename,
                mime="text/markdown",
            )

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
