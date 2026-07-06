"""
citation_builder.py

Builds structured citations and maps fact paths back to source paper nodes.
"""

from typing import Any, Dict, List, Set
import networkx as nx

from graph.query_engine.context_builder import GraphContext
from .provenance import Provenance


class CitationBuilder:
    """
    Scans retrieved graph context and creates bibliographic citation records.
    """

    def __init__(self, graph: nx.MultiDiGraph):
        self.graph = graph

    def build_citations(self, context: GraphContext) -> List[Provenance]:
        """
        Gathers unique provenance records from all entities and paths inside the context.
        """
        provenances: List[Provenance] = []
        seen_pairs: Set[tuple] = set()

        # Gather paper ids from retrieved entities
        for ent in context.entities:
            paper_ids_str = ent.get("paper_ids", "")
            if paper_ids_str:
                paper_ids = [p.strip() for p in paper_ids_str.split(",") if p.strip()]
                for pid in paper_ids:
                    pair = (ent["id"], pid)
                    if pair not in seen_pairs:
                        seen_pairs.add(pair)
                        prov = self._get_provenance(pid, ent.get("confidence", 1.0))
                        if prov:
                            provenances.append(prov)

        # Gather paper ids from paths/relationships
        for path in context.paths:
            for edge in path.edges:
                paper_ids_str = edge.get("paper_ids", "")
                if paper_ids_str:
                    paper_ids = [p.strip() for p in paper_ids_str.split(",") if p.strip()]
                    for pid in paper_ids:
                        # Grab edge confidence
                        conf = edge.get("confidence", 1.0)
                        pair = (edge.get("relationship", "REL"), pid)
                        if pair not in seen_pairs:
                            seen_pairs.add(pair)
                            prov = self._get_provenance(pid, conf)
                            if prov:
                                provenances.append(prov)

        # Deduplicate list by paper_id keeping highest confidence
        unique_provs: Dict[str, Provenance] = {}
        for prov in provenances:
            if prov.paper_id in unique_provs:
                if prov.confidence > unique_provs[prov.paper_id].confidence:
                    unique_provs[prov.paper_id] = prov
            else:
                unique_provs[prov.paper_id] = prov

        return list(unique_provs.values())

    def _get_provenance(self, paper_id: str, confidence: float) -> Provenance | None:
        """
        Resolves paper metadata from graph to formulate Provenance.
        """
        if paper_id not in self.graph:
            return None
        
        attrs = self.graph.nodes[paper_id]
        title = attrs.get("title") or attrs.get("name") or paper_id
        
        return Provenance(
            paper_id=paper_id,
            paper_title=title,
            confidence=confidence,
            page=attrs.get("page"),
            paragraph=attrs.get("paragraph")
        )
