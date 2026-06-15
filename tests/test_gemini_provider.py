"""Tests for src/ragapp/core/providers/gemini.py."""

import sys
from unittest.mock import MagicMock, patch


class TestGeminiProvider:
    """Tests for ragapp.core.providers.gemini.GeminiProvider."""

    def test_init_sets_attributes(self):
        from ragapp.core.providers.gemini import GeminiProvider

        p = GeminiProvider("gemini-pro", temperature=0.3, max_tokens=512)
        assert p._model == "gemini-pro"
        assert p.name == "Google Gemini"
        assert p._temperature == 0.3
        assert p._max_tokens == 512

    def test_chat_with_key(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_API_KEY", "goog-test-key")

        mock_response = MagicMock()
        mock_response.text = "Gemini says hello"

        mock_genai = MagicMock()
        mock_model_cls = MagicMock()
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_model_cls.return_value = mock_model_instance
        mock_genai.GenerativeModel = mock_model_cls

        with patch.dict(sys.modules, {"google.generativeai": mock_genai}):
            from ragapp.core.providers.gemini import GeminiProvider

            p = GeminiProvider("gemini-pro")
            msgs = [MagicMock(role="user", content="hello")]
            result = p.chat(msgs)
            assert result == "Gemini says hello"

    def test_chat_excludes_system_from_combined(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_API_KEY", "goog-test-key")

        mock_response = MagicMock()
        mock_response.text = "Response"

        mock_genai = MagicMock()
        mock_model_cls = MagicMock()
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_model_cls.return_value = mock_model_instance
        mock_genai.GenerativeModel = mock_model_cls

        with patch.dict(sys.modules, {"google.generativeai": mock_genai}):
            from ragapp.core.providers.gemini import GeminiProvider

            p = GeminiProvider("gemini-pro")
            msgs = [
                MagicMock(role="system", content="System prompt"),
                MagicMock(role="user", content="User query"),
            ]
            p.chat(msgs)
            call_arg = mock_model_instance.generate_content.call_args[0][0]
            assert "System prompt" not in call_arg
            assert "User query" in call_arg

    def test_chat_raises_key_missing(self, monkeypatch):
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

        from ragapp.core.providers.base import KeyMissingError as KME
        from ragapp.core.providers.gemini import GeminiProvider

        p = GeminiProvider("gemini-pro")
        msgs = [MagicMock(role="user", content="hello")]
        try:
            p.chat(msgs)
            assert False, "Should have raised KeyMissingError"
        except KME as e:
            assert "GOOGLE_API_KEY" in str(e)
