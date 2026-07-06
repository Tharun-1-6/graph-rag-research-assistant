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
        Generate a normal text response with retry logic.
        """
        import time
        import logging

        logger = logging.getLogger(__name__)
        max_retries = 5
        base_delay = 5.0

        for attempt in range(max_retries):
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
                err_str = str(e)
                is_retryable = any(code in err_str for code in ["503", "429", "RESOURCE_EXHAUSTED", "UNAVAILABLE"]) or "demand" in err_str.lower()
                
                if is_retryable and attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(
                        f"Gemini API unavailable or overloaded (attempt {attempt + 1}/{max_retries}). "
                        f"Retrying in {delay} seconds. Error: {err_str}"
                    )
                    time.sleep(delay)
                else:
                    raise RuntimeError(
                        f"Gemini generation failed: {e}"
                    )

        raise RuntimeError(
            "Gemini generation failed: exceeded maximum retries due to service unavailability."
        )

    # -------------------------------------------------

    def generate_json(
        self,
        prompt: str,
        temperature: float = 0.0,
    ) -> str:
        """
        Generate JSON output with retry logic for high demand/rate limits.
        """
        import time
        import logging

        logger = logging.getLogger(__name__)
        max_retries = 5
        base_delay = 5.0

        for attempt in range(max_retries):
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
                err_str = str(e)
                is_retryable = any(code in err_str for code in ["503", "429", "RESOURCE_EXHAUSTED", "UNAVAILABLE"]) or "demand" in err_str.lower()
                
                if is_retryable and attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(
                        f"Gemini API unavailable or overloaded (attempt {attempt + 1}/{max_retries}). "
                        f"Retrying in {delay} seconds. Error: {err_str}"
                    )
                    time.sleep(delay)
                else:
                    raise RuntimeError(
                        f"Gemini JSON generation failed: {e}"
                    )

        raise RuntimeError(
            "Gemini JSON generation failed: exceeded maximum retries due to service unavailability."
        )