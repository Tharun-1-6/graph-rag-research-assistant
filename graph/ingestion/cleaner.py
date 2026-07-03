"""
cleaner.py

Cleans extracted PDF text before it is sent to the
entity extraction stage.

Responsibilities
----------------
✓ Normalize whitespace
✓ Normalize unicode
✓ Remove excessive blank lines
✓ Remove page markers (optional)
✓ Store cleaned text back into the Document

Does NOT
---------
✗ Remove references
✗ Remove tables
✗ Remove equations
✗ Remove citations
✗ Perform NLP
"""

import re
import unicodedata

from .document import Document

class TextCleaner:
    """
    Cleans text extracted from PDF documents.
    """
    def __init__(self):
        pass

    # ---------------------------------------------------------
    # Public Methods
    # ---------------------------------------------------------

    def clean(self, document: Document) -> Document:
        """
        Cleans the raw text inside a Document object.
        Parameters
        ----------
        document : Document
        Returns
        -------
        Document
        """

        text = document.raw_text
        text = self._normalize_unicode(text)
        text = self._normalize_line_endings(text)
        text = self._remove_trailing_spaces(text)
        text = self._collapse_multiple_spaces(text)
        text = self._collapse_blank_lines(text)
        document.update_cleaned_text(text)
        return document

    # ---------------------------------------------------------
    # Private Methods
    # ---------------------------------------------------------

    def _normalize_unicode(self, text: str) -> str:
        """
        Normalizes unicode characters.
        """
        return unicodedata.normalize("NFKC", text)

    def _normalize_line_endings(self, text: str) -> str:
        """
        Converts Windows/Mac line endings to Unix.
        """
        return text.replace("\r\n", "\n").replace("\r", "\n")

    def _remove_trailing_spaces(self, text: str) -> str:
        """
        Removes trailing spaces from every line.
        """
        return "\n".join(line.rstrip() for line in text.split("\n"))

    def _collapse_multiple_spaces(self, text: str) -> str:
        """
        Converts multiple spaces into one.
        """
        return re.sub(r"[ ]{2,}", " ", text)

    def _collapse_blank_lines(self, text: str) -> str:
        """
        Limits consecutive blank lines to two.
        """
        return re.sub(r"\n{3,}", "\n\n", text)