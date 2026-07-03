"""
gemini.py

Gemini provider implementation.

Responsibilities
----------------
✓ Initialize Gemini client
✓ Send prompts
✓ Return text responses

Does NOT
---------
✗ Parse JSON
✗ Build prompts
✗ Know about GraphRAG
✗ Know about RAG
"""

from google import genai

from .base import BaseLLMProvider


class GeminiProvider(BaseLLMProvider):
    """
    Wrapper around Google's Gemini SDK.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.5-pro",
    ):
        super().__init__(api_key, model)

        self.client = genai.Client(
            api_key=api_key
        )

    # -------------------------------------------------
    # Public Methods
    # -------------------------------------------------

    def generate(
        self,
        prompt: str,
        temperature: float = 0.2,
    ) -> str:
        """
        Generate a normal text response.
        """

        try:

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "temperature": temperature,
                },
            )

            return response.text

        except Exception as e:

            raise RuntimeError(
                f"Gemini generation failed: {e}"
            )

    # -------------------------------------------------

    def generate_json(
        self,
        prompt: str,
        temperature: float = 0.0,
    ) -> str:
        """
        Generate JSON output.
        """

        try:

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "temperature": temperature,
                    "response_mime_type": "application/json",
                },
            )

            return response.text

        except Exception as e:

            raise RuntimeError(
                f"Gemini JSON generation failed: {e}"
            )