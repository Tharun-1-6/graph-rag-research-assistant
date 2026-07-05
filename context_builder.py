import json
from pathlib import Path
from typing import Dict, Any, List

BASE_DIR = Path(__file__).resolve().parent


def estimate_tokens(text: str) -> int:
    """Estimate the number of tokens in a text using a word-based heuristic."""
    # A standard heuristic is ~1.3 tokens per word
    return int(len(text.split()) * 1.3)


def is_nearly_identical(text1: str, text2: str, threshold: float = 0.90) -> bool:
    """Check if two texts are nearly identical using Jaccard word similarity."""
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return False
        
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    jaccard = len(intersection) / len(union)
    return jaccard >= threshold


def merge_text(t1: str, t2: str) -> str:
    """Merge two strings, aligning and removing overlapping suffix/prefix if present."""
    s1 = t1.strip()
    s2 = t2.strip()
    
    min_overlap = 15
    max_overlap = min(len(s1), len(s2))
    
    # Check if s1 ends with start of s2
    best_overlap_len = 0
    for overlap_len in range(min_overlap, max_overlap + 1):
        if s1[-overlap_len:] == s2[:overlap_len]:
            best_overlap_len = overlap_len
            
    if best_overlap_len > 0:
        return s1 + s2[best_overlap_len:]
        
    # Check if s2 ends with start of s1
    best_overlap_len_rev = 0
    for overlap_len in range(min_overlap, max_overlap + 1):
        if s2[-overlap_len:] == s1[:overlap_len]:
            best_overlap_len_rev = overlap_len
            
    if best_overlap_len_rev > 0:
        return s2 + s1[best_overlap_len_rev:]
        
    # No overlap detected; join with double newline
    return s1 + "\n\n" + s2


class ContextBuilder:
    """Processes retrieved chunks to deduplicate, merge, and format context for the LLM."""

    def __init__(self, max_context_chars: int = 8000, max_context_tokens: int = 2000):
        self.max_context_chars = max_context_chars
        self.max_context_tokens = max_context_tokens

    def deduplicate(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate or nearly identical chunks, keeping only the highest-ranked one."""
        deduplicated = []
        for chunk in chunks:
            is_dup = False
            for existing in deduplicated:
                if is_nearly_identical(chunk["content"], existing["content"]):
                    is_dup = True
                    break
            if not is_dup:
                deduplicated.append(chunk)
        return deduplicated

    def merge_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge adjacent/overlapping chunks from the same document."""
        # Work on a copy
        active_chunks = [dict(c) for c in chunks]
        
        merged_any = True
        while merged_any:
            merged_any = False
            i = 0
            while i < len(active_chunks):
                j = i + 1
                while j < len(active_chunks):
                    c1 = active_chunks[i]
                    c2 = active_chunks[j]
                    
                    same_source = (c1.get("source") == c2.get("source"))
                    
                    # Check page adjacency
                    p1 = c1.get("page")
                    p2 = c2.get("page")
                    adjacent_pages = False
                    if p1 is not None and p2 is not None:
                        try:
                            adjacent_pages = (abs(int(p1) - int(p2)) <= 1)
                        except (ValueError, TypeError):
                            adjacent_pages = False
                    elif p1 is None and p2 is None:
                        adjacent_pages = True  # Same document, no page info
                    
                    # Check text overlap
                    s1 = c1["content"].strip()
                    s2 = c2["content"].strip()
                    has_overlap = False
                    
                    # Look for overlap of at least 15 characters
                    min_len = min(len(s1), len(s2))
                    for k in range(15, min(min_len, 100) + 1):
                        if s1[-k:] == s2[:k] or s2[-k:] == s1[:k]:
                            has_overlap = True
                            break
                    
                    if same_source and (adjacent_pages or has_overlap):
                        # Merge c2 into c1
                        c1["content"] = merge_text(c1["content"], c2["content"])
                        
                        # Handle page updating
                        if p1 is not None and p2 is not None:
                            try:
                                min_p = min(int(p1), int(p2))
                                max_p = max(int(p1), int(p2))
                                c1["page"] = min_p if min_p == max_p else f"{min_p}-{max_p}"
                            except (ValueError, TypeError):
                                c1["page"] = p1
                        elif p1 is None:
                            c1["page"] = p2
                            
                        # Preserve highest rank
                        c1["rank"] = min(c1.get("rank", 999), c2.get("rank", 999))
                        
                        # Remove c2 and restart inner loop search
                        active_chunks.pop(j)
                        merged_any = True
                    else:
                        j += 1
                i += 1
                
        # Re-sort to preserve original relevance ranking
        active_chunks.sort(key=lambda x: x.get("rank", 999))
        return active_chunks

    def apply_budget(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Keep adding whole chunks in rank order until budget is reached."""
        budgeted_chunks = []
        current_chars = 0
        current_tokens = 0
        
        for chunk in chunks:
            chunk_content = chunk["content"]
            chunk_len = len(chunk_content)
            chunk_tokens = estimate_tokens(chunk_content)
            
            # Check if adding this chunk exceeds budget
            if (current_chars + chunk_len > self.max_context_chars) or \
               (current_tokens + chunk_tokens > self.max_context_tokens):
                # Discard this and subsequent chunks to stay under budget
                break
                
            budgeted_chunks.append(chunk)
            current_chars += chunk_len
            current_tokens += chunk_tokens
            
        return budgeted_chunks

    def build_context(self, retrieval_output: Dict[str, Any]) -> Dict[str, Any]:
        """Runs the entire Context Builder pipeline on retrieval output and saves context to JSON."""
        query = retrieval_output.get("query", "")
        raw_chunks = retrieval_output.get("retrieved_chunks", [])
        
        # 1. Remove duplicate chunks
        deduplicated = self.deduplicate(raw_chunks)
        
        # 2. Merge adjacent/overlapping chunks
        merged = self.merge_chunks(deduplicated)
        
        # 3. Apply token/character budget (also preserves relevance rank order)
        budgeted = self.apply_budget(merged)
        
        # 4. Format LLM Context output
        context_items = []
        for chunk in budgeted:
            context_items.append({
                "source": chunk.get("source", "Unknown"),
                "page": chunk.get("page"),
                "content": chunk.get("content", "")
            })
            
        llm_context = {
            "query": query,
            "context": context_items
        }
        
        # Save to llm_context.json in the workspace root
        output_file = BASE_DIR / "llm_context.json"
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(llm_context, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Failed to save LLM context JSON: {e}")
            
        return llm_context


def build_context(retrieval_output: Dict[str, Any], max_chars: int = 8000, max_tokens: int = 2000) -> Dict[str, Any]:
    """Helper function to run the context builder pipeline directly."""
    builder = ContextBuilder(max_context_chars=max_chars, max_context_tokens=max_tokens)
    return builder.build_context(retrieval_output)


if __name__ == "__main__":
    # Test execution
    retrieved_json_file = BASE_DIR / "retrieved_chunks.json"
    if retrieved_json_file.exists():
        try:
            with open(retrieved_json_file, "r", encoding="utf-8") as file:
                data = json.load(file)
            result = build_context(data)
            print("Successfully processed retrieval output into LLM context:")
            print(json.dumps(result, indent=4, ensure_ascii=False))
        except Exception as err:
            print(f"Error testing context builder: {err}")
    else:
        print("No retrieved_chunks.json found to test with.")
