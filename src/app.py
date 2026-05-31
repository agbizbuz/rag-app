import streamlit as st
import os
from rag_core.vector_store import VectorStore
from rag_core.parser import process_file
from rag_core.llm import get_llm_response
from config import settings

# Page configuration
st.set_page_config(page_title="Local RAG Assistant", page_icon="📚", layout="wide")

# ------------------------------------------------
# Session State Initialization
# ------------------------------------------------
if "vector_store" not in st.session_state:
    # We initialize on first load. The path is persistent on disk.
    st.session_state.vector_store = VectorStore()

# ------------------------------------------------
# Sidebar Configuration
# ------------------------------------------------
with st.sidebar:
    st.header("🛠️ Configuration")
    st.info("Environment variables (API keys) are automatically loaded from the `.env` file.")

    # Provider selection
    provider = st.radio("LLM Provider", options=["OpenAI", "Anthropic", "Google Gemini"], index=0)

    if provider == "OpenAI":
        st.info("Requires `OPENAI_API_KEY`")
        selected_model = st.selectbox("Select Model", ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"], index=0)
        st.success("✅ Ready (OpenAI)")
    elif provider == "Anthropic":
        st.info("Requires `ANTHROPIC_API_KEY`")
        selected_model = st.selectbox(
            "Select Model", ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"], index=2
        )
        st.success("✅ Ready (Anthropic)")
    else:
        st.info("Requires `GOOGLE_API_KEY`")
        selected_model = st.selectbox("Select Model", ["gemini-pro", "gemini-pro-vision"], index=0)
        st.success("✅ Ready (Google Gemini)")

    st.divider()

    # Database status
    db_status = st.session_state.vector_store.get_collection_size()
    st.markdown(f"**Database Status**\n\nDocuments Index: `{db_status}`")

    if st.button("🗑️ Clear Database", type="secondary"):
        st.session_state.vector_store.delete_collection()
        st.rerun()

# ------------------------------------------------
# Main Layout (Tabs)
# ------------------------------------------------
st.title("📚 Local Research RAG")
st.caption("A persistent, local, and secure Question Answering system powered by ChromaDB.")

tab_build, tab_query = st.tabs(["🛠️ Builder (Create DB)", "💬 Query (Ask Questions)"])

# --- TAB 1: BUILDER ---
with tab_build:
    st.header("Build Your Knowledge Base")
    st.markdown("""
    Upload PDF, DOCX, TXT, or CSV files here. The app will process, chunk, and persist them into a local vector database.
    The database is **persistent** and survives application restarts.
    """)

    uploaded_files = st.file_uploader(
        "Select files to index", type=["pdf", "txt", "docx", "csv"], accept_multiple_files=True
    )

    if uploaded_files and st.button("⚡ Process & Ingest Documents", type="primary"):
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
                st.session_state.vector_store.delete_collection()

# --- TAB 2: QUERY ---
with tab_query:
    st.header("Ask Your Documents")

    if st.session_state.vector_store.get_collection_size() > 0:
        user_query = st.text_input(
            "What would you like to know?", placeholder="e.g., 'What are the main themes of the uploaded documents?'"
        )

        if st.button("🔍 Search & Answer", type="primary"):
            if not user_query.strip():
                st.warning("Please enter a question.")
            else:
                with st.spinner("Retrieving relevant context and generating response..."):
                    # 1. RAG: Get relevant chunks
                    results = st.session_state.vector_store.query(user_query, n_results=3)

                    if results:
                        # Format context string for LLM
                        context_str = "\n\n---\n\n".join([r["text"] for r in results])

                        # 2. LLM: Generate answer
                        answer = get_llm_response(context_str, selected_model)

                        # 3. Display Results
                        st.subheader("🤖 AI Response")
                        st.write(answer)

                        st.divider()
                        st.subheader("📑 Relevant Context Retrieved")
                        for i, res in enumerate(results):
                            with st.expander(f"📄 Document Source {i + 1}"):
                                st.write(res["text"])
                                st.caption(
                                    f"Source: {res['metadata'].get('source', 'N/A')} | Page/Chunk: {res['metadata'].get('page', res['metadata'].get('chunk', res['metadata'].get('paragraph', 'N/A')))}"
                                )
                    else:
                        st.info("No relevant documents found in the database matching your query.")

    else:
        st.warning("🚨 Database is empty.")
        st.info("Please navigate to the **'Builder (Create DB)'** tab to ingest your documents first.")
        st.page_link("https://google.com", text="Google Search", use_container_width=True)
