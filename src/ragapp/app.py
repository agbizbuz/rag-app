import os
import requests
import streamlit as st
from core.llm import get_llm_response
from core.parser import process_file
from core.vector_store import VectorStore
from config import settings
def fetch_ollama_models(base_url: str) -> list[str]:
    """Fetch available models from an Ollama server."""
    try:
        resp = requests.get(f"{base_url}/api/tags", timeout=3)
        resp.raise_for_status()
        data = resp.json()
        return [f"ollama:{m['name']}" for m in data.get("models", [])]
    except Exception:
        return []
def fetch_lm_studio_models(base_url: str) -> list[str]:
    """Fetch available models from an LM Studio server."""
    try:
        resp = requests.get(f"{base_url}/v1/models", timeout=3)
        resp.raise_for_status()
        data = resp.json()
        return [f"lmstudio:{m['id']}" for m in data.get("data", [])]
    except Exception:
        return []

# Page configuration
st.set_page_config(page_title="Local RAG Assistant", page_icon="📚", layout="wide")

# ------------------------------------------------
# Session State Initialization
# ------------------------------------------------
if "vector_store" not in st.session_state:
    # We initialize on first load. The path is persistent on disk.
    st.session_state.vector_store = VectorStore()
_QUIT_HTML = """
<script>
try { window.open('about:blank', '_self').close(); } catch(e) {}
</script>
<div style="position:fixed;top:0;left:0;width:100vw;height:100vh;display:flex;align-items:center;justify-content:center;background:#f7f7f7;z-index:9999;font-family:sans-serif;">
  <div style="text-align:center;">
    <div style="font-size:48px;margin-bottom:16px;">👋</div>
    <h2 style="margin:0 0 8px;color:#333;">Session Ended</h2>
    <p style="color:#777;font-size:14px;">Close this tab to finish.</p>
    <p style="color:#999;font-size:12px;margin-top:16px;">(If the page did not close automatically, you can also stop the streamlit server with Ctrl+C in the terminal.)</p>
  </div>
</div>
"""
if st.session_state.get("_quit_requested"):
    import streamlit.components.v1 as _c
    _c.html(_QUIT_HTML, height=0, width=0)
    import sys; sys.exit(0)
# ------------------------------------------------
# Sidebar Configuration
# ------------------------------------------------
with st.sidebar:
    st.header("🛠️ Configuration")
    st.info("Environment variables (API keys) are automatically loaded from the `.env` file.")

    provider = st.radio(
        "LLM Provider",
        options=["OpenAI", "Anthropic", "Google Gemini", "Groq", "Ollama", "LM Studio", "HuggingFace"],
        index=0,
    )
    if provider == "OpenAI":
        st.info("Requires `OPENAI_API_KEY`")
        selected_model = st.selectbox(
            "Select Model", ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"], index=0
        )
        st.success("✅ Ready (OpenAI)")
    elif provider == "Anthropic":
        st.info("Requires `ANTHROPIC_API_KEY`")
        selected_model = st.selectbox(
            "Select Model",
            ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
            index=2,
        )
        st.success("✅ Ready (Anthropic)")
    elif provider == "Google Gemini":
        st.info("Requires `GOOGLE_API_KEY`")
        selected_model = st.selectbox(
            "Select Model", ["gemini-pro", "gemini-pro-vision"], index=0
        )
        st.success("✅ Ready (Google Gemini)")
    elif provider == "Groq":
        st.info("Requires `GROQ_API_KEY`")
        selected_model = st.selectbox(
            "Select Model",
            [
                "groq:llama-3.1-8b-instant",
                "groq:llama-3.1-70b-versatile",
                "groq:llama-3.1-405b-reasoning",
                "groq:gemma2-9b-it",
            ],
            index=0,
        )
        st.success("✅ Ready (Groq)")
    elif provider == "Ollama":
        st.info(
            "Local AI server. Start Ollama and run `ollama pull <model>` first.\n\n"
            "Change base URL in `.env` (`OLLAMA_BASE_URL`) if needed."
        )
        ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        available_models = fetch_ollama_models(ollama_url)
        if available_models:
            default_model = available_models[0]
        else:
            st.warning(f"⚠️ Could not reach Ollama server at `{ollama_url}`. Is it running?")
            default_model = "ollama:llama3.1"
        selected_model = st.selectbox(
            "Select Model", available_models if available_models else [default_model], index=0
        )
        st.success("✅ Ready (Ollama)")
    elif provider == "LM Studio":
        st.info(
            "Local AI server. Start a local model server in LM Studio first.\n\n"
            "Change base URL in `.env` (`LM_STUDIO_BASE_URL`) if needed."
        )
        lm_url = os.environ.get("LM_STUDIO_BASE_URL", "http://localhost:1234")
        available_models = fetch_lm_studio_models(lm_url)
        if available_models:
            default_model = available_models[0]
        else:
            st.warning(f"⚠️ Could not reach LM Studio server at `{lm_url}`. Is it running?")
            default_model = "lmstudio:llama-3.1-instruct"
        selected_model = st.selectbox(
            "Select Model", available_models if available_models else [default_model], index=0
        )
        st.success("✅ Ready (LM Studio)")
    elif provider == "HuggingFace":
        st.info(
            "Requires `HUGGINGFACE_API_KEY`.\n\n"
            "Uses HuggingFace Inference API. Free tier may be rate-limited."
        )
        selected_model = st.selectbox(
            "Select Model",
            [
                "meta-llama/Llama-3.3-70B-Instruct",
                "meta-llama/Meta-Llama-3.1-70B-Instruct",
                "mistralai/Mistral-7B-Instruct-v0.3",
                "nomic-ai/gpt4all-falcon",
            ],
            index=0,
        )
        st.success("✅ Ready (HuggingFace)")

    st.divider()

    # Database status
    db_status = st.session_state.vector_store.get_collection_size()
    st.markdown(f"**Database Status**\n\nDocuments Index: `{db_status}`")

    if st.button("🗑️ Clear Database", type="secondary"):
        st.session_state.vector_store.delete_collection()
        st.rerun()
    st.divider()
    if st.button("⏹️ Quit App", type="primary"):
        st.session_state._quit_requested = True
        st.rerun()
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
        st.page_link("https://google.com", label="Google Search", use_container_width=True)
