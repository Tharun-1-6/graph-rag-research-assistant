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

        # ---------------------------------------------
        # Automatic Paper Links
        # ---------------------------------------------
        paper_id = extraction.paper.id

        # Link Paper to Authors and proposed Methods/Architectures
        for entity in extraction.entities:
            if entity.type == "Author":
                self.graph.add_edge(
                    paper_id,
                    entity.id,
                    relationship="AUTHORED",
                    confidence=1.0,
                )
            elif entity.type in ("Method", "Architecture"):
                self.graph.add_edge(
                    paper_id,
                    entity.id,
                    relationship="PROPOSES",
                    confidence=1.0,
                )

        # Link Paper to Conference if present
        conf_name = extraction.paper.conference
        if conf_name:
            # Generate graph-safe ID for the conference
            import re
            conf_id = conf_name.lower()
            conf_id = re.sub(r"[^\w\s-]", "", conf_id)
            conf_id = re.sub(r"[-\s]+", "_", conf_id).strip("_")

            # Add Conference node if it doesn't exist
            if conf_id not in self.graph:
                self.graph.add_node(
                    conf_id,
                    type="Conference",
                    name=conf_name,
                )

            self.graph.add_edge(
                paper_id,
                conf_id,
                relationship="PUBLISHED_AT",
                confidence=1.0,
            )

        return self.graph

    # =====================================================
    # Paper
    # =====================================================

    def _add_paper(
        self,
        extraction: ExtractionResult,
    ) -> None:

        paper = extraction.paper
        
        attrs = {
            "type": "Paper",
            "title": paper.title,
            "year": paper.year,
            "conference": paper.conference,
            "abstract": paper.abstract,
        }
        # Filter out None values
        attrs = {k: v for k, v in attrs.items() if v is not None}

        self.graph.add_node(
            paper.id,
            **attrs
        )

    # =====================================================
    # Entity
    # =====================================================

    def _add_entity(
        self,
        entity: Entity,
    ) -> None:

        attrs = {
            "type": entity.type,
            "name": entity.name,
            "description": entity.description,
        }
        # Filter out None values
        attrs = {k: v for k, v in attrs.items() if v is not None}

        self.graph.add_node(
            entity.id,
            **attrs
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