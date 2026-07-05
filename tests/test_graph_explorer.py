"""
test_graph_explorer.py

Unit tests for ExplorerVisualizer dashboard generation.
"""

from pathlib import Path
import networkx as nx

from graph.visualization.explorer import ExplorerVisualizer


def divider(title: str):
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)


def main():
    divider("RUNNING GRAPH EXPLORER VISUALIZATION TESTS")

    # Load graphml
    graphml_path = Path("data/graphs/attention.graphml")
    if not graphml_path.exists():
        print("⚠️ Graphml file not found. Creating mock graph.")
        graph = nx.MultiDiGraph()
        graph.add_node("attention_is_all_you_need", type="Paper", title="Attention Is All You Need", year=2017)
        graph.add_node("transformer", type="Method", name="Transformer")
        graph.add_edge("attention_is_all_you_need", "transformer", relationship="PROPOSES", confidence=1.0)
    else:
        print(f"Loading graph from {graphml_path}...")
        graph = nx.read_graphml(graphml_path)

    # Output file
    output_html = Path("data/graphs/explorer_test.html")
    if output_html.exists():
        output_html.unlink()

    visualizer = ExplorerVisualizer()
    saved_path = visualizer.visualize_explorer(graph, output_html)

    print(f"Saved interactive explorer dashboard to: {saved_path}")

    # Assertions
    assert saved_path.exists(), "Explorer visualization HTML file was not created!"
    
    # Check that injected elements are in the HTML code
    with open(saved_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "explorer-panel" in content, "Control panel missing from explorer HTML!"
        assert "highlightShortestPath" in content, "Shortest path script missing from explorer HTML!"
        assert "toggleSelectedNeighbors" in content, "Expand/collapse neighbors script missing from explorer HTML!"
        assert "resetExplorer" in content, "Reset script missing from explorer HTML!"

    print("✓ Passed!")
    divider("ALL GRAPH EXPLORER VISUALIZATION TESTS PASSED SUCCESSFUL")


if __name__ == "__main__":
    main()
