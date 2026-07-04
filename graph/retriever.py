"""
retriever.py

Retrieves relational context from a NetworkX knowledge graph.
"""

from pathlib import Path
import re
from typing import Dict, List, Set, Tuple

import networkx as nx

from graph.graph_builder.serializer import GraphSerializer


class GraphRetriever:
    """
    Handles graph-based retrieval of relational context from a knowledge graph.
    """

    def __init__(self, graph_path_or_dir: str | Path):
        """
        Loads the graph from either a direct file path or a directory containing a graph.
        """
        path = Path(graph_path_or_dir)
        self.graph = nx.MultiDiGraph()

        if path.is_dir():
            # Try to load default graphml or json
            graphml_files = list(path.glob("*.graphml"))
            json_files = list(path.glob("*.json"))
            if graphml_files:
                self.graph = nx.read_graphml(graphml_files[0])
            elif json_files:
                self.graph = GraphSerializer.load(json_files[0])
            else:
                raise FileNotFoundError(f"No graph files found in directory {path}")
        else:
            if path.suffix == ".graphml":
                self.graph = nx.read_graphml(path)
            elif path.suffix == ".json":
                self.graph = GraphSerializer.load(path)
            else:
                raise ValueError(f"Unsupported graph file format: {path.suffix}")

    def retrieve_relational_context(self, query: str, top_n: int = 5) -> str:
        """
        Extracts entities from the query, finds matching nodes,
        gathers their relational context (neighbors and edges), and formats it as markdown.
        """
        # 1. Extract keywords from the query
        keywords = self._extract_keywords(query)
        if not keywords:
            return "No relational context found."

        # 2. Find matching nodes
        matched_nodes = self._find_matching_nodes(keywords, top_n)
        if not matched_nodes:
            return "No matching entities found in the knowledge graph."

        # 3. Retrieve node descriptions and edges
        context_parts = []
        context_parts.append("### Relevant Entities")
        
        visited_nodes = set()
        edges_to_format = []

        for node_id, score in matched_nodes:
            if node_id not in self.graph:
                continue
            attrs = self.graph.nodes[node_id]
            node_type = attrs.get("type", "Unknown")
            name = attrs.get("name") or attrs.get("title") or node_id
            description = attrs.get("description") or attrs.get("abstract") or "No description available."
            
            visited_nodes.add(node_id)
            context_parts.append(f"- **{name}** (Type: {node_type}): {description}")

            # Retrieve outgoing edges for this node
            if node_id in self.graph:
                for neighbor in self.graph.neighbors(node_id):
                    edge_data = self.graph.get_edge_data(node_id, neighbor)
                    if edge_data is not None:
                        if self.graph.is_multigraph():
                            for key, data in edge_data.items():
                                edges_to_format.append((node_id, neighbor, data))
                        else:
                            edges_to_format.append((node_id, neighbor, edge_data))
            
            # Retrieve incoming edges for this node
            if node_id in self.graph and hasattr(self.graph, "predecessors"):
                for predecessor in self.graph.predecessors(node_id):
                    edge_data = self.graph.get_edge_data(predecessor, node_id)
                    if edge_data is not None:
                        if self.graph.is_multigraph():
                            for key, data in edge_data.items():
                                edges_to_format.append((predecessor, node_id, data))
                        else:
                            edges_to_format.append((predecessor, node_id, edge_data))

        # Deduplicate and format relationships
        unique_edges = {}
        for u, v, data in edges_to_format:
            rel_type = data.get("relationship", "RELATED_TO")
            edge_key = (u, rel_type, v)
            unique_edges[edge_key] = data

        if unique_edges:
            context_parts.append("\n### Relational Context (Entity Connections)")
            for (u, rel_type, v), data in unique_edges.items():
                u_attrs = self.graph.nodes.get(u, {})
                v_attrs = self.graph.nodes.get(v, {})
                
                u_name = u_attrs.get("name") or u_attrs.get("title") or u
                v_name = v_attrs.get("name") or v_attrs.get("title") or v
                
                context_parts.append(f"- **{u_name}** --[{rel_type}]--> **{v_name}**")

        return "\n".join(context_parts)

    def _extract_keywords(self, query: str) -> List[str]:
        """
        Tokenizes the query and extracts unique, meaningful keywords.
        """
        # Convert to lowercase and find words
        words = re.findall(r"\b\w{3,}\b", query.lower())
        
        # Simple stop words filter
        stop_words = {
            "what", "how", "why", "who", "where", "when", "which",
            "the", "and", "for", "with", "from", "that", "this",
            "these", "those", "are", "was", "were", "been", "have",
            "has", "had", "can", "could", "should", "would", "about",
            "model", "paper", "graph", "retrieve", "context"
        }
        
        keywords = []
        for word in words:
            if word in stop_words:
                continue
            keywords.append(word)
            # Simple stemming: if plural, add singular; if singular, add plural version
            if word.endswith("s") and len(word) > 3:
                if word.endswith("es"):
                    keywords.append(word[:-2])
                keywords.append(word[:-1])
            elif not word.endswith("s"):
                keywords.append(word + "s")
                
        return list(set(keywords))

    def _find_matching_nodes(self, keywords: List[str], top_n: int) -> List[Tuple[str, int]]:
        """
        Searches nodes in the graph for keyword matches and returns the top scoring nodes.
        """
        node_scores = {}

        # 1. Match against node attributes
        for node_id, attrs in self.graph.nodes(data=True):
            score = 0
            
            # Fields to search
            search_fields = [
                node_id.lower(),
                attrs.get("name", "").lower(),
                attrs.get("title", "").lower(),
                attrs.get("description", "").lower(),
                attrs.get("abstract", "").lower(),
                attrs.get("type", "").lower()
            ]

            for keyword in keywords:
                for field in search_fields:
                    if keyword in field:
                        # Give higher weight to matches in node ID, name, or title
                        if field == search_fields[0] or field == search_fields[1] or field == search_fields[2]:
                            score += 5
                        else:
                            score += 1

            if score > 0:
                node_scores[node_id] = score

        # 2. Match against relationship types (e.g. query "propose" matches relationship PROPOSES)
        for u, v, data in self.graph.edges(data=True):
            rel_type = data.get("relationship", "").lower()
            for keyword in keywords:
                # If keyword matches the relationship type, score the endpoints
                if keyword in rel_type or rel_type in keyword:
                    node_scores[u] = node_scores.get(u, 0) + 4
                    node_scores[v] = node_scores.get(v, 0) + 4

        # Sort by score descending
        sorted_nodes = sorted(node_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_nodes[:top_n]
