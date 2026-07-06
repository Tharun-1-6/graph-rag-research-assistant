"""
path_search.py

Implements graph traversal strategies (bounded BFS, DFS, shortest paths, and simple paths)
to find multi-hop reasoning chains connecting seed nodes.
"""

from collections import deque
from dataclasses import dataclass
from typing import Any, Dict, List, Set, Tuple
import networkx as nx


@dataclass
class ReasoningPath:
    """
    Represents a full multi-hop reasoning path through the knowledge graph.
    """
    nodes: List[str]  # Node IDs in order: [u, v, w]
    edges: List[Dict[str, Any]]  # Edge attributes: [e_uv, e_vw]

    def to_string(self, graph: nx.MultiDiGraph) -> str:
        """
        Formats path to string representation: Node1 --[RELATIONSHIP]--> Node2
        """
        parts = []
        for i, node in enumerate(self.nodes):
            node_attrs = graph.nodes.get(node, {})
            name = node_attrs.get("name") or node_attrs.get("title") or node
            parts.append(f"{name}")
            if i < len(self.edges):
                rel = self.edges[i].get("relationship", "RELATED_TO")
                parts.append(f" --[{rel}]--> ")
        return "".join(parts)


class PathSearcher:
    """
    Executes depth-bounded and relationship-constrained path search strategies.
    """

    def __init__(self, graph: nx.MultiDiGraph):
        self.graph = graph

    def find_all_paths(
        self,
        seeds: List[str],
        max_depth: int = 3,
        allowed_relationships: List[str] = None
    ) -> List[ReasoningPath]:
        """
        Orchestrates path searches. Finds paths between seeds if multiple seeds exist,
        and expands neighborhood paths for single/all seeds.
        """
        if len(seeds) > 1:
            # Multi-seed paths (Phase 3 path discovery between nodes)
            paths = self.find_paths_between_seeds(seeds, max_depth, allowed_relationships)
            # Also expand around the seeds to collect surrounding context
            paths.extend(self.expand_neighborhood_paths(seeds, min(max_depth, 2), allowed_relationships))
            return self._deduplicate_paths(paths)
        else:
            # Single-seed lookup (expand neighborhood)
            return self.expand_neighborhood_paths(seeds, max_depth, allowed_relationships)

    def find_paths_between_seeds(
        self,
        seeds: List[str],
        max_depth: int = 3,
        allowed_relationships: List[str] = None
    ) -> List[ReasoningPath]:
        """
        Discovers paths connecting any two seed nodes (Multi-hop Path Discovery).
        """
        reasoning_paths: List[ReasoningPath] = []
        undirected = self.graph.to_undirected()

        # Find paths between every pair of seeds
        for i in range(len(seeds)):
            for j in range(i + 1, len(seeds)):
                source = seeds[i]
                target = seeds[j]
                
                if source not in self.graph or target not in self.graph:
                    continue

                try:
                    # Retrieve simple paths up to cutoff
                    simple_paths = list(nx.all_simple_paths(undirected, source, target, cutoff=max_depth))
                    for path in simple_paths:
                        # Reconstruct edge attributes from multi-digraph
                        edge_attrs_list = self._reconstruct_path_edges(path, allowed_relationships)
                        if edge_attrs_list is not None:
                            reasoning_paths.append(ReasoningPath(nodes=path, edges=edge_attrs_list))
                except Exception:
                    pass

        return reasoning_paths

    def expand_neighborhood_paths(
        self,
        seeds: List[str],
        max_depth: int = 2,
        allowed_relationships: List[str] = None
    ) -> List[ReasoningPath]:
        """
        Executes bounded BFS from seed nodes to gather local relational neighborhood paths.
        """
        reasoning_paths: List[ReasoningPath] = []
        is_multi = self.graph.is_multigraph()
        
        for seed in seeds:
            if seed not in self.graph:
                continue

            # Queue: (current_node, path_nodes, path_edges)
            queue = deque([(seed, [seed], [])])
            visited: Set[Tuple[str, ...]] = { (seed,) }

            while queue:
                curr, path_nodes, path_edges = queue.popleft()

                # Add path to results if it contains edges (is multi-hop)
                if len(path_edges) > 0:
                    reasoning_paths.append(ReasoningPath(nodes=path_nodes, edges=path_edges))

                if len(path_edges) >= max_depth:
                    continue

                # 1. Traverse outgoing edges (successors)
                for succ in self.graph.successors(curr):
                    edge_data = self.graph.get_edge_data(curr, succ)
                    if edge_data is not None:
                        attrs_list = list(edge_data.values()) if is_multi else [edge_data]
                        for data in attrs_list:
                            if allowed_relationships and data.get("relationship") not in allowed_relationships:
                                continue
                            new_path = tuple(path_nodes + [succ])
                            if new_path not in visited:
                                visited.add(new_path)
                                data_copy = dict(data)
                                data_copy["source"] = curr
                                data_copy["target"] = succ
                                queue.append((succ, list(new_path), path_edges + [data_copy]))

                # 2. Traverse incoming edges (predecessors)
                for pred in self.graph.predecessors(curr):
                    edge_data = self.graph.get_edge_data(pred, curr)
                    if edge_data is not None:
                        attrs_list = list(edge_data.values()) if is_multi else [edge_data]
                        for data in attrs_list:
                            if allowed_relationships and data.get("relationship") not in allowed_relationships:
                                continue
                            new_path = tuple(path_nodes + [pred])
                            if new_path not in visited:
                                visited.add(new_path)
                                data_copy = dict(data)
                                data_copy["source"] = pred
                                data_copy["target"] = curr
                                queue.append((pred, list(new_path), path_edges + [data_copy]))

        return reasoning_paths

    def _reconstruct_path_edges(
        self,
        path: List[str],
        allowed_relationships: List[str] = None
    ) -> List[Dict[str, Any]] | None:
        """
        Helper extracting matching edge attributes for a sequence of path nodes.
        """
        edges: List[Dict[str, Any]] = []
        is_multi = self.graph.is_multigraph()

        for idx in range(len(path) - 1):
            u = path[idx]
            v = path[idx + 1]
            
            # Check both directions
            edge_data = None
            source_dir, target_dir = u, v
            if self.graph.has_edge(u, v):
                edge_data = self.graph.get_edge_data(u, v)
                source_dir, target_dir = u, v
            elif self.graph.has_edge(v, u):
                edge_data = self.graph.get_edge_data(v, u)
                source_dir, target_dir = v, u

            if edge_data is None:
                return None
                
            attrs_list = list(edge_data.values()) if is_multi else [edge_data]
            chosen_data = None
            for data in attrs_list:
                if allowed_relationships is None or data.get("relationship") in allowed_relationships:
                    chosen_data = dict(data)
                    chosen_data["source"] = source_dir
                    chosen_data["target"] = target_dir
                    break
            
            if chosen_data is None:
                return None
                
            edges.append(chosen_data)
            
        return edges

    def _deduplicate_paths(self, paths: List[ReasoningPath]) -> List[ReasoningPath]:
        """
        Deduplicates reasoning paths that visit the same sequence of nodes.
        """
        seen = set()
        deduped = []
        for path in paths:
            path_key = tuple(path.nodes)
            if path_key not in seen:
                seen.add(path_key)
                deduped.append(path)
        return deduped
