# SOLID Refactoring Plan — RAG App

## Summary of Findings

| Principle | Violations Found | Severity |
|-----------|-----------------|----------|
| **SRP** (Single Responsibility) | 4 | High |
| **OCP** (Open/Closed) | 2 | High |
| **LSP** (Liskov Substitution) | 0 | — |
| **ISP** (Interface Segregation) | 2 | Medium |
| **DIP** (Dependency Inversion) | 3 | High |
| **Cross-cutting structural issues** | 6 | Medium |

Total: **17 actionable items**, grouped into **4 phases**.

---

## PHASE 1 — Extract LLM Routing Layer (OCP + DIP + SRP)

### Goal
Replace the monolithic `get_llm_response` function with a strategy-based provider interface so new providers can be added without modifying existing code.

### Current Problem (`src/ragapp/core/llm.py`)
- `get_llm_response` is a 205-line function handling **7 different providers** via if/elif chains.
- Provider selection, prompt templating, API calls, and error handling are all in one function.
- Hard to test individual provider implementations.
- Adding a new provider requires editing this function (OCP violation).

### Target Architecture

```
src/ragapp/core/llm.py          — Strategy interface + provider registry
src/ragapp/core/providers/
├── __init__.py                 — ProviderProtocol definition
├── base.py                     — BaseProvider abstract class
├── openai.py                   — OpenAI (and Groq as subclass)
├── anthropic.py                — Anthropic/Claude provider
├── gemini.py                   — Google Gemini provider
├── ollama.py                   — Ollama provider (OpenAI-compatible wrapper)
├── lm_studio.py               — LM Studio provider (OpenAI-compatible wrapper)
├── huggingface.py              — HuggingFace Inference API provider
└── routing.py                  — Provider lookup, registry, prefix dispatch
```

### Concrete Changes

#### 1. Define a `ProviderProtocol` (abstract base class)

Create `src/ragapp/core/providers/base.py`:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol

@dataclass
class ChatMessage:
    role: str       # "system" | "user" | "assistant"
    content: str

@dataclass
class ChatCompletion:
    content: str

class ProviderError(Exception):
    """Base exception for provider-level errors."""

class MissingKeyError(ProviderError):
    """Raised when an API key is not configured."""

class Provider(Protocol):
    @abstractmethod
    def chat(self, messages: list[ChatMessage], temperature: float = 0.0) -> str: ...

class BaseProvider(ABC):
    name: str                          # class attribute for display
    priority: int = 50                 # lower = checked first in registry

    @abstractmethod
    def chat(self, messages: list[ChatMessage], temperature: float = 0.0) -> str: ...

    def validate_key(self, key_name: str) -> None:
        """Raise MissingKeyError if env var is not set."""
        import os
        if not os.environ.get(key_name):
            raise MissingKeyError(f"`{key_name}` is missing in the environment.")
```

#### 2. Implement each provider

**`src/ragapp/core/providers/openai.py`:**
- `OpenAIProvider(BaseProvider)` — uses `openai.OpenAI` client.
- Class attribute `name = "OpenAI"`, handles models not prefixed with anything or starting with `gpt:`.
- `GroqProvider(OpenAIProvider)` sets `name = "Groq"` and overrides `chat()` to set `base_url="https://api.groq.com/openai/v1"` via a property or constructor parameter.

**`src/ragapp/core/providers/anthropic.py`:**
- `AnthropicProvider(BaseProvider)` — uses `anthropic.Anthropic` client.
- Validates `ANTHROPIC_API_KEY`, maps `claude-*` models.

**`src/ragapp/core/providers/gemini.py`:**
- `GeminiProvider(BaseProvider)` — lazy-imports `google.generativeai`.
- Validates `GOOGLE_API_KEY`.

**`src/ragapp/core/providers/ollama.py`:**
- `OllamaProvider(BaseProvider)` — creates an OpenAI-compatible client with custom `base_url`.

**`src/ragapp/core/providers/lm_studio.py`:**
- `LMStudioProvider(BaseProvider)` — same pattern as Ollama but different base URL.

**`src/ragapp/core/providers/huggingface.py`:**
- `HuggingFaceProvider(BaseProvider)` — uses raw `requests.post()`.
- Validates `HUGGINGFACE_API_KEY`. Handles both list and string response formats.

#### 3. Create the Router (`src/ragapp/core/providers/routing.py`)

```python
from .base import Provider, MissingKeyError, ProviderError

