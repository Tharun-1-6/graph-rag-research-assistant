import os
from groq import Groq
from .base import BaseLLMProvider

class GroqProvider(BaseLLMProvider):
    """
    Wrapper around Groq's SDK.
    """

    def __init__(self, api_key: str, model: str = "llama-3.3-70b-specdec"):
        super().__init__(api_key, model)
        self.client = Groq(api_key=api_key)

    def generate(self, prompt: str, temperature: float = 0.2) -> str:
        """
        Generate response using Groq.
        """
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
        )
        return completion.choices[0].message.content

    def generate_json(self, prompt: str, temperature: float = 0.0) -> str:
        """
        Generate structured JSON response using Groq.
        """
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            response_format={"type": "json_object"}
        )
        return completion.choices[0].message.content
