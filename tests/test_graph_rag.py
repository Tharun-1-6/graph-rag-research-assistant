"""
test_graph_rag.py

Integration test for GraphRAG retrieval and question answering.
"""

from pathlib import Path

from graph.ingestion.loader import PDFLoader
from graph.ingestion.cleaner import TextCleaner
from graph.extraction.extractor import GraphExtractor
from graph.graph_builder.builder import GraphBuilder
from graph.graph_builder.serializer import GraphSerializer
from graph.rag import GraphRAG


PDF_PATH = Path(
    r"C:\Projects Tharun\RAG and GraphRAG based llm\data\papers\1-Attention Is All You Need.pdf"
)
GRAPH_DIR = Path("data/graphs")
GRAPH_PATH = GRAPH_DIR / "attention.graphml"


def divider(title):
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)


def ensure_graph_exists():
    """
    Ensures that the knowledge graph exists, building it if necessary.
    """
    if GRAPH_PATH.exists():
        print(f"Using existing graph at {GRAPH_PATH}")
        return

    print("Knowledge graph not found. Building it from the PDF...")
    GRAPH_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Ingestion
    loader = PDFLoader()
    document = loader.load(PDF_PATH)
    cleaner = TextCleaner()
    document = cleaner.clean(document)

    # 2. Extraction
    extractor = GraphExtractor()
    extraction = extractor.extract(document)

    # 3. Build Graph
    builder = GraphBuilder()
    graph = builder.build(extraction)

    # 4. Save Graph
    serializer = GraphSerializer(GRAPH_DIR)
    serializer.save_graphml(graph, "attention.graphml")
    serializer.save_json(graph, "attention.json")
    print("Knowledge graph built and saved successfully.")


def main():
    divider("PREPARING DATA")
    ensure_graph_exists()

    divider("INITIALIZING GRAPHRAG")
    rag = GraphRAG(GRAPH_PATH)

    queries = [
        "Who wrote the Attention Is All You Need paper?",
        "What model or architecture does the paper propose?",
        "What datasets and benchmarks are used to evaluate the model?",
    ]

    for i, query_text in enumerate(queries, 1):
        divider(f"QUERY {i}: {query_text}")
        
        print("\n[RETRIEVING RELATIONAL CONTEXT]")
        context = rag.retriever.retrieve_relational_context(query_text)
        print(context)
        
        print("\n[GENERATING ANSWER FROM LLM]")
        answer = rag.query(query_text)
        print(answer)


if __name__ == "__main__":
    main()
