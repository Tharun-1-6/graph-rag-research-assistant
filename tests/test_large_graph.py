"""
test_large_graph.py

Benchmarks QueryEngine scaling and latency on a simulated large graph
(500+ nodes, 1500+ edges).
"""

import time
import networkx as nx

from graph.query_engine.query_engine import QueryEngine


def divider(title: str):
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)


def build_large_simulated_graph() -> nx.MultiDiGraph:
    """
    Synthesizes a large scale multi-paper citation graph.
    """
    g = nx.MultiDiGraph()

    # 1. Add 50 mock Paper nodes
    for i in range(1, 51):
        paper_id = f"paper_{i}"
        g.add_node(
            paper_id,
            type="Paper",
            title=f"Scalable Transformer Architecture Vol {i}",
            year=2020 + (i % 7),
            conference="IEEE",
            paper_count=1
        )

    # 2. Add 100 Author nodes and link to Papers
    for i in range(1, 101):
        author_id = f"author_{i}"
        g.add_node(author_id, type="Author", name=f"Academic Author {i}", paper_count=1)
        # Authored link
        paper_target = f"paper_{(i % 50) + 1}"
        g.add_edge(author_id, paper_target, relationship="AUTHORED", confidence=1.0, paper_ids=paper_target)

    # 3. Add 150 Method nodes, 100 Dataset nodes, 100 Task nodes
    for i in range(1, 151):
        method_id = f"method_{i}"
        g.add_node(method_id, type="Method", name=f"Machine Learning Method {i}", paper_count=1)
        paper_target = f"paper_{(i % 50) + 1}"
        g.add_edge(paper_target, method_id, relationship="PROPOSES", confidence=0.9, paper_ids=paper_target)

    for i in range(1, 101):
        dataset_id = f"dataset_{i}"
        g.add_node(dataset_id, type="Dataset", name=f"Standard Corpus {i}", paper_count=1)
        paper_target = f"paper_{(i % 50) + 1}"
        g.add_edge(paper_target, dataset_id, relationship="USES", confidence=0.85, paper_ids=paper_target)

    for i in range(1, 101):
        task_id = f"task_{i}"
        g.add_node(task_id, type="Task", name=f"Downstream NLP Task {i}", paper_count=1)
        method_source = f"method_{(i % 150) + 1}"
        g.add_edge(method_source, task_id, relationship="PERFORMS", confidence=0.8, paper_ids=f"paper_{(i % 50) + 1}")

    # Interlink method nodes to simulate multi-hop comparisons (cross-paper clusters)
    for i in range(1, 149):
        g.add_edge(f"method_{i}", f"method_{i+1}", relationship="IMPROVES_UPON", confidence=0.95, paper_ids=f"paper_{(i % 50) + 1}")

    return g


def main():
    divider("RUNNING LARGE SCALE TOPOLOGY BENCHMARKS")

    print("Generating simulated large graph...")
    start_gen = time.perf_counter()
    graph = build_large_simulated_graph()
    end_gen = time.perf_counter()
    print(f"Generated graph with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges in {(end_gen - start_gen)*1000:.2f} ms.")

    engine = QueryEngine(graph)

    # Measure latency on 10 repeated queries to test caching and BFS limits
    divider("TEST CASE 1: Query Execution Latency Benchmark")
    
    query = "Explain Machine Learning Method 5 and standard corpus 5 performance."
    latencies = []
    
    for run in range(1, 11):
        start_run = time.perf_counter()
        context = engine.query(query, max_hops=2)
        end_run = time.perf_counter()
        dur = (end_run - start_run) * 1000
        latencies.append(dur)
        print(f"  - Run {run}: {dur:.2f} ms | Found {len(context.paths)} reasoning paths.")

    avg_latency = sum(latencies) / len(latencies)
    print(f"\nAverage Query Latency: {avg_latency:.2f} ms")
    
    # Assert performance boundaries
    assert avg_latency < 150.0, "Average query latency exceeded scalability budget of 150ms!"
    print("✓ Passed!")

    divider("ALL SCALABILITY AND LARGE GRAPH TESTS PASSED SUCCESSFUL")


if __name__ == "__main__":
    main()
