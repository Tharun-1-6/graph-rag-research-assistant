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
        self.provider = get_provider()

    # ---------------------------------------------------------
    # Public Methods
    # ---------------------------------------------------------

    def generate( self, prompt: str, temperature: float = 0.2,) -> str:
        """
        Generate a normal text response.
        """
        return self.provider.generate(
            prompt=prompt,
            temperature=temperature,
        )

    def generate_json( self, prompt: str, temperature: float = 0.0 ) -> str:
        """
        Generate a JSON response.

        Returns
        -------
        str
            Raw JSON string.
        """

        return self.provider.generate_json(
            prompt=prompt,
            temperature=temperature,
        )

    # ---------------------------------------------------------

    def __repr__(self):

        return (
            f"LLMClient(provider={self.provider})"
        )