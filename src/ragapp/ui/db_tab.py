"""DB info tab: stats, document inventory, management."""

from __future__ import annotations

import pandas as pd
import streamlit as st


def render_db_tab(vs) -> None:  # noqa: PLR0912
    """Render the Database Info tab UI."""

    st.header("Database Info")

    if "confirm_delete" not in st.session_state:
        st.session_state["confirm_delete"] = False

    # Collection overview cards
    vs._ensure_collection()  # noqa: SLF001
    doc_count = vs.get_collection_size()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Collection Name", vs.collection_name)
    with col2:
        st.metric("Total Chunks", f"{doc_count:,}")
    with col3:
        st.metric("Database Path", vs.db_path)

    st.write("")

    # Document inventory table
    if doc_count == 0:
        st.info(
            "The database is empty. "
            "Use the **Builder** tab to ingest documents."
        )
    else:
        docs = vs.get_all_documents()
        rows: list[dict] = []
        for d in docs:
            meta = d.get("metadata") or {}
            source = meta.get("source", "unknown")

            page = meta.get("page")
            row_idx = meta.get("row")
            paragraph = meta.get("paragraph")
            chunk_num_val = meta.get("chunk")

            if page is not None:
                type_label = "PDF"
                location = f"Page {page}"
            elif row_idx is not None:
                type_label = "CSV"
                location = f"Row {row_idx}"
            elif paragraph is not None:
                type_label = "DOCX"
                location = f"Paragraph {paragraph}"
            elif chunk_num_val is not None:
                type_label = "TXT"
                location = f"Chunk {chunk_num_val}"
            else:
                type_label = "UNK"
                location = "-"

            preview = (d.get("text") or "").strip()[:80]

            rows.append({
                "source": source,
                "type": type_label,
                "location": location,
                "preview": preview,
            })

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.write("---")

    # Management section
    st.markdown("### Management")

    if st.session_state.get("confirm_delete"):
        st.warning("This will permanently delete all indexed documents.")
        _, btn_col, _ = st.columns([3, 1, 3])
        with btn_col:
            if st.button(
                "Confirm Delete", type="primary", use_container_width=True
            ):
                vs.delete_collection()
                st.session_state["vector_store"]._collection = None  # noqa: SLF001
                st.session_state["confirm_delete"] = False
                st.toast("Database cleared.", icon="\U0001f5d1\ufe0f")
    else:
        if st.button("Clear Database", type="primary"):
            st.session_state["confirm_delete"] = True
