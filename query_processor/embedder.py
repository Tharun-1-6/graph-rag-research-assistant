import os
import re
import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer

class LocalEmbedder:
    """
    Wrapper around the local SentenceTransformers model.
    """
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        # Loads the local embedding model
        self.model = SentenceTransformer(model_name)

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Embeds a list of text strings."""
        if not texts:
            return np.array([])
        return self.model.encode(texts, convert_to_numpy=True)

    def embed_query(self, query: str) -> np.ndarray:
        """Embeds a single query string."""
        return self.model.encode(query, convert_to_numpy=True)


class SemanticEmbeddingChunker:
    """
    Chunks text semantically by splitting the text into sentences,
    embedding them, and breaking at points where consecutive sentence
    similarities drop below a dynamic percentile threshold.
    """
    def __init__(self, embedder: LocalEmbedder, threshold_percentile: float = 85.0):
        self.embedder = embedder
        self.threshold_percentile = threshold_percentile

    def _split_into_sentences(self, text: str) -> List[str]:
        # Split by sentence boundaries, preserving abbreviations
        sentence_end = re.compile(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s')
        sentences = sentence_end.split(text)
        return [s.strip() for s in sentences if s.strip()]

    def chunk_text(self, text: str) -> List[str]:
        sentences = self._split_into_sentences(text)
        if len(sentences) <= 3:
            return [text]

        # 1. Embed sentences
        embeddings = self.embedder.embed_texts(sentences)
        
        # 2. Calculate cosine similarities between consecutive sentences
        similarities = []
        for i in range(len(embeddings) - 1):
            vec1 = embeddings[i]
            vec2 = embeddings[i+1]
            # Cosine similarity
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            if norm1 == 0 or norm2 == 0:
                sim = 0.0
            else:
                sim = np.dot(vec1, vec2) / (norm1 * norm2)
            similarities.append(sim)
            
        # 3. Determine threshold percentile for splitting (split at drops in similarity)
        # Cosine distance = 1 - similarity
        distances = [1.0 - s for s in similarities]
        threshold_dist = np.percentile(distances, self.threshold_percentile)
        
        # 4. Group sentences into chunks based on threshold boundary
        chunks = []
        current_chunk = [sentences[0]]
        
        for i in range(len(sentences) - 1):
            dist = distances[i]
            if dist > threshold_dist:
                # We hit a semantic boundary; close the current chunk and start a new one
                chunks.append(" ".join(current_chunk))
                current_chunk = [sentences[i+1]]
            else:
                current_chunk.append(sentences[i+1])
                
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
        return chunks


class EmbeddedVectorStore:
    """
    Self-contained local vector store that caches semantic chunks
    and embeddings in a pickle file to avoid re-embedding.
    """
    def __init__(self, index_path: str | Path, embedder: LocalEmbedder):
        self.index_path = Path(index_path)
        self.embedder = embedder
        self.data: List[Dict[str, Any]] = []
        self._load_index()

    def _load_index(self):
        if self.index_path.exists():
            try:
                with open(self.index_path, "rb") as f:
                    self.data = pickle.load(f)
                print(f"[EmbeddedVectorStore] Loaded cached index with {len(self.data)} chunks.")
            except Exception as e:
                print(f"[EmbeddedVectorStore] Error loading cache index: {e}. Starting fresh.")
                self.data = []

    def save_index(self):
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.index_path, "wb") as f:
            pickle.dump(self.data, f)
        print(f"[EmbeddedVectorStore] Saved index with {len(self.data)} chunks to {self.index_path.name}")

    def add_document(self, doc_id: str, title: str, chunks: List[str]):
        """Embeds and indexes document chunks."""
        # Filter out existing chunks for this doc_id to avoid duplicates
        self.data = [item for item in self.data if item["doc_id"] != doc_id]
        
        if not chunks:
            return
            
        print(f"Embedding {len(chunks)} semantic chunks for '{title}'...")
        embeddings = self.embedder.embed_texts(chunks)
        
        for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            self.data.append({
                "doc_id": doc_id,
                "title": title,
                "chunk_id": idx,
                "text": chunk,
                "embedding": emb
            })
        self.save_index()

    def retrieve(self, query: str, top_k: int = 4) -> str:
        """Retrieves the top K semantically similar chunks for a query."""
        if not self.data:
            return "No documents indexed."
            
        # 1. Embed query
        query_emb = self.embedder.embed_query(query)
        q_norm = np.linalg.norm(query_emb)
        if q_norm == 0:
            return "Empty query embedding."
            
        # 2. Compute cosine similarity against all chunks
        scored_chunks = []
        for item in self.data:
            emb = item["embedding"]
            emb_norm = np.linalg.norm(emb)
            if emb_norm == 0:
                sim = 0.0
            else:
                sim = np.dot(query_emb, emb) / (q_norm * emb_norm)
            scored_chunks.append((sim, item))
            
        # 3. Sort and retrieve
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_items = scored_chunks[:top_k]
        
        context_parts = []
        for score, item in top_items:
            context_parts.append(
                f"Source: {item['title']} (Paragraph {item['chunk_id']}, Similarity: {score:.3f})\n"
                f"Content: {item['text']}"
            )
        return "\n\n---\n\n".join(context_parts)
