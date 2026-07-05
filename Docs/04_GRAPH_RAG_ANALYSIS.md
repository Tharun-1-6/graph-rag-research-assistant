# GraphRAG Implementation Analysis

This document evaluates the project's GraphRAG implementation against standard patterns and industry best practices.

---

## 1. GraphRAG Architecture Assessment

### Is it actually Graph RAG?
Currently, **no**. The repository contains the **Graph Construction** and **Ingestion** parts of a GraphRAG system, but lacks the **Retrieval** (RAG) and **Querying** components.
- **What exists:** An ingestion pipeline that parses PDFs and uses an LLM to extract nodes and relationships under a rigid ontology, inserting them into a NetworkX graph structure.
- **What is missing:** Vector database storage, text chunk embedding, entity-to-chunk linking, graph traversal query logic, and an LLM generation step that uses retrieved graph context.

### Which Graph RAG Architecture does it follow?
If completed, it is positioned to follow a **Schema-Driven / Ontology-Based GraphRAG** architecture, similar to Microsoft's GraphRAG or custom knowledge-graph-enhanced RAG systems.
- Unlike Microsoft's GraphRAG which uses hierarchical community summaries of text chunks, this project relies on a **structured domain ontology** (defined in `schema.py`) to enforce valid node classes (e.g. `Method`, `Dataset`, `Metric`) and edges.
- It attempts to resolve entities globally across document boundaries via `EntityNormalizer`.

---

## 2. Step-by-Step GraphRAG Pipeline Analysis

### Graph Creation Process
- The graph is created using the NetworkX library as a `MultiDiGraph` (directed graph allowing multiple edges between the same nodes).
- Paper metadata is linked as the primary source hub, and entities are added as independent nodes.

### Entity & Relationship Extraction Process
- Extraction is performed in a single shot per document text by passing the cleaned text to Gemini (`gemini-2.5-flash` or `gemini-2.5-pro`).
- The prompt defined in `llm/prompts.py` specifies a strict JSON structure containing authors, methods, datasets, etc., and a list of relationships mapping source and target.
- **Critique:** The extraction prompt is extremely basic. It provides no context on how to segment very long research papers (e.g., chunking), meaning the entire text is sent at once, which can exceed the model's single-response token limit or result in skipped details (context window degradation).

### Missing GraphRAG Components
- **Community Detection:** Standard GraphRAG architectures (like Microsoft's) run Leiden or Louvain community detection algorithms on the graph to cluster related topics and generate abstract summaries of these communities. There is no community detection implemented.
- **Retrieval & Traversal Strategy:** There is no code to query the graph. A typical strategy involves:
  1. *Entity Linking:* Extracting entities from a user query, linking them to nodes in the KG.
  2. *Graph Traversal:* Performing $N$-hop neighborhood lookups or PageRank-based walks.
- **Embedding Strategy:** There are no embeddings generated for nodes or text chunks.
- **Query Planning & Retrieval Ranking:** No query decomposition or graph-retrieval ranking algorithms exist.

---

## 3. Comparison Against Best Practices

| Standard GraphRAG Best Practice | Current Project Implementation | Gap / Critique |
| :--- | :--- | :--- |
| **Document Chunking:** Documents are split into overlapping chunks (e.g., 600 tokens) before entity extraction. | Entire paper text is sent to the LLM in one prompt. | **High Risk:** The LLM will miss fine-grained entities/relationships due to long context length constraints. |
| **Entity Resolution:** Fuzzy matching and semantic clustering of entity names. | Exact lowercase conversion and character stripping in `normalizer.py`. | **Weak:** A minor change in phrasing (e.g., "Transformer model" vs. "Transformer architecture") will fail to merge. |
| **Hierarchical Clustering:** Grouping graph nodes into communities to support global summaries. | Flat network topology. | Cannot answer broad global queries (e.g., "What are the overall trends in the uploaded papers?"). |
| **Hybrid Search:** Combines vector similarity on chunks with graph traversal. | No vector storage or query logic implemented. | No capability to retrieve context. |

---

## 4. Strengths, Weaknesses, and Bottlenecks

### Strengths
1. **Strong Schema Enforcement:** Enforcing `VALID_CONNECTIONS` prevents "hallucinated" relationship types from the LLM, keeping the graph clean and aligned to the academic domain.
2. **Modular Architecture:** The parser, validator, and normalizer are isolated, making it easy to swap parsing rules or normalization techniques.

### Weaknesses & Architectural Mistakes
1. **Duplicate and Broken Graph Architectures:** `GraphBuilder` works but is basic. `GraphManager` is broken due to non-existent factory imports. This causes imports to fail and creates confusion about which class to use.
2. **Lack of Chunking:** Feeding 30k+ characters of scientific text to Gemini in one prompt will lead to incomplete extractions.
3. **No Vector Indexing:** A graph without chunk embeddings cannot handle queries that do not exactly match entity names.

### Performance Bottlenecks & Scalability Concerns
- **In-Memory NetworkX:** NetworkX stores the entire graph in RAM. For thousands of papers, this will exhaust memory. A graph database (e.g. Neo4j, FalkorDB) is required for production.
- **API Limits and Cost:** Running full-text JSON extraction on every paper without incremental chunking is computationally expensive and runs into rate limit issues on larger document batches.
