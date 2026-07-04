"""
ranker.py

Ranks nodes and edges in a traversed subgraph using semantic, structural, and schema heuristics.
"""

from typing import Dict, List, Set, Tuple
import networkx as nx


class NodeRanker:
    """
    Ranks nodes in a traversed subgraph using a combination of match score,
    type priorities, distance decay, and verb boosts.
    """

    NODE_PRIORITIES: Dict[str, float] = {
        "Paper": 1.0,
        "Method": 1.0,
        "Architecture": 1.0,
        
        "Dataset": 0.8,
        "Benchmark": 0.8,
        
        "Author": 0.7,
        "Topic": 0.7,
        
        "Metric": 0.5,
        "Institution": 0.5,
    }

    # Type priorities dynamically mapped by query intent
    INTENT_PRIORITIES: Dict[str, Dict[str, float]] = {
        "AUTHOR_QUERY": {"Author": 1.0, "Paper": 0.9, "Institution": 0.8},
        "METHOD_QUERY": {"Method": 1.0, "Architecture": 1.0, "Paper": 0.8, "Dataset": 0.7, "Topic": 0.7},
        "DATASET_QUERY": {"Dataset": 1.0, "Benchmark": 0.9, "Paper": 0.8},
        "BENCHMARK_QUERY": {"Benchmark": 1.0, "Dataset": 0.9, "Paper": 0.8},
        "EXPLANATION_QUERY": {"Method": 1.0, "Topic": 0.9, "Paper": 0.8, "Architecture": 0.8},
        "COMPARISON_QUERY": {"Method": 1.0, "Architecture": 1.0, "Topic": 0.8},
        "INSTITUTION_QUERY": {"Institution": 1.0, "Author": 0.9, "Paper": 0.7},
        "METRIC_QUERY": {"Metric": 1.0, "Benchmark": 0.8, "Method": 0.7},
        "TASK_QUERY": {"Task": 1.0, "Method": 0.8, "Dataset": 0.7},
    }

    HIGH_PRIORITY_RELS = {"AUTHORED", "AFFILIATED_WITH", "PROPOSES", "USES", "EVALUATED_ON"}

    def __init__(self, node_priorities: Dict[str, float] = None, intent_priorities: Dict[str, Dict[str, float]] = None):
        if node_priorities:
            self.NODE_PRIORITIES = {**self.NODE_PRIORITIES, **node_priorities}
        if intent_priorities:
            self.INTENT_PRIORITIES = {**self.INTENT_PRIORITIES, **intent_priorities}

    def rank(
        self,
        subgraph: nx.MultiDiGraph,
        seed_scores: Dict[str, float],
        query_verbs: List[str],
        query_entities: List[str] = None,
        intent: str = "GENERAL_QUERY",
    ) -> Tuple[List[Tuple[str, float]], Dict[str, Tuple[float, List[Tuple[str, str, str]]]]]:
        """
        Ranks nodes in the traversed subgraph based on relationship paths.

        Returns
        -------
        ranked_nodes : List[Tuple[str, float]]
            List of (node_id, score) sorted descending.
        node_paths : Dict[str, Tuple[float, List[Tuple[str, str, str]]]]
            Mapping of node_id -> (path_score, path_edges_list).
        """
        if not subgraph or len(subgraph) == 0:
            return [], {}

        query_entities = query_entities or []
        query_verbs_upper = [v.upper() for v in query_verbs]

        seed_nodes = [node for node, score in seed_scores.items() if score > 0.0]
        if not seed_nodes:
            seed_nodes = list(subgraph.nodes())

        undirected_sub = subgraph.to_undirected()
        max_deg = max([deg for _, deg in subgraph.degree()]) if len(subgraph) > 0 else 1

        # Upgrade 6: Relationship Chain Ranking & Path Tracking
        node_paths: Dict[str, Tuple[float, List[Tuple[str, str, str]]]] = {}

        for node in subgraph.nodes():
            best_score = 0.0
            best_edges = []

            for seed in seed_nodes:
                if seed in undirected_sub and node in undirected_sub:
                    try:
                        # Find the shortest path nodes
                        path_nodes = nx.shortest_path(undirected_sub, source=seed, target=node)
                        
                        # Format edge transitions
                        path_edges = []
                        edge_score_sum = 0.0
                        for i in range(len(path_nodes) - 1):
                            u, v = path_nodes[i], path_nodes[i+1]
                            edge_data = subgraph.get_edge_data(u, v)
                            rel = "RELATED_TO"
                            if edge_data is not None:
                                if subgraph.is_multigraph():
                                    for key, data in edge_data.items():
                                        rel = data.get("relationship", "RELATED_TO")
                                        break
                                else:
                                    rel = edge_data.get("relationship", "RELATED_TO")
                            
                            path_edges.append((u, rel, v))
                            
                            if rel.upper() in self.HIGH_PRIORITY_RELS:
                                edge_score_sum += 10.0
                            else:
                                edge_score_sum += 2.0

                        path_len = len(path_nodes) - 1
                        dist_penalty = 5.0 * path_len
                        avg_edge_score = (edge_score_sum / path_len) if path_len > 0 else 0.0

                        # Calculate individual features
                        node_attrs = subgraph.nodes[node]
                        node_name_clean = (node_attrs.get("name") or node_attrs.get("title") or node).lower().strip()
                        node_id_clean = node.lower().strip()
                        
                        # 1. Exact Match (Weight: 40)
                        exact_match = False
                        for ent in query_entities:
                            ent_clean = ent.lower().strip()
                            if ent_clean == node_name_clean or ent_clean == node_id_clean:
                                exact_match = True
                                break
                        exact_score = 40.0 if exact_match else 0.0

                        # 2. Node Type Priority based on Intent (Weight: 15)
                        node_type = node_attrs.get("type", "Unknown")
                        intent_dict = self.INTENT_PRIORITIES.get(intent, {})
                        priority = intent_dict.get(node_type, self.NODE_PRIORITIES.get(node_type, 0.5))
                        type_score = 15.0 * priority

                        # 3. Matcher Confidence of Seed (Weight: 5)
                        seed_match_score = seed_scores.get(seed, 0.0)
                        conf_score = 5.0 * seed_match_score

                        # 4. Centrality (Weight: 5)
                        node_deg = subgraph.degree(node) if node in subgraph else 0
                        centrality_score = 5.0 * (node_deg / max(1, max_deg))

                        # Sum with edge score boost and path length penalty
                        total_score = exact_score + type_score + avg_edge_score + conf_score + centrality_score - dist_penalty
                        normalized_score = max(0.0, min(total_score, 100.0)) / 100.0

                        # Upgrade 5: Duplicate Path Elimination (keep only the highest scoring path)
                        if normalized_score >= best_score:
                            best_score = normalized_score
                            best_edges = path_edges

                    except (nx.NetworkXNoPath, nx.NodeNotFound):
                        pass

            node_paths[node] = (best_score, best_edges)

        # Upgrade 11: Graph Connected Component Detection & Pruning
        # Keep only the component with the highest cumulative node score, unless it is COMPARISON_QUERY.
        if intent != "COMPARISON_QUERY" and len(undirected_sub) > 0:
            components = list(nx.connected_components(undirected_sub))
            if len(components) > 1:
                best_component = None
                best_comp_score = -1.0
                
                for comp in components:
                    comp_score = sum(node_paths[node][0] for node in comp if node in node_paths)
                    if comp_score > best_comp_score:
                        best_comp_score = comp_score
                        best_component = comp
                        
                if best_component:
                    # Drop nodes from other components
                    for node in list(subgraph.nodes()):
                        if node not in best_component:
                            # Prune from rankings and paths
                            node_paths[node] = (0.0, [])

        # Format ranked nodes list
        ranked_nodes = []
        for node, (score, _) in node_paths.items():
            if score > 0.0:
                ranked_nodes.append((node, score))
            else:
                ranked_nodes.append((node, 0.0))

        # Sort descending
        ranked_nodes = sorted(ranked_nodes, key=lambda x: x[1], reverse=True)
        return ranked_nodes, node_paths
