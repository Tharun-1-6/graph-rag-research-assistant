"""
main.py

Main interactive CLI executable for the Graph Retrieval Engine.
Orchestrates the retrieval pipeline from entity resolution to path traversal
and structured context formatting, stopping immediately after retrieval.
"""

import os
from pathlib import Path
import re
import sys
import time
from typing import Dict, Any, List

# Ensure project root is in path
sys.path.append(str(Path(__file__).parent))

from graph.graph_builder.graph_manager import GraphManager
from graph.query_engine.entity_resolver import EntityResolver
from graph.query_engine.planner import QueryPlanner
from graph.query_engine.query_engine import QueryEngine
from graph.statistics import generate_graph_statistics

# Configuration
GRAPH_PATH = Path("data/graphs/global_graph.graphml")


def safe_print(*args, sep=" ", end="\n"):
    """
    Gracefully prints text, replacing non-encodable characters to prevent console crashes.
    """
    text = sep.join(str(arg) for arg in args)
    try:
        sys.stdout.write(text + end)
        sys.stdout.flush()
    except UnicodeEncodeError:
        enc = sys.stdout.encoding or "ascii"
        safe_text = text.encode(enc, errors="replace").decode(enc)
        sys.stdout.write(safe_text + end)
        sys.stdout.flush()


def divider(title: str = "", char: str = "="):
    if title:
        safe_print(f"\n{char * 50}\n{title}\n{char * 50}")
    else:
        safe_print(char * 50)


def print_stats(graph):
    """
    Extracts and prints the current statistics profile of the loaded graph.
    """
    try:
        stats = generate_graph_statistics(graph)
        summary = stats.get("summary", {})

        safe_print("Graph Loaded Successfully\n")
        safe_print(f"Nodes: {summary.get('total_nodes', 0)}")
        safe_print(f"Edges: {summary.get('total_edges', 0)}")
        safe_print(f"Paper Count: {summary.get('number_of_papers', 0)}")
    except Exception as e:
        safe_print(f"[WARNING] Error computing statistics: {e}")


def display_help():
    safe_print("\nAvailable Commands:")
    safe_print("  graph stats       - Show statistics of the loaded graph")
    safe_print("  show papers       - List all papers currently indexed in the knowledge base")
    safe_print("  show authors      - List all authors in the graph")
    safe_print("  help              - Display this command reference list")
    safe_print("  exit / quit       - Terminate the session\n")


def display_papers(graph):
    papers = []
    for nid, attrs in graph.nodes(data=True):
        if attrs.get("type") == "Paper":
            papers.append(attrs.get("title") or nid)
    
    safe_print(f"\nIndexed Papers ({len(papers)}):")
    for i, p in enumerate(sorted(papers), 1):
        safe_print(f"  {i}. {p}")
    safe_print()


def display_authors(graph):
    authors = []
    for nid, attrs in graph.nodes(data=True):
        if attrs.get("type") == "Author":
            authors.append(attrs.get("name") or nid)
    
    safe_print(f"\nIndexed Authors ({len(authors)}):")
    for i, a in enumerate(sorted(authors), 1):
        safe_print(f"  {i}. {a}")
    safe_print()


def main():
    # 1. Load Graph
    if not GRAPH_PATH.exists():
        safe_print(f"[ERROR] Graph file not found at {GRAPH_PATH}.")
        safe_print("Please build the global graph first by running 'tests/test_multi_paper_graph.py'.")
        sys.exit(1)

    try:
        manager = GraphManager()
        manager.load_graph(GRAPH_PATH)
    except Exception as e:
        safe_print(f"[ERROR] Error loading graph file: {e}")
        sys.exit(1)

    print_stats(manager.graph)

    # 2. Initialize Components once
    resolver = EntityResolver(manager.graph)
    planner = QueryPlanner()
    engine = QueryEngine(manager.graph)

    divider("Graph Retrieval Engine")

    # 3. Interactive Loop
    while True:
        try:
            query = input("> ").strip()
            
            if not query:
                continue

            q_lower = query.lower()
            if q_lower in ["exit", "quit"]:
                safe_print("Goodbye!")
                break
            
            # Helper commands
            if q_lower == "help":
                display_help()
                continue
            elif q_lower == "graph stats":
                print_stats(manager.graph)
                continue
            elif q_lower == "show papers":
                display_papers(manager.graph)
                continue
            elif q_lower == "show authors":
                display_authors(manager.graph)
                continue

            # Process Query
            run_query_pipeline(query, resolver, planner, engine, manager.graph)

        except KeyboardInterrupt:
            safe_print("\nGoodbye!")
            break
        except Exception as e:
            safe_print(f"[WARNING] Unexpected session error: {e}")


