"""Builder tab component for document ingestion."""

from __future__ import annotations

import streamlit as st

# Absolute imports (requires PYTHONPATH=src)


def render_builder(vs, parser_registry, config_provider) -> None:
    """Render the Builder (Create DB) tab UI."""

    # File uploader
    uploaded_files = st.file_uploader(
        "Select files to index", type=["pdf", "txt", "docx", "csv"], accept_multiple_files=True
    )
    if uploaded_files and st.button("⚡ Process & Ingest Documents", type="primary"):
        _MAX_FILE_SIZE = config_provider.max_file_size_bytes  # Use config
        for f in uploaded_files:
            if f.size > _MAX_FILE_SIZE:
                st.error(f"File `{f.name}` exceeds the 50 MB limit and was skipped.")
                uploaded_files = None
                break
        if uploaded_files is not None:
            with st.spinner("Processing files and generating embeddings..."):
                chunks = []
                for uploaded_file in uploaded_files:
                    file_chunks = parser_registry.process_file(uploaded_file, config_provider)
                    chunks.extend(file_chunks)

                if chunks:
                    count = st.session_state.vector_store.add_documents(chunks)
                    st.balloons()
                    st.success(f"Successfully processed **{count}** chunks across **{len(uploaded_files)}** files!")
                else:
                    st.warning("No text content could be extracted from the provided files.")
