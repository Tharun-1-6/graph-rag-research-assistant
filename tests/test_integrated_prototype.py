import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from query_processor.router import QueryOrchestrator
from ingestion.ingest import IngestionPipeline
from retrieval.retrieve import RetrievalPipeline
from graph.retriever import GraphRetriever

def main():
    base_dir = Path(__file__).resolve().parents[1]
    papers_dir = base_dir / "data" / "papers"
    graphs_dir = base_dir / "data" / "graphs"
    global_graph_path = graphs_dir / "global_graph.graphml"

    print("======================================================================")
    print("               TESTING INTEGRATED GRAPH RAG PIPELINE                  ")
    print("======================================================================")

    # 1. Initialize retrievers
    print("\nInitializing RAG search indices and loading Upgraded Knowledge Graph...")
    ingestion_pipeline = IngestionPipeline()
    rag_retriever = RetrievalPipeline()
    if not rag_retriever.index_exists():
        print("Vector database index not found. Running ingestion pipeline...")
        ingestion_pipeline.run()
        
    graph_retriever = GraphRetriever(global_graph_path)

    # 2. Initialize Query Orchestrator
    orchestrator = QueryOrchestrator(
        rag_retriever=rag_retriever,
        graph_rag_retriever=graph_retriever
    )

    # 3. Query
    query = "Who proposed DeBERTa?"
    print(f"\nQuerying: {query}")
    response = orchestrator.run(query)

    print(f"\nRoute Chosen : {response['route']}")
    print(f"Reasoning    : {response['reasoning']}")

    # Print trace details
    graph_result = response.get("graph_result")
    if graph_result and hasattr(graph_result, "retrieval_trace"):
        trace = graph_result.retrieval_trace
        print("\n--- ENTITY RESOLUTION ---")
        matched_seeds = trace.get("matched_seeds", {})
        for seed, score in matched_seeds.items():
            print(f"  * {seed}: confidence {score:.2f}")

        print("\n--- QUERY INTENT ---")
        print(f"Intent: {trace.get('detected_intent')}")
        
        print("\n--- TRAVERSAL METRICS ---")
        stats = trace.get("statistics", {})
        print(f"Visited Nodes  : {stats.get('nodes_visited')}")
        print(f"Retained Nodes : {stats.get('nodes_retained')}")
        print(f"Retained Edges : {stats.get('edges_retained')}")
        print(f"Latency        : {stats.get('traversal_latency_ms'):.2f} ms")

        print("\n--- JSON RETRIEVAL CONTEXT ---")
        import json
        print(json.dumps(graph_result.retrieval_trace, indent=4, ensure_ascii=False)[:600] + "\n...")

    print(f"\n====================== ANSWER ({orchestrator.llm_client.active_model}) ======================")
    print(response['answer'])
    print("====================================================")

if __name__ == "__main__":
    main()
