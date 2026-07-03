"""
node_factory.py

Creates graph nodes from extraction models.

Responsibilities
----------------
✓ Convert Paper -> NetworkX node
✓ Convert Entity -> NetworkX node
✓ Preserve metadata
✓ Prevent duplicate node creation

Does NOT
---------
✗ Build relationships
✗ Validate extraction
✗ Call the LLM
✗ Save graphs
"""

from typing import Dict, Any

import networkx as nx

from graph.extraction.models import Paper, Entity


class NodeFactory:
    """
    Factory responsible for creating graph nodes.
    """

    def __init__(self, graph: nx.MultiDiGraph):
        self.graph = graph

    # =====================================================
    # Public Methods
    # =====================================================

    def add_paper(self, paper: Paper) -> None:
        """
        Add the Paper node to the graph.
        """

        if paper.id in self.graph:
            return

        self.graph.add_node(
            paper.id,
            type="Paper",
            title=paper.title,
            year=paper.year,
            conference=paper.conference,
            abstract=paper.abstract,
            metadata=paper.metadata,
        )

    # -----------------------------------------------------

    def add_entity(self, entity: Entity) -> None:
        """
        Add an entity node to the graph.
        """

        if entity.id in self.graph:
            return

        self.graph.add_node(
            entity.id,
            type=entity.type,
            name=entity.name,
            description=entity.description,
            metadata=entity.metadata,
        )

    # -----------------------------------------------------

    def add_entities(self, entities: list[Entity]) -> None:
        """
        Add multiple entity nodes.
        """

        for entity in entities:
            self.add_entity(entity)

    # =====================================================
    # Utility Methods
    # =====================================================

    def node_exists(self, node_id: str) -> bool:
        """
        Returns True if a node already exists.
        """

        return node_id in self.graph

    # -----------------------------------------------------

    def get_node_attributes(
        self,
        node_id: str,
    ) -> Dict[str, Any]:
        """
        Return node attributes.
        """

        return dict(self.graph.nodes[node_id])

    # -----------------------------------------------------

    def number_of_nodes(self) -> int:
        """
        Returns the current number of nodes.
        """

        return self.graph.number_of_nodes()

    # =====================================================
    # Representation
    # =====================================================

    def __repr__(self):

        return (
            f"NodeFactory("
            f"nodes={self.graph.number_of_nodes()})"
        )