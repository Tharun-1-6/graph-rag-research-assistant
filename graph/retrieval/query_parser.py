"""
query_parser.py

Parses natural language queries to extract keywords, candidate entities, and verbs without using an LLM.
"""

from dataclasses import dataclass, field
import re
from typing import Dict, List, Set

from .utils import STOP_WORDS, stem_word, clean_string


# Query Intents
AUTHOR_QUERY = "AUTHOR_QUERY"
METHOD_QUERY = "METHOD_QUERY"
DATASET_QUERY = "DATASET_QUERY"
BENCHMARK_QUERY = "BENCHMARK_QUERY"
TASK_QUERY = "TASK_QUERY"
METRIC_QUERY = "METRIC_QUERY"
INSTITUTION_QUERY = "INSTITUTION_QUERY"
EXPLANATION_QUERY = "EXPLANATION_QUERY"
COMPARISON_QUERY = "COMPARISON_QUERY"
GENERAL_QUERY = "GENERAL_QUERY"


@dataclass
class ParsedQuery:
    """
    Structured representation of a parsed query.
    """
    raw_query: str
    entities: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    verbs: List[str] = field(default_factory=list)
    noun_phrases: List[str] = field(default_factory=list)
    intent: str = GENERAL_QUERY


class QueryParser:
    """
    Extracts terms, entities, and relationship verbs from queries using heuristic NLP.
    """

    # Verbs/keywords mapping to relationship types in the schema
    RELATIONSHIP_VERBS: Dict[str, str] = {
        "author": "AUTHORED",
        "write": "AUTHORED",
        "wrote": "AUTHORED",
        "written": "AUTHORED",
        "by": "AUTHORED",
        
        "affiliate": "AFFILIATED_WITH",
        "work": "AFFILIATED_WITH",
        "belong": "AFFILIATED_WITH",
        "from": "AFFILIATED_WITH",
        
        "publish": "PUBLISHED_AT",
        "present": "PUBLISHED_AT",
        "appear": "PUBLISHED_AT",
        
        "propose": "PROPOSES",
        "introduce": "PROPOSES",
        "design": "PROPOSES",
        "create": "PROPOSES",
        "develop": "PROPOSES",
        
        "use": "USES",
        "employ": "USES",
        "utilize": "USES",
        "apply": "USES",
        
        "evaluate": "EVALUATED_ON",
        "test": "EVALUATED_ON",
        "benchmark": "EVALUATED_ON",
        "run": "EVALUATED_ON",
        
        "perform": "PERFORMS",
        "solve": "PERFORMS",
        "do": "PERFORMS",
        "achieve": "PERFORMS",
        
        "improve": "IMPROVES_UPON",
        "better": "IMPROVES_UPON",
        "outperform": "IMPROVES_UPON",
        
        "relate": "RELATED_TO",
        "connect": "RELATED_TO",
        "link": "RELATED_TO",
    }

    def parse(self, query: str) -> ParsedQuery:
        """
        Parses a raw question string into a ParsedQuery structure.
        """
        if not query:
            return ParsedQuery(raw_query="")

        # 1. Extract Capitalized Noun Phrases/Entities
        entities = self._extract_capitalized_phrases(query)

        # 2. Tokenize and clean raw words
        raw_words = re.findall(r"\b\w{3,}\b", query.lower())

        # 3. Extract keywords (excluding stop words) and expand stemming
        keywords = []
        for word in raw_words:
            if word in STOP_WORDS:
                continue
            # Add both original and stemmed variants to keywords
            keywords.extend(stem_word(word))
        keywords = list(set(keywords))

        # 4. Extract query relationship verbs
        verbs = []
        for word in raw_words:
            # Check if word stems to any known relationship verb
            for verb_stem, rel_type in self.RELATIONSHIP_VERBS.items():
                if verb_stem in word or word in verb_stem:
                    verbs.append(rel_type)
        verbs = list(set(verbs))

        # 5. Extract simple noun phrases (consecutive non-stop-word nouns/adjectives)
        noun_phrases = self._extract_noun_phrases(query, raw_words)

        # 6. Detect Query Intent
        intent = self._detect_intent(query, raw_words)

        return ParsedQuery(
            raw_query=query,
            entities=entities,
            keywords=keywords,
            verbs=verbs,
            noun_phrases=noun_phrases,
            intent=intent,
        )

    def _detect_intent(self, query: str, raw_words: List[str]) -> str:
        """
        Classifies the user query intent using rule-based heuristics.
        """
        q_lower = query.lower()
        
        # 0. Semantic router for 'who' questions (person queries)
        if "who" in raw_words:
            if any(w in q_lower for w in ["propose", "introduce", "design", "create", "develop"]):
                return METHOD_QUERY
            else:
                return AUTHOR_QUERY

        # 1. Institution Query: institution, university, lab, affiliated, works at, company, organization
        if (any(w in q_lower for w in ["institution", "university", "lab", "affiliated", "work at", "works at", "working at", "company", "organization"])
            or ("where" in raw_words and "work" in raw_words)):
            return INSTITUTION_QUERY
            
        # 2. Comparison Query: compare, difference, vs, versus, contrast, distinct, comparison
        if any(w in q_lower for w in ["compare", "difference", " vs ", "versus", "contrast", "different from", "comparison"]):
            return COMPARISON_QUERY
            
        # 3. Explanation Query: explain, what is, how does, describe, definition, mechanism, walkthrough, why does, detail
        if any(w in q_lower for w in ["explain", "what is", "how does", "describe", "definition", "mechanism", "walkthrough", "details of", "why", "detail"]):
            return EXPLANATION_QUERY
            
        # 4. Benchmark Query: benchmark, benchmarks, evaluation set
        if any(w in q_lower for w in ["benchmark", "evaluation set"]):
            return BENCHMARK_QUERY
            
        # 5. Dataset Query: dataset, datasets, corpus, raw data
        if any(w in q_lower for w in ["dataset", "corpus", "data"]):
            return DATASET_QUERY
            
        # 6. Metric Query: metric, metrics, score, bleu, f1, accuracy, perplexity, recall, precision
        if any(w in q_lower for w in ["metric", "score", "bleu", "perplexity", "f1", "accuracy", "recall", "precision"]):
            return METRIC_QUERY
            
        # 7. Task Query: task, tasks, job, jobs, perform, translation
        if any(w in q_lower for w in ["task", "job", "perform", "translation"]):
            return TASK_QUERY
            
        # 8. Author Query: who wrote, author, creator, by
        if any(w in q_lower for w in ["who wrote", "author", "creator", "by:"]) or "by" in raw_words:
            return AUTHOR_QUERY
            
        # 9. Method/Architecture Query: model, architecture, method, algorithm, self-attention, transformer
        if any(w in q_lower for w in ["model", "architecture", "method", "algorithm", "attention", "transformer", "network"]):
            return METHOD_QUERY
            
        return GENERAL_QUERY

    def _extract_capitalized_phrases(self, query: str) -> List[str]:
        """
        Extracts consecutive title-case word sequences as potential entities.
        """
        words = query.strip().split()
        if not words:
            return []

        phrases = []
        current_phrase = []

        question_starters = {
            "who", "what", "how", "why", "where", "when", "which",
            "is", "are", "do", "does", "did", "can", "could", "explain"
        }

        for i, word in enumerate(words):
            # Strip punctuation for check
            clean_word = re.sub(r"[^\w]", "", word)
            if not clean_word:
                continue

            is_capital = clean_word[0].isupper()
            is_first = (i == 0)

            # Skip first word if it's a typical question starter
            if is_first and clean_word.lower() in question_starters:
                continue

            if is_capital:
                current_phrase.append(clean_word)
            else:
                if current_phrase:
                    phrases.append(" ".join(current_phrase))
                    current_phrase = []

        if current_phrase:
            phrases.append(" ".join(current_phrase))

        # Also add individual words if they are part of a capitalized phrase
        all_entities = list(phrases)
        for phrase in phrases:
            if " " in phrase:
                all_entities.extend(phrase.split())

        return list(set([p.strip() for p in all_entities if p]))

    def _extract_noun_phrases(self, query: str, cleaned_words: List[str]) -> List[str]:
        """
        Extracts consecutive non-stop words as noun phrases.
        """
        words = re.findall(r"\b\w+\b", query.lower())
        phrases = []
        current_phrase = []

        for word in words:
            if len(word) > 2 and word not in STOP_WORDS:
                current_phrase.append(word)
            else:
                if len(current_phrase) > 1:
                    phrases.append(" ".join(current_phrase))
                current_phrase = []

        if len(current_phrase) > 1:
            phrases.append(" ".join(current_phrase))

        return list(set(phrases))
