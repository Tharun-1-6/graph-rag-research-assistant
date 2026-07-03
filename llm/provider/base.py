'''
This file is so that each llm that in the future that is created inherits the functions in this file 
This is so that each llm uses these fucntions to do each task 

for eg :
class GeminiProvider:
    def generate(self, prompt):
        ...
    def generate_json(self, prompt):
        ...
class OpenAIProvider:
    def ask(self, prompt):
        ...
    def extract_json(self, prompt):
        ...

'generate' and 'ask' does the same exact task but has different funciton names
base.py is implemented to avoid that
'''
from abc import ABC, abstractmethod

class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM providers.
    """

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    # -------------------------------------------------
    # Required Methods
    # -------------------------------------------------

    @abstractmethod
    def generate(self, prompt: str, temperature: float = 0.2,) -> str:
        """
        Generate a text response.
        Must be implemented by every provider.
        """
        pass

    @abstractmethod
    def generate_json( self, prompt: str, temperature: float = 0.0 ) -> str:
        """
        Generate a structured JSON response.
        Must be implemented by every provider.
        """
        pass

    # -------------------------------------------------
    # Optional Utility Methods
    # -------------------------------------------------

    def __repr__(self) :
        return (
            f"{self.__class__.__name__}"
            f"(model='{self.model}')"
        )