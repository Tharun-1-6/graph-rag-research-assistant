"""
test_path_ranking.py

Unit tests for PathRanker path scoring and ranking logic.
"""

from pathlib import Path
import networkx as nx

from graph.query_engine.path_search import PathSearcher
from graph.query_engine.path_ranker import PathRanker


def divider(title: str):
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)


def main():
    divider("RUNNING PATH RANKER TESTS")

    # Load graphml
    graphml_path = Path("data/graphs/attention.graphml")
    if not graphml_path.exists():
        print("⚠️ Graphml file not found. Creating mock graph.")
        graph = nx.MultiDiGraph()
        graph.add_node("transformer", type="Method", name="Transformer")
        graph.add_node("self_attention", type="Method", name="Self-Attention")
        graph.add_edge("transformer", "self_attention", relationship="USES", confidence=1.0)
    else:
        print(f"Loading graph from {graphml_path}...")
        graph = nx.read_graphml(graphml_path)

    searcher = PathSearcher(graph)
    ranker = PathRanker(graph)

    # 1. Search paths
    seeds = ["transformer", "self_attention"]
    raw_paths = searcher.find_all_paths(seeds, max_depth=2)
    print(f"Discovered {len(raw_paths)} raw paths.")

    # 2. Define matched node confidences
    resolved_conf = {
        "transformer": 1.0,
        "self_attention": 0.95
    }

    # 3. Rank paths
    divider("TEST CASE 1: Path Scoring & Ranking")
    ranked = ranker.rank(raw_paths, resolved_conf, max_paths=5)
    
    print(f"Top {len(ranked)} Ranked Paths:")
    for i, p in enumerate(ranked, 1):
        print(f"  {i}. [Score: {p.score:.4f} | Reason: {p.reason}]")
        print(f"     Path: {p.path_str}")
        print(f"     Nodes: {p.nodes}")
        assert 0.0 <= p.score <= 1.0, "Score not normalized between 0.0 and 1.0!"

    # Assert descending order
    for idx in range(len(ranked) - 1):
        assert ranked[idx].score >= ranked[idx + 1].score, "Paths not sorted descending by score!"

    assert len(ranked) > 0, "No ranked paths returned!"
    print("✓ Passed!")
    divider("ALL PATH RANKER TESTS PASSED SUCCESSFUL")


if __name__ == "__main__":
    main()
