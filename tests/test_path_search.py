"""
test_path_search.py

Unit tests for PathSearcher path discovery algorithms.
"""

from pathlib import Path
import networkx as nx

from graph.query_engine.path_search import PathSearcher, ReasoningPath


def divider(title: str):
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)


def main():
    divider("RUNNING PATH SEARCH ENGINE TESTS")

    # Load graphml
    graphml_path = Path("data/graphs/attention.graphml")
    if not graphml_path.exists():
        print("⚠️ Graphml file not found. Creating mock graph.")
        graph = nx.MultiDiGraph()
        graph.add_node("transformer", type="Method", name="Transformer")
        graph.add_node("self_attention", type="Method", name="Self-Attention")
        graph.add_edge("transformer", "self_attention", relationship="USES", confidence=1.0)
        graph.add_node("attention_mechanism", type="Method", name="Attention Mechanism")
        graph.add_edge("attention_mechanism", "self_attention", relationship="RELATED_TO", confidence=0.8)
    else:
        print(f"Loading graph from {graphml_path}...")
        graph = nx.read_graphml(graphml_path)

    searcher = PathSearcher(graph)

    # 1. Test Seed-to-Seed Path Discovery (multi-hop)
    divider("TEST CASE 1: Paths Between Seeds")
    seeds = ["transformer", "self_attention"]
    paths = searcher.find_paths_between_seeds(seeds, max_depth=2)
    
    print(f"Found {len(paths)} paths between {seeds}:")
    for p in paths:
        print(f"  - Path: {p.nodes} | {p.to_string(graph)}")

    assert len(paths) > 0, "No paths found between seeds!"
    print("✓ Passed!")

    # 2. Test Bounded Neighborhood Expansion
    divider("TEST CASE 2: Bounded Neighborhood BFS Expansion")
    seeds2 = ["transformer"]
    paths2 = searcher.expand_neighborhood_paths(seeds2, max_depth=2)
    
    print(f"Neighborhood expansion paths from {seeds2} (first 5):")
    for p in paths2[:5]:
        print(f"  - Path: {p.nodes} | {p.to_string(graph)}")

    assert len(paths2) > 0, "No neighborhood expansion paths found!"
    print("✓ Passed!")

    # 3. Test Relationship Type Constrained Traversal
    divider("TEST CASE 3: Path Search with Relationship Filters")
    # Only allow AUTHORED relationship
    paths3 = searcher.expand_neighborhood_paths(["transformer"], max_depth=2, allowed_relationships=["AUTHORED"])
    print(f"Neighborhood expansion paths with allowed_relationships=['AUTHORED']: {len(paths3)}")
    # Since transformer proposes self_attention, etc. (uses / proposes), AUTHORED paths should be 0 or small
    # Check that none of the retrieved paths have USES
    for p in paths3:
        for e in p.edges:
            assert e.get("relationship") == "AUTHORED", "Constraint violation: allowed relationship exceeded!"

    print("✓ Passed!")
    divider("ALL PATH SEARCH ENGINE TESTS PASSED SUCCESSFUL")


if __name__ == "__main__":
    main()
