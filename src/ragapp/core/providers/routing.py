"""Provider routing and registration logic."""


# Type aliases for protocol and provider types  
Protocol = str
ProviderProtocol = type  # Simplified - represents callable returning Provider class


class _Registry:
    """Singleton registry of available providers."""

    def __init__(self) -> None:
        self._registry: list[tuple[str, type]] = []

    def register(self, prefix: str, provider_class: type) -> None:
        """Register a provider with a model prefix.
        
        Args:
            prefix: Model ID prefix (empty string matches all).
            provider_class: The Provider class to use.
        """
        self._registry.append((prefix, provider_class))

    def resolve_provider(self, model_id: str) -> type:
        """Resolve a model ID to a provider class based on prefixes.
        
        Args:
            model_id: Full model identifier (e.g., "gpt-4o", "groq:llama3").
            
        Returns:
            The matching Provider class, or raises UnsupportedModelError if none match.
        """
        # Try exact prefix matches first (most specific)
        for prefix, provider_class in self._registry:
            if model_id.lower().startswith(prefix.lower()):
                return provider_class

        raise ValueError(f"No provider registered for model: {model_id}")


_REGISTRY = _Registry()
register = _REGISTRY.register
resolve_provider = _REGISTRY.resolve_provider


class UnsupportedModelError(Exception):
    """Raised when no provider matches the given model ID."""

    pass