_REGISTRY: dict[str, type[Provider]] = {}   # prefix → provider class

def register(prefix: str):
    """Decorator to register a provider for a model name prefix."""
    def wrapper(cls):
        _REGISTRY[prefix] = cls
        return cls
    return wrapper

def resolve_provider(llm_model: str) -> Provider:
    """Return a configured Provider instance for the given model string."""
    model_lower = llm_model.lower().strip()

    # Check registered prefixes first (most specific → least specific)
    for prefix, provider_cls in sorted(_REGISTRY.items(), key=lambda x: -len(x[0])):
        if model_lower.startswith(prefix):
            instance = provider_cls(model=llm_model)
            return instance

    # Hub-ID pattern (user/model) — HuggingFace
    import re
    if re.match(r"^[\w-]+/[\w.-]+$", llm_model.strip()):
        return _REGISTRY[""](model=llm_model)  # empty prefix = HuggingFace default

    raise ValueError(f"Unsupported model provider: {llm_model}")

# Import all providers to register them (side-effect registration)
from . import openai, anthropic, gemini, ollama, lm_studio, huggingface  # noqa: F401
```

#### 4. Rewrite `src/ragapp/core/llm.py` — thin facade

```python
from .providers.routing import resolve_provider
from .providers.base import MissingKeyError

def get_llm_response(query_context: str, llm_model: str, *, temperature: float = 0.2) -> str:
    """Query the LLM for the given model and context."""
    messages = [
        {"role": "system", "content": (
            "You are a highly capable research assistant. Answer the user's query "
            "strictly based on the provided context. If the context does not contain "
            "sufficient information, respectfully state that."
        )},
        {"role": "user", "content": f"{query_context}\n\n=== USER QUERY ===\n"},
    ]

    try:
        provider = resolve_provider(llm_model)
    except ValueError as e:
        return f"⚠️ {e}"

    try:
        return provider.chat(messages, temperature=temperature)
    except MissingKeyError as e:
        return f"⚠️ Error: {e}"
    except Exception as e:
        return f"⚠️ {type(provider).__name__} API Error: {e}"
```

#### 5. Delete `app.py` helper functions

- Remove `fetch_ollama_models()` and `fetch_lm_studio_models()` from `app.py`.
- Create a `ProviderCatalog` class (or add to `routing.py`) that exposes an `.available_models(base_url)` method per-provider for the UI dropdown population.

### Verification Checklist
- [ ] All 7 provider implementations exist as separate files
- [ ] Adding an 8th provider requires creating one new file and a decorator call — zero changes to `llm.py` or other providers
- [ ] `get_llm_response()` is under 30 lines
- [ ] Each provider can be unit-tested in isolation (mock its API client)
- [ ] Existing tests (`test_llm_routing.py`) still pass

---

## PHASE 2 — Extract Parser Strategy Layer (SRP + OCP + DIP)

### Goal
Replace the monolithic `process_file` function with a format-specific parser registry.

### Current Problem (`src/ragapp/core/parser.py`)
- One 76-line `if/elif` chain for PDF, TXT, CSV, DOCX.
- New formats require editing this function.
- No separation between parsing (file I/O) and chunking (text splitting).
- File extension detection is case-sensitive (`split(".")[-1].lower()`), but doesn't handle edge cases like `file.PDF` or double extensions.

### Target Architecture

```
src/ragapp/core/parser.py           — Entry point + registry
src/ragapp/core/parsers/
├── __init__.py                     — ParserProtocol, registry decorator
├── pdf_parser.py                   — PDF parsing (pypdf)
├── txt_parser.py                   — TXT chunking
├── csv_parser.py                   — CSV parsing (pandas)
└── docx_parser.py                  — DOCX parsing (python-docx)
```

### Concrete Changes

#### 1. Define the ParserProtocol

Create `src/ragapp/core/parsers/__init__.py`:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

@dataclass(frozen=True)
class Chunk:
    text: str
    metadata: dict  # e.g. {"source": "file.pdf", "page": 1, "paragraph": 0}

@runtime_checkable
class Parser(Protocol):
    @property
    def supported_extensions(self) -> tuple[str, ...]: ...

    @abstractmethod
    def parse(self, file) -> list[Chunk]: ...

class BaseParser(ABC):
    """Base class with shared utilities."""
    @staticmethod
    def _make_id() -> str:
        import uuid
        return str(uuid.uuid4())

    @staticmethod
    def _clean(text: str) -> str:
        return text.strip() if text else ""
```