def run_query_pipeline(query: str, resolver: EntityResolver, planner: QueryPlanner, engine: QueryEngine, graph):
    """
    Executes the Graph Retrieval pipeline.
    """
    timers = {}
    
    # USER QUERY
    divider("USER QUERY")
    safe_print(query)

    # ENTITY RESOLUTION
    t_start = time.perf_counter()
    STOP_WORDS = {
        "explain", "describe", "compare", "contrast", "what", "where", "how", "who", "why", 
        "the", "and", "a", "an", "of", "to", "in", "is", "for", "with", "on", "at", "by", 
        "from", "as", "about", "this", "that", "these", "those", "their", "its", "it"
    }
    clean_words = [w for w in re.findall(r"\b\w{3,}\b", query.lower()) if w not in STOP_WORDS]
    resolved_entities = resolver.resolve_many(clean_words)
    timers["Entity Resolution"] = (time.perf_counter() - t_start) * 1000

    divider("ENTITY RESOLUTION")
    safe_print("Resolved Entities:")
    if not resolved_entities:
        safe_print("  None")
    for ent in resolved_entities[:5]:
        safe_print(f"  * {ent.name} (id: {ent.id}, type: {ent.type}, confidence: {ent.confidence:.2f}, matched_by: {ent.matched_by})")

    # QUERY INTENT
    t_start = time.perf_counter()
    plan = planner.plan(query)
    timers["Planning"] = (time.perf_counter() - t_start) * 1000

    divider("QUERY INTENT")
    safe_print(f"Intent: {plan.intent}")
    safe_print(f"Allowed Relationships: {plan.allowed_relationships or 'All'}")
    safe_print(f"Traversal Depth: {plan.max_depth} hops")
    safe_print(f"Node Budget: {plan.max_nodes}")

    # TRAVERSAL & PATH RANKING
    t_start = time.perf_counter()
    seed_ids = []
    resolved_map = {}
    for ent in resolved_entities:
        if not plan.seed_types or ent.type in plan.seed_types:
            seed_ids.append(ent.id)
            resolved_map[ent.id] = ent.confidence
    if not seed_ids:
        seed_ids = [ent.id for ent in resolved_entities]
        resolved_map = {ent.id: ent.confidence for ent in resolved_entities}
    
    seed_ids = seed_ids[:8]  # cap seed size

    raw_paths = engine.searcher.find_all_paths(
        seeds=seed_ids,
        max_depth=plan.max_depth,
        allowed_relationships=plan.allowed_relationships
    )
    t_retrieve = (time.perf_counter() - t_start) * 1000
    timers["Retrieval"] = t_retrieve

    t_start = time.perf_counter()
    ranked_paths = engine.ranker.rank(raw_paths, resolved_map, max_paths=plan.max_paths)
    t_rank = (time.perf_counter() - t_start) * 1000
    timers["Ranking"] = t_rank

    divider("TRAVERSAL")
    safe_print(f"Seed Nodes: {', '.join(seed_ids) if seed_ids else 'None'}")
    
    visited_nodes = set(n for p in raw_paths for n in p.nodes)
    visited_edges_cnt = sum(len(p.edges) for p in raw_paths)
    
    safe_print(f"Visited Nodes: {len(visited_nodes)}")
    safe_print(f"Visited Edges: {visited_edges_cnt}")
    
    safe_print("\nTop Ranked Paths:")
    if not ranked_paths:
        safe_print("  No paths discovered.")
    for i, path in enumerate(ranked_paths[:5], 1):
        safe_print(f"  {i}. {path.path_str} [score: {path.score:.2f}]")

    # GRAPH CONTEXT
    context = engine.context_builder.build(ranked_paths)
    
    # Fallback to direct seed attributes if no paths found
    if not context.paths and resolved_entities:
        for ent in resolved_entities[:5]:
            if ent.id in graph:
                attrs = graph.nodes[ent.id]
                context.entities.append({
                    "id": ent.id,
                    "name": ent.name,
                    "type": ent.type,
                    "description": attrs.get("description") or attrs.get("abstract"),
                    "paper_count": attrs.get("paper_count", 1)
                })

    divider("GRAPH CONTEXT")
    context_markdown = context.to_markdown()
    safe_print(context_markdown)

    # Retrieval Metrics at bottom of context
    retrieved_nodes_cnt = len(context.entities) + len(context.papers)
    retrieved_edges_cnt = len(context.relationships)
    traversal_time_total = t_retrieve + t_rank
    
    safe_print("-" * 50)
    safe_print(f"Nodes Retrieved: {retrieved_nodes_cnt}")
    safe_print(f"Edges Retrieved: {retrieved_edges_cnt}")
    safe_print(f"Traversal Time: {traversal_time_total:.2f} ms")
    safe_print(f"Context Length: {len(context_markdown)} characters")
    safe_print(f"Retrieval Confidence: {context.confidence:.2f}")

    divider("END")
    
    import json
    divider("JSON RETRIEVAL CONTEXT")
    retrieval_context = context.to_dict(query, plan.intent)
    safe_print(json.dumps(retrieval_context, indent=4, ensure_ascii=False))
    divider()
    safe_print()


if __name__ == "__main__":
    main()
