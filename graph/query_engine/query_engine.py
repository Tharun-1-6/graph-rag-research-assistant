from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import networkx as nx

from .entity_resolver import EntityResolver, ResolvedEntity
from .planner import QueryPlanner, QueryPlan
from .path_search import PathSearcher, ReasoningPath
from .path_ranker import PathRanker, RankedPath
from .context_builder import ContextBuilder, GraphContext


@dataclass
class RetrievalResult:
    """
    Stable structured output contract returned by every retrieval function.
    """
    markdown_context: str
    retrieval_context: Dict[str, Any]
    graph_context: GraphContext

    def __getattr__(self, name: str) -> Any:
        # Transparently forward attributes/methods to the underlying graph_context
        return getattr(self.graph_context, name)


class QueryEngine:
    """
    Orchestrates the entire query execution pipeline, converting natural language questions
    to structured multi-hop Reasoning GraphContexts.
    """

    def __init__(self, graph: nx.MultiDiGraph):
        """
        Initializes query pipeline components.
        """
        self.graph = graph
        self.resolver = EntityResolver(graph)
        self.planner = QueryPlanner()
        self.searcher = PathSearcher(graph)
        self.ranker = PathRanker(graph)
        self.context_builder = ContextBuilder(graph)

    def query(self, user_query: str, max_hops: Optional[int] = None) -> RetrievalResult:
        """
        Executes a question retrieval run over the graph to output structured reasoning context.

        Parameters
        ----------
        user_query : str
            The natural language search query.
        max_hops : int, optional
            Configurable multi-hop limit override (Phase 6). If None, uses intent-aware defaults.

        Returns
        -------
        RetrievalResult
            The structured query engine retrieval result context.
        """
        # 1. Parse & Plan Intent Bounds
        plan = self.planner.plan(user_query)
        if max_hops is not None:
            plan.max_depth = max_hops

        # 2. Extract terms and Resolve Entities
        # Extract keywords by stripping common punctuation and cleaning strings, ignoring stop words
        import re
        STOP_WORDS = {
            "explain", "describe", "compare", "contrast", "what", "where", "how", "who", "why", 
            "the", "and", "a", "an", "of", "to", "in", "is", "for", "with", "on", "at", "by", 
            "from", "as", "about", "this", "that", "these", "those", "their", "its", "it"
        }
        clean_words = [w for w in re.findall(r"\b\w{3,}\b", user_query.lower()) if w not in STOP_WORDS]
        resolved_entities = self.resolver.resolve_many(clean_words)

        # Filter seed nodes to match allowed planner seed types
        seed_ids = []
        resolved_map = {}
        for ent in resolved_entities:
            if not plan.seed_types or ent.type in plan.seed_types:
                seed_ids.append(ent.id)
                resolved_map[ent.id] = ent.confidence

        if not seed_ids:
            # Fallback: if no typed seeds matched, try using all resolved entities regardless of type pre-filter
            seed_ids = [ent.id for ent in resolved_entities]
            resolved_map = {ent.id: ent.confidence for ent in resolved_entities}

        # Scalability constraint: Limit search seeds to top 8 to prevent traversal path combinatorial explosions
        seed_ids = seed_ids[:8]

        # 3. Discover Multi-Hop Traversal Paths
        raw_paths = self.searcher.find_all_paths(
            seeds=seed_ids,
            max_depth=plan.max_depth,
            allowed_relationships=plan.allowed_relationships
        )

        # 4. Score and Rank Complete Paths
        ranked_paths = self.ranker.rank(
            paths=raw_paths,
            resolved_confidences=resolved_map,
            max_paths=plan.max_paths
        )

        # 5. Formulate Structured GraphContext
        context = self.context_builder.build(ranked_paths)

        # Fallback: if no paths were found, populate context directly with resolved seed details
        if not context.paths and resolved_entities:
            context.entities = []
            for ent in resolved_entities[:5]:
                if ent.id in self.graph:
                    attrs = self.graph.nodes[ent.id]
                    context.entities.append({
                        "id": ent.id,
                        "name": ent.name,
                        "type": ent.type,
                        "description": attrs.get("description") or attrs.get("abstract"),
                        "paper_count": attrs.get("paper_count", 1)
                    })

        markdown_ctx = context.to_markdown()
        retrieval_ctx = context.to_dict(user_query, plan.intent)

        return RetrievalResult(
            markdown_context=markdown_ctx,
            retrieval_context=retrieval_ctx,
            graph_context=context
        )