#### 2. Implement individual parsers

Each parser is a thin class implementing `Parser`:

**`pdf_parser.py`:** Uses `pypdf.PdfReader`. Extracts pages, splits paragraphs, produces chunks with `{"source", "page", "paragraph"}` metadata.

**`txt_parser.py`:** Reads file bytes as UTF-8, applies 1000-char sliding window chunking with word-boundary detection. Produces chunks with `{"source", "chunk"}` metadata.

**`csv_parser.py`:** Uses `pandas.read_csv()`, converts each row to `" | ".join(...)`. Produces chunks with `{"source", "row"}` metadata.

**`docx_parser.py`:** Uses `Document()` from `python-docx`, iterates paragraphs. Produces chunks with `{"source", "paragraph"}` metadata.

#### 3. Rewrite registry + dispatch (`src/ragapp/core/parser.py`)

```python
from .parsers import Chunk, Parser
import importlib.metadata

_REGISTRY: dict[str, type[Parser]] = {}   # extension → parser class

def register(*extensions: str):
    def wrapper(cls):
        for ext in extensions:
            _REGISTRY[ext.lower()] = cls
        return cls
    return wrapper

def process_file(file) -> list[Chunk]:
    """Route an uploaded file to the correct parser and return chunks."""
    fname = getattr(file, "name", "")
    ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""

    parser_cls = _REGISTRY.get(ext)
    if not parser_cls:
        raise ValueError(f"Unsupported file format: .{ext}")

    instance = parser_cls()
    return instance.parse(file)

# Auto-register all parsers on import
from .parsers import pdf_parser, txt_parser, csv_parser, docx_parser  # noqa: F401
```

### Verification Checklist
- [ ] Each parser is a separate file with one format only
- [ ] Adding a new format (e.g., `.epub`) requires one new file + `@register("epub")` — zero changes to existing parsers
- [ ] `process_file()` is under 20 lines
- [ ] Unsupported formats raise a clear `ValueError` instead of silently returning empty list

---

## PHASE 3 — Extract VectorStore Responsibilities (SRP + ISP)

### Goal
Separate embedding configuration from vector store persistence. Add dependency injection for the settings object.

### Current Problems (`src/ragapp/core/vector_store.py`)
- Constructor does too much: reads settings, configures embeddings, creates ChromaDB client and collection.
- Embedding function selection is coupled to `os.environ.get("OPENAI_API_KEY")` inside the class — should be a factory decision.
- No way to inject a test vector store (e.g., in-memory) for unit tests.
- `typing.cast(...)` around embedding function is a workaround that masks real type issues.

### Target Architecture

```
src/ragapp/core/vector_store.py       — VectorStore (persistence only)
src/ragapp/core/embedding_function.py — Factory: returns OpenAI or SentenceTransformer
```

### Concrete Changes

#### 1. Create embedding factory (`src/ragapp/core/embedding_function.py`)

```python
def create_embedding_function() -> chromadb.EmbeddingFunction[chromadb.Documents] | None:
    """Return the configured embedding function, or None (ChromaDB default)."""
    if os.environ.get("OPENAI_API_KEY"):
        from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
        return OpenAIEmbeddingFunction(
            api_key=os.environ["OPENAI_API_KEY"],
            model_name="text-embedding-3-small",
        )
    return None  # ChromaDB uses SentenceTransformer locally by default
```

#### 2. Rewrite VectorStore (constructor-only changes)

