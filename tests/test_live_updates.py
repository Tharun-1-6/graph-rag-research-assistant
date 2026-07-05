"""
test_live_updates.py

Unit tests for GraphWatcher and live knowledge base index updating.
"""

import shutil
from pathlib import Path
import networkx as nx

from graph.watcher import GraphWatcher
from graph.graph_builder.graph_manager import GraphManager


def divider(title: str):
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)


def main():
    divider("RUNNING LIVE FOLDER WATCHER UPDATE TESTS")

    # Paths
    temp_dir = Path("data/temp_watcher_papers")
    shutil.rmtree(temp_dir, ignore_errors=True)
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    mock_graphml = Path("data/graphs/watcher_test_graph.graphml")
    if mock_graphml.exists():
        mock_graphml.unlink()

    # Create empty start graphml via GraphManager
    manager = GraphManager()
    manager.save_graph(mock_graphml)

    # Instantiate Watcher
    watcher = GraphWatcher(graph_path=mock_graphml, papers_dir=temp_dir)

    # 1. Verify initial scan is empty
    divider("TEST CASE 1: Empty Scan Check")
    scanned_empty = watcher.scan_and_update()
    print(f"Scanned empty directory: {scanned_empty}")
    assert len(scanned_empty) == 0, "Scan must be empty initially!"
    print("✓ Passed!")

    # 2. Simulate copying a research paper PDF
    divider("TEST CASE 2: Simulating PDF Copy Event")
    source_pdf = Path("data/papers/1-Attention Is All You Need.pdf")
    if not source_pdf.exists():
        print("⚠️ Source PDF not found. Skipping file ingestion execution.")
    else:
        target_pdf = temp_dir / "1-Attention Is All You Need.pdf"
        shutil.copy(source_pdf, target_pdf)
        print(f"Copied {source_pdf.name} to watch directory.")

        # Run poll scan
        new_papers = watcher.scan_and_update()
        print(f"Detected and processed papers: {[p.name for p in new_papers]}")
        assert len(new_papers) > 0, "Watcher failed to detect newly placed PDF!"
        
        # Load and verify graph has been updated with the Paper node
        updated_graph = nx.read_graphml(mock_graphml)
        paper_nodes = [n for n, d in updated_graph.nodes(data=True) if d.get("type") == "Paper"]
        print(f"Paper nodes present in updated graph: {paper_nodes}")
        assert len(paper_nodes) > 0, "Incremental merge failed: Paper node missing!"
        print("✓ Passed!")

    # Cleanup temp directory and mock file
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    if mock_graphml.exists():
        mock_graphml.unlink()

    divider("ALL WATCHER LIVE UPDATE TESTS PASSED SUCCESSFUL")


if __name__ == "__main__":
    main()
