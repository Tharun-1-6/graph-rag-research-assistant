"""
models.py

Pydantic models used throughout the GraphRAG extraction pipeline.

These models represent the structured output produced by the LLM
after entity extraction.

Pipeline
--------
LLM JSON
    │
    ▼
Pydantic Models
    │
    ▼
Validator
    │
    ▼
Normalizer
    │
    ▼
Graph Builder
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict

from .schema import NODE_TYPES, RELATIONSHIP_TYPES


# ==========================================================
# Base Model
# ==========================================================

class GraphBaseModel(BaseModel):
    """
    Base class for all graph models.

    Allows extra metadata fields returned by future LLMs
    without immediately breaking validation.
    """

    model_config = ConfigDict(
        extra="allow",
        validate_assignment=True,
        str_strip_whitespace=True,
    )


# ==========================================================
# Paper
# ==========================================================

class Paper(GraphBaseModel):
    """
    Represents the research paper itself.
    """

    id: str
    title: str
    year: Optional[int] = None
    conference: Optional[str] = None
    abstract: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ==========================================================
# Entity
# ==========================================================

class Entity(GraphBaseModel):
    """
    Generic graph node.

    Every non-paper node in the graph is represented
    using this model.

    Examples
    --------
    Author
    Dataset
    Method
    Benchmark
    Topic
    Task
    Institution
    """

    id: str
    name: str
    type: str
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def is_valid_type(self) -> bool:
        """
        Checks whether this entity type exists
        in the graph ontology.
        """

        return self.type in NODE_TYPES


# ==========================================================
# Relationship
# ==========================================================

class Relationship(GraphBaseModel):
    """
    Represents one graph edge.
    """

    source: str
    relationship: str
    target: str
    confidence: float = 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def is_valid_relationship(self) -> bool:

        return self.relationship in RELATIONSHIP_TYPES


# ==========================================================
# Extraction Result
# ==========================================================

class ExtractionResult(GraphBaseModel):
    """
    Complete structured extraction result.
    """
    paper: Paper
    entities: List[Entity] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # ------------------------------------------------------
    # Convenience Methods
    # ------------------------------------------------------

    def get_entities_by_type(self,entity_type: str) -> List[Entity]:
        """
        Returns all entities of a specific type.

        Example
        -------
        result.get_entities_by_type("Author")
        """

        return [
            entity
            for entity in self.entities
            if entity.type == entity_type
        ]

    def get_entity(self,entity_id: str) -> Optional[Entity]:
        """
        Finds an entity by ID.
        """

        for entity in self.entities:
            if entity.id == entity_id:
                return entity

        return None

    def entity_exists(self,entity_id: str) -> bool:

        return self.get_entity(entity_id) is not None

    def add_entity(self,entity: Entity) -> None:
        """
        Adds an entity only if it doesn't already exist.
        """

        if not self.entity_exists(entity.id):
            self.entities.append(entity)

    def add_relationship(self,relationship: Relationship) -> None:

        self.relationships.append(relationship)

    @property
    def num_entities(self) -> int:

        return len(self.entities)

    @property
    def num_relationships(self) -> int:

        return len(self.relationships)

    def summary(self) -> Dict[str, int]:
        """
        Returns the number of entities
        grouped by type.

        Example
        -------
        {
            "Author": 3,
            "Method": 1,
            "Dataset": 2
        }
        """

        counts = {}

        for entity in self.entities:

            counts[entity.type] = (
                counts.get(entity.type, 0) + 1
            )

        return counts

    def __repr__(self):
        return (
            f"ExtractionResult("
            f"paper='{self.paper.title}', "
            f"entities={len(self.entities)}, "
            f"relationships={len(self.relationships)})"
        )