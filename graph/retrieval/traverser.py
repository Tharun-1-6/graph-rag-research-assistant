"""
traverser.py

Traverses a NetworkX graph from candidate nodes using BFS or DFS up to a configurable depth.
"""

from typing import List, Set, Tuple
import networkx as nx


class GraphTraverser:
    """
    Performs graph traversals to extract localized subgraphs of context.
    """

    def __init__(self, graph: nx.MultiDiGraph):
        self.graph = graph

    def traverse(
        self,
        seed_nodes: List[str],
        max_depth: int = 2,
        direction: str = "both",
        mode: str = "bfs",
        allowed_relationships: List[str] = None,
        max_nodes: int = None,
    ) -> nx.MultiDiGraph:
        """
        Traverses the graph starting from seed nodes using allowed relationship filtering.
        """
        if not seed_nodes:
            return nx.MultiDiGraph()

        direction = direction.lower()
        if direction not in ("outgoing", "incoming", "both"):
            direction = "both"

        mode = mode.lower()
        if mode not in ("bfs", "dfs"):
            mode = "bfs"

        allowed_rels_set = set(allowed_relationships) if allowed_relationships else None

        # 1. Run traversal with relationship restrictions
        subgraph = self._run_traversal(
            seed_nodes=seed_nodes,
            max_depth=max_depth,
            direction=direction,
            mode=mode,
            allowed_rels=allowed_rels_set,
            max_nodes=max_nodes
        )

        # 2. Fallback Mode: if we got seed nodes but absolutely zero edges, 
        # run traversal again without relationship restrictions to guarantee context.
        if allowed_rels_set and subgraph.number_of_edges() == 0:
            subgraph = self._run_traversal(
                seed_nodes=seed_nodes,
                max_depth=max_depth,
                direction=direction,
                mode=mode,
                allowed_rels=None,
                max_nodes=max_nodes
            )

        return subgraph

    HIGH_PRIORITY_RELS = {"AUTHORED", "AFFILIATED_WITH", "PROPOSES", "USES", "EVALUATED_ON"}

    def _run_traversal(
        self,
        seed_nodes: List[str],
        max_depth: int,
        direction: str,
        mode: str,
        allowed_rels: Set[str] = None,
        max_nodes: int = None,
    ) -> nx.MultiDiGraph:
        """
        Performs the BFS or DFS traversal prioritizing Paper nodes and high-priority edges.
        """
        visited: Set[str] = set(seed_nodes)
        traversed_edges: Set[Tuple[str, str]] = set()

        if mode == "bfs":
            queue = [(node, 0) for node in seed_nodes if node in self.graph]
            
            while queue:
                if max_nodes and len(visited) >= max_nodes:
                    break

                node, depth = queue.pop(0)
                if depth >= max_depth:
                    continue

                neighbors = self._get_neighbors(node, direction)
                
                # Sort neighbors by priority: 
                # Category 0: Neighbor is a Paper (traversal hub)
                # Category 1: Edge is a high-priority relationship
                # Category 2: Edge is a RELATED_TO relationship (low-priority)
                def get_priority_category(n_tuple):
                    neighbor_id, _, rel = n_tuple
                    n_type = self.graph.nodes[neighbor_id].get("type", "Unknown")
                    if n_type == "Paper":
                        return 0
                    if rel in self.HIGH_PRIORITY_RELS:
                        return 1
                    return 2

                sorted_neighbors = sorted(neighbors, key=get_priority_category)

                for neighbor, is_outgoing, rel in sorted_neighbors:
                    # Enforce relationship filtering
                    u, v = (node, neighbor) if is_outgoing else (neighbor, node)
                    if not self._is_edge_allowed(u, v, allowed_rels):
                        continue

                    # If it's a low-priority RELATED_TO edge, only expand if budget is not met
                    if get_priority_category((neighbor, is_outgoing, rel)) == 2:
                        if max_nodes and len(visited) >= max_nodes:
                            continue

                    if neighbor not in visited:
                        if max_nodes and len(visited) >= max_nodes:
                            continue
                        visited.add(neighbor)
                        queue.append((neighbor, depth + 1))
                    
                    traversed_edges.add((u, v))
        else:
            # DFS Traversal with similar priorities
            stack = [(node, 0) for node in seed_nodes if node in self.graph]
            
            while stack:
                if max_nodes and len(visited) >= max_nodes:
                    break

                node, depth = stack.pop()
                if depth >= max_depth:
                    continue

                neighbors = self._get_neighbors(node, direction)
                
                def get_priority_category(n_tuple):
                    neighbor_id, _, rel = n_tuple
                    n_type = self.graph.nodes[neighbor_id].get("type", "Unknown")
                    if n_type == "Paper":
                        return 0
                    if rel in self.HIGH_PRIORITY_RELS:
                        return 1
                    return 2

                sorted_neighbors = sorted(neighbors, key=get_priority_category)

                for neighbor, is_outgoing, rel in sorted_neighbors:
                    u, v = (node, neighbor) if is_outgoing else (neighbor, node)
                    if not self._is_edge_allowed(u, v, allowed_rels):
                        continue

                    if get_priority_category((neighbor, is_outgoing, rel)) == 2:
                        if max_nodes and len(visited) >= max_nodes:
                            continue

                    if neighbor not in visited:
                        if max_nodes and len(visited) >= max_nodes:
                            continue
                        visited.add(neighbor)
                        stack.append((neighbor, depth + 1))
                    
                    traversed_edges.add((u, v))

        return self._build_subgraph(visited, traversed_edges)

    def _is_edge_allowed(self, u: str, v: str, allowed_rels: Set[str] = None) -> bool:
        """
        Checks whether the edge (u, v) is allowed based on relationship filters.
        """
        if not allowed_rels:
            return True

        edge_data = self.graph.get_edge_data(u, v)
        if edge_data is None:
            return False

        if self.graph.is_multigraph():
            for key, data in edge_data.items():
                rel = data.get("relationship", "").upper()
                if rel in allowed_rels:
                    return True
        else:
            rel = edge_data.get("relationship", "").upper()
            if rel in allowed_rels:
                return True

        return False

    def _get_neighbors(self, node: str, direction: str) -> List[Tuple[str, bool, str]]:
        """
        Helper to fetch neighboring nodes and their relationship types based on direction.
        Returns a list of tuples: (neighbor_node_id, is_outgoing_flag, relationship_type).
        """
        neighbors = []

        # Outgoing neighbors
        if direction in ("outgoing", "both"):
            for n in self.graph.neighbors(node):
                edge_data = self.graph.get_edge_data(node, n)
                if edge_data is not None:
                    if self.graph.is_multigraph():
                        for key, data in edge_data.items():
                            rel = data.get("relationship", "RELATED_TO").upper()
                            neighbors.append((n, True, rel))
                    else:
                        rel = edge_data.get("relationship", "RELATED_TO").upper()
                        neighbors.append((n, True, rel))

        # Incoming neighbors
        if direction in ("incoming", "both") and hasattr(self.graph, "predecessors"):
            for p in self.graph.predecessors(node):
                edge_data = self.graph.get_edge_data(p, node)
                if edge_data is not None:
                    if self.graph.is_multigraph():
                        for key, data in edge_data.items():
                            rel = data.get("relationship", "RELATED_TO").upper()
                            neighbors.append((p, False, rel))
                    else:
                        rel = edge_data.get("relationship", "RELATED_TO").upper()
                        neighbors.append((p, False, rel))

        return neighbors

    def _build_subgraph(self, nodes: Set[str], edges: Set[Tuple[str, str]]) -> nx.MultiDiGraph:
        """
        Creates a NetworkX subgraph from visited nodes and edges, preserving attributes.
        """
        subgraph = nx.MultiDiGraph()

        # Add nodes with their attributes
        for node in nodes:
            if node in self.graph:
                subgraph.add_node(node, **self.graph.nodes[node])

        # Add edges with their attributes
        for u, v in edges:
            if u in subgraph and v in subgraph:
                edge_data = self.graph.get_edge_data(u, v)
                if edge_data is not None:
                    if self.graph.is_multigraph():
                        for key, data in edge_data.items():
                            subgraph.add_edge(u, v, key=key, **data)
                    else:
                        subgraph.add_edge(u, v, **edge_data)

        return subgraph
