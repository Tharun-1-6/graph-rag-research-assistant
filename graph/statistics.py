"""
statistics.py

Computes and serializes comprehensive graph analysis statistics for the global GraphRAG knowledge base.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Union
import networkx as nx

logger = logging.getLogger(__name__)


def generate_graph_statistics(
    graph: nx.MultiDiGraph,
    output_path: Union[str, Path] = None
) -> Dict[str, Any]:
    """
    Analyzes the knowledge graph and computes structural metrics.

    Parameters
    ----------
    graph : nx.MultiDiGraph
        The NetworkX knowledge graph.
    output_path : Union[str, Path], optional
        The path to save the statistics as JSON.

    Returns
    -------
    Dict[str, Any]
        A dictionary containing the calculated graph metrics.
    """
    total_nodes = graph.number_of_nodes()
    total_edges = graph.number_of_edges()

    # 1. Group nodes by type
    nodes_by_type = {}
    papers_count = 0
    entities_count = 0
    
    for node, data in graph.nodes(data=True):
        node_type = data.get("type", "Unknown")
        nodes_by_type[node_type] = nodes_by_type.get(node_type, 0) + 1
        if node_type == "Paper":
            papers_count += 1
        else:
            entities_count += 1

    # 2. Group edges by relationship
    edges_by_relationship = {}
    for u, v, data in graph.edges(data=True):
        rel = data.get("relationship", "Unknown")
        edges_by_relationship[rel] = edges_by_relationship.get(rel, 0) + 1

    # 3. Find most connected authors & methods
    author_degrees = []
    method_degrees = []
    
    for node, data in graph.nodes(data=True):
        node_type = data.get("type", "")
        degree = graph.degree(node)
        name = data.get("name") or data.get("title") or node
        
        if node_type == "Author":
            author_degrees.append({"id": node, "name": name, "degree": degree})
        elif node_type == "Method":
            method_degrees.append({"id": node, "name": name, "degree": degree})

    most_connected_authors = sorted(author_degrees, key=lambda x: x["degree"], reverse=True)[:10]
    most_connected_methods = sorted(method_degrees, key=lambda x: x["degree"], reverse=True)[:10]

    # 4. Connect component metrics (using undirected representation)
    undirected = graph.to_undirected()
    components = list(nx.connected_components(undirected)) if total_nodes > 0 else []
    num_components = len(components)

    if components:
        lcc = max(components, key=len)
        lcc_size = len(lcc)
        # Average path length of the largest connected component to avoid division by zero / infinite distance
        lcc_subgraph = undirected.subgraph(lcc)
        if len(lcc) > 1:
            avg_path_length = nx.average_shortest_path_length(lcc_subgraph)
        else:
            avg_path_length = 0.0
    else:
        lcc_size = 0
        avg_path_length = 0.0

    # 5. Density and average degree
    density = nx.density(graph) if total_nodes > 0 else 0.0
    avg_degree = sum(dict(graph.degree()).values()) / max(1, total_nodes)

    stats = {
        "summary": {
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "number_of_papers": papers_count,
            "number_of_entities": entities_count,
            "density": round(density, 6),
            "average_degree": round(avg_degree, 2),
        },
        "nodes_by_type": nodes_by_type,
        "edges_by_relationship": edges_by_relationship,
        "connected_components": {
            "count": num_components,
            "largest_connected_component_size": lcc_size,
            "average_path_length_lcc": round(avg_path_length, 4),
        },
        "most_connected_authors": most_connected_authors,
        "most_connected_methods": most_connected_methods,
    }

    # Save to file if output path is provided
    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(stats, f, indent=4, ensure_ascii=False)
            logger.info(f"Statistics successfully written to {path}")
        except Exception as e:
            logger.error(f"Failed to write statistics to {path}: {e}")

    return stats
