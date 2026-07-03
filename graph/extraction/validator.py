"""
validator.py

Validates extracted GraphRAG entities and relationships.

Pipeline
--------
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

Responsibilities
----------------
✓ Validate entity types
✓ Validate relationship types
✓ Validate graph connections
✓ Remove duplicates
✓ Produce validation warnings

Does NOT
---------
✗ Call the LLM
✗ Normalize names
✗ Build graph
"""

from collections import Counter

from .models import (
    ExtractionResult,
    Entity,
    Relationship,
)

from .schema import (
    NODE_TYPES,
    RELATIONSHIP_TYPES,
    is_valid_connection,
)


class ExtractionValidator:
    """
    Validates an ExtractionResult.
    """

    def __init__(self):

        self.warnings = []

    # ---------------------------------------------------------

    def validate(
        self,
        result: ExtractionResult,
    ) -> ExtractionResult:
        """
        Runs every validation stage.
        """

        self.warnings.clear()

        result.entities = self._validate_entities(
            result.entities
        )

        result.relationships = self._validate_relationships(
            result.relationships,
            result,
        )

        self._validate_paper(result)

        return result

    # ---------------------------------------------------------
    # Paper
    # ---------------------------------------------------------

    def _validate_paper(
        self,
        result: ExtractionResult,
    ):

        if not result.paper.title:

            self.warnings.append(
                "Paper title missing."
            )

    # ---------------------------------------------------------
    # Entities
    # ---------------------------------------------------------

    def _validate_entities(
        self,
        entities,
    ):

        valid = []

        seen = set()

        for entity in entities:

            if entity.type not in NODE_TYPES:

                self.warnings.append(
                    f"Unknown entity type '{entity.type}' "
                    f"for '{entity.name}'"
                )
                continue

            if entity.id in seen:

                self.warnings.append(
                    f"Duplicate entity '{entity.id}' removed."
                )
                continue

            seen.add(entity.id)

            valid.append(entity)

        return valid

    # ---------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------

    def _validate_relationships(
        self,
        relationships,
        result,
    ):

        valid = []

        seen = set()

        entity_lookup = {
            entity.id: entity
            for entity in result.entities
        }

        paper_id = result.paper.id

        for relation in relationships:

            # ---------------------------------------------
            # relationship type
            # ---------------------------------------------

            if relation.relationship not in RELATIONSHIP_TYPES:

                self.warnings.append(
                    f"Unknown relationship "
                    f"'{relation.relationship}'"
                )

                continue

            # ---------------------------------------------
            # duplicate
            # ---------------------------------------------

            key = (
                relation.source,
                relation.relationship,
                relation.target,
            )

            if key in seen:

                self.warnings.append(
                    f"Duplicate relationship {key}"
                )

                continue

            seen.add(key)

            # ---------------------------------------------
            # source node
            # ---------------------------------------------

            if relation.source == paper_id:

                source_type = "Paper"

            elif relation.source in entity_lookup:

                source_type = entity_lookup[
                    relation.source
                ].type

            else:

                self.warnings.append(
                    f"Unknown source '{relation.source}'"
                )

                continue

            # ---------------------------------------------
            # target node
            # ---------------------------------------------

            if relation.target == paper_id:

                target_type = "Paper"

            elif relation.target in entity_lookup:

                target_type = entity_lookup[
                    relation.target
                ].type

            else:

                self.warnings.append(
                    f"Unknown target '{relation.target}'"
                )

                continue

            # ---------------------------------------------
            # ontology validation
            # ---------------------------------------------

            if not is_valid_connection(
                source_type,
                relation.relationship,
                target_type,
            ):

                self.warnings.append(
                    f"Illegal connection "
                    f"{source_type} --"
                    f"{relation.relationship}--> "
                    f"{target_type}"
                )

                continue

            valid.append(relation)

        return valid

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    def summary(
        self,
        result: ExtractionResult,
    ):

        counts = Counter()

        for entity in result.entities:
            counts[entity.type] += 1

        return {
            "entities": len(result.entities),
            "relationships": len(result.relationships),
            "entity_types": dict(counts),
            "warnings": len(self.warnings),
        }

    # ---------------------------------------------------------

    def print_report(self):

        print("\nValidation Report")
        print("-" * 40)

        if not self.warnings:
            print("No validation issues found.")
            return

        for warning in self.warnings:
            print(f"• {warning}")