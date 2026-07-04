"""
edge_factory.py

Creates graph edges from extraction relationships.

Responsibilities
----------------
✓ Convert Relationship -> NetworkX edge
✓ Preserve confidence scores
✓ Preserve metadata
✓ Skip invalid references

Does NOT
---------
✗ Create nodes
✗ Validate extraction
✗ Call the LLM
✗ Save graphs
"""

from typing import Dict, Any

import networkx as nx

from graph.extraction.models import Relationship


class EdgeFactory:
    """
    Factory responsible for creating graph edges.
    """

    def __init__(self, graph: nx.MultiDiGraph):
        self.graph = graph

    # =====================================================
    # Public Methods
    # =====================================================

    def add_relationship(
        self,
        relationship: Relationship,
    ) -> bool:
        """
        Add a relationship edge.

        Returns
        -------
        bool
            True if the edge was added or updated,
            False if either endpoint does not exist.
        """

        if relationship.source not in self.graph:
            return False

        if relationship.target not in self.graph:
            return False

        # Prevent duplicate edges by merging/updating if relationship exists
        if self.edge_exists(relationship.source, relationship.target, relationship.relationship):
            edges_data = self.graph.get_edge_data(relationship.source, relationship.target)
            if edges_data is not None:
                for key, edge_attrs in edges_data.items():
                    if edge_attrs.get("relationship") == relationship.relationship:
                        if relationship.confidence is not None:
                            edge_attrs["confidence"] = max(
                                edge_attrs.get("confidence", 0.0),
                                relationship.confidence
                            )
                        break
            return True

        attrs = {
            "relationship": relationship.relationship,
            "confidence": relationship.confidence,
        }
        # Filter out None values
        attrs = {k: v for k, v in attrs.items() if v is not None}

        self.graph.add_edge(
            relationship.source,
            relationship.target,
            **attrs
        )

        return True

    # -----------------------------------------------------

    def add_relationships(
        self,
        relationships: list[Relationship],
    ) -> int:
        """
        Add multiple relationships.

        Returns
        -------
        int
            Number of successfully added edges.
        """

        added = 0

        for relationship in relationships:

            if self.add_relationship(relationship):
                added += 1

        return added

    # =====================================================
    # Utility Methods
    # =====================================================

    def edge_exists(
        self,
        source: str,
        target: str,
        relationship: str | None = None,
    ) -> bool:
        """
        Check whether an edge exists.

        If relationship is None,
        checks for any edge between source and target.
        """

        if not self.graph.has_edge(source, target):
            return False

        if relationship is None:
            return True

        edges = self.graph.get_edge_data(source, target)

        if edges is None:
            return False

        for _, attributes in edges.items():

            if attributes.get("relationship") == relationship:
                return True

        return False

    # -----------------------------------------------------

    def get_edge_attributes(
        self,
        source: str,
        target: str,
    ) -> Dict[Any, Dict]:
        """
        Return all edge attributes between two nodes.
        """

        return self.graph.get_edge_data(source, target, default={})

    # -----------------------------------------------------

    def number_of_edges(self) -> int:
        """
        Return current edge count.
        """

        return self.graph.number_of_edges()

    # =====================================================
    # Representation
    # =====================================================

    def __repr__(self):

        return (
            f"EdgeFactory("
            f"edges={self.graph.number_of_edges()})"
        )