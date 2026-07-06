# GraphRAG Research Assistant — Tech Demo Walkthrough

---

## Slide 1 — Introduction

**"So what is this system, and why does it exist?"**

Traditional chatbots answer questions by searching through raw text — like using Ctrl+F on a giant document. That works fine for simple lookups, but the moment you ask something relational — *"How does this method connect to this dataset?"* or *"Who authored papers that proposed this architecture?"* — plain text search breaks down completely.

This project solves that with a **Hybrid RAG system** — it combines two retrieval strategies:

- **Vector RAG** — semantic text search using embeddings
- **Graph RAG** — structured traversal over a Knowledge Graph

Both live side by side, and the system intelligently decides which one to use for each query.

---

## Slide 2 — The Papers We Work With

**"Let's talk about what we're feeding into this system."**

The knowledge base is built from **landmark NLP research papers** — all PDFs:

- *Attention Is All You Need* (Transformers)
- *BERT* — Bidirectional Encoder Representations from Transformers
- *RoBERTa* — A Robustly Optimized BERT
- *ALBERT* — A Lite BERT
- *DeBERTa*

These aren't random picks. They form a tightly interconnected research family — same authors, shared datasets, methods that build on each other. This makes them a perfect stress test for relational reasoning.

---

## Slide 3 — The Ingestion Pipeline

**"Before we can ask anything, we need to build the knowledge base."**

When the system starts up, it checks whether a local index already exists. If not, it automatically kicks off the **Ingestion Pipeline**.

Two things are built in parallel:

### 1. Vector Index (FAISS)
- PDFs are parsed, cleaned, and chunked using LangChain's `RecursiveCharacterTextSplitter`
- Each chunk is embedded using `sentence-transformers/all-MiniLM-L6-v2`
- Embeddings are stored in a **local FAISS index** — no external vector DB needed

### 2. Knowledge Graph (GraphML)
- An LLM runs **entity and relationship extraction** over each paper
- It identifies entities like `Paper`, `Author`, `Method`, `Dataset`, `Architecture`, `Conference`
- It maps relationships like `AUTHORED`, `PROPOSES`, `USES_DATASET`, `CITES`, `TRAINED_ON`
- Everything is assembled into a **NetworkX MultiDiGraph** and persisted as a `.graphml` file

Both indexes live locally — the system is self-contained.

---

## Slide 4 — The Query Router

**"This is the brain of the system — the part that decides how to answer your question."**

Before any retrieval happens, every user query passes through the **Query Router**.

The router uses an LLM to classify the query into one of four routes:

| Route | When it's used |
|---|---|
| `RAG` | Specific facts, numbers, definitions — best answered from raw text |
| `GRAPH_RAG` | Relational, multi-hop, structural queries — best answered by traversing connections |
| `COMBINED` | Complex queries needing both graph traversal and text details |
| `GENERAL` | Greetings, off-topic, "what can you do?" — no retrieval needed |

The router is aware of the full graph ontology — it knows what node types and relationship types exist, and uses that knowledge to make the routing decision.

A simple greeting like *"hello"* is short-circuited immediately — no LLM call needed, no latency.

---

## Slide 5 — Vector RAG (The Text Side)

**"For factual, text-heavy queries — this is what fires."**

When a query is routed to `RAG` or `COMBINED`, the **Vector Retrieval Pipeline** runs:

1. The query is embedded using the same model used during ingestion
2. FAISS performs a cosine similarity search across all stored chunks
3. The top matching chunks are returned with page numbers and similarity scores
4. A `context_builder` deduplicates, merges, and formats these into clean Markdown snippets
5. These snippets are injected directly into the LLM prompt

This gives the LLM precise, grounded text to pull answers from — no hallucination about what the paper actually says.

---

## Slide 6 — Graph RAG (The Relational Side)

**"For questions about connections, authors, and lineage — this is the engine."**

When a query is routed to `GRAPH_RAG` or `COMBINED`, the **Graph Retriever** fires. This is a multi-stage pipeline:

### Step 1 — Query Parsing
The query is parsed to extract candidate entity names, keywords, noun phrases, and verbs.

### Step 2 — Intent Detection
A rule-based intent classifier maps the query to intents like `AUTHOR_QUERY`, `METHOD_QUERY`, `DATASET_QUERY`, `COMPARISON_QUERY`, and more. Each intent configures a specific retrieval plan.

### Step 3 — Retrieval Planning
Based on intent, the planner sets:
- Which node types to search
- Which relationship types are allowed
- How deep to traverse (depth 1 for simple author lookups, depth 3 for comparisons)
- Node budget limits

