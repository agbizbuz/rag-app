"""Tests for src/ragapp/core/providers/lm_studio.py."""

from unittest.mock import MagicMock, patch


class TestLMStudioProvider:
    """Tests for core.providers.lm_studio.LMStudioProvider."""

    def test_init_sets_base_url(self):
        from core.providers.lm_studio import LMStudioProvider

        p = LMStudioProvider("test-model")
        assert p._base_url == "http://localhost:1234/v1"

    def test_init_uses_env_base_url(self, monkeypatch):
        monkeypatch.setenv("LM_STUDIO_BASE_URL", "http://custom:1234/v1")
        from core.providers.lm_studio import LMStudioProvider

        p = LMStudioProvider("test-model")
        assert p._base_url == "http://custom:1234/v1"

    def test_chat_with_mock(self):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="LM Studio reply"))]

        with patch("core.providers.openai_compat.get_openai_client") as MockGetClient:
            mock_client_class = MagicMock()
            mock_instance = MagicMock()
            mock_instance.chat.completions.create.return_value = mock_response
            mock_client_class.return_value = mock_instance
            MockGetClient.return_value = mock_client_class

            from core.providers.lm_studio import LMStudioProvider

            p = LMStudioProvider("test-model")
            msgs = [MagicMock(role="user", content="hello")]
            result = p.chat(msgs)
            assert result == "LM Studio reply"
            mock_instance.chat.completions.create.assert_called_once()

    def test_chat_hardcodes_lm_studio_key(self):
        """LM Studio provider uses 'lm-studio' as api_key."""
        from core.providers.lm_studio import LMStudioProvider

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="OK"))]

        with patch("core.providers.openai_compat.get_openai_client") as MockGetClient:
            mock_client_class = MagicMock()
            mock_instance = MagicMock()
            mock_instance.chat.completions.create.return_value = mock_response
            mock_client_class.return_value = mock_instance
            MockGetClient.return_value = mock_client_class

            p = LMStudioProvider("test-model")
            msgs = [MagicMock(role="user", content="hello")]
            p.chat(msgs)
            # Verify the client was created with 'lm-studio' api_key
            call_kwargs = mock_client_class.call_args[1]
            assert call_kwargs["api_key"] == "lm-studio"



