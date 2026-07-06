import os
import re
import sys
import concurrent.futures
from pathlib import Path
import networkx as nx
from typing import List, Dict, Any

from graph.ingestion.loader import PDFLoader
from graph.ingestion.cleaner import TextCleaner
from graph.extraction.extractor import GraphExtractor
from graph.graph_builder.builder import GraphBuilder
from graph.graph_builder.serializer import GraphSerializer
from query_processor.router import QueryOrchestrator

from ingestion.ingest import IngestionPipeline
from retrieval.retrieve import RetrievalPipeline





def process_all_papers_to_graphs(papers_dir: Path, graphs_dir: Path):
    """
    Runs loading, cleaning, extraction, and graph building pipelines
    for all PDFs that do not have matching graphs yet.
    """
    loader = PDFLoader()
    cleaner = TextCleaner()
    extractor = GraphExtractor()
    builder = GraphBuilder()
    serializer = GraphSerializer(graphs_dir)
    
    pdf_files = list(papers_dir.glob("*.pdf"))
    for pdf_path in pdf_files:
        filename_stem = pdf_path.stem
        json_path = graphs_dir / f"{filename_stem}.json"
        
        if json_path.exists():
            print(f"Graph for '{pdf_path.name}' already exists. Skipping extraction.")
            continue
            
        print(f"\n--- Extracting and Building Graph for: {pdf_path.name} ---")
        try:
            doc = loader.load(pdf_path)
            doc = cleaner.clean(doc)
            print("Extracted text. Initiating LLM entity extraction...")
            extraction = extractor.extract(doc)
            print(f"Extracted {extraction.num_entities} entities and {extraction.num_relationships} relationships.")
            
            graph = builder.build(extraction)
            serializer.save_json(graph, f"{filename_stem}.json")
            serializer.save_graphml(graph, f"{filename_stem}.graphml")
            print(f"Graph saved to {json_path.name}")
        except Exception as e:
            print(f"Failed to process {pdf_path.name}: {e}")


def main():
    # Setup paths
    base_dir = Path(__file__).resolve().parent
    papers_dir = base_dir / "data" / "papers"
    graphs_dir = base_dir / "data" / "graphs"
    
    # Process papers on start if requested
    print("======================================================================")
    print("                 GRAPHRAG SYSTEM PROTOTYPE RUNNER                     ")
    print("======================================================================")
    
    choice = input("Do you want to process any new PDFs in data/papers? (y/n): ").strip().lower()
    if choice == 'y':
        process_all_papers_to_graphs(papers_dir, graphs_dir)
        
    # Initialize retrievers
    print("\nInitializing RAG search indices and loading Knowledge Graph...")
    
    # Ingest documents if index is empty
    ingestion_pipeline = IngestionPipeline()
    rag_retriever = RetrievalPipeline()
    if not rag_retriever.index_exists():
        print("Vector database index not found. Running ingestion pipeline...")
        ingestion_pipeline.run()
    
    # Load the real GraphRetriever
    global_graph_path = graphs_dir / "global_graph.graphml"
    if not global_graph_path.exists():
        global_graph_path = graphs_dir
        
    from graph.retriever import GraphRetriever
    graph_retriever = GraphRetriever(global_graph_path)
    
    # Initialize Query Orchestrator
    orchestrator = QueryOrchestrator(
        rag_retriever=rag_retriever,
        graph_rag_retriever=graph_retriever
    )
    
    print("\nPrototype is ready! Type 'exit' to quit.")
    while True:
        try:
            print("\n" + "="*80)
            query = input("Ask a question: ").strip()
            if not query:
                continue
            if query.lower() in ["exit", "quit"]:
                break
                
            print("\nProcessing routing and retrieval...")
            response = orchestrator.run(query)
            
            print(f"\nRoute Chosen : {response['route']}")
            print(f"Reasoning    : {response['reasoning']}")
            
            if response['route'] in ["RAG", "COMBINED"]:
                print(f"\n--- RAG Retrieval Context (Snippets) ---")
                print(response['rag_context'][:500] + ("..." if len(response['rag_context']) > 500 else ""))
                
            if response['route'] in ["GRAPH_RAG", "COMBINED"]:
                print(f"\n--- Graph Retrieval Context (Entities & Edges) ---")
                print(response['graph_context'][:500] + ("..." if len(response['graph_context']) > 500 else ""))
                
                # Check if we have the real GraphRetriever's result object
                graph_result = response.get("graph_result")
                if graph_result and hasattr(graph_result, "retrieval_trace"):
                    trace = graph_result.retrieval_trace
                    
                    # Print Entity Resolution (matched seeds)
                    print("\n--- ENTITY RESOLUTION ---")
                    print("Resolved Entities / Seeds:")
                    matched_seeds = trace.get("matched_seeds", {})
                    if not matched_seeds:
                        print("  None")
                    else:
                        for seed, score in matched_seeds.items():
                            node_type = graph_result.subgraph.nodes[seed].get("type", "Entity") if graph_result.subgraph and seed in graph_result.subgraph else "Entity"
                            print(f"  * {seed} (type: {node_type}, confidence: {score:.2f})")
                            
                    # Print Query Intent
                    print("\n--- QUERY INTENT ---")
                    print(f"Intent: {trace.get('detected_intent', 'Unknown')}")
                    plan = trace.get("retrieval_plan", {})
                    print(f"Allowed Relationships: {plan.get('allowed_relationships') or 'All'}")
                    print(f"Traversal Depth: {plan.get('max_depth')} hops")
                    
                    # Print Traversal details
                    print("\n--- TRAVERSAL ---")
                    stats = trace.get("statistics", {})
                    print(f"Visited Nodes: {stats.get('nodes_visited', 0)}")
                    print(f"Retained Nodes: {stats.get('nodes_retained', 0)}")
                    print(f"Retained Edges: {stats.get('edges_retained', 0)}")
                    print(f"Traversal Latency: {stats.get('traversal_latency_ms', 0.0):.2f} ms")
                    
                    # Print Top Ranked Paths
                    print("\nTop Ranked Nodes:")
                    ranked = trace.get("ranked_nodes", [])
                    if not ranked:
                        print("  No paths discovered.")
                    else:
                        for idx, (node_id, score) in enumerate(ranked[:5], 1):
                            print(f"  {idx}. {node_id} [score: {score:.2f}]")
                            
                    # Print JSON Retrieval Context
                    print("\n--- JSON RETRIEVAL CONTEXT ---")
                    import json
                    if hasattr(graph_result, "retrieval_context"):
                        print(json.dumps(graph_result.retrieval_context, indent=4, ensure_ascii=False))
                    else:
                        print(json.dumps(trace, indent=4, ensure_ascii=False))
                    print("-" * 50)
                
            print(f"\n====================== ANSWER ({orchestrator.llm_client.active_model}) ======================")
            print(response['answer'])
            print("====================================================")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\nAn error occurred during query execution: {e}")
            
    print("\nExiting prototype. Goodbye!")

if __name__ == "__main__":
    main()
