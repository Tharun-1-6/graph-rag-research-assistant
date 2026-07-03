"""
exporter.py

Exports Document objects to JSON and loads them back.

Responsibilities
----------------
✓ Save Document -> JSON
✓ Load JSON -> Document
✓ Export multiple documents

Does NOT
---------
✗ Clean text
✗ Read PDFs
✗ Build graphs
✗ Call LLMs
"""

from pathlib import Path
import json
from typing import List
from .document import Document


class DocumentExporter:
    """
    Handles saving and loading Document objects.
    """

    def __init__(self, output_dir: str | Path = "data/extracted"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------
    # Save Methods
    # ---------------------------------------------------------

    def save(self, document: Document) -> Path:
        """
        Saves a single Document as JSON.

        Parameters
        ----------
        document : Document

        Returns
        -------
        Path
            Path to the exported JSON file.
        """

        output_path = self.output_dir / f"{document.paper_id}.json"

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(
                document.to_dict(),
                f,
                indent=4,
                ensure_ascii=False
            )

        return output_path

    def save_all(self, documents: List[Document]) -> List[Path]:
        """
        Saves multiple Document objects.

        Parameters
        ----------
        documents : List[Document]

        Returns
        -------
        List[Path]
        """

        saved_files = []

        for document in documents:
            saved_files.append(self.save(document))

        return saved_files

    # ---------------------------------------------------------
    # Load Methods
    # ---------------------------------------------------------

    def load(self, json_path: str | Path) -> Document:
        """
        Loads a Document from a JSON file.

        Parameters
        ----------
        json_path : str | Path

        Returns
        -------
        Document
        """

        json_path = Path(json_path)

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return Document.from_dict(data)

    def load_all(self) -> List[Document]:
        """
        Loads every exported document.

        Returns
        -------
        List[Document]
        """

        documents = []

        json_files = sorted(self.output_dir.glob("*.json"))

        for file in json_files:
            documents.append(self.load(file))

        return documents