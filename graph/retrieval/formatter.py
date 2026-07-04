"""
formatter.py

Formats a ranked subgraph of context into a deterministic markdown context string ready for LLM consumption.
"""

from collections import defaultdict
import math
from typing import Dict, List, Tuple, Set
import networkx as nx


class ContextFormatter:
    """
    Transforms a ranked NetworkX subgraph into a structured, intent-aware markdown string.
    """

    # Section types permitted for each query intent (Upgrade 8)
    INTENT_ALLOWED_SECTIONS: Dict[str, Set[str]] = {
        "AUTHOR_QUERY": {"Paper", "Author", "Institution"},
        "METHOD_QUERY": {"Paper", "Method", "Architecture"},
        "DATASET_QUERY": {"Dataset", "Benchmark", "Paper"},
        "BENCHMARK_QUERY": {"Benchmark", "Dataset", "Paper"},
        "METRIC_QUERY": {"Metric", "Benchmark", "Method", "Paper"},
        "TASK_QUERY": {"Task", "Method", "Dataset", "Paper"},
        "EXPLANATION_QUERY": {"Method", "Architecture", "Topic", "Paper"},
        "COMPARISON_QUERY": {"Method", "Architecture", "Topic"},
        "INSTITUTION_QUERY": {"Institution", "Author", "Paper"},
    }

    # Diversity budgets (Upgrade 10) - percentage of total node budget allowed per type
    DIVERSITY_BUDGETS: Dict[str, float] = {
        "Method": 0.40,
        "Architecture": 0.40,
        "Author": 0.20,
        "Dataset": 0.20,
        "Paper": 0.20,
        "Benchmark": 0.10,
        "Institution": 0.10,
        "Metric": 0.10,
        "Topic": 0.10,
        "Task": 0.10,
    }

    def format(
        self,
        subgraph: nx.MultiDiGraph,
        ranked_nodes: List[Tuple[str, float]],
        node_paths: Dict[str, Tuple[float, List[Tuple[str, str, str]]]] = None,
        intent: str = "GENERAL_QUERY",
        max_nodes: int = 15,
        max_edges: int = 25,
        max_characters: int = 4000,
        min_score: float = 0.25,
        show_evidence: bool = False,
    ) -> str:
        """
        Formats a subgraph into a deterministic, budget-trimmed context string.
        """
        if not subgraph or len(subgraph) == 0:
            return "No relevant context found in the knowledge graph."

        # Filter out nodes below the minimum relevance score threshold
        filtered_ranked = [(node_id, score) for node_id, score in ranked_nodes if score >= min_score]
        
        # Upgrade 10: Apportion node budget by category (Diversity Capping)
        top_nodes_ids = []
        type_counts = defaultdict(int)
        
        for node_id, score in filtered_ranked:
            if len(top_nodes_ids) >= max_nodes:
                break
                
            if node_id in subgraph:
                node_type = subgraph.nodes[node_id].get("type", "Unknown")
                pct = self.DIVERSITY_BUDGETS.get(node_type, 0.20)
                type_max = max(1, math.ceil(max_nodes * pct))
                
                if type_counts[node_type] < type_max:
                    top_nodes_ids.append(node_id)
                    type_counts[node_type] += 1
                
        top_nodes_set = set(top_nodes_ids)

        if not top_nodes_ids:
            return "No relevant context found in the knowledge graph."

        # Group nodes by type
        nodes_by_type = defaultdict(list)
        for node_id in top_nodes_ids:
            if node_id in subgraph:
                attrs = subgraph.nodes[node_id]
                node_type = attrs.get("type", "Unknown")
                nodes_by_type[node_type].append((node_id, attrs))

        context_parts = []
        char_count = 0

        # Strict ordering of sections
        ordered_sections = [
            ("Paper", "Papers"),
            ("Author", "Authors"),
            ("Method", "Methods"),
            ("Architecture", "Architectures"),
            ("Dataset", "Datasets"),
            ("Benchmark", "Benchmarks"),
            ("Task", "Tasks"),
            ("Institution", "Institutions"),
            ("Metric", "Metrics"),
            ("Topic", "Topics"),
        ]

        known_types = set([t for t, _ in ordered_sections])
        all_sections_to_process = list(ordered_sections)
        
        # Capture any custom types
        remaining_types = sorted([t for t in nodes_by_type.keys() if t not in known_types])
        for r_type in remaining_types:
            all_sections_to_process.append((r_type, f"{r_type}s"))

        # Upgrade 8: Filter allowed sections based on intent (default: all if GENERAL_QUERY)
        allowed_sections = self.INTENT_ALLOWED_SECTIONS.get(intent, None)

        # Format Nodes by Type
        for node_type, section_header in all_sections_to_process:
            # Skip if not allowed for this intent
            if allowed_sections is not None and node_type not in allowed_sections:
                continue

            if node_type not in nodes_by_type:
                continue

            nodes_list = nodes_by_type[node_type]
            
            # Sort items inside sections alphabetically
            sorted_nodes = sorted(
                nodes_list, 
                key=lambda x: (x[1].get("name") or x[1].get("title") or x[0]).lower()
            )

            section_lines = [f"### {section_header}"]
            for node_id, attrs in sorted_nodes:
                name = attrs.get("name") or attrs.get("title") or node_id
                
                details = []
                if node_type == "Paper":
                    year = attrs.get("year")
                    conf = attrs.get("conference")
                    if year:
                        details.append(f"Year: {year}")
                    if conf:
                        details.append(f"Conference: {conf}")
                
                desc = attrs.get("description") or attrs.get("abstract")
                desc_str = f" - {desc}" if desc else ""
                details_str = f" ({', '.join(details)})" if details else ""
                
                # Upgrade 9: Evidence-Based Debug Output (show paths, score, etc.)
                evidence_str = ""
                if show_evidence and node_paths and node_id in node_paths:
                    p_score, p_edges = node_paths[node_id]
                    p_depth = len(p_edges)
                    
                    path_chain = ""
                    if p_edges:
                        steps = []
                        steps.append(p_edges[0][0])
                        for u, rel, v in p_edges:
                            steps.append(f"--[{rel}]--> {v}")
                        path_chain = " ".join(steps)
                    else:
                        path_chain = node_id
                        
                    evidence_str = f"\n  [Score: {p_score:.2f} | Depth: {p_depth} | Path: {path_chain}]"

                section_lines.append(f"- **{name}**{details_str}{desc_str}{evidence_str}")

            section_str = "\n".join(section_lines) + "\n\n"
            
            # Verify character budget
            if char_count + len(section_str) <= max_characters:
                context_parts.append(section_str)
                char_count += len(section_str)
            else:
                # Truncate section item-by-item
                header_line = f"### {section_header}\n"
                if char_count + len(header_line) <= max_characters:
                    context_parts.append(header_line)
                    char_count += len(header_line)
                    for item_line in section_lines[1:]:
                        full_item_line = item_line + "\n"
                        if char_count + len(full_item_line) <= max_characters:
                            context_parts.append(full_item_line)
                            char_count += len(full_item_line)
                        else:
                            break
                    context_parts.append("\n")
                    char_count += 1
                break

        # 3. Format Relationships (Edges) Deterministically
        relationships = []
        for u, v, data in subgraph.edges(data=True):
            if u in top_nodes_set and v in top_nodes_set:
                rel_type = data.get("relationship", "RELATED_TO")
                u_attrs = subgraph.nodes[u]
                v_attrs = subgraph.nodes[v]
                u_name = u_attrs.get("name") or u_attrs.get("title") or u
                v_name = v_attrs.get("name") or v_attrs.get("title") or v
                relationships.append((u_name, rel_type, v_name))

        unique_relationships = sorted(
            list(set(relationships)), 
            key=lambda x: (x[0].lower(), x[1].lower(), x[2].lower())
        )

        if unique_relationships:
            limited_rels = unique_relationships[:max_edges]
            rel_header = "### Relationships\n"
            
            if char_count + len(rel_header) <= max_characters:
                rel_lines = []
                rel_char_count = len(rel_header)
                
                for u_name, rel_type, v_name in limited_rels:
                    line = f"- **{u_name}** --[{rel_type}]--> **{v_name}**\n"
                    if char_count + rel_char_count + len(line) <= max_characters:
                        rel_lines.append(line)
                        rel_char_count += len(line)
                    else:
                        break
                        
                if rel_lines:
                    context_parts.append(rel_header + "".join(rel_lines))

        return "".join(context_parts).strip()
