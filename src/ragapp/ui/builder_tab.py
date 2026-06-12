"""Builder tab component for document ingestion."""

from __future__ import annotations

import streamlit as st

# Absolute imports (requires PYTHONPATH=src)
from ragapp.core.parser import process_file


def render_builder(vs) -> None:
    """Render the Builder (Create DB) tab UI."""

    # File uploader
    uploaded_files = st.file_uploader(
        "Select files to index", type=["pdf", "txt", "docx", "csv"], accept_multiple_files=True
    )
    if uploaded_files and st.button("⚡ Process & Ingest Documents", type="primary"):
        _MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
        for f in uploaded_files:
            if f.size > _MAX_FILE_SIZE:
                st.error(f"File `{f.name}` exceeds the 50 MB limit and was skipped.")
                uploaded_files = None
                break
        if uploaded_files is not None:
            with st.spinner("Processing files and generating embeddings..."):
                chunks = []
                for uploaded_file in uploaded_files:
                    file_chunks = process_file(uploaded_file)
                    chunks.extend(file_chunks)

                if chunks:
                    count = st.session_state.vector_store.add_documents(chunks)
                    st.balloons()
                    st.success(f"Successfully processed **{count}** chunks across **{len(uploaded_files)}** files!")
                else:
                    st.warning("No text content could be extracted from the provided files.")
