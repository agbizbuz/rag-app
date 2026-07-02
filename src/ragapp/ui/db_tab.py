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
    files = vs.get_all_files()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Collection Name", vs.collection_name)
    with col2:
        st.metric("Files Indexed", f"{len(files)}")
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
        if not files:
            st.info("No indexed files found.")
        else:
            rows: list[dict] = []
            for f in files:
                rows.append({
                    "File": f["source"],
                    "Type": f["type"],
                    "Chunks": f["chunk_count"],
                    "Pages/Range": f["page_range"],
                    "Preview": f["preview"],
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
