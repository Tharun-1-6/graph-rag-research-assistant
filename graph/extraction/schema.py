"""
schema.py

Defines the ontology (schema) for the GraphRAG knowledge graph.

This file acts as the single source of truth for:
- Allowed node types
- Allowed relationship types
- Allowed graph connections

Every component in the project should rely on this file
instead of hardcoding node or relationship names.

Used by:
---------
✓ prompt.py
✓ extractor.py
✓ validator.py
✓ graph_builder.py
✓ retriever.py
"""

from typing import Dict, Set, Tuple
# ==========================================================
# Node Types
# ==========================================================

NODE_TYPES: Set[str] = {
    "Paper",
    "Author",
    "Institution",
    "Conference",
    "Method",
    "Architecture",
    "Dataset",
    "Benchmark",
    "Task",
    "Metric",
    "Topic",
}


# ==========================================================
# Relationship Types
# ==========================================================

RELATIONSHIP_TYPES: Set[str] = {
    "AUTHORED",
    "AFFILIATED_WITH",
    "PUBLISHED_AT",
    "PROPOSES",
    "USES",
    "EVALUATED_ON",
    "PERFORMS",
    "IMPROVES_UPON",
    "BELONGS_TO",
    "RELATED_TO",
}

# ==========================================================
# Allowed Graph Connections
#
# (Source Node, Relationship, Target Node)
# ==========================================================

VALID_CONNECTIONS: Set[Tuple[str, str, str]] = {
    # ------------------------------------------------------
    # Paper Relationships
    # ------------------------------------------------------
    ("Paper", "AUTHORED", "Author"),
    ("Paper", "PUBLISHED_AT", "Conference"),
    ("Paper", "PROPOSES", "Method"),
    ("Paper", "PROPOSES", "Architecture"),
    ("Paper", "USES", "Dataset"),
    ("Paper", "USES", "Benchmark"),
    ("Paper", "USES", "Metric"),
    ("Paper", "BELONGS_TO", "Topic"),
    ("Paper", "RELATED_TO", "Task"),

    # ------------------------------------------------------
    # Author Relationships
    # ------------------------------------------------------
    ("Author", "AFFILIATED_WITH", "Institution"),

    # ------------------------------------------------------
    # Method Relationships
    # ------------------------------------------------------
    ("Method", "USES", "Dataset"),
    ("Method", "EVALUATED_ON", "Benchmark"),
    ("Method", "PERFORMS", "Task"),
    ("Method", "IMPROVES_UPON", "Method"),
    ("Method", "RELATED_TO", "Architecture"),

    # ------------------------------------------------------
    # Architecture Relationships
    # ------------------------------------------------------
    ("Architecture", "USES", "Dataset"),
    ("Architecture", "EVALUATED_ON", "Benchmark"),
    ("Architecture", "PERFORMS", "Task"),
    ("Architecture", "IMPROVES_UPON", "Architecture"),
    ("Architecture", "RELATED_TO", "Method"),

    # ------------------------------------------------------
    # Dataset Relationships
    # ------------------------------------------------------
    ("Dataset", "BELONGS_TO", "Topic"),
    ("Dataset", "RELATED_TO", "Task"),

    # ------------------------------------------------------
    # Benchmark Relationships
    # ------------------------------------------------------
    ("Benchmark", "RELATED_TO", "Task"),

    # ------------------------------------------------------
    # Topic Relationships
    # ------------------------------------------------------
    ("Topic", "RELATED_TO", "Topic"),
}

# ==========================================================
# Quick Lookup Dictionaries
# ==========================================================

# Relationship -> Possible Source Nodes
RELATION_TO_SOURCE: Dict[str, Set[str]] = {}
# Relationship -> Possible Target Nodes
RELATION_TO_TARGET: Dict[str, Set[str]] = {}

for source, relation, target in VALID_CONNECTIONS:

    RELATION_TO_SOURCE.setdefault(
        relation,
        set()
    ).add(source)

    RELATION_TO_TARGET.setdefault(
        relation,
        set()
    ).add(target)


# ==========================================================
# Helper Functions
# ==========================================================

def is_valid_node(node_type: str) -> bool:
    """
    Returns True if the node type exists.
    """
    return node_type in NODE_TYPES

def is_valid_relationship(relationship: str) -> bool:
    """
    Returns True if the relationship exists.
    """
    return relationship in RELATIONSHIP_TYPES


def is_valid_connection(
    source_type: str,
    relationship: str,
    target_type: str,
) -> bool:
    """
    Checks whether a graph edge is allowed.

    Example
    -------
    >>> is_valid_connection(
            "Paper",
            "PROPOSES",
            "Method"
        )

    True
    """
    return (
        source_type,
        relationship,
        target_type,
    ) in VALID_CONNECTIONS


def get_possible_sources(
    relationship: str,
) -> Set[str]:
    """
    Returns all possible source node types
    for a relationship.
    """
    return RELATION_TO_SOURCE.get(
        relationship,
        set(),
    )

def get_possible_targets(
    relationship: str,
) -> Set[str]:
    """
    Returns all possible target node types
    for a relationship.
    """

    return RELATION_TO_TARGET.get(
        relationship,
        set(),
    )


# ==========================================================
# Debug
# ==========================================================

if __name__ == "__main__":

    print("========== Graph Schema ==========\n")

    print("Node Types")

    for node in sorted(NODE_TYPES):
        print(f"  • {node}")

    print("\nRelationship Types")

    for relation in sorted(RELATIONSHIP_TYPES):
        print(f"  • {relation}")

    print("\nValid Connections")

    for connection in sorted(VALID_CONNECTIONS):
        print(connection)