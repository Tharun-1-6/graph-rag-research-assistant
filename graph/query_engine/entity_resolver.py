"""
entity_resolver.py

Resolves query target terms, entities, and keywords to valid graph node IDs
using acronym expansion, token overlap, alias matching, and typo-tolerant fuzzy metrics.
"""

from dataclasses import dataclass
from difflib import SequenceMatcher
import re
from typing import Dict, List, Set, Union
import networkx as nx

from graph.retrieval.utils import clean_string


@dataclass
class ResolvedEntity:
    """
    Represents a successfully resolved entity mapping to a graph node.
    """
    id: str
    name: str
    type: str
    confidence: float
    matched_by: str  # e.g., 'exact_id', 'exact_name', 'alias', 'acronym', 'fuzzy', 'token_overlap'


class EntityResolver:
    """
    Finds and resolves graph nodes corresponding to query terms.
    """

    ACRONYMS: Dict[str, str] = {
        "bert": "bert",
        "nsp": "next_sentence_prediction",
        "mlm": "masked_language_modeling",
        "sota": "state_of_the_art",
        "sot": "state_of_the_art",
        "glue": "glue",
        "squad": "squad",
        "bpe": "byte_level_bpe",
        "albert": "albert",
        "roberta": "roberta",
        "deberta": "deberta",
        "rnn": "recurrent_neural_network",
        "lstm": "long_short_term_memory",
        "nli": "natural_language_inference",
        "rte": "recognizing_textual_entailment",
        "wnli": "winograd_nli",
        "qqp": "quora_question_pairs",
        "mnli": "multi_genre_natural_language_inference",
        "ner": "named_entity_recognition",
    }

    def __init__(self, graph: nx.MultiDiGraph, min_score: float = 0.5):
        """
        Initializes the resolver with a Graph instance.
        """
        self.graph = graph
        self.min_score = min_score
        self._resolve_cache = {}

    def resolve(self, term: str) -> List[ResolvedEntity]:
        """
        Resolves a single search term/keyword against graph nodes.
        """
        term_clean = clean_string(term)
        if not term_clean:
            return []

        if term_clean in self._resolve_cache:
            return self._resolve_cache[term_clean]

        resolved: Dict[str, ResolvedEntity] = {}

        # 1. Resolve Acronyms
        expanded_acronym = self.ACRONYMS.get(term_clean)

        for node_id, attrs in self.graph.nodes(data=True):
            node_type = attrs.get("type", "Unknown")
            name = attrs.get("name") or attrs.get("title") or node_id
            name_clean = clean_string(name)
            node_id_clean = clean_string(node_id)
            title_clean = clean_string(attrs.get("title", ""))

            # A. Exact ID, Name, or Title match (Confidence: 1.0)
            if term_clean == node_id_clean or term_clean == name_clean or term_clean == title_clean:
                self._add_resolved(
                    resolved,
                    ResolvedEntity(
                        id=node_id,
                        name=name,
                        type=node_type,
                        confidence=1.0,
                        matched_by="exact_match"
                    )
                )
                continue

            # B. Acronym Expansion Match (Confidence: 0.98)
            if expanded_acronym:
                if expanded_acronym in node_id_clean or expanded_acronym in name_clean or expanded_acronym in title_clean:
                    self._add_resolved(
                        resolved,
                        ResolvedEntity(
                            id=node_id,
                            name=name,
                            type=node_type,
                            confidence=0.98,
                            matched_by="acronym"
                        )
                    )
                    continue

            # C. Alias Match (Confidence: 0.95)
            aliases_attr = attrs.get("aliases", "")
            if aliases_attr:
                aliases = (
                    [clean_string(a) for a in aliases_attr.split(",") if a]
                    if isinstance(aliases_attr, str)
                    else [clean_string(a) for a in aliases_attr if a]
                )
                if any(term_clean == alias or term_clean in alias for alias in aliases):
                    self._add_resolved(
                        resolved,
                        ResolvedEntity(
                            id=node_id,
                            name=name,
                            type=node_type,
                            confidence=0.95,
                            matched_by="alias"
                        )
                    )
                    continue

            # D. Token Overlap Match (Confidence: 0.90)
            term_tokens = set(term_clean.replace("_", " ").split())
            if len(term_tokens) >= 1:
                node_id_tokens = set(node_id_clean.replace("_", " ").split())
                node_name_tokens = set(name_clean.replace("_", " ").split())
                
                if term_tokens.issubset(node_id_tokens) or term_tokens.issubset(node_name_tokens):
                    self._add_resolved(
                        resolved,
                        ResolvedEntity(
                            id=node_id,
                            name=name,
                            type=node_type,
                            confidence=0.90,
                            matched_by="token_overlap"
                        )
                    )
                    continue

            # E. Fuzzy matching / Typo tolerance (Confidence: sequence similarity)
            # Mathematical pruning: if length difference > 3, SequenceMatcher ratio cannot exceed 0.8
            if abs(len(term_clean) - len(node_id_clean)) > 3 and abs(len(term_clean) - len(name_clean)) > 3:
                continue

            sim_id = SequenceMatcher(None, term_clean, node_id_clean).ratio()
            sim_name = SequenceMatcher(None, term_clean, name_clean).ratio()
            best_sim = max(sim_id, sim_name)

            if best_sim >= 0.80:
                self._add_resolved(
                    resolved,
                    ResolvedEntity(
                        id=node_id,
                        name=name,
                        type=node_type,
                        confidence=round(best_sim, 3),
                        matched_by="fuzzy"
                    )
                )

        # Filter out resolutions below the min_score and return sorted by confidence
        final_list = [r for r in resolved.values() if r.confidence >= self.min_score]
        sorted_res = sorted(final_list, key=lambda x: x.confidence, reverse=True)
        self._resolve_cache[term_clean] = sorted_res
        return sorted_res

    def resolve_many(self, terms: List[str]) -> List[ResolvedEntity]:
        """
        Resolves a list of keywords to graph nodes, deduplicating the target resolutions.
        """
        resolved_map: Dict[str, ResolvedEntity] = {}
        for term in terms:
            entities = self.resolve(term)
            for ent in entities:
                self._add_resolved(resolved_map, ent)
        return sorted(resolved_map.values(), key=lambda x: x.confidence, reverse=True)

    def _add_resolved(self, resolved_dict: Dict[str, ResolvedEntity], entity: ResolvedEntity) -> None:
        """
        Helper keeping the highest confidence resolution when multiple terms resolve to the same node.
        """
        if entity.id in resolved_dict:
            if entity.confidence > resolved_dict[entity.id].confidence:
                resolved_dict[entity.id] = entity
        else:
            resolved_dict[entity.id] = entity
