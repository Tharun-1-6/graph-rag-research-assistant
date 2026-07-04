"""
planner.py

Generates dynamic QueryPlans determining target node seed types, relationship filters,
and multi-hop traversal depths based on query intent analysis.
"""

from dataclasses import dataclass, field
import re
from typing import List, Set


@dataclass
class QueryPlan:
    """
    Structured query plan outlining reasoning bounds.
    """
    intent: str
    seed_types: List[str] = field(default_factory=list)
    allowed_relationships: List[str] = field(default_factory=list)
    max_depth: int = 2
    max_nodes: int = 20
    max_paths: int = 10


class QueryPlanner:
    """
    Analyzes questions to detect intent and yield search path limits.
    """

    # Core intents supported
    AUTHOR_QUERY = "AUTHOR_QUERY"
    METHOD_QUERY = "METHOD_QUERY"
    DATASET_QUERY = "DATASET_QUERY"
    BENCHMARK_QUERY = "BENCHMARK_QUERY"
    TASK_QUERY = "TASK_QUERY"
    METRIC_QUERY = "METRIC_QUERY"
    INSTITUTION_QUERY = "INSTITUTION_QUERY"
    EXPLANATION_QUERY = "EXPLANATION_QUERY"
    COMPARISON_QUERY = "COMPARISON_QUERY"
    RELATIONSHIP_QUERY = "RELATIONSHIP_QUERY"
    GENERAL_QUERY = "GENERAL_QUERY"

    def plan(self, query: str) -> QueryPlan:
        """
        Classifies query intent and returns the execution parameters.
        """
        q_lower = query.lower()
        words = re.findall(r"\b\w{3,}\b", q_lower)

        # 1. Detect Intent
        intent = self._detect_intent(q_lower, words)

        # 2. Map Intent to Constraints & Hop Depth
        if intent == self.AUTHOR_QUERY:
            return QueryPlan(
                intent=intent,
                seed_types=["Paper", "Author"],
                allowed_relationships=["AUTHORED", "AFFILIATED_WITH"],
                max_depth=1,
                max_nodes=15,
                max_paths=8
            )

        elif intent == self.INSTITUTION_QUERY:
            return QueryPlan(
                intent=intent,
                seed_types=["Institution", "Author", "Paper"],
                allowed_relationships=["AFFILIATED_WITH", "AUTHORED"],
                max_depth=1,
                max_nodes=15,
                max_paths=8
            )

        elif intent == self.METHOD_QUERY:
            return QueryPlan(
                intent=intent,
                seed_types=["Method", "Architecture", "Paper"],
                allowed_relationships=["PROPOSES", "USES", "RELATED_TO", "IMPROVES_UPON"],
                max_depth=2,
                max_nodes=20,
                max_paths=10
            )

        elif intent == self.DATASET_QUERY:
            return QueryPlan(
                intent=intent,
                seed_types=["Dataset", "Benchmark", "Paper"],
                allowed_relationships=["USES", "EVALUATED_ON", "RELATED_TO"],
                max_depth=2,
                max_nodes=20,
                max_paths=10
            )

        elif intent == self.BENCHMARK_QUERY:
            return QueryPlan(
                intent=intent,
                seed_types=["Benchmark", "Dataset", "Paper"],
                allowed_relationships=["USES", "EVALUATED_ON", "RELATED_TO"],
                max_depth=2,
                max_nodes=20,
                max_paths=10
            )

        elif intent == self.METRIC_QUERY:
            return QueryPlan(
                intent=intent,
                seed_types=["Metric", "Benchmark", "Method", "Paper"],
                allowed_relationships=["USES", "EVALUATED_ON", "RELATED_TO"],
                max_depth=2,
                max_nodes=20,
                max_paths=10
            )

        elif intent == self.TASK_QUERY:
            return QueryPlan(
                intent=intent,
                seed_types=["Task", "Method", "Dataset", "Paper"],
                allowed_relationships=["PERFORMS", "RELATED_TO", "USES"],
                max_depth=2,
                max_nodes=20,
                max_paths=10
            )

        elif intent == self.COMPARISON_QUERY:
            return QueryPlan(
                intent=intent,
                seed_types=["Method", "Architecture"],
                allowed_relationships=["RELATED_TO", "IMPROVES_UPON"],
                max_depth=3,  # Deeper paths for multi-hop comparison
                max_nodes=25,
                max_paths=12
            )

        elif intent == self.EXPLANATION_QUERY:
            return QueryPlan(
                intent=intent,
                seed_types=["Method", "Architecture", "Topic", "Paper"],
                allowed_relationships=["PROPOSES", "USES", "RELATED_TO", "IMPROVES_UPON", "BELONGS_TO"],
                max_depth=3,  # Deeper paths for descriptive context
                max_nodes=25,
                max_paths=12
            )

        elif intent == self.RELATIONSHIP_QUERY:
            return QueryPlan(
                intent=intent,
                seed_types=[],  # empty allows all types
                allowed_relationships=["AUTHORED", "PROPOSES", "USES", "EVALUATED_ON", "IMPROVES_UPON", "AFFILIATED_WITH"],
                max_depth=2,
                max_nodes=20,
                max_paths=10
            )

        else:  # GENERAL_QUERY fallback
            return QueryPlan(
                intent=self.GENERAL_QUERY,
                seed_types=[],
                allowed_relationships=[],
                max_depth=2,
                max_nodes=20,
                max_paths=10
            )

    def _detect_intent(self, q_lower: str, words: List[str]) -> str:
        """
        Heuristic NLP router classifying question intent.
        """
        # Semantic router for person/authorship queries
        if "who" in words:
            if any(w in q_lower for w in ["propose", "introduce", "design", "create", "develop"]):
                return self.METHOD_QUERY
            else:
                return self.AUTHOR_QUERY

        # Institution Query
        if (any(w in q_lower for w in ["institution", "university", "lab", "affiliated", "work at", "works at", "working at", "company", "organization"])
            or ("where" in words and "work" in words)):
            return self.INSTITUTION_QUERY

        # Comparison Query
        if any(w in q_lower for w in ["compare", "difference", " vs ", "versus", "contrast", "different from", "comparison"]):
            return self.COMPARISON_QUERY

        # Explanation Query
        if any(w in q_lower for w in ["explain", "what is", "how does", "describe", "definition", "mechanism", "walkthrough", "details of", "why", "detail"]):
            return self.EXPLANATION_QUERY

        # Benchmark Query
        if any(w in q_lower for w in ["benchmark", "evaluation set"]):
            return self.BENCHMARK_QUERY

        # Dataset Query
        if any(w in q_lower for w in ["dataset", "corpus", "data"]):
            return self.DATASET_QUERY

        # Metric Query
        if any(w in q_lower for w in ["metric", "score", "bleu", "perplexity", "f1", "accuracy", "recall", "precision"]):
            return self.METRIC_QUERY

        # Task Query
        if any(w in q_lower for w in ["task", "job", "perform", "translation"]):
            return self.TASK_QUERY

        # Relationship Query (e.g. connections, link, relationship)
        if any(w in q_lower for w in ["connect", "link", "relationship", "relation", "between"]):
            return self.RELATIONSHIP_QUERY

        # Author Query fallback
        if any(w in q_lower for w in ["who wrote", "author", "creator", "by:"]) or "by" in words:
            return self.AUTHOR_QUERY

        # Method/Architecture Query
        if any(w in q_lower for w in ["model", "architecture", "method", "algorithm", "attention", "transformer", "network"]):
            return self.METHOD_QUERY

        return self.GENERAL_QUERY
