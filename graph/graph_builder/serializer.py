"""
serializer.py

Serialization utilities for the GraphRAG knowledge graph.

Responsibilities
----------------
✓ Save NetworkX graph to JSON
✓ Load graph from JSON
✓ Convert graph to dictionary
✓ Convert dictionary back to graph

Does NOT
---------
✗ Build graphs
✗ Extract entities
✗ Call LLMs
"""

from pathlib import Path
import json

import networkx as nx


class GraphSerializer:
    """
    Handles serialization of NetworkX graphs.
    """

    # =====================================================
    # Dictionary Conversion
    # =====================================================

    @staticmethod
    def to_dict(graph: nx.MultiDiGraph) -> dict:
        """
        Convert a NetworkX graph into a dictionary.
        """

        nodes = []

        for node_id, attrs in graph.nodes(data=True):

            nodes.append({
                "id": node_id,
                **attrs
            })

        edges = []

        for source, target, attrs in graph.edges(data=True):

            edges.append({
                "source": source,
                "target": target,
                **attrs
            })

        return {
            "nodes": nodes,
            "edges": edges,
        }

    # =====================================================
    # Graph Reconstruction
    # =====================================================

    @staticmethod
    def from_dict(data: dict) -> nx.MultiDiGraph:
        """
        Reconstruct a graph from a dictionary.
        """

        graph = nx.MultiDiGraph()

        # -------------------------
        # Nodes
        # -------------------------

        for node in data.get("nodes", []):

            node = node.copy()

            node_id = node.pop("id")

            graph.add_node(
                node_id,
                **node
            )

        # -------------------------
        # Edges
        # -------------------------

        for edge in data.get("edges", []):

            edge = edge.copy()

            source = edge.pop("source")
            target = edge.pop("target")

            graph.add_edge(
                source,
                target,
                **edge
            )

        return graph

    # =====================================================
    # JSON Export
    # =====================================================

    @classmethod
    def save(
        cls,
        graph: nx.MultiDiGraph,
        path: str | Path,
    ) -> Path:
        """
        Save graph as JSON.
        """

        path = Path(path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        data = cls.to_dict(graph)

        with open(path, "w", encoding="utf-8") as f:

            json.dump(
                data,
                f,
                indent=4,
                ensure_ascii=False,
            )

        return path

    # =====================================================
    # JSON Import
    # =====================================================

    @classmethod
    def load(
        cls,
        path: str | Path,
    ) -> nx.MultiDiGraph:
        """
        Load graph from a JSON file.
        """

        path = Path(path)

        with open(path, "r", encoding="utf-8") as f:

            data = json.load(f)

        return cls.from_dict(data)

    # =====================================================
    # Convenience Methods
    # =====================================================

    @classmethod
    def save_pretty(
        cls,
        graph: nx.MultiDiGraph,
        path: str | Path,
    ):
        """
        Alias for save().

        Included for future support of
        prettier JSON formatting.
        """

        return cls.save(graph, path)