"""Tests for src/ragapp/core/providers/anthropic.py."""

from unittest.mock import MagicMock, patch


class TestAnthropicProvider:
    """Tests for core.providers.anthropic.AnthropicProvider."""

    def test_init_sets_attributes(self):
        from core.providers.anthropic import AnthropicProvider

        p = AnthropicProvider("anthropic:claude-3-opus", temperature=0.5, max_tokens=2048)
        assert p._model == "claude-3-opus"
        assert p.name == "Anthropic"
        assert p._max_tokens == 2048

    def test_chat_raises_key_missing(self, monkeypatch):
        """KeyMissingError raised when env var not set."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        from core.providers.anthropic import AnthropicProvider
        from core.providers.base import KeyMissingError as KME

        p = AnthropicProvider("anthropic:claude-3-opus")
        msgs = [MagicMock(role="user", content="hello")]
        try:
            p.chat(msgs)
            assert False, "Should have raised KeyMissingError"
        except KME as e:
            assert "ANTHROPIC_API_KEY" in str(e)

