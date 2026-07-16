"""Tests for src/ragapp/core/providers/anthropic.py."""

from unittest.mock import MagicMock, patch


class TestAnthropicProvider:
    """Tests for core.providers.anthropic.AnthropicProvider."""

    def test_init_sets_attributes(self):
        from core.providers.anthropic import AnthropicProvider

        p = AnthropicProvider("Antropic:claude:claude-3-opus", temperature=0.5, max_tokens=2048)
        assert p._model == "claude-3-opus"
        assert p.name == "Anthropic"
        assert p._max_tokens == 2048

    def test_chat_raises_key_missing(self, monkeypatch):
        """KeyMissingError raised when env var not set."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        from core.providers.anthropic import AnthropicProvider
        from core.providers.base import KeyMissingError as KME

        p = AnthropicProvider("Antropic:claude:claude-3-opus")
        msgs = [MagicMock(role="user", content="hello")]
        try:
            p.chat(msgs)
            assert False, "Should have raised KeyMissingError"
        except KME as e:
            assert "ANTHROPIC_API_KEY" in str(e)

    def test_chat_success_with_mocked_client(self, monkeypatch):
        """Test chat method body (lines 54-72 of anthropic.py) with mocked Anthropic client."""
        from core.providers import anthropic as anth_mod
        from core.providers.anthropic import AnthropicProvider

        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key")
        # Mock the response structure that AnthropicClient.messages.create() returns
        mock_content_block = MagicMock(text="Claude answer")
        mock_response = MagicMock()
        mock_response.content = [mock_content_block]

        with patch("anthropic.Anthropic") as MockAnthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            MockAnthropic.return_value = mock_client

            p = AnthropicProvider("Antropic:claude:claude-3-haiku")
            msgs = [MagicMock(role="user", content="hello"), MagicMock(role="system", content="Be concise")]
            result = p.chat(msgs)

        assert result == "Claude answer"
        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["model"] == "claude-3-haiku"
        assert len(call_kwargs["messages"]) == 1
        assert call_kwargs["messages"][0]["role"] == "user"

        # Verify system prompt was passed separately
        assert "system" in call_kwargs
        assert call_kwargs["system"] == "Be concise"
