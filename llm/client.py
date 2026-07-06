"""
client.py

High-level interface used by the rest of the project.

The rest of the application should ONLY interact with this class,
never directly with GeminiProvider, OpenAIProvider, etc.

Architecture

GraphRAG
    │
    ▼
LLMClient
    │
    ▼
Factory
    │
    ▼
Gemini / OpenAI / Groq / Ollama
"""

from llm.provider.factory import get_provider

class LLMClient:
    """
    High-level interface for interacting with LLMs.
    """

    def __init__(self):
        self.provider = None
        self.fallback_provider = None

        # Determine primary and fallback based on LLM_PROVIDER config
        from llm.config import LLM_PROVIDER
        primary_name = (LLM_PROVIDER or "groq").lower()
        fallback_name = "gemini" if primary_name == "groq" else "groq"

        # Check primary provider
        try:
            self.provider = get_provider(primary_name)
        except Exception:
            pass

        # Check fallback provider
        try:
            self.fallback_provider = get_provider(fallback_name)
        except Exception:
            pass

        # Shift to active provider silently
        if self.provider:
            p_name = "Groq" if primary_name == "groq" else "Gemini"
            print(f"[LLMClient] Active: {p_name} ({self.provider.model})")
        elif self.fallback_provider:
            self.provider = self.fallback_provider
            self.fallback_provider = None
            f_name = "Gemini" if fallback_name == "gemini" else "Groq"
            print(f"[LLMClient] Active: {f_name} ({self.provider.model})")
        else:
            raise ValueError("No LLM providers are configured. Please configure GEMINI_API_KEY or GROQ_API_KEY in your .env file.")

    @property
    def active_model(self) -> str:
        """Returns the name and model of the currently active provider."""
        provider_name = "Gemini" if self.provider.__class__.__name__ == "GeminiProvider" else "Groq"
        return f"{provider_name} ({self.provider.model})"

    # ---------------------------------------------------------
    # Public Methods
    # ---------------------------------------------------------

    def generate(self, prompt: str, temperature: float = 0.2) -> str:
        """
        Generate a normal text response.
        """
        try:
            return self.provider.generate(
                prompt=prompt,
                temperature=temperature,
            )
        except Exception:
            if self.fallback_provider:
                # Permanent switch to fallback
                self.provider = self.fallback_provider
                self.fallback_provider = None
                return self.provider.generate(
                    prompt=prompt,
                    temperature=temperature,
                )
            raise

    def generate_json(self, prompt: str, temperature: float = 0.0) -> str:
        """
        Generate a JSON response.
        """
        try:
            return self.provider.generate_json(
                prompt=prompt,
                temperature=temperature,
            )
        except Exception:
            if self.fallback_provider:
                # Permanent switch to fallback
                self.provider = self.fallback_provider
                self.fallback_provider = None
                return self.provider.generate_json(
                    prompt=prompt,
                    temperature=temperature,
                )
            raise

    # ---------------------------------------------------------

    def __repr__(self):
        return f"LLMClient(provider={self.provider})"