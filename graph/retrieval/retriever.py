"""
retriever.py

Orchestrator for the Graph Retrieval Engine.
"""

from dataclasses import dataclass, field
import time
from typing import Any, Dict, List, Tuple
import networkx as nx

from .query_parser import QueryParser, ParsedQuery
from .matcher import NodeMatcher
from .traverser import GraphTraverser
from .ranker import NodeRanker
from .formatter import ContextFormatter
from .planner import RetrievalPlanner, RetrievalPlan
from .evaluator import RetrievalEvaluator


@dataclass
class RetrievalResult:
    """
    Structured retrieval result containing the formatted context, full plans,
    matched seed nodes, ranked nodes, sub-graph, trace details, and metrics.
    """
    context: str
    nodes: List[Dict[str, Any]] = field(default_factory=list)
    edges: List[Dict[str, Any]] = field(default_factory=list)
    score: float = 0.0
    
    parsed_query: ParsedQuery = None
    query_intent: str = ""
    retrieval_plan: RetrievalPlan = None
    matched_nodes: Dict[str, float] = field(default_factory=dict)
    ranked_nodes: List[Tuple[str, float]] = field(default_factory=list)
    subgraph: nx.MultiDiGraph = None
    statistics: Dict[str, Any] = field(default_factory=dict)
    overall_score: float = 0.0
    retrieval_trace: Dict[str, Any] = field(default_factory=dict)


