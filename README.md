# 📚 Local Research RAG Assistant

A secure, persistent, and self-hosted **Retrieval-Augmented Generation (RAG)** web application built with **Streamlit**, **ChromaDB**, and **Python**.

This application allows you to ingest local documents (PDF, DOCX, TXT, CSV) into a persistent vector database and query them using state-of-the-art LLMs including **GPT-4**, **Claude**, **Gemini**, **Groq**, **Ollama** (local), **LM Studio** (local), and **HuggingFace**.

## ✨ Key Features

*   **🔒 100% Secure & Private**: All documents and API keys remain on your local machine. No data leaves your device unless explicitly sent to an LLM API.
*   **💾 Persistent Vector Database**: Powered by ChromaDB; your indexed documents survive app restarts.
*   **🤖 Provider Agnostic**: Switch seamlessly between **OpenAI**, **Anthropic (Claude)**, **Google Gemini**, **Groq**, **Ollama** (local), **LM Studio** (local), and **HuggingFace** within the UI.
*   **💻 Zero-Frontend Code**: Built entirely in Python using Streamlit for rapid, clean UI development.
*   **📄 Multi-Format Parsing**: Automatically chunks and processes PDFs, DOCX files, CSVs, and TXT files.

## 🏗️ Project Structure

```text
rag-app/
├── src/ragapp/                     # 📁 RAG Application source
│   ├── app.py                      # 🖥️ Main Streamlit Web Interface
│   ├── config.py                   # ⚙️ Settings and .env loader
│   ├── .env.example                # 🔑 Template for API keys
│   └── core/                       # 🧠 Core Application Logic
│       ├── __init__.py
│       ├── parser.py               # File parsing and chunking
│       ├── llm.py                  # LLM API abstraction
│       └── vector_store.py         # ChromaDB interaction
├── AGENTS.md                       # 📖 Agent/LLM usage guide
├── chroma_db/                      # 🗄️ Persistent Storage (auto-created)
├── pyproject.toml                  # 📦 Project dependencies
├── README.md                       # 📄 This file
└── uploads/                        # 📂 Temporary file storage (auto-created)
```

## 🚀 Getting Started

### Prerequisites
1.  **Python 3.10+** installed on your system.
2.  **`uv`** (Python package manager) installed. *[Install uv]*

### Installation
Sync dependencies using `uv` and install the app as package in editable mode:
```bash
uv sync
uv pip install -e .
```

### 1. Configure API Keys
Create a `.env` file and add your API keys. You don't need all of them unless you plan to use those specific providers.
```bash
cp src/ragapp/.env.example .env
```
Open `.env` in a text editor and paste your keys (you only need the ones for providers you plan to use):
```dotenv
OPENAI_API_KEY=pk-your-openai-key
ANTHROPIC_API_KEY=anthropic-api-key-placeholder
GOOGLE_API_KEY=your-google-gemini-key
GROQ_API_KEY=gsk-your-groq-key-here
HUGGINGFACE_API_KEY=hf_your-token-here
```

### 2. Launch the App
Run the Streamlit interface:
```bash
uv run streamlit run src/ragapp/app.py
```

1.  **Select a Provider**: In the sidebar, choose your LLM provider (OpenAI, Anthropic, Gemini, Groq, Ollama, LM Studio, or HuggingFace) and select a model.
2.  **Build Your Database**: Go to the **"Builder (Create DB)"** tab. Upload your documents (PDF, DOCX, TXT, CSV). Click **"Process & Ingest Documents"**. 
    *   *Note: The database is persistent. As long as you use the same `CHROMA_DB_PATH`, your data will be there next time you launch the app.*
3.  **Ask Questions**: Switch to the **"Query (Chat)"** tab. Type your question, and the app will retrieve relevant chunks from your uploaded documents and provide an AI-synthesized answer based on the context.

## ⚙️ Configuration

| Variable | Description | Default |
| :--- | :--- | :--- |
| `OPENAI_API_KEY` | Your OpenAI API key | empty |
| `ANTHROPIC_API_KEY` | Your Anthropic API key | empty |
| `GOOGLE_API_KEY` | Your Google Gemini API key | empty |
| `GROQ_API_KEY` | Your Groq API key | empty |
| `HUGGINGFACE_API_KEY` | Your HuggingFace Inference API key | empty |
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434/v1` |
| `LM_STUDIO_BASE_URL` | LM Studio server URL | `http://localhost:1234/v1` |
| `CHROMA_DB_PATH` | Path to the persistent ChromaDB storage | `./chroma_db` |
| `COLLECTION_NAME` | Name of the internal document collection | `my_rag_collection` |
| `DEFAULT_LLM` | Default model to initialize with | `gpt-4o-mini` |
| `LLM_TEMPERATURE` | Default generation temperature (0.0–1.0) | `0.2` |
| `LLM_MAX_TOKENS` | Default max tokens for responses | `1024` |

## 🐛 Troubleshooting

*   **"Missing API Key" error**: Ensure your `.env` file is in the project root (not `src/ragapp/`) and that you have restarted the Streamlit app after adding keys.
*   **"Database is empty"**: Make sure you have processed files in the "Builder" tab before attempting to query.
*   **Import Errors**: Ensure you ran `uv sync` in the project root directory before launching the app.
## 🧹 Code Quality
This project uses **ruff** for linting/formatting and **ty** for static type checking, enforced via **pre-commit** hooks.
```bash
# Lint (auto-fix what it can)
uv run ruff check . --fix
# Format
uv run ruff format .
# Type check
uv run ty check . --ignore unresolved-import
# Run all pre-commit hooks on every file
.vvenv/bin/pre-commit clean && uv run pre-commit run --all-files
# Run tests
uv run pytest tests/ -q
```

## 🍽️ License

MIT License. Feel free to use this for personal or commercial projects.
