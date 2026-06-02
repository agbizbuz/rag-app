# Knowledge Graph Report

## Corpus Summary

| Metric | Value |
|--------|-------|
| Total files | 7 |
| Total words | 1,814 |
| Nodes | 25 |
| Edges | 41 |

## File Inventory

| File | Nodes | Description |
|------|------:|-------------|
| `config.py` | 3 | Pydantic Settings with .env loading |
| `app.py` | 1 | Streamlit UI with sidebar config, Builder/Query tabs |
| `rag_core/vector_store.py` | 12 | ChromaDB persistence layer with embedding support |
| `rag_core/__init__.py` | 1 | Package init marker |
| `rag_core/llm.py` | 3 | Multi-provider LLM abstraction (OpenAI/Anthropic/Gemini) |
| `rag_core/parser.py` | 3 | Multi-format file parsing (PDF/TXT/CSV/DOCX) |
| `README.md` | 1 | Project documentation |

## Key Relationships

| Relation | Count | Description |
|----------|------:|-------------|
| `imports_from` | 13 | Module import dependencies |
| `imports` | 8 | Package/module imports |
| `method` | 6 | Class method references |
| `contains` | 5 | File contains relationships |
| `rationale_for` | 6 | Docstring-to-element mappings |
| `calls` | 2 | Function call edges |
| `inherits` | 1 | Class inheritance |

## Architecture Summary

This is a **Local Research RAG Assistant** -- a Streamlit-based web application
that ingests documents (PDF, DOCX, TXT, CSV) into a persistent ChromaDB vector
store and queries them using OpenAI, Anthropic, or Google Gemini LLMs.

### Layered Architecture

```
app.py (UI)
  ├── config.py (Settings)
  ├── rag_core/vector_store.py (VectorStore)
  │     ├── chromadb (PersistentClient)
  │     └── embedding functions (OpenAI/SentenceTransformer)
  ├── rag_core/parser.py (process_file)
  │     ├── pypdf (PdfReader)
  │     ├── python-docx (Document)
  │     └── pandas (CSV)
  ├── rag_core/llm.py (get_llm_response)
  │     ├── openai (OpenAI client)
  │     ├── anthropic (Anthropic client)
  │     └── google-generativeai (GenAI client)
  └── streamlit (UI framework)
```

### Data Flow

1. **Ingestion**: User uploads a file via `app.py` UI -> `parser.process_file()`
   creates chunks -> `vector_store.add_documents()` stores in ChromaDB
2. **Query**: User submits question via UI -> `vector_store.query()` retrieves
   top-k relevant chunks -> `get_llm_response()` synthesizes answer from context

### Module Dependencies

- `config.py` depends on: pydantic-settings, pydantic, python-dotenv, os
- `app.py` depends on: streamlit, os, config, rag_core (vector_store, parser, llm)
- `vector_store.py` depends on: chromadb, chromadb embedding functions, config/settings, os
- `llm.py` depends on: openai, anthropic, google-generativeai (conditional), os
- `parser.py` depends on: uuid, pandas, pypdf, python-docx