class GraphRetriever:
    """
    High-level API coordinating the graph retrieval pipeline components.
    """

    def __init__(self, graph_or_path: Any):
        from pathlib import Path
        if isinstance(graph_or_path, (str, Path)):
            path = Path(graph_or_path)
            self.graph = nx.MultiDiGraph()
            if path.is_dir():
                graphml_files = list(path.glob("*.graphml"))
                json_files = list(path.glob("*.json"))
                if graphml_files:
                    self.graph = nx.read_graphml(graphml_files[0])
                elif json_files:
                    from graph.graph_builder.serializer import GraphSerializer
                    self.graph = GraphSerializer.load(json_files[0])
                else:
                    raise FileNotFoundError(f"No graph files found in directory {path}")
            else:
                if path.suffix == ".graphml":
                    self.graph = nx.read_graphml(path)
                elif path.suffix == ".json":
                    from graph.graph_builder.serializer import GraphSerializer
                    self.graph = GraphSerializer.load(path)
                else:
                    raise ValueError(f"Unsupported graph file format: {path.suffix}")
        else:
            self.graph = graph_or_path

        self.parser = QueryParser()
        self.matcher = NodeMatcher(self.graph)
        self.traverser = GraphTraverser(self.graph)
        self.ranker = NodeRanker()
        self.formatter = ContextFormatter()
        self.planner = RetrievalPlanner()
        self.evaluator = RetrievalEvaluator(len(self.graph))

    def retrieve_relational_context(self, query: str, top_n: int = 5) -> str:
        """
        Backward compatibility wrapper for retrieve_relational_context.
        """
        result = self.retrieve(query, top_k=top_n)
        return result.context

    def retrieve(
        self,
        query: str,
        max_depth: int = None,
        direction: str = "both",
        mode: str = "bfs",
        top_k: int = None,
        max_edges: int = 25,
        max_characters: int = 4000,
        show_evidence: bool = False,
    ) -> RetrievalResult:
        """
        Retrieves relevant structured relational context from the knowledge graph.
        """
        start_time = time.perf_counter()

        # 1. Parse Query & Detect Intent
        parsed_query = self.parser.parse(query)

        # 2. Generate Retrieval Plan
        plan = self.planner.plan(parsed_query)

        # Resolve parameter overrides
        actual_depth = max_depth if max_depth is not None else plan.max_depth
        actual_top_k = top_k if top_k is not None else plan.max_nodes
        actual_max_nodes = plan.max_nodes

        # 3. Match Query Terms to Graph Nodes
        seed_scores = self.matcher.match(parsed_query)

        # Filter seed nodes by allowed seed types from plan if specified
        if plan.seed_types and seed_scores:
            filtered_seed_scores = {}
            for node, score in seed_scores.items():
                node_type = self.graph.nodes[node].get("type", "")
                if node_type in plan.seed_types:
                    filtered_seed_scores[node] = score
            if filtered_seed_scores:
                seed_scores = filtered_seed_scores

        if not seed_scores:
            empty_trace = {
                "query": query,
                "detected_intent": parsed_query.intent,
                "parsed_query": {
                    "entities": parsed_query.entities,
                    "keywords": parsed_query.keywords,
                    "verbs": parsed_query.verbs,
                },
                "retrieval_plan": {
                    "allowed_relationships": plan.allowed_relationships,
                    "max_depth": actual_depth,
                    "max_nodes": actual_max_nodes,
                },
                "matched_seeds": {},
                "ranked_nodes": [],
                "statistics": {
                    "precision": 0.0,
                    "recall": 0.0,
                    "avg_path_length": 0.0,
                    "traversal_latency_ms": round((time.perf_counter() - start_time) * 1000.0, 2),
                    "nodes_visited": 0,
                    "nodes_retained": 0,
                    "edges_retained": 0,
                    "context_size_chars": 0,
                }
            }
            return RetrievalResult(
                context="No relevant context found in the knowledge graph.",
                parsed_query=parsed_query,
                query_intent=parsed_query.intent,
                retrieval_plan=plan,
                matched_nodes={},
                ranked_nodes=[],
                subgraph=nx.MultiDiGraph(),
                statistics=empty_trace["statistics"],
                overall_score=0.0,
                retrieval_trace=empty_trace
            )

        # 4. Traverse Neighborhood Subgraph (respecting allowed relationships and node budgets)
        seed_nodes = list(seed_scores.keys())
        subgraph = self.traverser.traverse(
            seed_nodes=seed_nodes,
            max_depth=actual_depth,
            direction=direction,
            mode=mode,
            allowed_relationships=plan.allowed_relationships,
            max_nodes=actual_max_nodes,
        )

        # 5. Rank Paths in Subgraph
        ranked_nodes, node_paths = self.ranker.rank(
            subgraph=subgraph,
            seed_scores=seed_scores,
            query_verbs=parsed_query.verbs,
            query_entities=parsed_query.entities,
            intent=parsed_query.intent,
        )

        # 6. Format to Deterministic Markdown Context (supporting show_evidence debug details)
        context = self.formatter.format(
            subgraph=subgraph,
            ranked_nodes=ranked_nodes,
            node_paths=node_paths,
            intent=parsed_query.intent,
            max_nodes=actual_top_k,
            max_edges=max_edges,
            max_characters=max_characters,
            show_evidence=show_evidence,
        )

        # 7. Extract Structured Nodes & Edges Lists (for backward compatibility)
        # Filters out nodes with score of 0 (e.g., from other disconnected components)
        top_node_ids = set([node_id for node_id, score in ranked_nodes[:actual_top_k] if score > 0.0])
        
        nodes_list = []
        for node_id in top_node_ids:
            if node_id in subgraph:
                nodes_list.append({"id": node_id, **subgraph.nodes[node_id]})

        edges_list = []
        for u, v, data in subgraph.edges(data=True):
            if u in top_node_ids and v in top_node_ids:
                edges_list.append({
                    "source": u,
                    "target": v,
                    "relationship": data.get("relationship", "RELATED_TO"),
                    "confidence": data.get("confidence", 1.0),
                })

        # Calculate average matched seed confidence as query score
        overall_score = sum(seed_scores.values()) / len(seed_scores) if seed_scores else 0.0

        # Calculate statistics using the evaluator (Upgrade 13)
        eval_metrics = self.evaluator.evaluate(
            visited_nodes=set(subgraph.nodes()),
            retained_nodes=list(top_node_ids),
            retained_edges=edges_list,
            context=context,
            node_paths=node_paths,
            matched_seeds=list(seed_scores.keys()),
            start_time=start_time,
        )

        # Build trace details (Upgrade 12)
        retrieval_trace = {
            "query": query,
            "detected_intent": parsed_query.intent,
            "parsed_query": {
                "entities": parsed_query.entities,
                "keywords": parsed_query.keywords,
                "verbs": parsed_query.verbs,
            },
            "retrieval_plan": {
                "allowed_relationships": plan.allowed_relationships,
                "max_depth": actual_depth,
                "max_nodes": actual_max_nodes,
            },
            "matched_seeds": seed_scores,
            "ranked_nodes": [(nid, score) for nid, score in ranked_nodes if score > 0.0],
            "node_paths": {nid: path_edges for nid, (_, path_edges) in node_paths.items() if nid in top_node_ids},
            "statistics": eval_metrics
        }

        return RetrievalResult(
            context=context,
            nodes=nodes_list,
            edges=edges_list,
            score=overall_score,
            parsed_query=parsed_query,
            query_intent=parsed_query.intent,
            retrieval_plan=plan,
            matched_nodes=seed_scores,
            ranked_nodes=ranked_nodes,
            subgraph=subgraph,
            statistics=eval_metrics,
            overall_score=overall_score,
            retrieval_trace=retrieval_trace
        )
