"""
normalizer.py

Normalizes extracted entities before graph construction.

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
    │
    ▼
Graph Builder

Responsibilities
----------------
✓ Normalize entity names
✓ Normalize entity IDs
✓ Remove formatting inconsistencies
✓ Merge duplicate entities
✓ Update relationships after merging

Does NOT
---------
✗ Call the LLM
✗ Perform fuzzy matching
✗ Guess synonyms
✗ Build graphs
"""

from __future__ import annotations

import re

from .models import ExtractionResult


class EntityNormalizer:
    """
    Normalizes entities and relationships.
    """

    # ---------------------------------------------------------

    def normalize(
        self,
        result: ExtractionResult,
    ) -> ExtractionResult:

        id_mapping = {}

        unique_entities = {}

        # ---------------------------------------------
        # Normalize every entity
        # ---------------------------------------------

        for entity in result.entities:

            entity.name = self._normalize_name(entity.name)

            old_id = entity.id

            entity.id = self._generate_id(entity.name)

            # Duplicate after normalization
            if entity.id in unique_entities:

                id_mapping[old_id] = entity.id
                continue

            unique_entities[entity.id] = entity
            id_mapping[old_id] = entity.id

        result.entities = list(unique_entities.values())

        # ---------------------------------------------
        # Normalize paper
        # ---------------------------------------------

        result.paper.title = self._normalize_name(
            result.paper.title
        )

        paper_old = result.paper.id
        result.paper.id = self._generate_id(
            result.paper.title
        )

        id_mapping[paper_old] = result.paper.id

        # ---------------------------------------------
        # Update relationships
        # ---------------------------------------------

        seen = set()
        cleaned_relationships = []

        for relation in result.relationships:

            relation.source = id_mapping.get(
                relation.source,
                relation.source,
            )

            relation.target = id_mapping.get(
                relation.target,
                relation.target,
            )

            key = (
                relation.source,
                relation.relationship,
                relation.target,
            )

            if key in seen:
                continue

            seen.add(key)
            cleaned_relationships.append(relation)

        result.relationships = cleaned_relationships

        return result

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    @staticmethod
    def _normalize_name(name: str) -> str:
        """
        Cleans formatting while preserving
        natural capitalization.
        """

        if not name:
            return ""

        name = name.strip()

        name = re.sub(r"\s+", " ", name)

        return name

    @staticmethod
    def _generate_id(name: str) -> str:
        """
        Generates graph-safe IDs.

        Example
        -------
        Attention Is All You Need

        ->
        attention_is_all_you_need
        """

        name = name.lower()

        name = re.sub(r"[^\w\s-]", "", name)

        name = re.sub(r"[-\s]+", "_", name)

        return name.strip("_")