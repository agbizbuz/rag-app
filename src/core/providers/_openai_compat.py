"""Backwards-compatible wrapper around the public OpenAI compat module.

Existing test patches that target ``core.providers._openai_compat`` continue to
work without modification — they resolve to the same function in
:mod:`core.providers.openai_compat`.
"""

from .openai_compat import get_openai_client  # noqa: F401, re-export


__all__ = ["get_openai_client"]
