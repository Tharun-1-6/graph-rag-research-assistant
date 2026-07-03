from pathlib import Path

from graph.ingestion.loader import PDFLoader
from graph.ingestion.cleaner import TextCleaner

from graph.extraction.extractor import GraphExtractor

from graph.graph_builder.builder import GraphBuilder
from graph.graph_builder.serializer import GraphSerializer


PDF_PATH = Path(
    r"C:\Projects Tharun\RAG and GraphRAG based llm\data\papers\1-Attention Is All You Need.pdf"
)


def divider(title):
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)


def main():

    divider("STEP 1 : LOAD")

    loader = PDFLoader()
    document = loader.load(PDF_PATH)

    cleaner = TextCleaner()
    document = cleaner.clean(document)

    divider("STEP 2 : EXTRACTION")

    pipeline = GraphExtractor()

    extraction = pipeline.extract(document)

    print(extraction)

    divider("STEP 3 : BUILD GRAPH")

    builder = GraphBuilder()

    graph = builder.build(extraction)

    divider("GRAPH SUMMARY")

    print(f"Nodes : {graph.number_of_nodes()}")
    print(f"Edges : {graph.number_of_edges()}")

    print()

    print("First 15 Nodes")

    for node, data in list(graph.nodes(data=True))[:15]:
        print(node, data)

    print()

    print("First 15 Edges")

    for u, v, data in list(graph.edges(data=True))[:15]:
        print(u, "->", v, data)

    divider("STEP 4 : SAVE GRAPH")

    serializer = GraphSerializer("data/graphs")

    serializer.save_graphml(graph, "attention.graphml")
    serializer.save_json(graph, "attention.json")

    print("Graph saved successfully.")

    divider("TEST PASSED")


if __name__ == "__main__":
    main()