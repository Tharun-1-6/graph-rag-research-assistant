"""
retriever.py

Retrieves relational context from a NetworkX knowledge graph.
Redirects imports to the advanced, upgraded retrieval engine under graph/retrieval/.
"""

from .retrieval.retriever import GraphRetriever, RetrievalResult

__all__ = ["GraphRetriever", "RetrievalResult"]
