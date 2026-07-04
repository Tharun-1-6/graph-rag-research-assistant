"""
prompt_builder.py

Converts structured GraphContext reasoning chains and citations into clean, LLM-ready prompts.
"""

from typing import Any, Dict, List
from graph.query_engine.context_builder import GraphContext


class GraphPromptBuilder:
    """
    Transforms structured graph context into detailed prompts for RAG answer generation.
    """

    def build_prompt(self, context: GraphContext, query: str) -> str:
        """
        Creates the LLM prompt separating system directions, context details, and question.
        """
        system_instructions = (
            "You are an expert research assistant answering questions using a structured knowledge graph "
            "built from academic papers.\n"
            "INSTRUCTIONS:\n"
            "1. Answer the query relying ONLY on the retrieved structured graph context and reasoning paths.\n"
            "2. Do NOT speculate, extrapolate, or introduce outside knowledge not present in the graph.\n"
            "3. Ground your response with facts. Cite the source papers whenever appropriate.\n"
            "4. If the context does not contain enough information, explain what is missing."
        )

        # Build bibliography segment
        bib_lines = []
        if context.papers:
            bib_lines.append("### Source Papers & Bibliography")
            for i, p in enumerate(context.papers, 1):
                title = p.get("title", "Unknown Title")
                year = p.get("year", "N/A")
                conf = p.get("conference", "N/A")
                bib_lines.append(f"- **[{i}]** *\"{title}\"*, Published in {conf} ({year}). ID: {p['id']}")

        # Build key entities segment
        entity_lines = []
        if context.entities:
            entity_lines.append("### Key Entities")
            # Group by type
            by_type = {}
            for ent in context.entities:
                etype = ent.get("type", "Unknown")
                by_type.setdefault(etype, []).append(ent)
            
            for etype, ents in sorted(by_type.items()):
                entity_lines.append(f"#### {etype}s:")
                for e in ents:
                    desc = e.get("description") or "No description available."
                    paper_cnt = e.get("paper_count", 1)
                    entity_lines.append(f"  • **{e['name']}**: {desc} (Linked papers: {paper_cnt})")

        # Build reasoning chains segment
        path_lines = []
        if context.paths:
            path_lines.append("### Graph Reasoning Paths")
            for p in context.paths:
                path_lines.append(f"  • [Score: {p.score:.3f} | {p.reason}] {p.path_str}")

        # Build direct connections
        connection_lines = []
        if context.relationships:
            connection_lines.append("### Relationship Direct Connections")
            seen = set()
            for rel in context.relationships:
                u = rel.get("source_name") or rel["source"]
                v = rel.get("target_name") or rel["target"]
                rtype = rel["relationship"]
                rel_str = f"**{u}** --[{rtype}]--> **{v}**"
                if rel_str not in seen:
                    seen.add(rel_str)
                    connection_lines.append(f"  • {rel_str}")

        # Assemble segment blocks
        context_blocks = []
        if bib_lines:
            context_blocks.append("\n".join(bib_lines))
        if entity_lines:
            context_blocks.append("\n".join(entity_lines))
        if path_lines:
            context_blocks.append("\n".join(path_lines))
        if connection_lines:
            context_blocks.append("\n".join(connection_lines))

        context_segment = "\n\n".join(context_blocks) if context_blocks else "No relevant context found in the graph."

        prompt = f"""SYSTEM INSTRUCTIONS:
======================================================================
{system_instructions}
======================================================================

RETRIEVED GRAPH CONTEXT:
======================================================================
{context_segment}
======================================================================

User Query: {query}
"""
        return prompt