```python
class VectorStore:
    def __init__(self, db_path: str | None = None, collection_name: str | None = None):
        """Initialize with optional explicit paths; defaults to settings."""
        from .config import settings as cfg
        self.db_path = db_path or cfg.db_path
        self.collection_name = collection_name or cfg.collection_name

        self._client = chromadb.PersistentClient(path=self.db_path)
        self._embedding_fn = create_embedding_function()
        self._collection: chromadb.Collection | None = None

    @property
    def collection(self) -> chromadb.Collection:
        if self._collection is None:
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self._embedding_fn,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def add_documents(self, documents: list[dict]) -> int:
        ids = [doc["id"] for doc in documents]
        docs = [doc["text"] for doc in documents]
        metadatas = [doc.get("metadata", {}) for doc in documents]
        self.collection.add(ids=ids, documents=docs, metadatas=metadatas)
        return len(documents)

    def get_collection_size(self) -> int:
        return self.collection.count()

    def query(self, query_text: str, n_results: int = 3) -> list[dict]:
        if not self.collection or self.collection.count() == 0:
            return []
        try:
            results = self.collection.query(query_texts=[query_text], n_results=n_results)
            return [
                {"id": ids[i], "text": docs[i], "metadata": metas[i], "distance": dists[i]}
                for i in range(len(results["ids"][0]))
            ]
        except Exception:
            return []

    def delete_collection(self) -> None:
        self._client.delete_collection(self.collection_name)
        self._collection = None  # invalidate cache
```

#### 3. Remove `_get_or_create_collection` and `typing.cast` from original

### Verification Checklist
- [ ] VectorStore constructor no longer reads env vars directly — embedding selection is delegated to the factory
- [ ] Constructor accepts optional `db_path` and `collection_name` for test injection
- [ ] No more `typing.cast` workaround
- [ ] Collection cache invalidation on `delete_collection()`
- [ ] Existing integration tests pass

---

## PHASE 4 — Clean Up app.py (SRP + ISP + DIP)

### Goal
Split the ~270-line Streamlit app into smaller, focused modules. Inject dependencies instead of importing globals directly.

### Current Problem (`src/ragapp/app.py`)
- One file handles: page config, session state, sidebar UI, provider status checks, 7 model dropdowns, document upload, RAG query execution, quit button, Google Search link.
- No testable logic — all code is Streamlit side-effect calls (`st.*`, `os.environ.get()`).
- `_key_checks` dict (lines 84-92) and provider-specific UI are tightly coupled to specific providers.

### Target Architecture

```
src/ragapp/app.py                     — Entry point: import & run components
src/ragapp/ui/
├── sidebar.py                        — Sidebar config, model selector, key status
├── builder_tab.py                    — Builder tab (file upload, process button)
├── query_tab.py                      — Query tab (input, search button, results display)
└── components/
    ├── provider_catalog.py            — Model discovery for local providers
    └── status_indicators.py           — Key status + DB status widgets
```

### Concrete Changes

#### 1. Provider catalog (`src/ragapp/ui/components/provider_catalog.py`)

Replace `fetch_ollama_models()` and `fetch_lm_studio_models()`:

```python
@dataclass
class ProviderInfo:
    name: str
    key_env: str | None       # API key env var, or None for local servers
    model_options: list[str]  # Static model dropdown options
    discover_models: Callable[[str], list[str]] | None = None  # Dynamic discovery

PROVIDERS: list[ProviderInfo] = [
    ProviderInfo(
        name="OpenAI", key_env="OPENAI_API_KEY",
        model_options=["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
    ),
    ProviderInfo(
        name="Anthropic", key_env="ANTHROPIC_API_KEY",
        model_options=["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
    ),
    # ... one per provider, each with its own model options
]
```

#### 2. Sidebar builder (`src/ragapp/ui/sidebar.py`)

```python
def render_sidebar(vs: VectorStore):
    """Render sidebar configuration widget group."""
    with st.sidebar:
        st.header("Configuration")

        provider = st.radio(
            "LLM Provider",
            options=[p.name for p in PROVIDERS],
            index=0,
        )
        provider_info = next(p for p in PROVIDERS if p.name == provider)

        # Key status
        render_key_status(provider_info.key_env)

        # Model selector
        available = (
            provider_info.discover_models(os.environ.get(base_url_key))
            if provider_info.discover_models else provider_info.model_options
        )
        selected_model = st.selectbox("Select Model", available, index=0, key="_selected_model")

        # Temperature slider
        st.slider("Temperature", 0.0, 1.0, settings.llm_temperature, step=0.05, key="_temp_slider")

        render_db_status(vs)
```

