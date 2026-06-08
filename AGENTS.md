# AGENTS.md - Agent Guide for RAG App

## SOLID Design Principles

This RAG application follows **SOLID** design principles for maintainable, extensible architecture:

- **Single Responsibility Principle (SRP)**: Each class/module has one job — e.g., `VectorStore` only manages ChromaDB, parsers only handle file formats
- **Open/Closed Principle (OCP)**: Extensible without modification via registry pattern. New providers/parsers added by creating a new file and registering — zero changes to existing code  
- **Liskov Substitution Principle (LSP)**: All providers implement `ProviderProtocol`; all parsers implement `ParserProtocol`. Any provider can substitute another at runtime
- **Interface Segregation Principle (ISP)**: Clients depend only on needed methods. Separate protocols for chat vs embedding, parsing vs chunking
- **Dependency Inversion Principle (DIP)**: High-level modules (`llm.py`, `parser.py`) depend on abstractions (protocols), not concrete implementations

### Architecture Patterns Used

1. **Strategy Pattern**: Provider and Parser registries allow runtime selection of implementations based on model ID or file extension  
2. **Dependency Injection**: Settings injected into constructors; embedding creator injected into VectorStore for testability  
3. **Registry/Plugin Pattern**: New providers or parsers follow OCP — just create a new file with the appropriate protocol, add registration code

### Adding a New LLM Provider

1. Create `src/ragapp/core/providers/<name>.py` with class implementing `ProviderProtocol.chat()`
2. Register in `core/providers/__init__.py`: `register("prefix-", MyProvider)`
3. Add model options to `ui/components/provider_catalog.py` for UI dropdown population

### Adding a New Document Parser

1. Create `src/ragapp/core/parsers/<name>_parser.py` with class implementing `ParserProtocol.parse()`
2. Register in `core/parsers/__init__.py`: `@register("ext")` decorator on the parser class  
3. No changes to existing parsers or dispatcher required (OCP)

See [SOLID_REFACTORING_PLAN.md](SOLID_REFACTORING_PLAN.md) for detailed refactoring rationale and implementation notes.

## Project Overview

This is a Streamlit-based Retrieval-Augmented Generation (RAG) application that allows users to:
- Ingest local documents (PDF, DOCX, TXT, CSV) into a persistent vector database (ChromaDB)
- Query documents using LLMs (OpenAI GPT, Anthropic Claude, Google Gemini, Groq, Ollama, LM Studio, HuggingFace)

## Core Components

| File | Purpose |
|------|---------|
| `src/ragapp/app.py` | Main Streamlit UI with Builder and Query tabs |
| `src/ragapp/core/llm.py` | LLM abstraction layer for OpenAI, Anthropic, Gemini, Groq, Ollama, LM Studio, HuggingFace |
| `src/ragapp/core/parser.py` | File parsing and chunking for PDF, TXT, CSV, DOCX |
| `src/ragapp/core/vector_store.py` | ChromaDB persistence wrapper |
| `src/ragapp/config.py` | Pydantic settings with .env loading |

## Skills

### `debug_rag` (skill://debug_rag)
**Purpose:** Debug runtime issues with the RAG application.

**What it does:**
- Check environment variable loading and .env file validity
- Verify LLM provider connectivity (API keys, network)
- Inspect vector store state (collection size, embedding status)
- Trace document parsing pipeline failures
- Identify Streamlit session state issues

**When to use:**
- User reports "Missing API Key" errors
- Database appears empty or corrupted
- LLM responses are failing or returning errors
- Document upload/processing fails

**Common diagnostics:**
```bash
# Check environment
uv run python -c "from config import settings; print(settings)"
uv run python -c "from core.vector_store import VectorStore; vs = VectorStore(); print(f'Count: {vs.get_collection_size()}')"
uv run python -c "from core.llm import get_llm_response; print(get_llm_response('test', 'gpt-4o-mini'))"
```

### `query_rag` (skill://query_rag)
**Purpose:** Execute queries against the RAG system programmatically.

**What it does:**
- Direct query execution without UI
- Bypass Streamlit session state
- Test RAG retrieval quality
- Extract results in structured format

**When to use:**
- Validate query performance without UI overhead
- Write automated tests
- Extract RAG responses in scripts
- Test different n_results parameters

**Usage pattern:**
```python
from core.vector_store import VectorStore
vs = VectorStore()
results = vs.query("your question here", n_results=5)
for r in results:
    print(f"Distance: {r['distance']}, Text: {r['text'][:100]}")
```

### `test_parser` (skill://test_parser)
**Purpose:** Test document parsing for different file formats.
**What it does:**
- Validates PDF, TXT, CSV, DOCX parsing
- Checks chunk generation and metadata
- Identifies encoding or format errors
- Reports on parsing quality
**When to use:**
- Adding new document formats
- Debugging document processing failures
- Verifying chunk sizes and content
- Testing edge cases (empty files, large files)
**Testing command:**
```python
from core.parser import process_file
import io
chunks = process_file(io.BytesIO(b"test content"))
print(f"TXT chunks: {len(chunks)}")
```
### `inspect_core_module`
**Purpose:** Analyze and explain core module internals.

