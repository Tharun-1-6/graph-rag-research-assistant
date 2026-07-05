import argparse
import json
import sys
from pathlib import Path

from ingestion.ingest import IngestionPipeline
from retrieval.retrieve import RetrievalPipeline
from context_builder import build_context

# Reconfigure stdout/stderr to use UTF-8 to prevent 'charmap' encode crashes on Windows
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def run_rag(query: str, ingestion_pipeline: IngestionPipeline, retrieval_pipeline: RetrievalPipeline):
    """Executes RAG by running ingestion if the database index does not exist,

    then retrieves the top matched documents.
    """
    # Run ingestion if the index does not exist or is empty
    if not retrieval_pipeline.index_exists():
        print("Local FAISS database index not found. Running ingestion pipeline...")
        ingestion_pipeline.run()

    print(f"\nRetrieving relevant chunks for query: '{query}'...")
    results = retrieval_pipeline.run(query, k=5)
    return results


def main():
    """Run the CLI-based RAG app."""
    parser = argparse.ArgumentParser(description="Ask questions against a local RAG index")
    parser.add_argument("query", nargs="?", help="Question to search for")
    args = parser.parse_args()

    query = args.query or input("Enter your question: ").strip()
    if not query:
        print("No question provided.")
        return

    # Instantiate the modular pipelines
    ingestion_pipeline = IngestionPipeline()
    retrieval_pipeline = RetrievalPipeline()

    # Execute RAG by passing the query, ingestion pipeline, and retrieval pipeline
    try:
        retrieval_output = run_rag(query, ingestion_pipeline, retrieval_pipeline)
        llm_context = build_context(retrieval_output)

        # Pretty print the final LLM context JSON structure to console
        print(json.dumps(llm_context, indent=4, ensure_ascii=False))
    except Exception as e:
        print(f"Error executing RAG pipeline: {e}")


if __name__ == "__main__":
    main()
