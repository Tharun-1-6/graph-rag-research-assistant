"""
extractor.py

Main GraphRAG extraction pipeline.

Pipeline
--------
Document
    │
    ▼
Prompt Builder
    │
    ▼
LLM
    │
    ▼
Parser
    │
    ▼
Validator
    │
    ▼
Normalizer
    │
    ▼
ExtractionResult

Responsibilities
----------------
✓ Build extraction prompt
✓ Call the LLM
✓ Parse JSON
✓ Validate extraction
✓ Normalize entities
✓ Return ExtractionResult

Does NOT
---------
✗ Build graphs
✗ Store data
✗ Retrieve documents
"""

from __future__ import annotations

from graph.ingestion.document import Document

from llm.client import LLMClient
from llm.prompts import build_extraction_prompt

from .models import ExtractionResult
from .parser import ExtractionParser
from .validator import ExtractionValidator
from .normalizer import EntityNormalizer


class GraphExtractor:
    """
    High-level extraction pipeline.

    This is the only class the rest of the project
    should use for knowledge extraction.
    """

    def __init__(self):

        self.llm = LLMClient()

        self.parser = ExtractionParser()

        self.validator = ExtractionValidator()

        self.normalizer = EntityNormalizer()

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def extract(
        self,
        document: Document,
    ) -> ExtractionResult:
        """
        Extracts structured knowledge from one document.

        Parameters
        ----------
        document : Document

        Returns
        -------
        ExtractionResult
        """

        if not document.text.strip():

            raise ValueError(
                "Document contains no text."
            )

        # -------------------------------------------------
        # Build Prompt
        # -------------------------------------------------

        prompt = build_extraction_prompt(document)

        # -------------------------------------------------
        # LLM
        # -------------------------------------------------

        llm_output = self.llm.generate_json(prompt)

        # -------------------------------------------------
        # Parse
        # -------------------------------------------------

        result = self.parser.parse(llm_output)

        # -------------------------------------------------
        # Validate
        # -------------------------------------------------

        result = self.validator.validate(result)

        # -------------------------------------------------
        # Normalize
        # -------------------------------------------------

        result = self.normalizer.normalize(result)

        return result

    # ---------------------------------------------------------

    def extract_many(
        self,
        documents: list[Document],
    ) -> list[ExtractionResult]:
        """
        Extract multiple documents.

        Parameters
        ----------
        documents : list[Document]

        Returns
        -------
        list[ExtractionResult]
        """

        results = []

        for document in documents:

            results.append(
                self.extract(document)
            )

        return results

    # ---------------------------------------------------------

    def print_summary(
        self,
        result: ExtractionResult,
    ) -> None:
        """
        Prints a summary of the extraction.
        """

        print("\n" + "=" * 70)
        print("EXTRACTION SUMMARY")
        print("=" * 70)

        print(f"Paper : {result.paper.title}")
        print(f"Year  : {result.paper.year}")
        print(f"Conference : {result.paper.conference}")

        print()

        print(f"Entities      : {result.num_entities}")
        print(f"Relationships : {result.num_relationships}")

        print()

        print("Entity Counts")

        summary = result.summary()

        if not summary:
            print("None")

        else:

            for entity_type, count in sorted(summary.items()):

                print(f"  {entity_type:<15} : {count}")

        print()

        if self.validator.warnings:

            print("Validation Warnings")

            for warning in self.validator.warnings:

                print(f"  • {warning}")

        else:

            print("Validation Warnings : None")

        print("=" * 70)