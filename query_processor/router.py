import json
import logging
import concurrent.futures
from typing import Callable, Dict, Any, Optional

from llm.client import LLMClient
from graph.extraction.schema import NODE_TYPES, RELATIONSHIP_TYPES

logger = logging.getLogger(__name__)

class QueryRouter:
    """
    Classifies an input query to determine the best retrieval strategy based on
    the system ontology schema:
    - RAG: Text-based/vector search for specific, factual, local details.
    - GRAPH_RAG: Graph traversal for relational, comparative, multi-hop or structural queries.
    - COMBINED: Both methods for complex, cross-cutting queries.
    """
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()

    def route(self, query: str) -> Dict[str, Any]:
        """
        Classifies the query.
        Returns a dict: {"route": "RAG" | "GRAPH_RAG" | "COMBINED", "reasoning": str}
        """
        # Format schema metadata for the LLM
        nodes_str = ", ".join(sorted(NODE_TYPES))
        relations_str = ", ".join(sorted(RELATIONSHIP_TYPES))

        prompt = f"""You are an intelligent query router for a research assistant system.
We maintain a Knowledge Graph of research literature structured using the following ontology:

Entity Types (Nodes):
{nodes_str}

Relationship Types (Edges):
{relations_str}

Analyze the user's query:
1. "RAG": Choose this if the query is best answered by retrieving raw text paragraphs, specific facts, numbers, parameter details, definitions, or local details from inside the paper texts, without needing to traverse connections between different entities.
2. "GRAPH_RAG": Choose this if the query is best answered by traversing and analyzing connections, affiliations, or structural relationships between the Entity Types using the Relationship Types (e.g. tracing lineage, authorship, which Method uses which Dataset, etc.).
3. "COMBINED": Choose this if the query requires both (e.g., tracing a connection or comparing entities across the graph AND needing detailed factual definitions, parameter values, or exact text details from the papers).

Your response MUST be a valid JSON object matching the following schema exactly:
{{
    "route": "RAG" | "GRAPH_RAG" | "COMBINED",
    "reasoning": "A detailed explanation of why this route is chosen based on the required node/relationship types and text details."
}}

User Query:
"{query}"
"""
        try:
            response_text = self.llm_client.generate_json(prompt, temperature=0.0)
            data = json.loads(response_text)
            
            # Normalize route value
            route = data.get("route", "COMBINED").upper()
            if route not in ["RAG", "GRAPH_RAG", "COMBINED"]:
                route = "COMBINED"
                
            return {
                "route": route,
                "reasoning": data.get("reasoning", "Defaulting to combined routing.")
            }
        except Exception as e:
            logger.error(f"Error during query routing: {e}")
            return {
                "route": "COMBINED",
                "reasoning": f"Failed to classify query due to error: {str(e)}. Defaulted to COMBINED."
            }


