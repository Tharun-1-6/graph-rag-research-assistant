"""
graph_manager.py

Main manager for the GraphRAG knowledge graph.

Responsibilities
----------------
✓ Maintain the NetworkX graph
✓ Add nodes
✓ Add edges
✓ Retrieve nodes and edges
✓ Save graph
✓ Load graph
✓ Provide graph statistics

Does NOT
---------
✗ Extract entities
✗ Call the LLM
✗ Perform retrieval
"""

from pathlib import Path
from typing import Dict, List, Optional

import networkx as nx

from graph.extraction.models import Entity, Relationship, ExtractionResult

from .node_factory import NodeFactory
from .edge_factory import EdgeFactory


class GraphManager:
    """
    Wrapper around a NetworkX MultiDiGraph.
    """

    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.node_factory = NodeFactory(self.graph)
        self.edge_factory = EdgeFactory(self.graph)

    # =====================================================
    # Node Operations
    # =====================================================

    def add_entity(self, entity: Entity):
        """
        Add a single entity node.
        """
        self.node_factory.add_entity(entity)

    def add_entities(self, entities: List[Entity]):
        """
        Add multiple entity nodes.
        """
        self.node_factory.add_entities(entities)

    # =====================================================
    # Edge Operations
    # =====================================================

    def add_relationship(self, relationship: Relationship):
        """
        Add a graph edge.
        """
        self.edge_factory.add_relationship(relationship)

    def add_relationships(
        self,
        relationships: List[Relationship],
    ):
        """
        Add multiple edges.
        """

        for relationship in relationships:
            self.add_relationship(relationship)

    # =====================================================
    # Extraction Result
    # =====================================================

    def add_extraction(
        self,
        result: ExtractionResult,
    ):
        """
        Adds an entire extraction result to the graph.
        """

        # ---------------------------
        # Paper node
        # ---------------------------

        paper = result.paper

        if not self.graph.has_node(paper.id):

            self.graph.add_node(
                paper.id,
                type="Paper",
                title=paper.title,
                year=paper.year,
                conference=paper.conference,
                abstract=paper.abstract,
                metadata=paper.metadata,
            )

        # ---------------------------
        # Entity nodes
        # ---------------------------

        self.add_entities(result.entities)

        # ---------------------------
        # Relationships
        # ---------------------------

        self.add_relationships(result.relationships)

    # =====================================================
    # Query Methods
    # =====================================================

    def get_node(self, node_id: str):

        if self.graph.has_node(node_id):
            return self.graph.nodes[node_id]

        return None

    def get_neighbors(self, node_id: str):

        if not self.graph.has_node(node_id):
            return []

        return list(self.graph.neighbors(node_id))

    def has_node(self, node_id: str):

        return self.graph.has_node(node_id)

    def has_edge(
        self,
        source: str,
        target: str,
    ):

        return self.graph.has_edge(source, target)

    # =====================================================
    # Statistics
    # =====================================================

    @property
    def num_nodes(self):

        return self.graph.number_of_nodes()

    @property
    def num_edges(self):

        return self.graph.number_of_edges()

    def summary(self) -> Dict:

        node_types = {}

        for _, data in self.graph.nodes(data=True):

            node_type = data.get("type", "Unknown")

            node_types[node_type] = (
                node_types.get(node_type, 0) + 1
            )

        edge_types = {}

        for _, _, data in self.graph.edges(data=True):

            relation = data.get("relationship", "Unknown")

            edge_types[relation] = (
                edge_types.get(relation, 0) + 1
            )

        return {
            "nodes": self.num_nodes,
            "edges": self.num_edges,
            "node_types": node_types,
            "edge_types": edge_types,
        }

    # =====================================================
    # Persistence
    # =====================================================

    def save_graph(self, path: str | Path):
        """
        Save graph as GraphML.
        """

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        nx.write_graphml(self.graph, path)

    def load_graph(self, path: str | Path):
        """
        Load GraphML file.
        """

        self.graph = nx.read_graphml(path)

    # =====================================================
    # Utilities
    # =====================================================

    def clear(self):
        """
        Remove everything from the graph.
        """

        self.graph.clear()

    def __len__(self):
        return self.num_nodes

    def __repr__(self):

        return (
            f"GraphManager("
            f"nodes={self.num_nodes}, "
            f"edges={self.num_edges})"
        )