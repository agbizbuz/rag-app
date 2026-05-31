# 📚 Local Research RAG Assistant

A secure, persistent, and self-hosted **Retrieval-Augmented Generation (RAG)** web application built with **Streamlit**, **ChromaDB**, and **Python**.

This application allows you to ingest local documents (PDF, DOCX, TXT, CSV) into a persistent vector database and query them using state-of-the-art LLMs like GPT-4, Claude, or Gemini.

## ✨ Key Features

*   **🔒 100% Secure & Private**: All documents and API keys remain on your local machine. No data leaves your device unless explicitly sent to an LLM API.
*   **💾 Persistent Vector Database**: Powered by ChromaDB; your indexed documents survive app restarts.
*   **🤖 Provider Agnostic**: Switch seamlessly between **OpenAI**, **Anthropic (Claude)**, and **Google Gemini** within the UI.
*   **💻 Zero-Frontend Code**: Built entirely in Python using Streamlit for rapid, clean UI development.
*   **📄 Multi-Format Parsing**: Automatically chunks and processes PDFs, DOCX files, CSVs, and TXT files.

## 🏗️ Project Structure

```text
rag_app/
├── app.py                          # 🖥️ Main Streamlit Web Interface
├── config.py                       # ⚙️ Settings and .env loader
├── .env.example                    # 🔑 Template for API keys
├── pyproject.toml                  # 📦 Project dependencies
├── rag_core/                       # 🧠 Core Application Logic
│   ├── __init__.py
│   ├── parser.py                   # File parsing and chunking
│   ├── llm.py                      # LLM API abstraction
│   └── vector_store.py             # ChromaDB interaction
├── chroma_db/                      # 🗄️ Persistent Storage (auto-created)
├── uploads/                        # 📂 Temporary file storage (auto-created)
└── README.md
```

## 🚀 Getting Started

### Prerequisites
1.  **Python 3.10+** installed on your system.
2.  **`uv`** (Python package manager) installed. *[Install uv]*

### Installation
Navigate to the `rag_app` directory and sync dependencies:
```bash
cd rag_app
uv sync
```

### 1. Configure API Keys
Create a `.env` file and add your API keys. You don't need all of them unless you plan to use those specific providers.
```bash
cp .env.example .env
```
Open `.env` in a text editor and paste your keys:
```dotenv
OPENAI_API_KEY=pk-your-openai-key
ANTHROPIC_API_KEY=anthropic-api-key-placeholder
GOOGLE_API_KEY=your-google-gemini-key
```

### 2. Launch the App
Run the Streamlit interface:
```bash
streamlit run app.py
```

## 💡 How to Use

1.  **Select a Provider**: In the sidebar, choose your LLM provider (OpenAI, Anthropic, or Google Gemini) and select a model.
2.  **Build Your Database**: Go to the **"Builder (Create DB)"** tab. Upload your documents (PDF, DOCX, TXT, CSV). Click **"Process & Ingest Documents"**. 
    *   *Note: The database is persistent. As long as you use the same `CHROMA_DB_PATH`, your data will be there next time you launch the app.*
3.  **Ask Questions**: Switch to the **"Query (Chat)"** tab. Type your question, and the app will retrieve relevant chunks from your uploaded documents and provide an AI-synthesized answer based on the context.

## ⚙️ Configuration

| Variable | Description | Default |
| :--- | :--- | :--- |
| `OPENAI_API_KEY` | Your OpenAI API key | empty |
| `ANTHROPIC_API_KEY` | Your Anthropic API key | empty |
| `GOOGLE_API_KEY` | Your Google Gemini API key | empty |
| `CHROMA_DB_PATH` | Path to the persistent ChromaDB storage | `./chroma_db` |
| `COLLECTION_NAME` | Name of the internal document collection | `my_rag_collection` |
| `DEFAULT_LLM` | Default model to initialize with | `gpt-4o-mini` |

## 🐛 Troubleshooting

*   **"Missing API Key" error**: Ensure your `.env` file is in the same directory as `app.py` and that you have restarted the Streamlit app after adding keys.
*   **"Database is empty"**: Make sure you have processed files in the "Builder" tab before attempting to query.
*   **Import Errors**: Ensure you ran `uv sync` in the `rag_app` directory before attempting to `streamlit run app.py`.

## 🍽️ License

MIT License. Feel free to use this for personal or commercial projects.
