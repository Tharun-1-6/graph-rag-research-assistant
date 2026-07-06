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
    "source": "Exact Name of Source Entity",
    "relationship": "ALLOWED_RELATIONSHIP_TYPE",
    "target": "Exact Name of Target Entity"
}}

Relationship Rules:
1. The "source" and "target" values MUST match exactly one of the entity strings you extracted in the lists (e.g. authors, institutions, methods, datasets, etc.) or the paper's title.
2. Create all valid relationships described in the paper. For example, connect authors to institutions (AFFILIATED_WITH), papers to proposed methods (PROPOSES), methods to datasets (USES), etc.
3. Only use the allowed relationship types below.

Allowed relationship types:

AUTHORED
AFFILIATED_WITH
PUBLISHED_AT
PROPOSES
USES
EVALUATED_ON
PERFORMS
IMPROVES_UPON
BELONGS_TO
RELATED_TO

Research Paper
==============

{document.cleaned_text}
"""

    return prompt