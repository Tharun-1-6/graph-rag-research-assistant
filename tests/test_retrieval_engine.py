"""
test_retrieval_engine.py

Comprehensive test suite verifying all 14 upgrades of the Graph Retrieval Engine.
"""

from pathlib import Path
import networkx as nx

from graph.retrieval.retriever import GraphRetriever


GRAPH_PATH = Path("data/graphs/attention.graphml")


def divider(title: str):
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)


def main():
    divider("PREPARING DATA & INJECTING DYNAMIC TEST SCENARIOS")
    if not GRAPH_PATH.exists():
        raise FileNotFoundError(
            f"Graph file not found at {GRAPH_PATH}. Please run test_graph_builder.py first."
        )

    print(f"Loading graph from {GRAPH_PATH}...")
    graph = nx.read_graphml(GRAPH_PATH)
    print(f"Original graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges.")

    # 1. Dynamically inject aliases for alias matching test (Upgrade 1)
    if "attention_is_all_you_need" in graph:
        graph.nodes["attention_is_all_you_need"]["aliases"] = "attention, transformer paper, base paper"
        print("-> Injected alias 'transformer paper' into 'attention_is_all_you_need'")

    # 2. Dynamically inject a disconnected component to verify Component Pruning (Upgrade 11)
    graph.add_node("disconnected_paper", type="Paper", title="An Unrelated Research Paper", year="2025")
    graph.add_node("disconnected_method", type="Method", name="Mock Algorithm X")
    graph.add_edge("disconnected_paper", "disconnected_method", relationship="PROPOSES")
    print("-> Injected disconnected graph component: 'disconnected_paper' --[PROPOSES]--> 'disconnected_method'")

    divider("INITIALIZING GRAPH RETRIEVER")
    retriever = GraphRetriever(graph)

    # 12 detailed query test cases representing all intents and conditions
    test_cases = [
        {
            "id": "1. EXACT MATCH & AUTHOR INTENT",
            "query": "Who wrote the Attention paper?",
            "expected_intent": "AUTHOR_QUERY",
            "check": lambda r: "ashish_vaswani" in [n["id"] for n in r.nodes]
        },
        {
            "id": "2. ALIAS MATCH TEST",
            "query": "Who wrote the transformer paper?",  # 'transformer paper' is an alias
            "expected_intent": "AUTHOR_QUERY",
            "check": lambda r: "attention_is_all_you_need" in [n["id"] for n in r.nodes]
        },
        {
            "id": "3. DISCONNECTED COMPONENT PRUNING",
            "query": "Who proposed the Transformer architecture? Also show Mock Algorithm X.",
            # 'Mock Algorithm X' matches disconnected component. Transformer matches main component.
            # Main component has higher score, so disconnected mock nodes should be pruned.
            "expected_intent": "METHOD_QUERY",
            "check": lambda r: "disconnected_method" not in [n["id"] for n in r.nodes]
        },
        {
            "id": "4. DATASET_QUERY",
            "query": "Which datasets did the paper evaluate on?",
            "expected_intent": "DATASET_QUERY",
            "check": lambda r: any("dataset" in n["type"].lower() for n in r.nodes)
        },
        {
            "id": "5. BENCHMARK_QUERY",
            "query": "What benchmarks are used?",
            "expected_intent": "BENCHMARK_QUERY",
            "check": lambda r: any("benchmark" in n["type"].lower() for n in r.nodes)
        },
        {
            "id": "6. INSTITUTION_QUERY",
            "query": "Where do the authors work?",
            "expected_intent": "INSTITUTION_QUERY",
            "check": lambda r: any("institution" in n["type"].lower() for n in r.nodes)
        },
        {
            "id": "7. EXPLANATION_QUERY (DEPTH 3)",
            "query": "Explain how the self-attention mechanism works.",
            "expected_intent": "EXPLANATION_QUERY",
            "check": lambda r: len(r.nodes) > 2
        },
        {
            "id": "8. COMPARISON_QUERY (DISCONNECTED ALLOWED)",
            "query": "Compare recurrent neural networks and Mock Algorithm X.",
            # In COMPARISON_QUERY, disconnected component mock node X should NOT be pruned.
            "expected_intent": "COMPARISON_QUERY",
            "check": lambda r: "disconnected_method" in [n["id"] for n in r.nodes]
        },
        {
            "id": "9. METRIC_QUERY",
            "query": "What are the scores and bleu metrics?",
            "expected_intent": "METRIC_QUERY",
            "check": lambda r: any("metric" in n["type"].lower() for n in r.nodes)
        },
        {
            "id": "10. TASK_QUERY",
            "query": "What machine learning tasks are performed?",
            "expected_intent": "TASK_QUERY",
            "check": lambda r: any("task" in n["type"].lower() for n in r.nodes)
        },
        {
            "id": "11. FUZZY TYPO SCENARIO",
            "query": "Who is Ashish Vaswni?",
            "expected_intent": "AUTHOR_QUERY",
            "check": lambda r: "ashish_vaswani" in [n["id"] for n in r.nodes]
        },
        {
            "id": "12. PLURAL STEMMING SCENARIO",
            "query": "Tell me about the translation tasks.",
            "expected_intent": "TASK_QUERY",
            "check": lambda r: any("task" in n["type"].lower() for n in r.nodes)
        }
    ]

    for case in test_cases:
        query_text = case["query"]
        divider(f"TESTING {case['id']}: '{query_text}'")

        # Run retrieval with evidence logs enabled
        result = retriever.retrieve(query_text, show_evidence=True)
        
        # Verify result outputs
        print(f"  Detected Intent: {result.query_intent} (Expected: {case['expected_intent']})")
        print(f"  Plan: seeds={result.retrieval_plan.seed_types}, allowed_relationships={result.retrieval_plan.allowed_relationships}, depth={result.retrieval_plan.max_depth}")
        print(f"  Evaluation Metrics: {result.statistics}")

        print("\n  [Formatted Context (Truncated Preview)]")
        print("  " + "-" * 50)
        lines = result.context.split("\n")
        preview = "\n  ".join(lines[:15])
        print(f"  {preview}")
        if len(lines) > 15:
            print("    ...")
        print("  " + "-" * 50)

        # Validations
        assert result.query_intent == case["expected_intent"], f"Incorrect intent detection. Found {result.query_intent}."
        assert len(result.nodes) > 0, "No nodes were retrieved."
        assert len(result.context) > 0, "Context string is empty."
        assert case["check"](result), "Check assertion failed for this query pathway."
        print(f"✅ {case['id']} Passed!")

    # Verify Budget Constraints (Upgrade 10 & 14)
    divider("TESTING UPGRADE 10: CONTEXT BUDGET CONSTRAINTS")
    budget_query = "Explain self-attention, Transformer, and LSTM architectures."
    
    budget_result = retriever.retrieve(
        budget_query,
        top_k=4,            # max 4 nodes
        max_edges=2,         # max 2 relationships
        max_characters=250   # short character budget
    )
    
    print(f"Budget test query: '{budget_query}'")
    print(f"Budget test statistics: {budget_result.statistics}")
    print("\n[Budget Formatted Context]")
    print("-" * 50)
    print(budget_result.context)
    print("-" * 50)

    # Validations for budgets
    assert len(budget_result.nodes) <= 4, "Exceeded max_nodes budget."
    assert len(budget_result.edges) <= 2, "Exceeded max_edges budget."
    assert len(budget_result.context) <= 250, "Exceeded max_characters budget."
    assert not budget_result.context.endswith("-->"), "Context was cut in half at relationship arrow."
    print("✅ Budget Constraints Verification Passed!")

    divider("ALL 14 RETRIEVAL UPGRADES COMPLETED & PASSED INTEGRATION BENCHMARKS")


if __name__ == "__main__":
    main()
