"""
path_ranker.py

Ranks complete multi-hop reasoning paths using node confidence, relationship relevance,
path length penalties, degree hub centrality, and paper overlap metrics.
"""

from dataclasses import dataclass
from typing import Any, Dict, List
import networkx as nx

from .path_search import ReasoningPath


@dataclass
class RankedPath:
    """
    Represents a scored and ranked reasoning path.
    """
    score: float  # Normalized score between 0.0 and 1.0
    nodes: List[str]
    edges: List[Dict[str, Any]]
    reason: str
    path_str: str  # Formatted human-readable string


class PathRanker:
    """
    Scores and ranks reasoning paths to select the top-k paths for LLM reasoning.
    """

    REL_WEIGHTS: Dict[str, float] = {
        "AUTHORED": 1.0,
        "PROPOSES": 1.0,
        "IMPROVES_UPON": 0.95,
        "USES": 0.90,
        "EVALUATED_ON": 0.85,
        "PERFORMS": 0.85,
        "AFFILIATED_WITH": 0.80,
        "PUBLISHED_AT": 0.60,
        "RELATED_TO": 0.50,
    }

    def __init__(self, graph: nx.MultiDiGraph):
        self.graph = graph

    def rank(
        self,
        paths: List[ReasoningPath],
        resolved_confidences: Dict[str, float],
        max_paths: int = 10
    ) -> List[RankedPath]:
        """
        Calculates scores for a list of paths and returns the top-k ranked paths.
        """
        ranked_paths: List[RankedPath] = []
        if not paths:
            return []

        # Find max degree in the graph for normalized hub centrality calculations
        degrees = [self.graph.degree(n) for n in self.graph.nodes]
        max_degree = max(degrees) if degrees else 1.0

        for path in paths:
            # 1. Base Seed Confidence Score (mean of resolved seeds, fallback 0.8 for matched nodes, 1.0 for discovered)
            seed_scores = []
            for node in path.nodes:
                if node in resolved_confidences:
                    seed_scores.append(resolved_confidences[node])
                else:
                    # Discoverable node, start with neutral high rating
                    seed_scores.append(0.85)
            seed_conf = sum(seed_scores) / len(seed_scores)

            # 2. Relationship Relevance Score (mean of edge labels weights)
            rel_scores = [self.REL_WEIGHTS.get(e.get("relationship", ""), 0.5) for e in path.edges]
            rel_score = sum(rel_scores) / len(rel_scores) if rel_scores else 1.0

            # 3. Edge Confidence Score
            edge_conf_scores = [e.get("confidence", 1.0) for e in path.edges]
            edge_conf = sum(edge_conf_scores) / len(edge_conf_scores) if edge_conf_scores else 1.0

            # 4. Path Length/Depth Penalty (Shorter paths preferred)
            depth_penalty = 1.0 / (len(path.nodes) ** 0.5)

            # 5. Hub Centrality Boost (favor paths travelling through high-degree hub nodes)
            path_degrees = [self.graph.degree(n) for n in path.nodes]
            avg_deg = sum(path_degrees) / len(path_degrees) if path_degrees else 1.0
            degree_boost = min(1.3, 1.0 + (avg_deg / (max_degree * 5.0)))

            # 6. Paper Overlap Boost (favors nodes mentioned in multiple papers)
            overlap_count = sum(1 for n in path.nodes if self.graph.nodes.get(n, {}).get("paper_count", 1) > 1)
            overlap_boost = min(1.2, 1.0 + (overlap_count * 0.05))

            # Calculate Raw Path Score
            raw_score = seed_conf * rel_score * edge_conf * depth_penalty * degree_boost * overlap_boost
            
            # Normalize to standard 0.0 to 1.0 range
            normalized_score = min(1.0, max(0.0, raw_score))

            # Construct explanation reason string
            reasons = []
            if seed_conf > 0.9:
                reasons.append("Exact match seed")
            if rel_score > 0.9:
                reasons.append("High priority relationship")
            if len(path.nodes) <= 2:
                reasons.append("Short path depth")
            if overlap_boost > 1.0:
                reasons.append("Contains shared entities")
            
            reason_str = ", ".join(reasons) if reasons else "Contextual path discovery"

            path_str = path.to_string(self.graph)

            ranked_paths.append(
                RankedPath(
                    score=round(normalized_score, 4),
                    nodes=path.nodes,
                    edges=path.edges,
                    reason=reason_str,
                    path_str=path_str
                )
            )

        # Sort descending by score
        sorted_ranked = sorted(ranked_paths, key=lambda x: x.score, reverse=True)
        return sorted_ranked[:max_paths]