class QueryOrchestrator:
    """
    Orchestrates the retrieval flow by routing the query, executing
    the required retrieval pipelines (RAG and/or Graph-RAG) in parallel if needed,
    and synthesizing/comparing their contexts if both are run.
    """
    def __init__(
        self,
        rag_retriever: Optional[Callable[[str], str]] = None,
        graph_rag_retriever: Optional[Callable[[str], str]] = None,
        llm_client: Optional[LLMClient] = None
    ):
        self.rag_retriever = rag_retriever
        self.graph_rag_retriever = graph_rag_retriever
        self.llm_client = llm_client or LLMClient()
        self.router = QueryRouter(self.llm_client)

    def register_rag_retriever(self, retriever: Callable[[str], str]) -> None:
        """Register the RAG retrieval function/pipeline hook."""
        self.rag_retriever = retriever

    def register_graph_rag_retriever(self, retriever: Callable[[str], str]) -> None:
        """Register the Graph-RAG retrieval function/pipeline hook."""
        self.graph_rag_retriever = retriever

    def _execute_retriever(self, name: str, retriever: Optional[Any], query: str) -> Any:
        """Executes a retriever safely, returning empty string or error info on failure."""
        if not retriever:
            logger.warning(f"{name} retriever is not registered.")
            return f"[{name} context unavailable: Retriever not registered]"
        try:
            # 1. Handle GraphRetriever (upgraded v3 Graph RAG)
            if retriever.__class__.__name__ == "GraphRetriever" and hasattr(retriever, "retrieve"):
                return retriever.retrieve(query)
                
            # 2. Execute RAG / general callable
            result = retriever(query) if callable(retriever) else retriever.run(query)
            
            # 3. Format LangChain/FAISS dictionary output if returned
            if isinstance(result, dict) and "retrieved_chunks" in result:
                # Import context builder dynamically to apply deduplication and character budgets
                from context_builder import build_context
                llm_context_data = build_context(result)
                
                # Format into a clean Markdown block for LLM consumption
                formatted_snippets = []
                for idx, item in enumerate(llm_context_data.get("context", []), 1):
                    source = item.get("source", "Unknown Document")
                    page = f", Page {item.get('page')}" if item.get("page") is not None else ""
                    content = item.get("content", "").strip()
                    formatted_snippets.append(f"[{idx}] Source: {source}{page}\n{content}")
                    
                return "\n\n---\n\n".join(formatted_snippets)
                
            return str(result)
        except Exception as e:
            logger.error(f"Error executing {name} retriever: {e}")
            return f"[{name} context retrieval error: {str(e)}]"

    def consolidate_contexts(self, query: str, rag_context: str, graph_context: str) -> str:
        """
        Uses the LLM to compare, consolidate, and clean up the retrieved context.
        Resolves conflicts and generates a coherent consolidated knowledge base.
        """
        prompt = f"""You are a knowledge consolidation layer.
We have retrieved two sets of context for the query: "{query}"

1. Vector RAG Context (Text-based facts, local snippets):
---
{rag_context}
---

2. Graph-RAG Context (Relational structures, entity connections, schema ontology paths):
---
{graph_context}
---

Your task:
- Compare both contexts.
- Reconcile any duplicate or contradictory information.
- Synthesize them into a clean, comprehensive, structured knowledge base context that directly helps answer the user's query.
- Maintain key details, specific metrics, author names, methods, and relationships.
- Keep the output clear and factual.

Consolidated Context:
"""
        try:
            return self.llm_client.generate(prompt, temperature=0.2)
        except Exception as e:
            logger.error(f"Error during context consolidation: {e}")
            return f"--- Vector RAG Context ---\n{rag_context}\n\n--- Graph-RAG Context ---\n{graph_context}"

    def generate_answer(self, query: str, context: str) -> str:
        """
        Uses the consolidated context to answer the user's query.
        """
        prompt = f"""You are a helpful and expert AI research assistant.
Your task is to answer the user's query using the provided context.
Ensure the answer is comprehensive, accurate, and directly grounded in the provided context.

Query:
{query}

Context:
---
{context}
---

Answer:
"""
        try:
            return self.llm_client.generate(prompt, temperature=0.3)
        except Exception as e:
            logger.error(f"Error during final answer generation: {e}")
            return f"[Error generating answer: {str(e)}]"

    def run(self, query: str) -> Dict[str, Any]:
        """
        Runs the full routing, retrieval, and answering pipeline.
        
        Returns:
            Dict containing:
                "route": The chosen route.
                "reasoning": The route decision reasoning.
                "rag_context": Raw RAG context (if executed).
                "graph_context": Raw Graph-RAG context (if executed).
                "graph_result": Full RetrievalResult object (if executed).
                "final_context": Synthesized and compared context built for the LLM.
                "answer": The generated answer based on the context.
        """
        route_decision = self.router.route(query)
        route = route_decision["route"]
        reasoning = route_decision["reasoning"]

        rag_context = ""
        graph_context = ""
        graph_result = None
        final_context = ""

        if route == "RAG":
            rag_context = self._execute_retriever("RAG", self.rag_retriever, query)
            final_context = rag_context

        elif route == "GRAPH_RAG":
            graph_result = self._execute_retriever("GRAPH_RAG", self.graph_rag_retriever, query)
            if hasattr(graph_result, "context"):
                graph_context = graph_result.context
            else:
                graph_context = str(graph_result)
            final_context = graph_context

        else:  # COMBINED
            # Execute both in parallel using ThreadPoolExecutor
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                rag_future = executor.submit(self._execute_retriever, "RAG", self.rag_retriever, query)
                graph_future = executor.submit(self._execute_retriever, "GRAPH_RAG", self.graph_rag_retriever, query)
                
                # Wait for both to complete
                rag_context = rag_future.result()
                graph_result = graph_future.result()

            if hasattr(graph_result, "context"):
                graph_context = graph_result.context
            else:
                graph_context = str(graph_result)

            # Compare and consolidate the outputs
            final_context = self.consolidate_contexts(query, rag_context, graph_context)

        # Generate the final answer using the compiled context
        answer = self.generate_answer(query, final_context)

        return {
            "query": query,
            "route": route,
            "reasoning": reasoning,
            "rag_context": rag_context,
            "graph_context": graph_context,
            "graph_result": graph_result,
            "final_context": final_context,
            "answer": answer
        }
