import datetime
import json
from pathlib import Path
from typing import Dict, Any

# pyrefly: ignore [missing-import]
from langchain_community.vectorstores import FAISS
# pyrefly: ignore [missing-import]
from langchain_community.embeddings import HuggingFaceEmbeddings
print("Imports successful")

BASE_DIR = Path(__file__).resolve().parent.parent


class RetrievalPipeline:
    """Retrieval pipeline that loads a local FAISS database and searches for matching documents."""

    def __init__(self, persist_dir=None, embeddings_model="sentence-transformers/all-MiniLM-L6-v2"):
        self.persist_dir = Path(persist_dir or BASE_DIR / "db")
        self.embeddings_model = embeddings_model

    def index_exists(self) -> bool:
        """Check if index files exist in persist_dir."""
        return self.persist_dir.exists() and any(self.persist_dir.iterdir())

    def run(self, query: str, k: int = 5) -> Dict[str, Any]:
        """Execute retrieval to return top k matched documents in a structured JSON dictionary."""
        if not self.index_exists():
            raise FileNotFoundError(
                f"No FAISS index found at {self.persist_dir}. Run the ingestion step first."
            )

        embeddings = HuggingFaceEmbeddings(model_name=self.embeddings_model)
        vectorstore = FAISS.load_local(
            str(self.persist_dir),
            embeddings,
            allow_dangerous_deserialization=True,
        )
        
        # Perform similarity search with score
        docs_and_scores = vectorstore.similarity_search_with_score(query, k=k)

        retrieved_chunks = []
        for index, (doc, score) in enumerate(docs_and_scores, start=1):
            source = doc.metadata.get("source", "Unknown")
            source_name = Path(source).name if source != "Unknown" else "Unknown"
            page = doc.metadata.get("page", None)
            
            chunk_data = {
                "chunk_id": index,
                "rank": index,
                "source": source_name,
                "page": page,
                "content": doc.page_content
            }
            # FAISS with L2 distance returns Euclidean distance, where smaller is more relevant.
            # Thus, we name it 'distance'.
            if score is not None:
                chunk_data["distance"] = float(score)
                
            retrieved_chunks.append(chunk_data)

        # Get ISO-8601 timestamp in UTC
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        result_json = {
            "query": query,
            "retrieval_metadata": {
                "retriever": "vector",
                "embedding_model": self.embeddings_model,
                "top_k": k,
                "timestamp": timestamp
            },
            "retrieved_chunks": retrieved_chunks
        }

        # Save to retrieved_chunks.json at the workspace root
        output_file = BASE_DIR / "retrieved_chunks.json"
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result_json, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Failed to save retrieved chunks JSON: {e}")

        return result_json


def load_vectorstore(persist_dir=None):
    """Load vectorstore from persist_dir (backward compatibility)."""
    persist_dir = Path(persist_dir or BASE_DIR / "db")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return FAISS.load_local(
        str(persist_dir),
        embeddings,
        allow_dangerous_deserialization=True,
    )


def retrieve_documents(query, k=5, persist_dir=None):
    """Retrieve documents matching query (backward compatibility)."""
    pipeline = RetrievalPipeline(persist_dir=persist_dir)
    return pipeline.run(query, k=k)


if __name__ == "__main__":
    import sys
    query = sys.argv[1] if len(sys.argv) > 1 else "What is this project about?"
    try:
        pipeline = RetrievalPipeline()
        results = pipeline.run(query)
        print(json.dumps(results, indent=4, ensure_ascii=False))
    except FileNotFoundError as e:
        print(e)
