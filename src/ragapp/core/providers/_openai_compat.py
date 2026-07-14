"""Shared OpenAI client getter for standardizing mock patches in tests."""

def get_openai_client():
    """Return the OpenAI client class. Tests can patch this function directly."""
    from openai import OpenAI
    return OpenAI
