"""
graph_retriever.py

Defines interfaces and wrappers for the graph-based retrieval component in hybrid search.
"""

from abc import ABC, abstractmethod
from typing import Any, List
import networkx as nx

from graph.query_engine.query_engine import QueryEngine
from graph.query_engine.context_builder import GraphContext


class GraphRetrieverInterface(ABC):
    """
    Interface for graph context retrieval.
    """

    @abstractmethod
    def retrieve(self, query: str) -> GraphContext:
        """
        Retrieves GraphContext for a query.
        """
        pass


class GraphRetrieverWrapper(GraphRetrieverInterface):
    """
    Wraps the upgraded QueryEngine to conform to the hybrid GraphRetrieverInterface.
    """

    def __init__(self, graph: nx.MultiDiGraph):
        self.engine = QueryEngine(graph)

    def retrieve(self, query: str) -> GraphContext:
        return self.engine.query(query)
