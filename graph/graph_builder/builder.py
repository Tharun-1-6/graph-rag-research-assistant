"""
builder.py

Builds a NetworkX knowledge graph from an ExtractionResult.

Pipeline
--------
ExtractionResult
        │
        ▼
GraphBuilder
        │
        ▼
NetworkX MultiDiGraph

Responsibilities
----------------
✓ Create Paper node
✓ Create Entity nodes
✓ Create Relationship edges
✓ Preserve metadata

Does NOT
---------
✗ Call the LLM
✗ Parse JSON
✗ Validate extraction
✗ Normalize entities
"""

from typing import Optional

import networkx as nx

from graph.extraction.models import (
    ExtractionResult,
    Entity,
    Relationship,
)


class GraphBuilder:
    """
    Converts an ExtractionResult into a NetworkX graph.
    """

    def __init__(self):
        self.graph = nx.MultiDiGraph()

    # =====================================================
    # Public
    # =====================================================

    def build(
        self,
        extraction: ExtractionResult,
    ) -> nx.MultiDiGraph:
        """
        Build a graph from an ExtractionResult.
        """

        # Reset graph
        self.graph = nx.MultiDiGraph()

        # Add paper
        self._add_paper(extraction)

        # Add entities
        for entity in extraction.entities:
            self._add_entity(entity)

        # Add relationships
        for relationship in extraction.relationships:
            self._add_relationship(relationship)

        return self.graph

    # =====================================================
    # Paper
    # =====================================================

    def _add_paper(
        self,
        extraction: ExtractionResult,
    ) -> None:

        paper = extraction.paper

        self.graph.add_node(
            paper.id,
            type="Paper",
            title=paper.title,
            year=paper.year,
            conference=paper.conference,
            abstract=paper.abstract,
            metadata=paper.metadata,
        )

    # =====================================================
    # Entity
    # =====================================================

    def _add_entity(
        self,
        entity: Entity,
    ) -> None:

        self.graph.add_node(
            entity.id,
            type=entity.type,
            name=entity.name,
            description=entity.description,
            metadata=entity.metadata,
        )

    # =====================================================
    # Relationship
    # =====================================================

    def _add_relationship(
        self,
        relationship: Relationship,
    ) -> None:

        # Skip invalid references
        if relationship.source not in self.graph:
            return

        if relationship.target not in self.graph:
            return

        self.graph.add_edge(
            relationship.source,
            relationship.target,
            relationship=relationship.relationship,
            confidence=relationship.confidence,
            metadata=relationship.metadata,
        )

    # =====================================================
    # Statistics
    # =====================================================

    def number_of_nodes(self) -> int:
        return self.graph.number_of_nodes()

    def number_of_edges(self) -> int:
        return self.graph.number_of_edges()

    # =====================================================
    # Helpers
    # =====================================================

    def get_graph(self) -> nx.MultiDiGraph:
        return self.graph

    def clear(self) -> None:
        self.graph.clear()

    # =====================================================
    # Representation
    # =====================================================

    def __repr__(self):

        return (
            f"GraphBuilder("
            f"nodes={self.graph.number_of_nodes()}, "
            f"edges={self.graph.number_of_edges()})"
        )