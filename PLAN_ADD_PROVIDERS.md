# Plan: Add HuggingFace, Groq, Ollama, LM Studio LLM Providers

## Current Architecture (summary)

- `config.py` — Pydantic `Settings` class with env-var fields (`openai_api_key`, `anthropic_api_key`, `google_api_key`)
- `core/llm.py` — Single dispatch function `get_llm_response(query_context, llm_model)` that checks model string for provider hints and calls the right SDK/API
- `app.py` — Sidebar radio select for provider with per-provider model dropdowns
- `.env.example` — Documents which env vars to set

## Provider Analysis

| Provider | API Style | Key Env Vars | Default Base URL | Notes |
|---|---|---|---|---|
| **Groq** | OpenAI-compatible | `GROQ_API_KEY` | `https://api.groq.com/openai/v1` | Reuses `openai` SDK with custom `base_url` |
| **Ollama** | OpenAI-compatible | (none) | `http://localhost:11434/v1` | Fully local; models pulled via `ollama pull <name>` |
| **LM Studio** | OpenAI-compatible | (none) | `http://localhost:1234/v1` | Local server must be started in LM Studio UI |
| **HuggingFace** | REST inference API | `HUGGINGFACE_API_KEY` | `https://api-inference.huggingface.co/models/{model}` | Uses direct HTTP; models listed on HF Hub. Also supports OpenAI-compatible if running TGI locally. |

### Design decision: Groq/Ollama/LM Studio share the OpenAI client
All three expose an OpenAI-compatible chat completions endpoint. The existing `openai` SDK import is reused — we just pass a custom `base_url` and no API key (for local providers). This avoids adding four new imports.

HuggingFace is different: it uses a per-model REST endpoint, not a unified completions API. We'll use `requests` with the Inference API.

---

## Changes

### Phase 1: Config (`src/ragapp/config.py`)

Add fields to `Settings`:
```python
groq_api_key: str = ""
huggingface_api_key: str = ""
# Local providers need no key, but allow custom URLs:
ollama_base_url: str = "http://localhost:11434/v1"
lm_studio_base_url: str = "http://localhost:1234/v1"
```

### Phase 2: LLM dispatch (`src/ragapp/core/llm.py`)

Add four new branches to `get_llm_response`, following the existing pattern:

#### Groq branch (model string contains `"groq"`):
- Validate `GROQ_API_KEY`
- Create `OpenAI(api_key=..., base_url="https://api.groq.com/openai/v1")`
- Call `chat.completions.create()` — same API as OpenAI

#### Ollama branch (model string contains `"ollama"` or starts with `" llama"`, `"mistral"`, etc.):
- No key needed
- Create `OpenAI(api_key="ollama", base_url=settings.ollama_base_url)`
- Call `chat.completions.create()`
- Model names come from `ollama list` (e.g., `llama3.1`, `mistral-nemo`, `phi3`)

#### LM Studio branch (model string contains `"lmstudio"` or `*lm-s*`):
- No key needed
- Create `OpenAI(api_key="lm-studio", base_url=settings.lm_studio_base_url)`
- Call `chat.completions.create()`

#### HuggingFace branch (model string contains `"hf"`, `"huggingface"`, or matches a HF model ID pattern like `"meta-llama/Llama-3..."`):
- Validate `HUGGINGFACE_API_KEY`
- Use `requests.post()` with URL `https://api-inference.huggingface.co/models/{model}` and header `Authorization: Bearer {key}`
- Parse JSON response (expects `[{"generated_text": "..."}]`)
- Fallback to `"nomic-ai/gpt4all-falcon"` if no model name given for the HF path

### Phase 3: UI (`src/ragapp/app.py`)

Expand the sidebar radio select to six options:
```python
providers = ["OpenAI", "Anthropic", "Google Gemini", "Groq", "Ollama", "LM Studio", "HuggingFace"]
```

For each provider, wire model dropdowns:

| Provider | Models |
|---|---|
| Groq | `llama-3.1-8b-instant`, `llama-3.1-70b-versatile`, `llama-3.1-405b-reasoning`, `gemma2-9b-it` |
| Ollama | `"(pull models with 'ollama pull <name>' first)"` — show placeholder + info; or fetch dynamically via HTTP (out of scope for v1) |
| LM Studio | `"(start server in LM Studio app)"` — same placeholder approach as Ollama |
| HuggingFace | `nomic-ai/gpt4all-falcon`, `meta-llama/Llama-3.3-70B-Instruct`, `mistralai/Mistral-7B-Instruct-v0.3` |

### Phase 4: `.env.example`

Append for each new provider:
```
# Groq API Key
GROQ_API_KEY=gsk-your-groq-key-here

# HuggingFace API Key
HUGGINGFACE_API_KEY=hf_your-token-here

# Ollama base URL (change if running on different host/port)
OLLAMA_BASE_URL=http://localhost:11434/v1

# LM Studio base URL (default port is 1234)
LM_STUDIO_BASE_URL=http://localhost:1234/v1
```

### Phase 5: Dependencies (`pyproject.toml`)

Add `requests` if not already present (for HuggingFace Inference API):
```
"requests>=2.31.0",
```

Groq, Ollama, and LM Studio need **no new dependencies** — they reuse the existing `openai` SDK.

---

## File-level Change Summary

| File | What changes |
|---|---|
| `src/ragapp/config.py` | 4 new Settings fields |
| `src/ragapp/core/llm.py` | 4 new dispatch branches (~60 lines of code) |
| `src/ragapp/app.py` | Radio options: 3→7; model dropdowns per provider |
| `src/ragapp/.env.example` | 4 new env var docs |
| `pyproject.toml` | Add `requests` dep |

---

## Verification Checklist

- [ ] Run `uv run python -c "from config import settings; print(settings)"` — confirms all new fields load with defaults
- [ ] Start Ollama locally → `curl http://localhost:11434/v1/models` → test a query through the app (select Ollama provider)
- [ ] Set `GROQ_API_KEY` in `.env` → select Groq provider → verify response
- [ ] Start LM Studio with a local model server → select LM Studio provider → verify response
- [ ] Set `HUGGINGFACE_API_KEY` → select HuggingFace → verify inference API call
- [ ] Run full Streamlit app (`uv run streamlit run src/ragapp/app.py`) — no import errors, sidebar renders all 7 providers

## Risks & Mitigations

1. **Ollama/LM Studio base URL mismatch** — Allow configurable URLs in `.env` (Phase 1) rather than hardcoding
2. **HuggingFace free tier rate limits** — Add a note in the UI (`st.warning`) when using HF that the free inference API may be slow/limited; suggest self-hosted TGI for production use
3. **Model name conflicts** — Use explicit provider prefix in model names (e.g., `"groq:llama-3.1-8b"`, `"ollama:llama3.1"`) so the dispatch logic never misroutes
4. **OpenAI SDK not supporting custom base_url without `api_key`** — Set a dummy key (`"ollama"`, `"lm-studio"`) for local providers; both Ollama and LM Studio accept any string
