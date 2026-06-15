"""Tests for src/ragapp/core/providers/base.py."""

from ragapp.core.providers.base import (
    ChatMessage,
    KeyMissingError,
    Provider,
    RAGError,
    UnsupportedModelError,
)


class TestProviderBase:
    """Tests for the abstract Provider base class."""

    def test_provider_is_abstract(self):
        """Cannot instantiate Provider directly."""
        try:
            Provider()
            assert False, "Should not be able to instantiate abstract class"
        except TypeError:
            pass  # Expected

    def test_validate_key_present(self):
        """validate_key passes when env var is set."""
        import os

        os.environ["TEST_KEY"] = "secret"
        try:
            provider = _TestProvider()
            provider.validate_key("TEST_KEY")  # Should not raise
        finally:
            del os.environ["TEST_KEY"]

    def test_validate_key_missing(self):
        """validate_key raises KeyMissingError when env var is not set."""
        import os

        if "MISSING_KEY_TEST" in os.environ:
            del os.environ["MISSING_KEY_TEST"]

        provider = _TestProvider()
        try:
            provider.validate_key("MISSING_KEY_TEST")
            assert False, "Should have raised KeyMissingError"
        except KeyMissingError as e:
            assert "MISSING_KEY_TEST" in str(e)

    def test_rag_error_hierarchy(self):
        """RAGError is the base class."""
        exc = RAGError("test")
        assert isinstance(exc, Exception)
        assert issubclass(KeyMissingError, RAGError)
        assert issubclass(UnsupportedModelError, RAGError)


class TestChatMessage:
    """Tests for providers ChatMessage (from base module)."""

    def test_init(self):
        msg = ChatMessage("system", "You are helpful")
        assert msg.role == "system"
        assert msg.content == "You are helpful"

    def test_repr(self):
        msg = ChatMessage("user", "hello")
        assert "ChatMessage(role='user'" in repr(msg)


class _TestProvider(Provider):
    """Concrete subclass of Provider for testing."""

    name = "Test"

    def chat(self, messages, temperature=0.0):
        return "test response"


class TestProviderProtocol:
    """Tests for the provider protocol and routing."""

    def test_registry_resolve_by_prefix(self):
        from ragapp.core.providers import _REGISTRY

        # These should be registered by the auto-registration in __init__
        p = _REGISTRY.resolve_provider("gpt-4o-mini")
        assert p is not None

    def test_registry_raises_for_unknown(self):
        from ragapp.core.providers.routing import _Registry

        r = _Registry()
        try:
            r.resolve_provider("xyz-nonexistent-model")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "No provider registered for model" in str(e)


class TestAllExport:
    """Tests that __all__ contains expected symbols."""

    def test_all_exports(self):
        from ragapp.core.providers.base import __all__

        expected = [
            "RAGError",
            "KeyMissingError",
            "UnsupportedModelError",
            "ChatMessage",
            "Provider",
        ]
        for name in expected:
            assert name in __all__, f"{name} should be in __all__"
