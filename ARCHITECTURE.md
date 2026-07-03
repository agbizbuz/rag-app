# Architecture Document

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Core Modules](#core-modules)
4. [Ingestion Pipeline](#ingestion-pipeline)
5. [Query & Retrieval Flow](#query--retrieval-flow)
6. [Provider Routing](#provider-routing)
7. [Parser Registry](#parser-registry)
8. [Evaluation Framework](#evaluation-framework)
9. [Configuration & Dependency Injection](#configuration--dependency-injection)

---

## Overview

This is a **Streamlit-based RAG application** that ingests local documents into a ChromaDB vector store and answers queries using pluggable LLM backends. The codebase is organized in four layers:

| Layer | Location | Responsibility |
|---|---|---|
| **UI** | `src/ragapp/ui/` | Streamlit widgets, tab rendering, session state management |
| **Core** | `src/ragapp/core/` | Business logic — parsers, providers, retrievers, vector store |
| **Config** | `src/ragapp/config_provider.py` | Singleton settings + API key getters |
| **Root** | `src/ragapp/app.py` | Streamlit entry point, session-state wiring, tab orchestration |

---

## System Architecture

```mermaid
graph TB
    subgraph UI["UI Layer (Streamlit)"]
        App["app.py\nTab Orchestration"]
        Builder["builder_tab.py\nUpload + Ingest"]
        Query["query_tab.py\nSearch & Answer"]
        Eval["evaluation_tab.py\nPerformance Dashboard"]
        DBInfo["db_tab.py\nDatabase Management"]
        Sidebar["sidebar.py\nProvider / Model Selector"]
    end

    subgraph Core["Core Layer"]
        VS["vector_store.py\nChromaDB CRUD"]
        Retriever["retriever.py\nRAGRetriever"]
        Hybrid["hybrid_retriever.py\nBM25 + Semantic RRF"]
        Keyword["keyword_search.py\nBM25Scorer"]
        EmbedMgr["embedding_manager.py\nEmbedding Config"]
        Evaluator["evaluator.py\nLLM-Judge"]
        LLM["llm.py\nget_llm_response"]
        Parser["parser.py\nprocess_file"]

        subgraph Parsers["Document Parsers"]
            BaseP["base.py\nChunk, ParserProtocol"]
            PDF["pdf_parser.py"]
            TXT["txt_parser.py"]
            CSV["csv_parser.py"]
            DOCX["docx_parser.py"]
        end

        subgraph Providers["LLM Providers"]
            BasePr["base.py\nProvider, ChatMessage"]
            Routing["routing.py\nRegistry + resolve_provider"]
            OpenAI["openai.py"]
            Anthropic["anthropic.py"]
            Gemini["gemini.py"]
            Ollama["ollama.py"]
            LMStudio["lm_studio.py"]
            HF["huggingface.py"]
        end
    end

    subgraph Config["Configuration"]
        CP["config_provider.py\nConfigProvider Singleton"]
        Env[".env / os.environ"]
    end

    subgraph Storage["Persistence"]
        ChromaDB["chroma_db/\nChromaDB Collection"]
        EvalLog["evaluation_logs.json\nEvaluation Records"]
    end

    App --> Builder
    App --> Query
    App --> Eval
    App --> DBInfo
    App --> Sidebar

    Builder --> Parser
    Parser --> Parsers
    Parser --> VS
    VS --> ChromaDB

    Query --> Retriever
    Query --> LLM
    Query --> Evaluator
    Retriever --> Hybrid
    Retriever --> VS
    Hybrid --> Keyword
    Hybrid --> VS
    LLM --> Routing
    Routing --> Providers
    Evaluator --> EvalLog

    Sidebar --> CP
    Parser -. reads .-> CP
    Retriever -. reads .-> CP
    EmbedMgr -. used by .-> VS
    VS -. uses .-> EmbedMgr
```

---

## Core Modules

### Class Hierarchy — Retrieval

```mermaid
classDiagram
    class RAGRetriever {
        +VectorStore vector_store
        +ConfigProvider _config
        +retrieve(query, n_results) list[dict]
        +format_context(results) str
        +retrieve_formatted_context(query, n_results) str
    }

    class HybridRetriever {
        +int _rrf_k
        +retrieve(query, n_results) list[dict]
        -_reciprocal_rank_fusion(semantic, keyword, k) list[dict]
    }

    class KeywordSearcher {
        +BM25Okapi _bm25
        +list _documents
        +search(query, n_results) list[dict]
    }

    class VectorStore {
        +chromadb.Client _client
        +EmbeddingManager _embedding_manager
        +add_documents(chunks) int
        +query(query_text, n_results) list[dict]
        +get_collection_size() int
        +get_all_files() list[dict]
        +delete_collection() void
    }

    class EmbeddingManager {
        +get_embedding_function() Optional[object]
        +is_openai bool
    }

    HybridRetriever --|> RAGRetriever : inherits
    HybridRetriever --> KeywordSearcher : composes
    HybridRetriever --> VectorStore : delegates
    RAGRetriever --> VectorStore : delegates
    VectorStore --> EmbeddingManager : uses
```

### Class Hierarchy — Providers & Parsers

```mermaid
classDiagram
    class Provider {
        <<ABC>>
        +str name
        +abstract chat(messages, temperature) str
        +validate_key(key_name) void
    }

    class ProviderProtocol {
        <<Protocol>>
        +chat(messages, temperature) str
    }

    class OpenAIProvider {
        +chat(messages, temperature) str
    }

    class AnthropicProvider {
        +chat(messages, temperature) str
    }

    class GeminiProvider {
        +chat(messages, temperature) str
    }

    class OllamaProvider {
        +model str (stripped prefix)
        +base_url str
        +chat(messages, temperature) str
    }

    class LMStudioProvider {
        +chat(messages, temperature) str
    }

    class HuggingFaceProvider {
        +chat(messages, temperature) str
    }

    class _Registry {
        -list[tuple] _registry
        +register(prefix, provider_class)
        +resolve_provider(model_id) type
    }

    class Chunk {
        <<frozen dataclass>>
        +str text
        +dict metadata
    }

    class Parser {
        <<Protocol>>
        +supported_extensions tuple[str]
        +parse(file) list[Chunk]
    }

    class BaseParser {
        <<ABC>>
        +_make_id() str
        +_clean(text) str
    }

    class PdfParser
    class TxtParser
    class CsvParser
    class DocxParser

    Provider <|-- ProviderProtocol : implements
    OpenAIProvider --|> Provider : extends
    AnthropicProvider --|> Provider : extends
    GeminiProvider --|> Provider : extends
    OllamaProvider --|> Provider : extends
    LMStudioProvider --|> Provider : extends
    HuggingFaceProvider --|> Provider : extends
    _Registry --> Provider : registers

    Chunk --> Parser : returned by
    BaseParser <|-- PdfParser : implements
    BaseParser <|-- TxtParser : implements
    BaseParser <|-- CsvParser : implements
    BaseParser <|-- DocxParser : implements
```

---

## Ingestion Pipeline

```mermaid
sequenceDiagram
    participant U as UI (Builder Tab)
    participant A as app.py
    participant P as parser.py
    participant REG as Parser Registry
    participant V as VectorStore
    participant CH as ChromaDB

    U->>A: file_uploader (PDF/TXT/CSV/DOCX)
    A->>P: process_file(uploaded_file)
    P->>P: extract extension from filename

    alt .pdf
        P->>REG: _EXTENSION_MAP["pdf"]
        REG-->>P: PdfParser
        P->>PdfParser: parse(file) -> list[Chunk]
        Note over PdfParser: pypdf → split large pages into chunks
    else .txt
        P->>REG: _EXTENSION_MAP["txt"]
        REG-->>P: TxtParser
        P->>TxtParser: parse(file) -> list[Chunk]
        Note over TxtParser: word-boundary chunking
    else .csv
        P->>REG: _EXTENSION_MAP["csv"]
        REG-->>P: CsvParser
        P->>CsvParser: parse(file) -> list[Chunk]
        Note over CsvParser: one row = one chunk
    else .docx
        P->>REG: _EXTENSION_MAP["docx"]
        REG-->>P: DocxParser
        P->>DocxParser: parse(file) -> list[Chunk]
        Note over DocxParser: tables → markdown, lists formatted
    else
        P-->>U: [] (unsupported format)
    end

    loop for each Chunk
        P->>P: wrap in {"id": uuid, "text", "metadata"}
    end

    U->>V: add_documents(chunks)
    V->>CH: chromadb.Collection.add(ids, documents, metadatas)
    CH-->>V: success count
    V-->>U: chunk count (displayed as toast)
```

### Extension Mapping

The registry is built at import time — zero configuration needed:

```python
# parser.py (module-level, eager init)
_EXTENSION_MAP: dict[str, type] = {}
for _cls in (CsvParser, DocxParser, PdfParser, TxtParser):
    for _ext in _cls.supported_extensions:
        _EXTENSION_MAP[_ext] = _cls
```

---

## Query & Retrieval Flow

```mermaid
sequenceDiagram
    participant U as UI (Query Tab)
    participant A as app.py
    participant H as HybridRetriever
    participant VS as VectorStore
    participant K as KeywordSearcher
    participant LLM as get_llm_response
    participant REG as Provider Registry
    participant P as Provider Impl

    U->>A: user submits query
    A->>H: retrieve_formatted_context(query)
    H->>H: read config.retrieval_mode

    alt mode == "semantic"
        H->>VS: query(query, n_results)
        VS-->>H: cosine similarity results
    else mode == "keyword"
        H->>VS: get_all_documents()
        VS-->>H: all doc chunks
        H->>K: search(query, n_results)
        K-->>H: BM25 ranked results
    else mode == "hybrid" (default)
        H->>VS: query(query, n*2 candidates)
        VS-->>H: semantic results
        H->>VS: get_all_documents()
        VS-->>H: all docs for BM25
        H->>K: search(query, n*2 candidates)
        K-->>H: keyword results
        H->>H: reciprocal_rank_fusion(semantic, keyword)
        Note over H: score[i] += 1/(k+rank) per list
    end

    H-->>A: formatted context string

    A->>LLM: get_llm_response(context, query, model)
    LLM->>REG: resolve_provider(model)
    REG-->>LLM: ProviderClass (e.g. OpenAIProvider)
    LLM->>P: instance.chat(messages)
    P-->>LLM: generated text
    LLM-->>A: response string

    A->>A: EvaluationManager().record(…)\n+ thumbs feedback stored in session
    A-->>U: streamed answer + sources + metrics
```

### Retrieval Mode Selection

The config value `retrieval_mode` (from `.env`, default `"hybrid"`) controls behavior. In hybrid mode, **Reciprocal Rank Fusion** (RRF) merges the two ranked lists:

```
score(doc_id) = Σ 1 / (k + rank_in_list_i)    for each list containing doc_id
final = sorted(results, key=score, reverse=True)
```

---

## Provider Routing

Model IDs are routed to provider classes via prefix matching in `_Registry`:

```mermaid
graph LR
    M[model ID] --> R{resolve_provider}
    R --> |starts with<br/>"groq:"| G[Groq → OpenAIProvider]
    R --> |starts with<br/>"ollama:"| O[OllamaProvider]
    R --> |starts with<br/>"lmstudio:"<br/>or "lm-studio:"| L[LMStudioProvider]
    R --> |starts with<br/>"hf-"| H[HuggingFaceProvider]
    R --> |starts with<br/>"claude-"| C[AnthropicProvider]
    R --> |starts with "gemini"| E[GeminiProvider]
    R --> |empty prefix match| N[OpenAIProvider (default)]
    R --> |no match| ERR[UnsupportedModelError]
```

**Registration order matters.** The `__init__.py` registers providers in priority order: specific prefixes before the empty default. Groq and OpenAI share the same provider class but differ only in which API key is validated (`GROQ_API_KEY` vs `OPENAI_API_KEY`).

---

## Parser Registry

```mermaid
flowchart TD
    Start[uploaded file] --> Ext{extract extension}
    Ext --> |pdf| PDF[PdfParser]
    Ext --> |txt| TXT[TxtParser]
    Ext --> |csv| CSV[CsvParser]
    Ext --> |docx| DOCX[DocxParser]
    Ext --> |other| Empty[return []]

    PDF --> Chunking[pypdf → split long pages<br/>into chunk_size paragraphs]
    TXT --> Chunking2[word-boundary chunking<br/>with smart merges]
    CSV --> Rows[one row = one chunk<br/>no chunk_size param]
    DOCX --> Blocks[paragraphs, tables → markdown,<br/>bullets/numbers formatted]

    Chunking --> Merge[wrap in Chunk dataclass]
    Chunking2 --> Merge
    Rows --> Merge
    Blocks --> Merge

    Merge --> Done[{list[dict]<br/>id + text + metadata}]
```

---

## Evaluation Framework

```mermaid
classDiagram
    class EvaluationRecord {
        +str record_id
        +str query
        +str answer
        +str model
        +float latency
        +list chunk_distances
        +str rating
        +float faithfulness_score
        +float relevance_score
        +float avg_distance
        +to_dict() Dict
        +from_dict(Dict) EvaluationRecord
    }

    class EvaluationManager {
        +str log_path
        +record(query, answer, model, latency,<br/>  context_chunks, rating)
        +get_records() list[EvaluationRecord]
        +_load() list[dict]
        +_save(records) None
    }

    class LLMJudge {
        +str api_key
        +evaluate(record) EvaluationRecord
        -_parse_scores(text) tuple[float, float]
    }

    EvaluationManager --> EvaluationRecord : manages
    LLMJudge --> EvaluationRecord : produces
```

Evaluation records are auto-captured on every query (stored in `evaluation_logs.json`). The **Evaluation tab** aggregates metrics — thumbs-up %, avg latency, avg vector distance, and AI-judge faithfulness/relevance scores.

---

## Configuration & Dependency Injection

```mermaid
graph LR
    Env[os.environ / .env] --> Settings[Settings<br/>(Pydantic BaseModel)]
    Settings --> CP[ConfigProvider<br/>(singleton wrapper)]

    CP --> |inject| VS["VectorStore(config_provider)"]
    CP --> |inject| RET["HybridRetriever(config_provider)"]
    CP --> |inject| EMB["EmbeddingManager(config_provider)"]
    CP --> |read-only| LLM["get_llm_response(config_provider)"]

    CP --> KEY1[api_key_getters<br/>openai_key, anthropic_key, ...]
    CP --> CFG["retrieval_mode, n_results,<br/>chunk_size, system_prompt,..."]
```

`ConfigProvider` is the central injection point. All core modules accept it as an optional constructor argument — tests inject fakes; production uses the singleton from `get_config()`.

### Settings Reference

| Key | Default | Used By |
|---|---|---|
| `OPENAI_API_KEY` | _(empty)_ | Embedding, OpenAI provider |
| `ANTHROPIC_API_KEY` | _(empty)_ | Anthropic provider |
| `GOOGLE_API_KEY` | _(empty)_ | Gemini provider |
| `GROQ_API_KEY` | _(empty)_ | Groq variant (uses OpenAIProvider) |
| `HUGGINGFACE_API_KEY` | _(empty)_ | HuggingFace provider |
| `CHROMA_DB_PATH` | `./chroma_db` | VectorStore persistence |
| `COLLECTION_NAME` | `my_rag_collection` | ChromaDB collection identity |
| `DEFAULT_LLM` | `gpt-4o-mini` | Sidebar default model |
| `LLM_TEMPERATURE` | `0.2` | All LLM inference |
| `LLM_MAX_TOKENS` | `1024` | All LLM inference |
| `LLM_SYSTEM_PROMPT` | _(default in code)_ | System message in every prompt |
| `CHUNK_SIZE` | `1000` | Parser word-boundary threshold |
| `N_RESULTS` | `3` | Default vector query count |
| `RETRIEVAL_MODE` | `hybrid` | retriever mode selector |
| `OLLAMA_BASE_URL` | `http://localhost:11434/v1` | OllamaProvider, model discovery |
| `LM_STUDIO_BASE_URL` | `http://localhost:1234/v1` | LMStudioProvider, model discovery |
