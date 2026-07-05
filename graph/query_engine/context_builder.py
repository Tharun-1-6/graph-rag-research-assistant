"""
context_builder.py

Aggregates retrieved reasoning paths, entities, relationships, papers,
and citation structures into a unified, structured GraphContext object.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Set
import networkx as nx

from .path_ranker import RankedPath


@dataclass
class GraphContext:
    """
    Structured context compiled from query engine execution.
    """
    entities: List[Dict[str, Any]] = field(default_factory=list)
    paths: List[RankedPath] = field(default_factory=list)
    relationships: List[Dict[str, Any]] = field(default_factory=list)
    papers: List[Dict[str, Any]] = field(default_factory=list)
    citations: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 1.0

    def to_markdown(self) -> str:
        """
        Compiles the structured attributes into a clean, markdown context format.
        """
        if not self.paths and not self.entities:
            return "No relevant context found in the knowledge graph."

        markdown = []

        # 1. Cited Papers Bibliography
        if self.papers:
            markdown.append("### Source Papers & Bibliography")
            for i, p in enumerate(self.papers, 1):
                title = p.get("title", "Unknown Title")
                year = p.get("year", "N/A")
                conf = p.get("conference", "N/A")
                markdown.append(f"- **[{i}]** *\"{title}\"*, Published in {conf} ({year}). ID: {p['id']}")
            markdown.append("")

        # 2. Key Entities
        if self.entities:
            markdown.append("### Relevant Entities")
            # Group by type
            by_type = {}
            for ent in self.entities:
                etype = ent.get("type", "Unknown")
                by_type.setdefault(etype, []).append(ent)
            
            for etype, ents in sorted(by_type.items()):
                markdown.append(f"#### {etype}s")
                for e in ents:
                    desc = e.get("description") or e.get("abstract") or "No description available."
                    paper_cnt = e.get("paper_count", 1)
                    markdown.append(f"- **{e['name']}**: {desc} (Papers linked: {paper_cnt})")
            markdown.append("")

        # 3. Active Reasoning Paths
        if self.paths:
            markdown.append("### Reasoning Chains")
            for p in self.paths:
                markdown.append(f"- [Score: {p.score:.3f} | {p.reason}] {p.path_str}")
            markdown.append("")

        # 4. Connection Details
        if self.relationships:
            markdown.append("### Direct Entity Connections")
            seen = set()
            for rel in self.relationships:
                u = rel.get("source_name") or rel["source"]
                v = rel.get("target_name") or rel["target"]
                rtype = rel["relationship"]
                rel_str = f"**{u}** --[{rtype}]--> **{v}**"
                if rel_str not in seen:
                    seen.add(rel_str)
                    markdown.append(f"- {rel_str}")
            markdown.append("")

        return "\n".join(markdown)

    def to_dict(self, query: str, query_type: str = "") -> Dict[str, Any]:
        """
        Serializes context into the stable JSON machine-readable output contract.
        """
        import datetime
        
        # Categorize entities
        categorized = {
            "authors": [],
            "methods": [],
            "architectures": [],
            "datasets": [],
            "benchmarks": [],
            "tasks": [],
            "institutions": [],
            "metrics": [],
            "topics": []
        }
        
        type_mapping = {
            "Author": "authors",
            "Method": "methods",
            "Architecture": "architectures",
            "Dataset": "datasets",
            "Benchmark": "benchmarks",
            "Task": "tasks",
            "Institution": "institutions",
            "Metric": "metrics",
            "Topic": "topics"
        }
        
        for ent in self.entities:
            etype = ent.get("type")
            target_key = type_mapping.get(etype)
            if target_key:
                entity_obj = {
                    "name": ent["name"],
                    "description": ent.get("description") or ""
                }
                if "paper_count" in ent:
                    entity_obj["paper_count"] = ent["paper_count"]
                
                # Filter out empty fields and optional properties
                entity_obj = {k: v for k, v in entity_obj.items() if v is not None}
                categorized[target_key].append(entity_obj)
                
        # Format papers
        papers_list = []
        for p in self.papers:
            paper_obj = {
                "title": p.get("title") or p["id"],
                "paper_id": p["id"]
            }
            if p.get("year"):
                try:
                    paper_obj["year"] = int(p["year"])
                except Exception:
                    pass
            if p.get("conference"):
                paper_obj["conference"] = p["conference"]
            papers_list.append(paper_obj)
            
        # Format relationships
        rels_list = []
        for r in self.relationships:
            rels_list.append({
                "source": r.get("source_name") or r["source"],
                "relationship": r["relationship"],
                "target": r.get("target_name") or r["target"]
            })
            
        # Compile metadata
        retrieved_nodes_cnt = len(self.entities) + len(self.papers)
        retrieved_edges_cnt = len(self.relationships)
        
        metadata = {
            "nodes_retrieved": retrieved_nodes_cnt,
            "edges_retrieved": retrieved_edges_cnt,
            "graph_version": "1.0",
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "query_type": query_type
        }
        
        return {
            "query": query,
            "papers": papers_list,
            "authors": categorized["authors"],
            "methods": categorized["methods"],
            "architectures": categorized["architectures"],
            "datasets": categorized["datasets"],
            "benchmarks": categorized["benchmarks"],
            "tasks": categorized["tasks"],
            "institutions": categorized["institutions"],
            "metrics": categorized["metrics"],
            "topics": categorized["topics"],
            "relationships": rels_list,
            "citations": self.citations,
            "metadata": metadata
        }


class ContextBuilder:
    """
    Orchestrates extraction of nodes, edges, and citation sources from ranked paths.
    """

    def __init__(self, graph: nx.MultiDiGraph):
        self.graph = graph

    def build(self, ranked_paths: List[RankedPath]) -> GraphContext:
        """
        Extracts structured info from reasoning paths and formats GraphContext.
        """
        if not ranked_paths:
            return GraphContext()

        unique_node_ids: Set[str] = set()
        relationships: List[Dict[str, Any]] = []
        
        # 1. Collect all unique nodes and edges in the paths
        for path in ranked_paths:
            for node in path.nodes:
                unique_node_ids.add(node)
            for edge in path.edges:
                relationships.append(edge)

        # 2. Separate papers and other entities
        entities: List[Dict[str, Any]] = []
        papers: List[Dict[str, Any]] = []
        paper_citations_map = {}
        citation_counter = 1

        for nid in unique_node_ids:
            if nid not in self.graph:
                continue
            attrs = self.graph.nodes[nid]
            node_type = attrs.get("type", "Unknown")
            name = attrs.get("name") or attrs.get("title") or nid

            node_data = {
                "id": nid,
                "name": name,
                "type": node_type,
                "description": attrs.get("description") or attrs.get("abstract"),
                "paper_count": attrs.get("paper_count", 1),
                "paper_ids": attrs.get("paper_ids", "")
            }

            if node_type == "Paper":
                papers.append({
                    "id": nid,
                    "title": attrs.get("title") or name,
                    "year": attrs.get("year"),
                    "conference": attrs.get("conference"),
                })
                paper_citations_map[nid] = citation_counter
                citation_counter += 1
            else:
                entities.append(node_data)

        # 3. Add source paper naming to relationship edges
        annotated_rels = []
        for rel in relationships:
            src = rel.get("source")
            tgt = rel.get("target")
            
            # Look up names for edge representation
            src_name = self.graph.nodes.get(src, {}).get("name") or self.graph.nodes.get(src, {}).get("title") or src
            tgt_name = self.graph.nodes.get(tgt, {}).get("name") or self.graph.nodes.get(tgt, {}).get("title") or tgt
            
            annotated_rels.append({
                "source": src,
                "source_name": src_name,
                "target": tgt,
                "target_name": tgt_name,
                "relationship": rel.get("relationship", "RELATED_TO"),
                "confidence": rel.get("confidence", 1.0)
            })

        # Calculate average confidence
        conf_sum = sum(p.score for p in ranked_paths)
        avg_conf = conf_sum / len(ranked_paths) if ranked_paths else 1.0

        return GraphContext(
            entities=entities,
            paths=ranked_paths,
            relationships=annotated_rels,
            papers=papers,
            citations=list(paper_citations_map.keys()),
            confidence=round(avg_conf, 3)
        )
