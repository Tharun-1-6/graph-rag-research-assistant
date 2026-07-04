"""
planner.py

Generates dynamic RetrievalPlans based on the QueryIntent and parsed terms.
"""

from dataclasses import dataclass, field
from typing import List

from .query_parser import (
    ParsedQuery,
    AUTHOR_QUERY,
    METHOD_QUERY,
    DATASET_QUERY,
    BENCHMARK_QUERY,
    TASK_QUERY,
    METRIC_QUERY,
    INSTITUTION_QUERY,
    EXPLANATION_QUERY,
    COMPARISON_QUERY,
    GENERAL_QUERY,
)


@dataclass
class RetrievalPlan:
    """
    Retrieval configuration dynamically planned for a query.
    """
    intent: str
    seed_types: List[str] = field(default_factory=list)
    allowed_relationships: List[str] = field(default_factory=list)
    max_depth: int = 2
    max_nodes: int = 15
    expand_neighbors: bool = True


class RetrievalPlanner:
    """
    Maps QueryIntent to structured retrieval configurations.
    """

    def plan(self, parsed_query: ParsedQuery) -> RetrievalPlan:
        """
        Generates a RetrievalPlan for the given ParsedQuery.
        """
        intent = parsed_query.intent

        if intent == AUTHOR_QUERY:
            return RetrievalPlan(
                intent=intent,
                seed_types=["Paper", "Author"],
                allowed_relationships=["AUTHORED", "AFFILIATED_WITH"],
                max_depth=1,
                max_nodes=10,
            )
            
        elif intent == METHOD_QUERY:
            return RetrievalPlan(
                intent=intent,
                seed_types=["Method", "Architecture", "Paper"],
                allowed_relationships=["PROPOSES", "USES", "RELATED_TO", "IMPROVES_UPON"],
                max_depth=2,
                max_nodes=15,
            )
            
        elif intent == DATASET_QUERY:
            return RetrievalPlan(
                intent=intent,
                seed_types=["Dataset", "Benchmark", "Paper"],
                allowed_relationships=["USES", "EVALUATED_ON", "RELATED_TO"],
                max_depth=2,
                max_nodes=15,
            )
            
        elif intent == BENCHMARK_QUERY:
            return RetrievalPlan(
                intent=intent,
                seed_types=["Benchmark", "Dataset", "Paper"],
                allowed_relationships=["USES", "EVALUATED_ON", "RELATED_TO"],
                max_depth=2,
                max_nodes=15,
            )
            
        elif intent == EXPLANATION_QUERY:
            return RetrievalPlan(
                intent=intent,
                seed_types=["Method", "Architecture", "Topic", "Paper"],
                allowed_relationships=["PROPOSES", "USES", "RELATED_TO", "IMPROVES_UPON", "BELONGS_TO"],
                max_depth=3,
                max_nodes=20,
            )
            
        elif intent == COMPARISON_QUERY:
            return RetrievalPlan(
                intent=intent,
                seed_types=["Method", "Architecture"],
                allowed_relationships=["RELATED_TO", "IMPROVES_UPON"],
                max_depth=3,
                max_nodes=20,
            )
            
        elif intent == INSTITUTION_QUERY:
            return RetrievalPlan(
                intent=intent,
                seed_types=["Institution", "Author", "Paper"],
                allowed_relationships=["AFFILIATED_WITH", "AUTHORED"],
                max_depth=1,
                max_nodes=15,
            )
            
        elif intent == METRIC_QUERY:
            return RetrievalPlan(
                intent=intent,
                seed_types=["Metric", "Benchmark", "Method", "Paper"],
                allowed_relationships=["USES", "EVALUATED_ON", "RELATED_TO"],
                max_depth=2,
                max_nodes=15,
            )
            
        elif intent == TASK_QUERY:
            return RetrievalPlan(
                intent=intent,
                seed_types=["Task", "Method", "Dataset", "Paper"],
                allowed_relationships=["PERFORMS", "RELATED_TO", "USES"],
                max_depth=2,
                max_nodes=15,
            )
            
        else:  # GENERAL_QUERY or default fallback
            return RetrievalPlan(
                intent=GENERAL_QUERY,
                seed_types=[],  # empty permits all
                allowed_relationships=[],  # empty permits all
                max_depth=2,
                max_nodes=15,
            )
