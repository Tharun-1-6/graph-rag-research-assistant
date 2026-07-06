"""
test_query_engine.py

Unit and integration tests for QueryEngine.
"""

from pathlib import Path
import networkx as nx

from graph.query_engine.query_engine import QueryEngine


def divider(title: str):
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)


def main():
    divider("RUNNING QUERY ENGINE TESTS")

    # Load graphml
    graphml_path = Path("data/graphs/attention.graphml")
    if not graphml_path.exists():
        print("⚠️ Graphml file not found. Creating mock graph.")
        graph = nx.MultiDiGraph()
        graph.add_node("transformer", type="Method", name="Transformer", description="A self-attention network")
        graph.add_node("self_attention", type="Method", name="Self-Attention", description="Dot-product alignment")
        graph.add_edge("transformer", "self_attention", relationship="USES", confidence=1.0)
    else:
        print(f"Loading graph from {graphml_path}...")
        graph = nx.read_graphml(graphml_path)

    # Ensure mock node is present for intent tests
    if "transformer" not in graph:
        graph.add_node("transformer", type="Method", name="Transformer", description="A self-attention network")

    engine = QueryEngine(graph)

    # 1. Test Query Pipeline Execution
    divider("TEST CASE 1: Query Execution & Context Builder")
    context = engine.query("Explain self-attention components inside the Transformer model.")
    
    print(f"Confidence score: {context.confidence}")
    print(f"Retrieved entities: {[e['name'] for e in context.entities]}")
    print(f"Retrieved reasoning paths count: {len(context.paths)}")
    print(f"Retrieved bibliography: {[p['title'] for p in context.papers]}")

    print("\n[Structured Markdown Output]")
    print("-" * 50)
    print(context.to_markdown())
    print("-" * 50)

    assert len(context.entities) > 0, "No entities populated in structured context!"
    print("✓ Passed!")
    divider("ALL QUERY ENGINE TESTS PASSED SUCCESSFUL")


if __name__ == "__main__":
    main()
