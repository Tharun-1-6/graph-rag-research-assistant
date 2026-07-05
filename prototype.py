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


class SimpleRAGRetriever:
    """
    Simple keyword/phrase relevance retriever over sliding text chunks of PDF papers.
    """
    def __init__(self, papers_dir: Path):
        self.papers_dir = papers_dir
        self.chunks = []
        self.loader = PDFLoader()
        self.cleaner = TextCleaner()
        self._load_and_chunk_papers()

    def _load_and_chunk_papers(self):
        pdf_files = list(self.papers_dir.glob("*.pdf"))
        print(f"Indexing RAG text chunks from {len(pdf_files)} PDF papers...")
        for pdf_path in pdf_files:
            try:
                doc = self.loader.load(pdf_path)
                doc = self.cleaner.clean(doc)
                text = doc.text
                
                # Split text into paragraphs
                paragraphs = re.split(r'\n\s*\n', text)
                for idx, para in enumerate(paragraphs):
                    para = para.strip()
                    # Keep reasonably sized paragraphs
                    if len(para) > 80:
                        self.chunks.append({
                            "paper_title": doc.metadata.get("title", doc.filename),
                            "chunk_id": idx,
                            "text": para
                        })
            except Exception as e:
                print(f"Warning: Failed to index text for {pdf_path.name}: {e}")

    def __call__(self, query: str) -> str:
        # Rank chunks by simple word match overlap
        query_words = [w.lower() for w in re.findall(r'\w+', query) if len(w) > 2]
        if not query_words:
            return "No valid search keywords in query."
            
        scored_chunks = []
        for chunk in self.chunks:
            score = 0
            text_lower = chunk["text"].lower()
            for word in query_words:
                if word in text_lower:
                    # Direct occurrence score
                    score += text_lower.count(word)
            if score > 0:
                scored_chunks.append((score, chunk))
                
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_chunks = scored_chunks[:4]  # Retrieve top 4 chunks
        
        if not top_chunks:
            return "No matching text snippets found in the documents."
            
        context_parts = []
        for score, chunk in top_chunks:
            context_parts.append(
                f"Source: {chunk['paper_title']} (Paragraph {chunk['chunk_id']})\n"
                f"Content: {chunk['text']}"
            )
        return "\n\n---\n\n".join(context_parts)


class SimpleGraphRetriever:
    """
    Loads serialized NetworkX graphs and retrieves entity subgraphs/edges
    based on entity mentions found in the user query.
    """
    def __init__(self, graphs_dir: Path):
        self.graphs_dir = graphs_dir
        self.graph = nx.MultiDiGraph()
        self._load_graphs()

    def _load_graphs(self):
        json_files = list(self.graphs_dir.glob("*.json"))
        print(f"Loading knowledge graphs from {len(json_files)} files...")
        for json_path in json_files:
            try:
                g = GraphSerializer.load(json_path)
                self.graph = nx.compose(self.graph, g)
            except Exception as e:
                print(f"Warning: Failed to load graph {json_path.name}: {e}")
        print(f"Combined graph holds {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges.")

    def __call__(self, query: str) -> str:
        query_lower = query.lower()
        matched_nodes = []
        
        # Match nodes whose name or ID appears in the user query
        for node, data in self.graph.nodes(data=True):
            node_name = data.get("name", "").lower() or str(node).lower()
            if node_name and (node_name in query_lower or str(node).lower() in query_lower):
                matched_nodes.append((node, data))
                
        # Fallback: if no specific node name matches, check if query asks for a broad type of nodes
        if not matched_nodes:
            type_keywords = {
                "method": "Method",
                "methods": "Method",
                "author": "Author",
                "authors": "Author",
                "dataset": "Dataset",
                "datasets": "Dataset",
                "institution": "Institution",
                "institutions": "Institution",
                "architecture": "Architecture",
                "architectures": "Architecture",
                "benchmark": "Benchmark",
                "benchmarks": "Benchmark",
                "metric": "Metric",
                "metrics": "Metric",
                "task": "Task",
                "tasks": "Task",
                "paper": "Paper",
                "papers": "Paper"
            }
            matched_types = set()
            # Split query into words to check matching keywords
            query_words = re.findall(r'\w+', query_lower)
            for word in query_words:
                if word in type_keywords:
                    matched_types.add(type_keywords[word])
            
            if matched_types:
                for node, data in self.graph.nodes(data=True):
                    if data.get("type") in matched_types:
                        matched_nodes.append((node, data))
                        
        if not matched_nodes:
            return "No matching entities found in the Knowledge Graph."
            
        context_parts = []
        for node, data in matched_nodes:
            node_type = data.get("type", "Entity")
            name = data.get("name", str(node))
            desc = data.get("description", "No description available")
            
            context_parts.append(f"\nEntity: {name} ({node_type})\nDescription: {desc}")
            
            # Fetch incoming/outgoing relations
            connections = []
            for u, v, attr in self.graph.in_edges(node, data=True):
                rel = attr.get("relationship", "CONNECTED_TO")
                u_name = self.graph.nodes[u].get("name", str(u))
                connections.append(f"  <- ({rel}) <- {u_name}")
                
            for u, v, attr in self.graph.out_edges(node, data=True):
                rel = attr.get("relationship", "CONNECTED_TO")
                v_name = self.graph.nodes[v].get("name", str(v))
                connections.append(f"  -> ({rel}) -> {v_name}")
                
            if connections:
                context_parts.extend(connections[:10])  # limit to 10 connections per node
                
        return "\n".join(context_parts)


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
    rag_retriever = SimpleRAGRetriever(papers_dir)
    
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
