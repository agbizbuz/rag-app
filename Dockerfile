# Stage 1: Base builder with uv
FROM python:3.10-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Environment for uv
ENV UV_PROJECT_ENVIRONMENT=/opt/.venv
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app

# Install dependencies (cached if pyproject.toml / uv.lock unchanged)
COPY pyproject.toml uv.lock ./
# Pre-install dependencies to cache this layer
RUN uv sync --frozen --no-install-project

# ==========================================
# Stage 2: Development & Testing
# ==========================================
FROM builder AS dev

# Copy the rest of the application
COPY . .

# Sync including project code and dev dependencies
RUN uv sync --frozen

# Ensure virtualenv is on PATH
ENV PATH="/opt/.venv/bin:$PATH"

EXPOSE 8501

CMD ["uv", "run", "rag-app", "--server.address=0.0.0.0"]

# ==========================================
# Stage 3: Production Builder (no dev dependencies)
# ==========================================
FROM builder AS prod-builder
# Re-sync without dev dependencies
RUN uv sync --frozen --no-install-project --no-dev
COPY . .
RUN uv sync --frozen --no-dev

# ==========================================
# Stage 4: Production Runtime
# ==========================================
FROM python:3.10-slim AS prod

# Keep image minimal by not including uv
ENV PATH="/opt/.venv/bin:$PATH"
WORKDIR /app

# Copy the production virtual environment
COPY --from=prod-builder /opt/.venv /opt/.venv
# Copy application code
COPY --from=prod-builder /app /app

EXPOSE 8501

CMD ["rag-app", "--server.address=0.0.0.0"]
