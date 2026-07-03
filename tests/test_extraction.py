"""
test_extraction.py

Integration test for the entire extraction pipeline.

Pipeline
--------
PDF
    │
    ▼
Loader
    │
    ▼
Cleaner
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
"""

from pathlib import Path
from graph.ingestion.loader import PDFLoader
from graph.ingestion.cleaner import TextCleaner
from graph.extraction.extractor import GraphExtractor


# --------------------------------------------------------
# Change this if required
# --------------------------------------------------------

TEST_PDF = Path(
    r"C:\Projects Tharun\RAG and GraphRAG based llm\data\papers\1-Attention Is All You Need.pdf"
)


# --------------------------------------------------------

def divider(title):
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)


def main():

    divider("STEP 1 : LOAD DOCUMENT")
    loader = PDFLoader()
    document = loader.load(TEST_PDF)
    print(document)
    divider("STEP 2 : CLEAN DOCUMENT")
    cleaner = TextCleaner()
    document = cleaner.clean(document)
    print(document)
    divider("STEP 3 : EXTRACT KNOWLEDGE")
    extractor = GraphExtractor()
    result = extractor.extract(document)
    divider("PAPER")
    print(result.paper)
    divider("ENTITY SUMMARY")
    print(result.summary())
    divider("ENTITIES")
    for entity in result.entities:
        print(entity)
    divider("RELATIONSHIPS")
    for relationship in result.relationships:
        print(relationship)
    divider("VALIDATION WARNINGS")
    if extractor.validator.warnings:
        for warning in extractor.validator.warnings:
            print("-", warning)
    else:
        print("No warnings")
    divider("FINAL SUMMARY")
    print("Paper           :", result.paper.title)
    print("Entities        :", result.num_entities)
    print("Relationships   :", result.num_relationships)
    print("\nEntity Counts")
    for k, v in result.summary().items():
        print(f"{k:<15}: {v}")
    divider("SUCCESS")
    print("Extraction pipeline completed successfully.")

if __name__ == "__main__":
    main()