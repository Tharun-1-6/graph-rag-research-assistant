"""
parser.py

Converts raw LLM JSON into strongly typed Pydantic models.

Pipeline
--------
LLM JSON
    │
    ▼
Parser
    │
    ▼
ExtractionResult
    │
    ▼
Validator
    │
    ▼
Normalizer

Responsibilities
----------------
✓ Parse JSON string
✓ Parse JSON dictionary
✓ Build Pydantic models
✓ Handle malformed JSON

Does NOT
---------
✗ Validate ontology
✗ Normalize entities
✗ Call the LLM
"""

from __future__ import annotations

import json
from typing import Any, Dict

from pydantic import ValidationError

from .models import (
    Entity,
    ExtractionResult,
    Paper,
    Relationship,
)


class ExtractionParser:
    """
    Converts LLM output into Pydantic models.
    """

    # ---------------------------------------------------------
    # Public Methods
    # ---------------------------------------------------------

    def parse(self, data: str | Dict[str, Any]) -> ExtractionResult:
        """
        Parses either:

        • JSON string
        • Python dictionary

        Returns
        -------
        ExtractionResult
        """

        if isinstance(data, str):
            data = self._parse_json_string(data)

        return self._build_result(data)

    # ---------------------------------------------------------
    # Private Methods
    # ---------------------------------------------------------

    def _parse_json_string(
        self,
        text: str,
    ) -> Dict[str, Any]:
        """
        Converts JSON string -> dictionary.
        """

        try:
            return json.loads(text)

        except json.JSONDecodeError as e:
            raise ValueError(
                f"Invalid JSON returned by LLM:\n{e}"
            ) from e

    def _build_result(
        self,
        data: Dict[str, Any],
    ) -> ExtractionResult:
        """
        Builds the ExtractionResult model.
        """

        try:

            paper = Paper(
                **data.get("paper", {})
            )

            entities = []

            relationships = []

            # ---------------------------------------------
            # Generic entities
            # ---------------------------------------------

            if "entities" in data:

                for entity in data["entities"]:
                    entities.append(Entity(**entity))

            else:
                # -----------------------------------------
                # Backwards compatibility
                #
                # Older prompts return:
                # authors
                # methods
                # datasets
                # ...
                # -----------------------------------------

                entity_groups = {
                    "authors": "Author",
                    "institutions": "Institution",
                    "methods": "Method",
                    "architectures": "Architecture",
                    "datasets": "Dataset",
                    "benchmarks": "Benchmark",
                    "tasks": "Task",
                    "metrics": "Metric",
                    "topics": "Topic",
                    "conferences": "Conference",
                }

                for key, entity_type in entity_groups.items():

                    for name in data.get(key, []):

                        entities.append(
                            Entity(
                                id=self._generate_id(name),
                                name=name,
                                type=entity_type,
                            )
                        )

            # ---------------------------------------------
            # Relationships
            # ---------------------------------------------

            for relationship in data.get(
                "relationships",
                [],
            ):
                relationships.append(
                    Relationship(**relationship)
                )

            return ExtractionResult(
                paper=paper,
                entities=entities,
                relationships=relationships,
                metadata=data.get("metadata", {}),
            )

        except ValidationError as e:
            raise ValueError(
                f"Pydantic validation failed:\n{e}"
            ) from e

    # ---------------------------------------------------------
    # Utility
    # ---------------------------------------------------------

    @staticmethod
    def _generate_id(name: str) -> str:
        """
        Generates a graph-safe ID from a name.

        Example
        -------
        Attention Is All You Need
            ->
        attention_is_all_you_need
        """

        return (
            name.lower()
            .replace("-", "_")
            .replace(" ", "_")
        )


# ---------------------------------------------------------
# Convenience Function
# ---------------------------------------------------------

def parse_extraction(
    data: str | Dict[str, Any],
) -> ExtractionResult:
    """
    Convenience wrapper.

    Example
    -------
    result = parse_extraction(json_string)
    """

    parser = ExtractionParser()

    return parser.parse(data)