"""
merger.py

Implements result merging strategies (e.g. Reciprocal Rank Fusion) for hybrid search.
"""

from typing import Any, Dict, List
from graph.query_engine.context_builder import GraphContext


class ResultMerger:
    """
    Combines outputs from both graph reasoning paths and vector database retrievals.
    """

    def merge(
        self,
        graph_context: GraphContext,
        vector_results: List[Dict[str, Any]],
        graph_weight: float = 0.7,
        vector_weight: float = 0.3
    ) -> Dict[str, Any]:
        """
        Merges retrieved results. Returns a combined hybrid payload dictionary.
        """
        # Weighted rank placeholder
        merged_payload = {
            "graph_context": graph_context,
            "vector_results": vector_results,
            "weights": {
                "graph": graph_weight,
                "vector": vector_weight
            },
            "confidence": graph_context.confidence * graph_weight
        }
        return merged_payload
