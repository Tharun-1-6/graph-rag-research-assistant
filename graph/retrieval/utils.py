"""
utils.py

Helper utilities for graph retrieval.
"""

from difflib import SequenceMatcher
import re
from typing import List, Set


# Common stop words to ignore during retrieval keyword extraction
STOP_WORDS: Set[str] = {
    "what", "how", "why", "who", "where", "when", "which", "whose", "whom",
    "the", "and", "for", "with", "from", "that", "this", "these", "those",
    "are", "was", "were", "been", "have", "has", "had", "can", "could",
    "should", "would", "about", "model", "paper", "graph", "retrieve", "context",
    "does", "did", "doing", "do", "is", "of", "in", "on", "at", "to", "by", "an",
    "as", "it", "its", "they", "them", "their", "our", "we", "you", "your"
}


def clean_string(text: str) -> str:
    """
    Cleans formatting and removes punctuation while keeping lowercase words.
    """
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"\s+", " ", text)


def string_similarity(a: str, b: str) -> float:
    """
    Calculates sequence similarity between two strings (0.0 to 1.0) using SequenceMatcher.
    """
    if not a or not b:
        return 0.0
    a_clean = clean_string(a)
    b_clean = clean_string(b)
    
    if a_clean == b_clean:
        return 1.0
        
    return SequenceMatcher(None, a_clean, b_clean).ratio()


def stem_word(word: str) -> List[str]:
    """
    Performs simple stemming/expansion to map between singular and plural forms.
    """
    word = word.lower().strip()
    if len(word) <= 3:
        return [word]
        
    expanded = [word]
    if word.endswith("s"):
        if word.endswith("es"):
            expanded.append(word[:-2])
        expanded.append(word[:-1])
    else:
        expanded.append(word + "s")
        if word.endswith(("ch", "sh", "x", "z", "s", "o")):
            expanded.append(word + "es")
            
    return list(set(expanded))
