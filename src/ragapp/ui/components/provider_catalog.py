"""Provider catalog — model options and discovery for the UI."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class ProviderInfo:
    name: str
    key_env: str | None       # API key env var, or ``None`` for local servers
    model_options: list[str]  # static dropdown options
    discover_models: Callable[[str], list[str]] | None = None  # dynamic discovery
    base_url_key: str | None = None


PROVIDERS: list[ProviderInfo] = [
    ProviderInfo(
        name="OpenAI",
        key_env="OPENAI_API_KEY",
        model_options=["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
    ),
    ProviderInfo(
        name="Anthropic",
        key_env="ANTHROPIC_API_KEY",
        model_options=[
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ],
    ),
    ProviderInfo(
        name="Google Gemini",
        key_env="GOOGLE_API_KEY",
        model_options=["gemini-pro", "gemini-pro-vision"],
    ),
    ProviderInfo(
        name="Groq",
        key_env="GROQ_API_KEY",
        model_options=[
            "groq:llama-3.1-8b-instant",
            "groq:llama-3.1-70b-versatile",
            "groq:llama-3.1-405b-reasoning",
            "groq:gemma2-9b-it",
        ],
    ),
]


def fetch_ollama_models(base_url: str) -> list[str]:
    """Fetch available models from an Ollama server."""
    import requests

    try:
        resp = requests.get(f"{base_url}/api/tags", timeout=3)
        resp.raise_for_status()
        return [f"{m['name']}" for m in resp.json().get("models", [])]
    except Exception:
        return []


def fetch_lm_studio_models(base_url: str) -> list[str]:
    """Fetch available models from an LM Studio server."""
    import requests

    try:
        resp = requests.get(f"{base_url}/v1/models", timeout=3)
        resp.raise_for_status()
        return [f"lmstudio:{m['id']}" for m in resp.json().get("data", [])]
    except Exception:
        return []


# Extend PROVIDERS with local servers that need dynamic discovery
PROVIDERS.append(
    ProviderInfo(
        name="LM Studio",
        key_env=None,
        model_options=[],
        discover_models=fetch_lm_studio_models,
        base_url_key="LM_STUDIO_BASE_URL",
    )
)

# Always include Ollama with default URL for discovery
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL")
PROVIDERS.append(
    ProviderInfo(
        name="Ollama",
        key_env=None,
        model_options=[],
        discover_models=fetch_ollama_models,
        base_url_key="OLLAMA_BASE_URL",
    )
)

PROVIDERS.append(
    ProviderInfo(
        name="HuggingFace",
        key_env="HUGGINGFACE_API_KEY",
        model_options=[
            "meta-llama/Llama-3.3-70B-Instruct",
            "meta-llama/Meta-Llama-3.1-70B-Instruct",
            "mistralai/Mistral-7B-Instruct-v0.3",
            "nomic-ai/gpt4all-falcon",
        ],
    )
)

