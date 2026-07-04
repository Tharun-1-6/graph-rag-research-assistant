"""
test_multi_paper_graph.py

Integration test verifying multi-paper global graph construction, merging,
and cross-paper entity connections.
"""

from pathlib import Path
from dotenv import load_dotenv
import networkx as nx

from graph.configs import PAPERS_DIR
from graph.ingestion.loader import PDFLoader
from graph.ingestion.cleaner import TextCleaner
from graph.extraction.extractor import GraphExtractor
from graph.graph_builder.graph_manager import GraphManager
from graph.graph_builder.serializer import GraphSerializer
from graph.statistics import generate_graph_statistics
from graph.visualization.visualizer import GlobalVisualizer

load_dotenv()


def divider(title: str):
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)


def main():
    divider("RUNNING MULTI-PAPER GRAPH CONSTRUCTION AND MERGING TEST")

    # 1. Gather all PDFs
    pdf_paths = sorted(list(PAPERS_DIR.glob("*.pdf")))
    print(f"Found {len(pdf_paths)} research papers in {PAPERS_DIR}:")
    for path in pdf_paths:
        print(f"  - {path.name}")

    if not pdf_paths:
        print("❌ No PDFs found. Please check data/papers/ directory.")
        return

    # 2. Ingest and extract each paper, merging into a single GraphManager
    manager = GraphManager()
    loader = PDFLoader()
    cleaner = TextCleaner()
    extractor = GraphExtractor()

    for idx, path in enumerate(pdf_paths, 1):
        divider(f"PROCESSING PAPER {idx}/{len(pdf_paths)}: {path.name}")
        
        # Load & Clean
        doc = loader.load(path)
        doc = cleaner.clean(doc)
        
        # Extract (cached dynamically to prevent duplicate LLM calls)
        print("Extracting entities and relationships (using caching)...")
        result = extractor.extract(doc)
        
        print(f"Extraction result: {result.num_entities} entities, {result.num_relationships} relationships.")
        
        # Merge
        print(f"Merging '{result.paper.title}' into the global graph...")
        manager.add_extraction(result)

    divider("GRAPH CONSTRUCTION COMPLETED")
    print(f"Consolidated Global Graph: {manager.num_nodes} nodes, {manager.num_edges} edges.")

    # 3. Save graph
    divider("SAVING GLOBAL GRAPH")
    graphs_dir = Path("data/graphs")
    graphs_dir.mkdir(parents=True, exist_ok=True)

    global_graphml_path = graphs_dir / "global_graph.graphml"
    global_json_path = graphs_dir / "global_graph.json"

    # Save via manager
    manager.save_graph(global_graphml_path)
    # Save via serializer to json
    GraphSerializer.save(manager.graph, global_json_path)
    print(f"Saved GraphML to: {global_graphml_path}")
    print(f"Saved JSON to: {global_json_path}")

    # 4. Reload graph to verify persistence
    divider("RELOADING GLOBAL GRAPH FOR VALIDATION")
    reloaded_manager = GraphManager()
    reloaded_manager.load_graph(global_graphml_path)
    print(f"Reloaded Graph: {reloaded_manager.num_nodes} nodes, {reloaded_manager.num_edges} edges.")

    # 5. Verify Metrics & Deduplication
    divider("VERIFICATION AND SANITY CHECKS")

    # Paper count check
    papers = [n for n, data in reloaded_manager.graph.nodes(data=True) if data.get("type") == "Paper"]
    print(f"Number of Paper nodes: {len(papers)} (Expected: {len(pdf_paths)})")
    assert len(papers) == len(pdf_paths), f"Expected {len(pdf_paths)} paper nodes, found {len(papers)}."

    # Author count check
    authors = [n for n, data in reloaded_manager.graph.nodes(data=True) if data.get("type") == "Author"]
    print(f"Number of Author nodes: {len(authors)}")

    # Method count check
    methods = [n for n, data in reloaded_manager.graph.nodes(data=True) if data.get("type") == "Method"]
    print(f"Number of Method nodes: {len(methods)}")

    # Duplicate node check
    # Check if there are any nodes with identical names
    names = {}
    for node, data in reloaded_manager.graph.nodes(data=True):
        name = data.get("name") or data.get("title") or node
        names[name] = names.get(name, 0) + 1
    duplicates = {k: v for k, v in names.items() if v > 1}
    print(f"Duplicate node names found: {len(duplicates)}")
    if duplicates:
        print("Warning: Duplicate node names found:", duplicates)
    assert len(duplicates) == 0, "Deduplication failed! Duplicate node names exist."

    # Duplicate edge check
    # In MultiDiGraph, multiple edges between u and v are allowed.
    # Check if there are duplicate (u, v, rel) triples
    edge_triples = []
    for u, v, data in reloaded_manager.graph.edges(data=True):
        rel = data.get("relationship", "RELATED_TO")
        edge_triples.append((u, v, rel))
    unique_triples = set(edge_triples)
    duplicate_edge_count = len(edge_triples) - len(unique_triples)
    print(f"Duplicate relationship edges count: {duplicate_edge_count}")
    assert duplicate_edge_count == 0, f"Deduplication failed! Found {duplicate_edge_count} duplicate relationship edges."

    # Cross-paper links & Shared entities
    shared_nodes = []
    for node, data in reloaded_manager.graph.nodes(data=True):
        if data.get("type") != "Paper":
            paper_ids_str = data.get("paper_ids", "")
            papers_list = [p.strip() for p in paper_ids_str.split(",") if p.strip()]
            if len(papers_list) > 1:
                shared_nodes.append((node, data.get("type"), papers_list))

    print(f"\nShared entities (cross-paper references: linked to >1 paper): {len(shared_nodes)}")
    for node, node_type, linked_papers in sorted(shared_nodes, key=lambda x: len(x[2]), reverse=True)[:15]:
        print(f"  • Entity: '{node}' ({node_type}) - Mentioned in {len(linked_papers)} papers: {linked_papers}")

    # Shared authors
    shared_authors = [s for s in shared_nodes if s[1] == "Author"]
    print(f"\nShared authors (cross-paper authors): {len(shared_authors)}")
    for node, _, linked_papers in shared_authors:
        print(f"  • Author: '{node}' co-authored {len(linked_papers)} papers in corpus: {linked_papers}")

    # 6. Generate statistics
    divider("COMPUTING STRUCTURAL STATISTICS")
    stats = generate_graph_statistics(reloaded_manager.graph, graphs_dir / "statistics.json")
    print(f"Average Node Degree: {stats['summary']['average_degree']}")
    print(f"Density: {stats['summary']['density']}")
    print(f"Number of Connected Components: {stats['connected_components']['count']}")
    print(f"Largest Component Size: {stats['connected_components']['largest_connected_component_size']}")
    print(f"Average path length of LCC: {stats['connected_components']['average_path_length_lcc']}")

    # 7. Generate PyVis HTML
    divider("GENERATING INTERACTIVE GLOBAL VISUALIZATION")
    visualizer = GlobalVisualizer()
    vis_path = visualizer.visualize(reloaded_manager.graph, graphs_dir / "graph.html")
    print(f"PyVis visualization HTML saved successfully at: {vis_path}")

    divider("INTEGRATION TEST PASSED SUCCESSFUL")


if __name__ == "__main__":
    main()
