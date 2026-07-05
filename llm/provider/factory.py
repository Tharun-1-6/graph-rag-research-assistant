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

from .gemini import GeminiProvider

def get_provider(name: str = None):
    """
    Returns the configured LLM provider (supports gemini and groq).
    """
    import os
    provider_name = (name or LLM_PROVIDER).lower()

    if provider_name == "gemini":
        api_key = os.getenv("GEMINI_API_KEY") or LLM_API_KEY
        if not api_key:
            raise ValueError("GEMINI_API_KEY not configured.")
        return GeminiProvider(
            api_key=api_key,
            model=LLM_MODEL or "gemini-2.5-flash",
        )

    elif provider_name == "groq":
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not configured.")
        from .groq import GroqProvider
        return GroqProvider(
            api_key=api_key,
            model="llama-3.3-70b-versatile"
        )

    raise ValueError(f"Unsupported provider: {provider_name}")