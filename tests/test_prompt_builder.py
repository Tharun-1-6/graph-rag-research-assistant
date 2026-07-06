"""
test_prompt_builder.py

Unit tests for GraphPromptBuilder template generation.
"""

from graph.query_engine.context_builder import GraphContext
from graph.query_engine.path_ranker import RankedPath
from graph.prompt_builder import GraphPromptBuilder


def divider(title: str):
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)


def main():
    divider("RUNNING PROMPT BUILDER TESTS")

    # 1. Create a structured GraphContext
    context = GraphContext(
        entities=[
            {"id": "bert", "name": "BERT", "type": "Method", "description": "Language model"},
            {"id": "roberta", "name": "RoBERTa", "type": "Method", "description": "Optimized BERT"}
        ],
        paths=[
            RankedPath(score=0.95, nodes=["bert", "roberta"], edges=[{"relationship": "IMPROVES_UPON"}], reason="Exact match seed", path_str="BERT --[IMPROVES_UPON]--> RoBERTa")
        ],
        relationships=[
            {"source": "bert", "source_name": "BERT", "target": "roberta", "target_name": "RoBERTa", "relationship": "IMPROVES_UPON"}
        ],
        papers=[
            {"id": "roberta_paper", "title": "RoBERTa: A Robustly Optimized BERT Pretraining Approach", "year": 2019, "conference": "arXiv"}
        ]
    )

    builder = GraphPromptBuilder()
    query = "How does RoBERTa improve upon BERT?"

    prompt = builder.build_prompt(context, query)

    print("[Generated Prompt Output]")
    print("-" * 50)
    print(prompt)
    print("-" * 50)

    # Validations
    assert "SYSTEM INSTRUCTIONS" in prompt, "System instructions section missing!"
    assert "RETRIEVED GRAPH CONTEXT" in prompt, "Retrieved context section missing!"
    assert "Source Papers & Bibliography" in prompt, "Bibliography section missing!"
    assert "Key Entities" in prompt, "Key entities section missing!"
    assert "Reasoning Paths" in prompt, "Paths section missing!"
    assert query in prompt, "Query text missing from final prompt!"

    print("✓ Passed!")
    divider("ALL PROMPT BUILDER TESTS PASSED SUCCESSFUL")


if __name__ == "__main__":
    main()
