"""
utils.py

Utility functions for the GraphRAG graph layer.

Responsibilities
----------------
✓ Generate graph-safe IDs
✓ Deduplicate entities
✓ Deduplicate relationships
✓ Graph statistics
✓ Lookup helpers

Does NOT
---------
✗ Build graphs
✗ Extract entities
✗ Serialize graphs
✗ Call the LLM
"""

import re
from collections import Counter
from typing import Dict, List

import networkx as nx

from graph.extraction.models import Entity, Relationship


# ==========================================================
# ID Helpers
# ==========================================================

def make_graph_id(name: str) -> str:
    """
    Converts a string into a graph-safe identifier.

    Example
    -------
    Attention Is All You Need
        -> attention_is_all_you_need
    """

    name = name.lower()

    name = re.sub(r"[^\w\s-]", "", name)

    name = re.sub(r"[-\s]+", "_", name)

    return name.strip("_")


# ==========================================================
# Entity Helpers
# ==========================================================

def deduplicate_entities(
    entities: List[Entity],
) -> List[Entity]:
    """
    Removes duplicate entities using entity ID.
    """

    unique = {}

    for entity in entities:
        unique[entity.id] = entity

    return list(unique.values())


def group_entities_by_type(
    entities: List[Entity],
) -> Dict[str, List[Entity]]:
    """
    Groups entities according to their type.
    """

    grouped = {}

    for entity in entities:

        grouped.setdefault(
            entity.type,
            []
        ).append(entity)

    return grouped


# ==========================================================
# Relationship Helpers
# ==========================================================

def deduplicate_relationships(
    relationships: List[Relationship],
) -> List[Relationship]:
    """
    Removes duplicate graph edges.
    """

    seen = set()

    unique = []

    for relationship in relationships:

        key = (
            relationship.source,
            relationship.relationship,
            relationship.target,
        )

        if key not in seen:

            seen.add(key)

            unique.append(relationship)

    return unique


# ==========================================================
# Graph Helpers
# ==========================================================

def node_exists(
    graph: nx.MultiDiGraph,
    node_id: str,
) -> bool:
    """
    Returns True if the node exists.
    """

    return graph.has_node(node_id)


def edge_exists(
    graph: nx.MultiDiGraph,
    source: str,
    target: str,
    relationship: str,
) -> bool:
    """
    Checks whether a relationship already exists.
    """

    if not graph.has_edge(source, target):
        return False

    edges = graph.get_edge_data(source, target)

    for _, attributes in edges.items():

        if (
            attributes.get("relationship")
            == relationship
        ):
            return True

    return False


# ==========================================================
# Statistics
# ==========================================================

def graph_statistics(
    graph: nx.MultiDiGraph,
) -> Dict:
    """
    Returns useful graph statistics.
    """

    node_counter = Counter()

    edge_counter = Counter()

    for _, data in graph.nodes(data=True):

        node_counter[data.get("type", "Unknown")] += 1

    for _, _, data in graph.edges(data=True):

        edge_counter[
            data.get("relationship", "Unknown")
        ] += 1

    return {
        "num_nodes": graph.number_of_nodes(),
        "num_edges": graph.number_of_edges(),
        "node_types": dict(node_counter),
        "relationship_types": dict(edge_counter),
    }


# ==========================================================
# Lookup Helpers
# ==========================================================

def find_nodes_by_type(
    graph: nx.MultiDiGraph,
    node_type: str,
) -> List[str]:
    """
    Returns all node IDs of a given type.
    """

    return [

        node

        for node, attrs in graph.nodes(data=True)

        if attrs.get("type") == node_type

    ]


def find_node_by_name(
    graph: nx.MultiDiGraph,
    name: str,
):
    """
    Returns the first node whose name matches.
    """

    name = name.lower()

    for node, attrs in graph.nodes(data=True):

        if attrs.get(
            "name",
            "",
        ).lower() == name:

            return node

    return None


# ==========================================================
# Debug
# ==========================================================

def print_graph_summary(
    graph: nx.MultiDiGraph,
):
    """
    Prints a concise graph summary.
    """

    stats = graph_statistics(graph)

    print("=" * 60)
    print("GRAPH SUMMARY")
    print("=" * 60)

    print(f"Nodes : {stats['num_nodes']}")
    print(f"Edges : {stats['num_edges']}")

    print("\nNode Types")

    for node_type, count in sorted(
        stats["node_types"].items()
    ):

        print(f"  {node_type:<15} {count}")

    print("\nRelationship Types")

    for rel, count in sorted(
        stats["relationship_types"].items()
    ):

        print(f"  {rel:<20} {count}")