**What it does:**
- Trace data flow through pipeline stages
- Explain class/method contracts
- Identify dependencies and side effects
- Map function signatures to responsibilities

**When to use:**
- Understanding chunking behavior
- Debugging embedding selection (OpenAI vs SentenceTransformer)
- Understanding metadata schema for stored documents
- Tracing query result formatting

**Key data structures:**
- Document chunk: `{'id': str, 'text': str, 'metadata': {'source': str, 'page'|'chunk'|'row'|'paragraph': int}}`
- Query result: `{'id': str, 'text': str, 'metadata': dict, 'distance': float}`

### `manage_chromadb` (skill://manage_chromadb)
**Purpose:** Inspect and manage ChromaDB persistence layer.
**What it does:**
- Check database path and collection configuration
- Inspect disk usage and collection metadata
- Handle database lifecycle (create, delete, recreate)
- Verify embedding function configuration
**When to use:**
- "Database is empty" errors after restart
- Vector store fails to initialize
- User wants to reset entire knowledge base
- Investigating storage paths
**Commands:**
```python
from core.vector_store import VectorStore
vs = VectorStore()
print(f"Documents: {vs.get_collection_size()}")
print(f"DB path: {vs.db_path}")
# To clear (destructive):
# vs.delete_collection()
```
**Embedding configuration:**
- If `OPENAI_API_KEY` set → uses OpenAI `text-embedding-3-small`
- Otherwise → ChromaDB defaults to SentenceTransformer

## API Keys and Configuration

Required environment variables (see `src/ragapp/.env.example`):

| Variable | Purpose | Default |
|----------|---------|---------|
| `OPENAI_API_KEY` | OpenAI/GPT model access | empty |
| `ANTHROPIC_API_KEY` | Anthropic/Claude access | empty |
| `GOOGLE_API_KEY` | Google Gemini access | empty |
| `GROQ_API_KEY` | Groq API access | empty |
| `HUGGINGFACE_API_KEY` | HuggingFace Inference API access | empty |
| `CHROMA_DB_PATH` | Vector store persistence path | `./chroma_db` |
| `COLLECTION_NAME` | ChromaDB collection name | `my_rag_collection` |
| `DEFAULT_LLM` | Default model selector | `gpt-4o-mini` |
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434/v1` |
| `LM_STUDIO_BASE_URL` | LM Studio server URL | `http://localhost:1234/v1` |

## Provider Model Prefixes

Model names are prefixed to route to the correct provider in `get_llm_response`:

| Prefix | Provider | Example |
|--------|----------|---------|
| `groq:` | Groq (cloud) | `groq:llama-3.1-8b-instant` |
| `ollama:` | Ollama (local) | `ollama:llama3.1` |
| `lmstudio:` or `lm-studio:` | LM Studio (local) | `lmstudio:llama-3.1-instruct` |
| *none* (Hub ID pattern) | HuggingFace Inference API | `meta-llama/Llama-3.3-70B-Instruct` |
| No prefix (`gpt-*`) | OpenAI | `gpt-4o-mini` |
| No prefix (`claude-*`) | Anthropic | `claude-3-haiku-20240307` |
| No prefix (`gemini-*`) | Google Gemini | `gemini-pro` |

### Dynamic Model Discovery

For **Ollama** and **LM Studio**, the app fetches available models at runtime:
- Ollama: queries `{OLLAMA_BASE_URL}/api/tags`
- LM Studio: queries `{LM_STUDIO_BASE_URL}/v1/models`

If the server is unreachable, a fallback default model is used with a warning.

### Quit Button

A **⏹️ Quit App** button in the sidebar stops Streamlit execution via `st.stop()`. Use it to halt the app without closing the browser window.
## File Format Support

| Format | Parser | Metadata |
|--------|--------|----------|
| `.pdf` | `pypdf` | source, page |
| `.txt` | native | source, chunk |
| `.csv` | `pandas` | source, row |
| `.docx` | `python-docx` | source, paragraph |

## Common Patterns

### Document chunk structure
```python
{
    'id': str,          # uuid4
    'text': str,        # extracted text content
    'metadata': {       # source-specific
        'source': str,  # original filename
        'page': int     # PDF only
        'chunk': int    # TXT only
        'row': int      # CSV only
        'paragraph': int  # DOCX only
    }
}
```

### LLM response handling
The `get_llm_response` function returns either:
- LLM-generated text content
- Error string prefixed with `⚠️` for missing keys or API failures
- Fallback message for unsupported models

### Embedding selection priority
1. If `OPENAI_API_KEY` set → uses OpenAI `text-embedding-3-small`
2. Otherwise → ChromaDB defaults to SentenceTransformer locally
