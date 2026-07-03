"""
factory.py

Creates and returns the configured LLM provider.
"""

from llm.config import (
    LLM_PROVIDER,
    LLM_API_KEY,
    LLM_MODEL,
)

from .gemini import GeminiProvider

def get_provider():
    """
    Returns the configured LLM provider.
    """
    provider = LLM_PROVIDER.lower()

    if provider == "gemini":
        return GeminiProvider(
            api_key=LLM_API_KEY,
            model=LLM_MODEL,
        )

    # Future providers
    #
    # elif provider == "groq":
    #     return GroqProvider(...)
    #
    # elif provider == "ollama":
    #     return OllamaProvider(...)

    raise ValueError(f"Unsupported provider: {LLM_PROVIDER}")