#### 3. Builder tab (`src/ragapp/ui/builder_tab.py`)

```python
def render_builder(vs: VectorStore):
    """Render the document builder tab."""
    st.header("Build Your Knowledge Base")
    uploaded_files = st.file_uploader(
        "Select files to index", type=["pdf", "txt", "docx", "csv"], accept_multiple_files=True
    )

    if uploaded_files and st.button("Process & Ingest Documents"):
        _process_and_ingest(vs, uploaded_files)
```

#### 4. Query tab (`src/ragapp/ui/query_tab.py`)

```python
def render_query_tab(vs: VectorStore, llm_model: str):
    """Render the query tab with RAG execution."""
    if vs.get_collection_size() == 0:
        st.warning("Database is empty.")
        return

    user_query = st.text_input("What would you like to know?", placeholder="e.g., 'What are the main themes?'")

    if st.button("Search & Answer"):
        _execute_rag(vs, user_query, llm_model)
```

#### 5. Thin `app.py` entry point

```python
from ui.sidebar import render_sidebar
from ui.builder_tab import render_builder
from ui.query_tab import render_query_tab
from config import settings

st.set_page_config(page_title="Local RAG Assistant", page_icon="📚", layout="wide")

if "vector_store" not in st.session_state:
    st.session_state.vector_store = VectorStore()

quit_html = """..."""  # Keep as-is; it's UI-specific and untestable anyway

tab_build, tab_query = st.tabs(["Builder (Create DB)", "Query (Ask Questions)"])

with tab_build:
    render_builder(st.session_state.vector_store)

with tab_query:
    llm_model = st.session_state.get("_selected_model", settings.default_llm)
    render_query_tab(st.session_state.vector_store, llm_model)
```

### Verification Checklist
- [ ] `app.py` is under 50 lines of actual logic (not just imports/boilerplate)
- [ ] All UI modules accept dependencies as function parameters (no module-level `st.*` calls in non-render functions)
- [ ] Key status rendering is parameterized (no hardcoded provider checks in app.py)
- [ ] Model selector data is driven by `PROVIDERS` catalog, not if/elif chains

---

## CROSS-CUTTING FIXES (Applied Throughout All Phases)

### C1. Eliminate try/except import anti-pattern
**Where:** `llm.py:10-15`, `vector_store.py:6-9`

Both files use `try: from config import settings except ImportError: from config import settings`.

**Fix:** Centralize in `config.py`:
```python
# At top of config.py — always succeeds:
_SETTINGS = Settings()  # .env loading handled automatically
```
All modules do `from config import settings` (when running from within `src/ragapp`) or use a single `_resolve_settings()` function in a shared `_utils.py` module.

### C2. Standardize error types
**Where:** All modules return `⚠️ Error:` prefixed strings for user display.

**Fix:** Define exception hierarchy:
```python
class RAGError(Exception): pass
class KeyMissingError(RAGError): pass
class UnsupportedModelError(RAGError): pass
class ParseError(RAGError): pass
class StorageError(RAGError): pass
```
Business logic returns exceptions; UI layer catches and renders `⚠️` messages. This makes testing possible.

### C3. Add type annotations across the board
**Where:** All four modules have minimal or no type hints on public functions.

**Fix:** Annotate all public function signatures:
```python
def process_file(file) -> list[Chunk]:          → def process_file(file: UploadedFile) -> list[Chunk]:
def get_llm_response(query_context, llm_model) → def get_llm_response(query_context: str, llm_model: str, *, temperature: float = 0.2) -> str:
```

### C4. Extract MAX_FILE_SIZE as a named constant
**Where:** `app.py:210` — `_MAX_FILE_SIZE = 50 * 1024 * 1024`

**Fix:** Move to config: `max_file_size_bytes: int = Field(default=50 * 1024 * 1024, validation_alias="MAX_FILE_SIZE")`

