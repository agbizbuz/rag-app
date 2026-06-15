"""Tests for src/ragapp/core/providers/huggingface.py."""

import os
from unittest.mock import MagicMock, patch


class TestHuggingFaceProvider:
    """Tests for ragapp.core.providers.huggingface.HuggingFaceProvider."""

    def test_init_sets_attributes(self):
        from ragapp.core.providers.huggingface import HuggingFaceProvider

        p = HuggingFaceProvider("meta-llama/Llama-3.3-70B-Instruct", temperature=0.5, max_tokens=2048)
        assert p._model == "meta-llama/Llama-3.3-70B-Instruct"
        assert p.name == "HuggingFace"

    def test_chat_with_key(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"generated_text": "HF says hello"}]
        mock_response.raise_for_status = MagicMock()

        with patch.dict(os.environ, {"HUGGINGFACE_API_KEY": "hf-test-key"}):
            with patch("requests.post", return_value=mock_response) as mock_post:
                from ragapp.core.providers.huggingface import HuggingFaceProvider

                p = HuggingFaceProvider("meta-llama/Llama-3.3-70B-Instruct")
                msgs = [MagicMock(role="user", content="hello")]
                result = p.chat(msgs)
                assert result == "HF says hello"
                mock_post.assert_called_once()
                call_kwargs = mock_post.call_args[1]
                assert call_kwargs["headers"]["Authorization"] == "Bearer hf-test-key"

    def test_chat_with_string_response(self):
        """Handle raw string response from HF API."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = "Direct text response"
        mock_response.raise_for_status = MagicMock()

        with patch.dict(os.environ, {"HUGGINGFACE_API_KEY": "hf-test-key"}):
            with patch("requests.post", return_value=mock_response):
                from ragapp.core.providers.huggingface import HuggingFaceProvider

                p = HuggingFaceProvider("test-model")
                msgs = [MagicMock(role="user", content="hello")]
                result = p.chat(msgs)
                assert result == "Direct text response"

    def test_chat_raises_unexpected_format(self):
        """Raise RuntimeError for unexpected response format."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"weird": "dict"}
        mock_response.raise_for_status = MagicMock()

        with patch.dict(os.environ, {"HUGGINGFACE_API_KEY": "hf-test-key"}):
            with patch("requests.post", return_value=mock_response):
                from ragapp.core.providers.huggingface import HuggingFaceProvider

                p = HuggingFaceProvider("test-model")
                msgs = [MagicMock(role="user", content="hello")]
                try:
                    p.chat(msgs)
                    assert False, "Should have raised RuntimeError"
                except RuntimeError as e:
                    assert "Unexpected HuggingFace response format" in str(e)

    def test_chat_raises_key_missing(self):
        """Raise KeyMissingError when HF_API_KEY is not set."""
        env_orig = os.environ.get("HUGGINGFACE_API_KEY")
        if "HUGGINGFACE_API_KEY" in os.environ:
            del os.environ["HUGGINGFACE_API_KEY"]

        try:
            from ragapp.core.providers.base import KeyMissingError as KME
            from ragapp.core.providers.huggingface import HuggingFaceProvider

            p = HuggingFaceProvider("test-model")
            msgs = [MagicMock(role="user", content="hello")]
            try:
                p.chat(msgs)
                assert False, "Should have raised KeyMissingError"
            except KME as e:
                assert "HUGGINGFACE_API_KEY" in str(e)
        finally:
            if env_orig is not None:
                os.environ["HUGGINGFACE_API_KEY"] = env_orig
