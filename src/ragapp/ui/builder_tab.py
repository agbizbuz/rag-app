"""Builder tab component for document ingestion."""

from __future__ import annotations

import streamlit as st

# Absolute imports (requires PYTHONPATH=src)
from ragapp.config import settings
from ragapp.core.parser import process_file


def render_builder(vs) -> None:
    """Render the Builder (Create DB) tab UI."""

    # File uploader
    uploaded = st.file_uploader(
        "Upload a document", type=["pdf", "txt", "csv", "docx"]
    )

    if not uploaded:
        return

    # Display file info
    file_name = uploaded.name
    col1, col2 = st.columns([0.5, 0.5])
    with col1:
        st.write(f"**File:** {file_name}")
        chunking_method = settings.chunk_size

    if st.button("Ingest", type="primary"):
        # Chunk the file
        try:
            chunks = process_file(uploaded.read(), chunk_size=chunking_method)  # type: ignore[arg-type]
            
            # Add to vector store
            added = vs.add_documents(chunks)

            st.success(f"Added {added} document(s). Total in DB: {vs.get_collection_size()}")

        except Exception as e:
            st.error(f"Ingestion failed: {e}")

    # Show current doc stats
    st.write()
    st.markdown(
        "**Chunk Size:** `chunking_method`"  # type: ignore[name-defined]
        if chunking_method
        else f"**Chunk size:** `{chunking_method}`"
    )

