"""
vector_retriever.py

Defines interfaces and placeholder implementations for the vector database retrieval.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class VectorRetrieverInterface(ABC):
    """
    Interface for vector database retrieval.
    """

    @abstractmethod
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieves text segments matching semantic embedding similarity.
        """
        pass


class PlaceholderVectorRetriever(VectorRetrieverInterface):
    """
    Placeholder vector retriever to be integrated with embedding search in the future.
    """

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Placeholder return value. Returns empty results or structural mock.
        """
        # Return empty list for now as embeddings are not implemented yet.
        return []
