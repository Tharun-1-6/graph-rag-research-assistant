"""
Graph Builder Package

Responsible for converting ExtractionResult objects into
NetworkX knowledge graphs.

Public Classes
--------------
GraphBuilder
    Converts ExtractionResult -> NetworkX graph

GraphManager
    Convenience wrapper around a graph instance

GraphSerializer
    Save/load graphs in various formats

NodeFactory
    Creates graph nodes

EdgeFactory
    Creates graph edges
"""

from .builder import GraphBuilder
from .graph_manager import GraphManager
from .serializer import GraphSerializer
from .node_factory import NodeFactory
from .edge_factory import EdgeFactory

__all__ = [
    "GraphBuilder",
    "GraphManager",
    "GraphSerializer",
    "NodeFactory",
    "EdgeFactory",
]