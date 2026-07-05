"""
test_performance.py

Benchmarks execution latencies, memory footprint, and network topologies.
"""

import time
import os
import sys
import logging
from pathlib import Path
import networkx as nx

from graph.graph_builder.graph_manager import GraphManager
from graph.retrieval.retriever import GraphRetriever

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_memory_usage_mb() -> float:
    """
    Returns current process resident memory usage in Megabytes.
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        # Fallback if psutil is not available
        return 0.0


def divider(title: str):
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)


def run_benchmarks():
    divider("RUNNING GRAPHRAG PERFORMANCE BENCHMARKS")

    # Use global graph if built, otherwise fallback to single attention graph
    graph_path = Path("data/graphs/global_graph.graphml")
    if not graph_path.exists():
        graph_path = Path("data/graphs/attention.graphml")
        print(f"⚠️ Global graph not found. Falling back to single paper graph: {graph_path}")

    if not graph_path.exists():
        print(f"❌ Error: No graph files found at {graph_path}. Please run build pipeline first.")
        sys.exit(1)

    print(f"Target Graph: {graph_path.resolve()}")

    # 1. Measure Loading Time
    start_time = time.perf_counter()
    initial_mem = get_memory_usage_mb()
    
    manager = GraphManager()
    manager.load_graph(graph_path)
    
    load_time = time.perf_counter() - start_time
    loaded_mem = get_memory_usage_mb()
    mem_overhead = loaded_mem - initial_mem if loaded_mem > 0 else 0.0

    print(f"✓ Graph Loading Time: {load_time * 1000.0:.2f} ms")
    print(f"✓ Resident Memory Usage: {loaded_mem:.2f} MB (Overhead: {mem_overhead:.2f} MB)")

    # 2. Structural Metrics
    divider("GRAPH TOPOLOGY METRICS")
    graph = manager.graph
    num_nodes = graph.number_of_nodes()
    num_edges = graph.number_of_edges()
    
    avg_degree = sum(dict(graph.degree()).values()) / max(1, num_nodes)
    
    undirected = graph.to_undirected()
    components = list(nx.connected_components(undirected)) if num_nodes > 0 else []
    num_components = len(components)
    
    if components:
        lcc = max(components, key=len)
        lcc_size = len(lcc)
    else:
        lcc = set()
        lcc_size = 0

    print(f"Total Nodes: {num_nodes}")
    print(f"Total Edges: {num_edges}")
    print(f"Average Node Degree: {avg_degree:.2f}")
    print(f"Number of Connected Components: {num_components}")
    print(f"Largest Connected Component (LCC) Size: {lcc_size} nodes ({lcc_size / max(1, num_nodes) * 100.0:.2f}%)")

    # 3. Measure Serialization (Save) Time
    divider("SERIALIZATION BENCHMARKS")
    temp_save_path = Path("data/graphs/perf_temp_graph.graphml")
    
    start_time = time.perf_counter()
    manager.save_graph(temp_save_path)
    save_time = time.perf_counter() - start_time
    
    # Cleanup temp file
    if temp_save_path.exists():
        temp_save_path.unlink()
        
    print(f"✓ GraphML Serialization Time: {save_time * 1000.0:.2f} ms")

    # 4. Measure Traversal and Retrieval Time
    divider("RETRIEVAL & NEIGHBORHOOD TRAVERSAL BENCHMARKS")
    retriever = GraphRetriever(graph_path)
    
    test_queries = [
        "Who proposed the Transformer architecture?",
        "Explain RoBERTa datasets.",
        "Compare BERT and DeBERTa methods.",
    ]

    for idx, query in enumerate(test_queries, 1):
        print(f"\nQuery {idx}: '{query}'")
        
        # Benchmark parser & retrieval orchestration
        start_time = time.perf_counter()
        result = retriever.retrieve(query)
        retrieve_time = time.perf_counter() - start_time
        
        # Extract traversal statistics from trace
        stats = result.statistics
        print(f"  - Retrieval Latency: {retrieve_time * 1000.0:.2f} ms")
        print(f"  - Traversal Depth used: {result.retrieval_plan.max_depth}")
        print(f"  - Nodes Visited: {stats.get('nodes_visited')}")
        print(f"  - Nodes Retained: {stats.get('nodes_retained')}")
        print(f"  - Edges Retained: {stats.get('edges_retained')}")
        print(f"  - Context Size (chars): {stats.get('context_size_chars')}")
        print(f"  - Path length average: {stats.get('avg_path_length')}")

    divider("PERFORMANCE BENCHMARKS COMPLETED")


if __name__ == "__main__":
    run_benchmarks()
