# ==============================================================================
# GOOGLE COLAB EMBEDDING GENERATOR
# ==============================================================================
# Copy and paste this script into a Google Colab notebook cell.
# Make sure to upload 'raw_docs.json' to the Colab files section before running.
# ==============================================================================

import json
import pickle
import numpy as np
import re
from typing import List, Dict, Any

# Install SentenceTransformers if not present
try:
    from sentence_transformers import SentenceTransformer
    print("SentenceTransformers is already installed.")
except ImportError:
    print("Installing sentence-transformers...")
    import subprocess
    subprocess.run(["pip", "install", "-q", "sentence-transformers"])
    from sentence_transformers import SentenceTransformer


class ColabSemanticChunker:
    """
    Chunks text semantically by splitting the text into sentences,
    embedding them, and breaking at points where consecutive sentence
    similarities drop below a dynamic percentile threshold.
    """
    def __init__(self, model, threshold_percentile: float = 85.0):
        self.model = model
        self.threshold_percentile = threshold_percentile

    def _split_into_sentences(self, text: str) -> List[str]:
        sentence_end = re.compile(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s')
        sentences = sentence_end.split(text)
        return [s.strip() for s in sentences if s.strip()]

    def chunk_text(self, text: str) -> List[str]:
        sentences = self._split_into_sentences(text)
        if len(sentences) <= 3:
            return [text]

        # Embed sentences
        embeddings = self.model.encode(sentences, convert_to_numpy=True)
        
        # Calculate cosine similarities between consecutive sentences
        similarities = []
        for i in range(len(embeddings) - 1):
            vec1 = embeddings[i]
            vec2 = embeddings[i+1]
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            if norm1 == 0 or norm2 == 0:
                sim = 0.0
            else:
                sim = np.dot(vec1, vec2) / (norm1 * norm2)
            similarities.append(sim)
            
        # Cosine distance = 1 - similarity
        distances = [1.0 - s for s in similarities]
        threshold_dist = np.percentile(distances, self.threshold_percentile)
        
        chunks = []
        current_chunk = [sentences[0]]
        
        for i in range(len(sentences) - 1):
            dist = distances[i]
            if dist > threshold_dist:
                chunks.append(" ".join(current_chunk))
                current_chunk = [sentences[i+1]]
            else:
                current_chunk.append(sentences[i+1])
                
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
        return chunks


def main():
    # 1. Load the raw documents
    input_file = "raw_docs.json"
    output_file = "vector_index.pkl"
    
    # Change this to your preferred 200M+ parameter embedding model
    model_name = "BAAI/bge-large-en-v1.5" 
    
    print(f"Loading raw documents from {input_file}...")
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            documents = json.load(f)
    except FileNotFoundError:
        print(f"Error: Please upload '{input_file}' to your Colab workspace first!")
        return

    print(f"Loading embedding model: {model_name}...")
    # Will automatically run on GPU/TPU if available in Colab runtime
    model = SentenceTransformer(model_name)
    chunker = ColabSemanticChunker(model, threshold_percentile=85.0)
    
    vector_data = []
    
    for doc in documents:
        doc_id = doc["doc_id"]
        title = doc["title"]
        text = doc["text"]
        
        print(f"\nProcessing '{title}'...")
        chunks = chunker.chunk_text(text)
        print(f"  • Created {len(chunks)} semantic chunks.")
        
        print("  • Generating high-dimensional embeddings...")
        embeddings = model.encode(chunks, convert_to_numpy=True)
        
        for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            vector_data.append({
                "doc_id": doc_id,
                "title": title,
                "chunk_id": idx,
                "text": chunk,
                "embedding": emb
            })
            
    print(f"\nSaving {len(vector_data)} embedded chunks to {output_file}...")
    with open(output_file, "wb") as f:
        pickle.dump(vector_data, f)
        
    print("\n==================================================")
    print(f"SUCCESS: Download '{output_file}' and place it in your local query_processor/ directory!")
    print("==================================================")

if __name__ == "__main__":
    main()
