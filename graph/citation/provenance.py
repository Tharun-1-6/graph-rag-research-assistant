"""
provenance.py

Defines structural models for fact provenance tracking and verification.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Provenance:
    """
    Defines the origin of a graph fact (node or relationship).
    """
    paper_id: str
    paper_title: str
    confidence: float
    page: Optional[int] = None
    paragraph: Optional[int] = None

    def to_citation_str(self) -> str:
        """
        Formats the provenance to a standard citation tag: [Title, p. Page]
        """
        page_str = f", p. {self.page}" if self.page is not None else ""
        return f"[{self.paper_title}{page_str}]"
