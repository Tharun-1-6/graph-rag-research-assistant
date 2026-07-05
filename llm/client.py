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

        # Check Gemini provider
        try:
            self.provider = get_provider("gemini")
        except Exception:
            pass

        # Check Groq provider
        try:
            self.fallback_provider = get_provider("groq")
        except Exception:
            pass

        # Shift to active provider silently
        if self.provider:
            print(f"[LLMClient] Active: Gemini ({self.provider.model})")
        elif self.fallback_provider:
            self.provider = self.fallback_provider
            self.fallback_provider = None
            print(f"[LLMClient] Active: Groq ({self.provider.model})")
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