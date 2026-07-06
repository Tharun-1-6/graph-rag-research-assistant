"""
test_entity_resolution.py

Unit and integration tests for EntityResolver and QueryPlanner.
"""

from pathlib import Path
import networkx as nx

from graph.query_engine.entity_resolver import EntityResolver
from graph.query_engine.planner import QueryPlanner


def divider(title: str):
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)


def main():
    divider("RUNNING ENTITY RESOLUTION AND PLANNER TESTS")

    # Load default test graphml file
    graphml_path = Path("data/graphs/attention.graphml")
    if not graphml_path.exists():
        # Fallback to creating a tiny mock graph
        print("⚠️ Graphml file not found. Creating mock graph.")
        graph = nx.MultiDiGraph()
    else:
        print(f"Loading graph from {graphml_path}...")
        graph = nx.read_graphml(graphml_path)

    # Ensure mock nodes are present for testing resolver capabilities
    if "ashish_vaswani" not in graph:
        graph.add_node("ashish_vaswani", type="Author", name="Ashish Vaswani")
    if "next_sentence_prediction_nsp" not in graph:
        graph.add_node("next_sentence_prediction_nsp", type="Method", name="Next Sentence Prediction")

    resolver = EntityResolver(graph)
    planner = QueryPlanner()

    # 1. Test Exact Match
    divider("TEST CASE 1: Exact Match Resolution")
    res1 = resolver.resolve("Vaswani")
    print("Resolved 'Vaswani':", res1)
    # Check if ashish_vaswani is present in match list
    resolved_ids = [r.id for r in res1]
    print("Found resolved IDs:", resolved_ids)
    assert any("vaswani" in rid for rid in resolved_ids), "Exact match resolution failed!"
    print("✓ Passed!")

    # 2. Test Acronym Match
    divider("TEST CASE 2: Acronym Match Resolution")
    res2 = resolver.resolve("NSP")
    print("Resolved 'NSP':", res2)
    resolved_ids2 = [r.id for r in res2]
    print("Found resolved IDs:", resolved_ids2)
    assert any("nsp" in rid for rid in resolved_ids2), "Acronym resolution failed!"
    print("✓ Passed!")

    # 3. Test Typo Tolerance Match
    divider("TEST CASE 3: Typo Tolerance Match Resolution")
    res3 = resolver.resolve("Ashish Vaswni")
    print("Resolved 'Ashish Vaswni':", res3)
    resolved_ids3 = [r.id for r in res3]
    print("Found resolved IDs:", resolved_ids3)
    assert any("vaswani" in rid for rid in resolved_ids3), "Typo tolerant resolution failed!"
    print("✓ Passed!")

    # 4. Test Multi-Term Resolution
    divider("TEST CASE 4: Multi-Term Resolution")
    res4 = resolver.resolve_many(["Vaswani", "NSP", "attention"])
    print("Resolved multiple terms:", [(r.id, r.confidence, r.matched_by) for r in res4])
    assert len(res4) >= 2, "Multi-term resolution failed!"
    print("✓ Passed!")

    # 5. Test Query Planning Intent Detection
    divider("TEST CASE 5: Query Planner Intent Classification")
    queries = [
        ("Who wrote the Attention paper?", QueryPlanner.AUTHOR_QUERY),
        ("Where does Ashish Vaswani work?", QueryPlanner.INSTITUTION_QUERY),
        ("Compare BERT and GPT models.", QueryPlanner.COMPARISON_QUERY),
        ("Explain dynamic masking technique.", QueryPlanner.EXPLANATION_QUERY),
        ("What datasets are used for evaluation?", QueryPlanner.DATASET_QUERY),
    ]

    for q, expected in queries:
        plan = planner.plan(q)
        print(f"Query: '{q}' -> Intent: '{plan.intent}' (Expected: '{expected}')")
        assert plan.intent == expected, f"Intent mismatch! Expected {expected}, got {plan.intent}"

    print("✓ Passed!")
    divider("ALL RESOLUTION AND PLANNING TESTS PASSED SUCCESSFUL")


if __name__ == "__main__":
    main()
