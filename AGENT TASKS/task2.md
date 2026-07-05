You are working in a **new Git branch** containing the complete **Graph RAG pipeline**.

Your responsibilities are **strictly limited to analysis**.

### Rules

* Download and inspect all new files in this branch.
* **Do NOT modify, refactor, optimize, or generate any code.**
* **Do NOT edit a single file.**
* Treat the repository as read-only.
* Your only goal is to understand how the Graph RAG system works.

### What to Analyze

1. Explain the complete Graph RAG pipeline from input to output.
2. Identify the responsibilities of each major component.
3. Describe the data flow through the system.
4. Explain how the graph is constructed and traversed.
5. Identify all important interfaces, classes, functions, and configuration files.
6. Determine the expected inputs and outputs of the pipeline.
7. Pay special attention to the final output.

### Important Context

The Graph RAG pipeline produces an **LLM Context JSON**.

This JSON **does not contain the retrieved paper contents**. Instead, it describes the **relationships between research papers** (citations, semantic links, clusters, graph connections, etc.). It is intended to become one source of context for our orchestration layer.

### Integration Task (Analysis Only)

After understanding the pipeline, explain how it could integrate with our newly built LLM layer.

Specifically answer:

* Where should the Graph RAG pipeline be invoked?
* Which component should consume the generated LLM Context JSON?
* How should this relationship context be passed into the LLM pipeline?
* What interface would make the Graph RAG layer independent of the LLM implementation?
* What assumptions does the Graph RAG pipeline currently make that should be removed?

### Existing Architecture Change

Our current system contains a **temporary dummy RAG pipeline**.

Your task is to explain:

* How that dummy RAG layer can be cleanly disconnected.
* Which interfaces should remain unchanged.
* How the Graph RAG layer can replace it while keeping the overall architecture modular.
* How to ensure the Graph RAG pipeline remains completely independent from the LLM layer.

### Deliverables

Provide a report containing:

1. High-level architecture overview.
2. Pipeline walkthrough.
3. Component responsibilities.
4. Input/output specifications.
5. LLM Context JSON schema and explanation.
6. Recommended integration plan.
7. Required architectural changes (analysis only).
8. Potential issues or design improvements.

**Do not implement anything. Do not write code. Do not edit files. Only analyze the branch and produce a detailed architectural report.**