### C5. Extract query result formatting from app.py into vector_store
**Where:** `app.py:249-264` — context string joining and source metadata rendering logic lives in UI layer.

**Fix:** Add method to VectorStore:
```python
def format_results(self, results: list[dict], max_text_length: int = 500) -> str:
    """Format query results into a readable context string for LLM."""
    ...

def format_sources(self, results: list[dict]) -> list[dict]:
    """Extract formatted source info for UI display."""
    ...
```

### C6. Extract temperature/max_tokens from global settings lookup
**Where:** `llm.py:44-46` — `_get_settings()` is called inside every response.

**Fix:** Pass temperature as explicit parameter to `get_llm_response`, and resolve settings at call site (or cache in the provider constructor, not on every invocation).

---

## FILE CHANGE SUMMARY

| File | Action | Lines → New Lines |
|------|--------|-------------------|
| `src/ragapp/core/llm.py` | Truncate to ~30-line facade | 205 → ~30 |
| `src/ragapp/core/providers/*` | **NEW** — 7 provider files + routing | 0 → ~200 |
| `src/ragapp/core/parser.py` | Truncate to ~15-line dispatch | 76 → ~15 |
| `src/ragapp/core/parsers/*` | **NEW** — 4 parser files | 0 → ~100 |
| `src/ragapp/core/vector_store.py` | Simplify constructor, lazy collection | ~95 → ~50 |
| `src/ragapp/core/embedding_function.py` | **NEW** — embedding factory | 0 → ~20 |
| `src/ragapp/app.py` | Thin entry point | ~270 → ~40 |
| `src/ragapp/ui/*` | **NEW** — 4 UI modules + components | 0 → ~150 |
| `src/ragapp/core/config.py` | Minor: add max_file_size field | 33 → ~36 |

**Net file count:** +14 new files, -1 monolithic app.py effectively replaced by modular structure.

---

## IMPLEMENTATION ORDER FOR AGENT

Execute phases strictly in this order (each phase depends on the previous being complete):

### Step 1: Phase 1 — LLM Routing Layer
1. Create `src/ragapp/core/providers/` directory
2. Write `base.py` with `ProviderProtocol`, `BaseProvider`, exception classes
3. Write each provider implementation file (openai, anthropic, gemini, ollama, lm_studio, huggingface)
4. Write `routing.py` with registry + decorator + `resolve_provider()`
5. Rewrite `llm.py` as thin facade (~30 lines)
6. Run existing tests: `uv run pytest tests/test_llm_routing.py -v`

### Step 2: Phase 2 — Parser Layer
1. Create `src/ragapp/core/parsers/` directory
2. Write `__init__.py` with `Chunk` dataclass, `ParserProtocol`, registry decorator
3. Write each parser implementation (pdf_parser, txt_parser, csv_parser, docx_parser)
4. Rewrite `parser.py` as thin dispatch (~15 lines)
5. Run existing tests: `uv run pytest tests/test_parser.py -v`

### Step 3: Phase 3 — VectorStore Cleanup
1. Create `embedding_function.py` factory
2. Rewrite `vector_store.py` (constructor simplification, lazy collection, dependency injection for test paths)
3. Verify no more `typing.cast` or direct env var reads in VectorStore

### Step 4: Phase 4 — App Cleanup
1. Create `src/ragapp/ui/` directory structure
2. Write `components/provider_catalog.py` with `PROVIDERS` list
3. Write `ui/sidebar.py` — parameterized sidebar renderer
4. Write `ui/builder_tab.py` — file upload handler
5. Write `ui/query_tab.py` — RAG query execution
6. Rewrite `app.py` as thin entry point (~40 lines)

### Step 5: Cross-Cutting Fixes
1. Add `RAGError` exception hierarchy (all files reference it instead of string prefixes)
2. Add type annotations to all public function signatures
3. Move `_MAX_FILE_SIZE` to config.py
4. Extract result formatting into VectorStore methods
5. Fix import resolution — single source of truth in config.py

### Final Verification
- Run full test suite: `uv run pytest -v`
- Manual Streamlit smoke test: `uv run streamlit run src/ragapp/app.py`
- Verify all 7 providers work (API keys configured)
- Test all 4 file formats upload correctly
- Test clearing database and querying still works
