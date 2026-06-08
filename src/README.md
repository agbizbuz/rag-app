# RAG App - How to Run

## Prerequisites

1. Install dependencies:
```bash
uv sync
```

2. Set up environment variables (copy from example):
```bash
cp .env.example .env
# Edit .env and set your API keys
```

## Running the Application

### Option 1: Via uv run (RECOMMENDED)
```bash
PYTHONPATH=src uv run streamlit run src/ragapp/app.py
```

### Option 2: Direct Python execution
```bash
cd src && PYTHONPATH=. streamlit run ragapp/app.py
```

## Key Notes

- **`PYTHONPATH=src` is required** because `ragapp` is a package nested under `src/`, not a top-level module. This allows Python to resolve imports like `from ragapp.config import settings`.

- The app uses **absolute imports** (e.g., `from ragapp.core.llm import get_llm_response`) which work when PYTHONPATH=src includes the parent directory containing `ragapp` as a package.

## Development

### Running tests
```bash
uv run pytest tests/test_llm_routing.py -v
uv run pytest tests/test_parser.py -v
```

### Code formatting/linting
```bash
uv run ruff check src/ --fix
```
