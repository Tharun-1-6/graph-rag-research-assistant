"""
loader.py

Loads research papers from PDF files and converts them into
Document objects.

Responsibilities
----------------
✓ Open PDF files
✓ Extract raw text
✓ Populate Document objects

Does NOT
---------
✗ Clean text
✗ Extract entities
✗ Build graph
✗ Save JSON
"""

from pathlib import Path
from typing import List
import fitz  # PyMuPDF

from .document import Document


class PDFLoader:
    """
    Loads PDF research papers into Document objects.
    """

    def __init__(self):
        pass

    # ---------------------------------------------------------
    # Public Methods
    # ---------------------------------------------------------

    def load(self, pdf_path: str | Path) -> Document:
        """
        Load a single PDF.

        Parameters
        ----------
        pdf_path : str | Path

        Returns
        -------
        Document
        """

        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        document = Document.from_file(str(pdf_path))

        raw_text = self._extract_text(pdf_path)

        document.update_raw_text(raw_text)

        # Basic metadata available without using an LLM
        document.add_metadata("num_pages", self._count_pages(pdf_path))
        document.add_metadata("source", str(pdf_path))

        return document

    def load_directory(self, directory: str | Path) -> List[Document]:
        """
        Load every PDF inside a directory.

        Parameters
        ----------
        directory : str | Path

        Returns
        -------
        List[Document]
        """

        directory = Path(directory)

        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        documents = []

        pdf_files = sorted(directory.glob("*.pdf"))

        for pdf in pdf_files:
            documents.append(self.load(pdf))

        return documents

    # ---------------------------------------------------------
    # Private Methods
    # ---------------------------------------------------------

    def _extract_text(self, pdf_path: Path) -> str:
        """
        Extract raw text from a PDF.

        Returns
        -------
        str
        """
        text_parts = []

        with fitz.open(pdf_path) as pdf:

            for page in pdf:
                page_text = page.get_text("text")

                text_parts.append(page_text)

        return "\n".join(text_parts)

    def _count_pages(self, pdf_path: Path) -> int:
        """
        Returns the number of pages in the PDF.
        """

        with fitz.open(pdf_path) as pdf:
            return len(pdf)