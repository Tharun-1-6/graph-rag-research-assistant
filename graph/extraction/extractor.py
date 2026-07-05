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
        import re
        import json
        from pathlib import Path

        if not document.text.strip():
            raise ValueError(
                "Document contains no text."
            )

        # -------------------------------------------------
        # Caching logic
        # -------------------------------------------------
        paper_ref = getattr(document, "paper_id", None) or getattr(document, "filename", None) or "unknown"
        safe_ref = re.sub(r"[^\w\s-]", "", str(paper_ref)).strip().lower()
        safe_ref = re.sub(r"[-\s]+", "_", safe_ref)
        
        cache_dir = Path("data/processed/extractions")
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f"{safe_ref}_extracted.json"

        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                return ExtractionResult.model_validate(cached_data)
            except Exception:
                # If cache is corrupt, proceed to call LLM
                pass

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

        # -------------------------------------------------
        # Save to cache
        # -------------------------------------------------
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(result.model_dump(), f, indent=4, ensure_ascii=False)
        except Exception:
            pass

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