### Step 4 — Seed Matching
Candidate entities from the query are matched against graph nodes using hierarchical matching (exact → alias → fuzzy). Confidence scores are assigned.

### Step 5 — Graph Traversal
Starting from the matched seed nodes, the traverser walks the graph following priority relationships first (`AUTHORED`, `PROPOSES` before generic `RELATED_TO`). **Paper nodes are treated as traversal hubs** — they bridge authors, methods, datasets, and architectures.

### Step 6 — Ranking & Pruning
Retrieved nodes are scored based on path length, edge weight, and exact match bonuses. Connected component pruning keeps only the most relevant subgraph (or both components for comparison queries).

### Step 7 — Context Formatting
The ranked subgraph is formatted into a structured Markdown block — organized by intent — and injected into the LLM prompt.

---

## Slide 7 — The LLM Layer

**"Multiple models, switchable on the fly."**

The system supports multiple LLM providers through a clean **factory pattern**:

- **Groq** — Llama 3.3 70B (default), Llama 3.1 8B, Qwen 3 32B, GPT OSS 120B
- **Google Gemini** — Gemini 2.5 Flash

You can switch models from a **dropdown in the UI** — no server restart needed. The orchestrator swaps the provider dynamically per request.

The LLM receives:
- The retrieved context (graph subgraph, text chunks, or both)
- A structured prompt designed for the detected intent
- And returns a clean, natural language answer

---

## Slide 8 — The Web Interface

**"Let's look at the actual UI."**

The frontend is a clean Flask web app with two main panels, switchable via tabs:

### 💬 Chat Interface
- Type any question about the papers
- The orchestrator routes, retrieves, and answers in real time
- Responses are rendered as full Markdown — including headers, code blocks, and lists
- A collapsible **"Routing & Retrieval Details"** block shows exactly what happened:
  - Which route was chosen and why
  - Graph traversal metrics (nodes visited, edges retained, latency)
  - Top ranked nodes with scores
  - The raw text snippets that were retrieved

### 🕸️ Knowledge Graph Explorer
- The full Knowledge Graph is rendered as an **interactive vis.js network**
- You can click any node to inspect it
- A side panel shows the node's type, connections, and description
- You can generate AI descriptions for nodes — the LLM pulls RAG context and writes a concise 2–3 sentence summary, saved back into the graph
- You can even **chat about a specific node** — a focused chat interface appears, pre-loaded with that node's relationships and document context

---

## Slide 9 — The Debug Trace

**"This part is what makes it transparent."**

Every response includes a live **retrieval trace** showing the system's internal reasoning:

- **Route Chosen** — `RAG`, `GRAPH_RAG`, or `COMBINED`
- **Reasoning** — why the LLM router picked that route
- **Resolved Seeds** — which graph nodes were matched from the query (with confidence scores)
- **Detected Intent** — e.g., `METHOD_QUERY`, `AUTHOR_QUERY`
- **Traversal Latency** — how long the graph walk took in milliseconds
- **Nodes Visited vs. Retained** — showing how the pruning worked
- **Top Ranked Nodes** — the nodes that contributed most to the answer
- **Vector Snippets** — the exact text chunks pulled from FAISS

This makes the system fully auditable — you can see exactly why it answered the way it did.

---

## Slide 10 — Quick Demo Flow

**"Here's what I'll show you live."**

1. **Ask a factual question** → *"What is the masked language model objective used in BERT?"*
   - Routes to `RAG` — answers from paper text directly

2. **Ask a relational question** → *"Who are the authors of the paper that proposed the Transformer architecture?"*
   - Routes to `GRAPH_RAG` — traverses `Paper → AUTHORED_BY → Author`

3. **Ask a comparison** → *"How does BERT differ from ALBERT in terms of architecture?"*
   - Routes to `COMBINED` — uses both graph connections and text snippets

4. **Open the Graph Explorer** → Click a node, generate a description, chat about it

5. **Switch models** → Swap from Llama 3.3 to Gemini 2.5 Flash mid-session

---

## Slide 11 — Summary

**"What did we build?"**

A **self-contained, hybrid RAG research assistant** that:

- Ingests real research PDFs and builds both a vector index and a knowledge graph automatically
- Intelligently routes every query to the right retrieval strategy
- Traverses entity relationships with intent-awareness, depth budgets, and path ranking
- Supports multiple LLMs switchable at runtime
- Presents a clean chat UI with transparent, auditable retrieval traces
- Includes an interactive graph explorer with AI-generated node descriptions and node-focused chat

Everything runs locally. No cloud vector DB. No external graph database. Just Python, Flask, FAISS, NetworkX, and the LLM APIs.

---

*Built as a research prototype exploring hybrid retrieval architectures for scientific literature.*
