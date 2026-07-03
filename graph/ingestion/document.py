"""
document.py

Defines the core Document object used throughout the GraphRAG pipeline.

A Document represents one research paper after it has been loaded
from disk but before entity extraction.

This object is shared between:

    loader.py
    cleaner.py
    exporter.py
    extractor.py
"""

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Any
import re


@dataclass
class Document:
    """
    Represents one research paper.

    Attributes
    ----------
    paper_id : str
        Unique identifier for the paper.

    filename : str
        Original filename.

    file_path : str
        Absolute/relative path of the PDF.

    raw_text : str
        Text extracted directly from the PDF.

    cleaned_text : str
        Cleaned version of the extracted text.

    metadata : dict
        Stores metadata such as title, authors,
        year, conference, etc.
    """

    paper_id: str
    filename: str
    file_path: str

    raw_text: str = ""
    cleaned_text: str = ""

    metadata: Dict[str, Any] = field(default_factory=dict)

    # ---------------------------------------------------
    # Static Helpers
    # ---------------------------------------------------

    @staticmethod
    def generate_id(name: str) -> str:
        """
        Converts any string into a graph-safe identifier.

        Examples
        --------
        "Attention Is All You Need"
            -> attention_is_all_you_need

        "GPT-3 Paper"
            -> gpt_3_paper

        "RoBERTa (2019)"
            -> roberta_2019
        """

        name = name.lower()

        # Remove everything except letters,
        # numbers, spaces, underscores and hyphens
        name = re.sub(r"[^\w\s-]", "", name)

        # Replace spaces/hyphens with underscores
        name = re.sub(r"[-\s]+", "_", name)

        # Remove leading/trailing underscores
        return name.strip("_")

    # ---------------------------------------------------
    # Factory Methods
    # ---------------------------------------------------

    @classmethod
    def from_file(cls, pdf_path: str):
        """
        Creates an empty Document from a PDF path.

        PDF loading happens later in loader.py.
        """

        path = Path(pdf_path)

        return cls(
            paper_id=cls.generate_id(path.stem),
            filename=path.name,
            file_path=str(path),
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """
        Reconstructs a Document from a dictionary.
        """

        return cls(**data)

    # ---------------------------------------------------
    # Update Methods
    # ---------------------------------------------------

    def update_raw_text(self, text: str) -> None:
        """
        Stores raw extracted PDF text.
        """

        self.raw_text = text

    def update_cleaned_text(self, text: str) -> None:
        """
        Stores cleaned text.
        """

        self.cleaned_text = text

    def add_metadata(self, key: str, value: Any) -> None:
        """
        Adds or updates a single metadata field.
        """

        self.metadata[key] = value

    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        Updates multiple metadata fields.
        """

        self.metadata.update(metadata)

    # ---------------------------------------------------
    # Properties
    # ---------------------------------------------------

    @property
    def text(self) -> str:
        """
        Returns cleaned text if available,
        otherwise returns raw text.

        Downstream modules should always use:

            document.text
        """

        return self.cleaned_text if self.cleaned_text else self.raw_text

    # ---------------------------------------------------
    # Serialization
    # ---------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the Document into a dictionary.
        """

        return asdict(self)

    # ---------------------------------------------------
    # Representation
    # ---------------------------------------------------

    def __repr__(self) -> str:

        return (
            f"Document("
            f"id='{self.paper_id}', "
            f"file='{self.filename}', "
            f"raw_chars={len(self.raw_text)}, "
            f"clean_chars={len(self.cleaned_text)}, "
            f"metadata={len(self.metadata)})"
        )