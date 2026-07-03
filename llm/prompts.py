'''
this file stores all the prompts that are going to be used in this project 
'''
"""
prompt.py

Stores all prompt templates used by the project.

For now, only the extraction prompt is implemented.
More prompts can be added later for routing,
answer generation and summarization.
"""

from graph.ingestion.document import Document

def build_extraction_prompt(
    document: Document,
) -> str:
    """
    Builds the extraction prompt.
    """

    prompt = f"""
You are an expert AI researcher.

Your task is to extract structured knowledge from the following research paper.

Return ONLY valid JSON.

The JSON MUST follow this schema:

{{
    "paper": {{
        "id": "",
        "title": "",
        "year": "",
        "conference": ""
    }},

    "authors": [],

    "institutions": [],

    "methods": [],

    "architectures": [],

    "datasets": [],

    "benchmarks": [],

    "tasks": [],

    "metrics": [],

    "topics": [],

    "relationships": []
}}

Relationship format:

{{
    "source": "",
    "relationship": "",
    "target": ""
}}

Allowed relationship types:

AUTHORED
PROPOSES
USES
EVALUATED_ON
PERFORMS
BASED_ON
IMPROVES_UPON
BELONGS_TO
AFFILIATED_WITH
PUBLISHED_AT

Research Paper
==============

{document.cleaned_text}
"""

    return prompt