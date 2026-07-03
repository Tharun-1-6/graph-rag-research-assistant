"""
utils.py

Utility functions used across the GraphRAG extraction pipeline.

Responsibilities
----------------
✓ Generate graph-safe IDs
✓ Normalize names
✓ Remove duplicate entities
✓ Safe JSON loading
✓ Pretty printing

Does NOT
---------
✗ Call LLMs
✗ Validate graph
✗ Build graph
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .models import Entity


# ==========================================================
# ID Generation
# ==========================================================

def generate_id(name: str) -> str:
    """
    Converts text into a graph-safe identifier.

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


# ==========================================================
# Name Normalization
# ==========================================================

def normalize_name(name: str) -> str:
    """
    Basic normalization for entity names.

    Example
    -------
    " transformer "
        ->
    "Transformer"
    """

    name = re.sub(r"\s+", " ", name)

    return name.strip().title()


# ==========================================================
# JSON Helpers
# ==========================================================

def load_json(path: str | Path) -> dict:
    """
    Loads JSON from disk.
    """

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: Any, path: str | Path) -> None:
    """
    Saves JSON to disk.
    """

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False,
        )


# ==========================================================
# Entity Helpers
# ==========================================================

def deduplicate_entities(
    entities: list[Entity],
) -> list[Entity]:
    """
    Removes duplicate entities using their IDs.
    """

    unique = {}

    for entity in entities:
        unique[entity.id] = entity

    return list(unique.values())


# ==========================================================
# Pretty Printing
# ==========================================================

def print_header(title: str) -> None:
    """
    Prints a formatted section header.
    """

    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)