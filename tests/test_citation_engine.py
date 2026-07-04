"""
test_citation_engine.py

Unit tests for CitationBuilder fact provenance mapping.
"""

from pathlib import Path
import networkx as nx

from graph.query_engine.context_builder import GraphContext
from graph.query_engine.path_ranker import RankedPath
from graph.citation.citation_builder import CitationBuilder


def divider(title: str):
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)


def main():
    divider("RUNNING CITATION ENGINE TESTS")

    # Load graphml
    graphml_path = Path("data/graphs/attention.graphml")
    if not graphml_path.exists():
        print("⚠️ Graphml file not found. Creating mock graph.")
        graph = nx.MultiDiGraph()
        graph.add_node("attention_is_all_you_need", type="Paper", title="Attention Is All You Need", year=2017, conference="NIPS")
        graph.add_node("transformer", type="Method", name="Transformer")
        graph.add_edge("attention_is_all_you_need", "transformer", relationship="PROPOSES", confidence=1.0, paper_ids="attention_is_all_you_need")
    else:
        print(f"Loading graph from {graphml_path}...")
        graph = nx.read_graphml(graphml_path)

    # Ensure paper ID tracking properties are present on nodes and edges
    # For testing, let's inject paper_ids metadata into the edges of the graph
    for edge in list(graph.edges(data=True)):
        data = edge[-1]
        data["paper_ids"] = "attention_is_all_you_need"
        
    for node, data in graph.nodes(data=True):
        if data.get("type") != "Paper":
            data["paper_ids"] = "attention_is_all_you_need"

    builder = CitationBuilder(graph)

    # 1. Construct Mock context
    context = GraphContext(
        entities=[
            {"id": "transformer", "name": "Transformer", "type": "Method", "paper_ids": "attention_is_all_you_need"}
        ],
        paths=[
            RankedPath(score=0.9, nodes=["attention_is_all_you_need", "transformer"], edges=[{"relationship": "PROPOSES", "paper_ids": "attention_is_all_you_need"}], reason="Test path", path_str="Attention Is All You Need --[PROPOSES]--> Transformer")
        ],
        relationships=[
            {"source": "attention_is_all_you_need", "source_name": "Attention Is All You Need", "target": "transformer", "target_name": "Transformer", "relationship": "PROPOSES", "paper_ids": "attention_is_all_you_need"}
        ],
        papers=[
            {"id": "attention_is_all_you_need", "title": "Attention Is All You Need", "year": 2017, "conference": "NIPS 2017"}
        ]
    )

    # 2. Build citations
    divider("TEST CASE 1: Citation Provenance Extraction")
    provenances = builder.build_citations(context)
    
    print(f"Extracted {len(provenances)} citations:")
    for prov in provenances:
        print(f"  - Citation: {prov.to_citation_str()} | ID: {prov.paper_id} | Confidence: {prov.confidence}")
        assert prov.paper_title == "Attention Is All You Need", "Incorrect citation title mapping!"

    assert len(provenances) > 0, "No provenance citations extracted!"
    print("✓ Passed!")
    divider("ALL CITATION ENGINE TESTS PASSED SUCCESSFUL")


if __name__ == "__main__":
    main()
