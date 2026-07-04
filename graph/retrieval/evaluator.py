"""
evaluator.py

Evaluates the performance and quality of retrieval runs (Precision, Recall, Latency, etc.).
"""

import time
from typing import Any, Dict, List, Set


class RetrievalEvaluator:
    """
    Computes heuristic metrics to measure search and traversal quality.
    """

    def __init__(self, base_graph_size: int = 1):
        self.base_graph_size = base_graph_size

    def evaluate(
        self,
        visited_nodes: Set[str],
        retained_nodes: List[str],
        retained_edges: List[Dict[str, Any]],
        context: str,
        node_paths: Dict[str, Any],
        matched_seeds: List[str],
        start_time: float,
    ) -> Dict[str, Any]:
        """
        Calculates search precision, recall proxy, average path length, and latency.
        """
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000.0

        n_visited = len(visited_nodes)
        n_retained = len(retained_nodes)

        # Precision: Proportion of visited nodes that were actually selected for context
        precision = n_retained / max(1, n_visited)

        # Recall: Proportion of matched seed entities that were successfully retained
        seeds_set = set(matched_seeds)
        retained_seeds = seeds_set.intersection(set(retained_nodes))
        recall = len(retained_seeds) / max(1, len(seeds_set))

        # Average Path Length (hops from seed nodes)
        path_lengths = []
        for node in retained_nodes:
            if node in node_paths:
                _, path_edges = node_paths[node]
                path_lengths.append(len(path_edges))
        avg_path_len = sum(path_lengths) / max(1, len(path_lengths))

        # Edge utilization
        edge_utilization = len(retained_edges)

        return {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "avg_path_length": round(avg_path_len, 2),
            "traversal_latency_ms": round(latency_ms, 2),
            "nodes_visited": n_visited,
            "nodes_retained": n_retained,
            "edges_retained": edge_utilization,
            "context_size_chars": len(context),
        }
