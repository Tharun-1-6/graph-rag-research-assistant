"""
matcher.py

Matches query terms against knowledge graph nodes using exact, substring, and fuzzy matching.
"""

from typing import Dict, List
import networkx as nx

from .query_parser import ParsedQuery
from .utils import clean_string, string_similarity


class NodeMatcher:
    """
    Locates candidate nodes matching query entities and keywords, returning match scores.
    """

    # Seed node type mappings allowed by query intent
    INTENT_SEED_TYPES = {
        "AUTHOR_QUERY": {"Author", "Paper", "Institution"},
        "METHOD_QUERY": {"Method", "Architecture", "Paper"},
        "DATASET_QUERY": {"Dataset", "Benchmark", "Paper"},
        "BENCHMARK_QUERY": {"Benchmark", "Dataset", "Paper"},
        "EXPLANATION_QUERY": {"Method", "Architecture", "Topic", "Paper"},
        "COMPARISON_QUERY": {"Method", "Architecture"},
        "INSTITUTION_QUERY": {"Institution", "Author", "Paper"},
        "METRIC_QUERY": {"Metric", "Benchmark", "Method", "Paper"},
        "TASK_QUERY": {"Task", "Method", "Dataset", "Paper"},
    }

    def __init__(self, graph: nx.MultiDiGraph, min_score: float = 0.3):
        self.graph = graph
        self.min_score = min_score

    def match(self, parsed_query: ParsedQuery) -> Dict[str, float]:
        """
        Scans graph nodes hierarchically and filters by intent-allowed seed types.
        """
        matched_nodes: Dict[str, float] = {}

        # Combine all match search targets from query
        targets = []
        targets.extend(parsed_query.entities)
        targets.extend(parsed_query.keywords)
        targets.extend(parsed_query.noun_phrases)
        targets = list(set([clean_string(t) for t in targets if t]))

        if not targets:
            return matched_nodes

        # Upgrade 2: Pre-filter graph nodes by type based on intent
        allowed_types = self.INTENT_SEED_TYPES.get(parsed_query.intent, None)
        filtered_graph_nodes = []
        for node_id, attrs in self.graph.nodes(data=True):
            node_type = attrs.get("type", "Unknown")
            if allowed_types is not None and node_type not in allowed_types:
                continue
            filtered_graph_nodes.append((node_id, attrs))

        # Upgrade 1: Hierarchical matching checking each target individually
        for target in targets:
            target_matches: Dict[str, float] = {}
            
            # Level 1 & 2: Exact ID, Name/Title, or Type match (Score: 1.0)
            for node_id, attrs in filtered_graph_nodes:
                node_id_clean = clean_string(node_id)
                node_name_clean = clean_string(attrs.get("name", ""))
                node_title_clean = clean_string(attrs.get("title", ""))
                node_type_clean = clean_string(attrs.get("type", ""))
                
                if (target == node_id_clean or 
                    target == node_name_clean or 
                    target == node_title_clean or 
                    (target == node_type_clean and node_type_clean in {"benchmark", "dataset", "metric", "task", "author", "institution"})):
                    target_matches[node_id] = 1.0
                    
            if target_matches:
                # Exact matches found - STOP searching lower-confidence levels for this target
                for nid, sc in target_matches.items():
                    matched_nodes[nid] = max(matched_nodes.get(nid, 0.0), sc)
                continue

            # Level 3: Alias Match (Score: 0.95)
            target_tokens = set(target.split())
            for node_id, attrs in filtered_graph_nodes:
                aliases_attr = attrs.get("aliases", "")
                if aliases_attr:
                    if isinstance(aliases_attr, str):
                        aliases = [clean_string(a) for a in aliases_attr.split(",") if a]
                    else:
                        aliases = [clean_string(a) for a in aliases_attr if a]
                        
                    for alias in aliases:
                        alias_tokens = set(alias.split())
                        if target == alias or (target_tokens and target_tokens.issubset(alias_tokens)):
                            target_matches[node_id] = 0.95
                        
            if target_matches:
                for nid, sc in target_matches.items():
                    matched_nodes[nid] = max(matched_nodes.get(nid, 0.0), sc)
                continue

            # Level 4: Exact Token Overlap (Score: 0.90)
            target_tokens = set(target.replace("_", " ").split())
            if len(target_tokens) >= 1:
                for node_id, attrs in filtered_graph_nodes:
                    node_id_clean = clean_string(node_id)
                    node_name_clean = clean_string(attrs.get("name", ""))
                    node_title_clean = clean_string(attrs.get("title", ""))
                    
                    node_id_tokens = set(node_id_clean.replace("_", " ").split())
                    node_name_tokens = set(node_name_clean.replace("_", " ").split())
                    node_title_tokens = set(node_title_clean.replace("_", " ").split())
                    
                    if (target_tokens.issubset(node_id_tokens) or 
                        target_tokens.issubset(node_name_tokens) or 
                        target_tokens.issubset(node_title_tokens)):
                        target_matches[node_id] = 0.90
                        
            if target_matches:
                for nid, sc in target_matches.items():
                    matched_nodes[nid] = max(matched_nodes.get(nid, 0.0), sc)
                continue

            # Level 5: High-Confidence Fuzzy Match (Score: SequenceMatcher ratio > 0.90)
            for node_id, attrs in filtered_graph_nodes:
                node_id_clean = clean_string(node_id)
                node_name_clean = clean_string(attrs.get("name", ""))
                node_title_clean = clean_string(attrs.get("title", ""))
                
                for term in [node_id_clean, node_name_clean, node_title_clean]:
                    if not term:
                        continue
                    sim = string_similarity(target, term)
                    if sim > 0.90:
                        target_matches[node_id] = sim
                        
            if target_matches:
                for nid, sc in target_matches.items():
                    matched_nodes[nid] = max(matched_nodes.get(nid, 0.0), sc)

        # Filter by min_score
        final_matched = {nid: sc for nid, sc in matched_nodes.items() if sc >= self.min_score}
        return final_matched
