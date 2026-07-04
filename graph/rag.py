"""
rag.py

Orchestrates the GraphRAG pipeline: retrieves relational context and prompts the LLM to generate an answer.
"""

from pathlib import Path
from llm.client import LLMClient
from graph.retriever import GraphRetriever


class GraphRAG:
    """
    Main pipeline for running Graph-based Retrieval-Augmented Generation.
    """

    def __init__(self, graph_path_or_dir: str | Path):
        """
        Initializes the retriever and LLM client.
        """
        self.retriever = GraphRetriever(graph_path_or_dir)
        self.llm = LLMClient()

    def query(self, user_query: str) -> str:
        """
        Answers a user query using relational context retrieved from the graph.
        """
        # Retrieve context
        context = self.retriever.retrieve_relational_context(user_query)

        # Build prompt
        prompt = f"""You are an expert research assistant answering questions using a structured knowledge graph built from academic papers.

Below is the relevant relational context (entities and their connections) retrieved from the knowledge graph:
======================================================================
{context}
======================================================================

User Query: {user_query}

Instructions:
1. Provide a comprehensive, accurate answer to the user query based ONLY on the retrieved relational context.
2. Structure your answer clearly, highlighting the entities and relationships mentioned in the context.
3. If the context does not contain enough information to answer the query, say so and list what information is missing.
"""

        # Generate response
        response = self.llm.generate(prompt)
        return response
