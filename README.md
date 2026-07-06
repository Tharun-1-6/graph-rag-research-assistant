# GraphRAG Research Assistant

A self-contained **Hybrid Retrieval-Augmented Generation (RAG)** system for querying scientific literature. It combines a semantic vector index (FAISS) and a structured knowledge graph (NetworkX) to answer both factual and relational questions over research papers — with full transparency into every retrieval decision.

---

## Features

- **Hybrid Retrieval** — Intelligent query routing between Vector RAG, Graph RAG, or both
- **Knowledge Graph** — LLM-extracted entities and relationships from research PDFs, persisted as GraphML
- **Intent-Aware Graph Traversal** — 14-optimization retrieval engine with adaptive depths, path ranking, and pruning
- **Multi-LLM Support** — Groq (Llama 3.3 70B, Llama 3.1 8B, Qwen 3 32B) and Google Gemini 2.5 Flash, switchable at runtime
- **Interactive Web UI** — Flask chat interface with Markdown rendering and a live vis.js graph explorer
- **Auditable Traces** — Every response includes a full retrieval trace: route chosen, seeds matched, nodes traversed, latency
- **Self-Contained** — No external vector DB or graph database; everything runs locally

---

## Architecture Overview

```
User Query
    │
    ▼
┌─────────────────┐
│   Query Router  │  ← LLM-based classifier
└────────┬────────┘
         │
    ┌────┴─────┐
    │          │
    ▼          ▼
Vector RAG  Graph RAG
(FAISS)     (NetworkX)
    │          │
    └────┬─────┘
         ▼
   Context Builder
         │
         ▼
     LLM Response
```

### Routing Modes

| Route | When Used |
|---|---|
| `RAG` | Factual / definition queries — answered from raw text |
| `GRAPH_RAG` | Relational / multi-hop queries — answered by graph traversal |
| `COMBINED` | Complex queries requiring both text and graph context |
| `GENERAL` | Greetings and off-topic — no retrieval needed |

---

## Project Structure

```
graph_rag/
├── app.py                  # Flask application entry point
├── prototype.py            # CLI prototype
├── main.py                 # Pipeline orchestration
├── context_builder.py      # Vector context deduplication & formatting
│
├── graph/                  # Graph RAG engine
│   ├── ingestion/          # PDF parsing and entity extraction
│   ├── extraction/         # LLM-based entity & relationship extraction
│   ├── graph_builder/      # NetworkX graph construction & serialization
│   ├── retrieval/          # Graph retriever (matcher, planner, traverser, ranker, formatter)
│   ├── retriever.py        # GraphRetriever public interface
│   └── rag.py              # Graph RAG orchestration
│
├── ingestion/              # Vector RAG ingestion (LangChain + FAISS)
│   └── ingest.py
├── retrieval/              # Vector RAG retrieval
│   └── retrieve.py
├── query_processor/        # Query routing & orchestration
│   └── router.py
│
├── data/
│   ├── papers/             # Source PDF research papers
│   └── graphs/             # Persisted GraphML knowledge graph
├── db/                     # Local FAISS vector index (auto-generated)
│
├── static/                 # Frontend CSS & JS
├── templates/              # Flask HTML templates
└── tests/                  # Integration and retrieval benchmarks
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- API keys for at least one LLM provider (Groq or Google Gemini)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd graph_rag
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv .venv

   # Windows
   .venv\Scripts\activate

   # macOS / Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   Create a `.env` file in the project root:
   ```env
   GROQ_API_KEY=your_groq_api_key
   GEMINI_API_KEY=your_gemini_api_key
   ```

5. **Add your research papers**

   Place PDF files into `data/papers/`. The system ingests them automatically on first startup.

### Running the Web App

```bash
python app.py
```

Open `http://localhost:5000` in your browser.

On first run, the system will automatically:
- Build the FAISS vector index from the PDFs
- Load the pre-built knowledge graph from `data/graphs/global_graph.graphml`

### Running the CLI

```bash
python prototype.py
```

---

## Knowledge Base

The system is built around a curated set of landmark NLP research papers:

| Paper | Key Contribution |
|---|---|
| *Attention Is All You Need* | Transformer architecture |
| *BERT* | Bidirectional pre-training for NLP |
| *RoBERTa* | Optimized BERT pre-training |
| *ALBERT* | Parameter-efficient BERT variant |
| *DeBERTa* | Disentangled attention mechanisms |

These papers form a tightly interconnected research family — shared authors, datasets, and methods — making them an ideal stress test for relational reasoning.

---

## Graph RAG Pipeline

The graph retriever runs a 7-stage pipeline per query:

1. **Query Parsing** — Extracts candidate entity names, keywords, noun phrases, and verbs
2. **Intent Detection** — Rule-based classifier maps to intents: `AUTHOR_QUERY`, `METHOD_QUERY`, `DATASET_QUERY`, `COMPARISON_QUERY`, etc.
3. **Retrieval Planning** — Sets node types, allowed relationships, traversal depth (1–3), and node budgets per intent
4. **Seed Matching** — Hierarchical matching against graph nodes: exact → alias → fuzzy, with confidence scores
5. **Graph Traversal** — Priority-first BFS: high-value edges (`AUTHORED`, `PROPOSES`) before `RELATED_TO`; Paper nodes used as traversal hubs
6. **Ranking & Pruning** — Path scoring with distance penalties and exact-match bonuses; connected component pruning
7. **Context Formatting** — Intent-aware Markdown output, injected into the LLM prompt

### Graph Ontology

**Node Types**: `Paper`, `Author`, `Method`, `Dataset`, `Architecture`, `Conference`

**Relationship Types**: `AUTHORED`, `PROPOSES`, `USES_DATASET`, `CITES`, `TRAINED_ON`, `RELATED_TO`, and more

---

## Supported LLM Providers

| Provider | Models |
|---|---|
| **Groq** | Llama 3.3 70B *(default)*, Llama 3.1 8B, Qwen 3 32B, GPT OSS 120B, Mixtral 8x7B, Gemma 2 9B |
| **Google Gemini** | Gemini 2.5 Flash |

Models are switchable from the UI dropdown with no server restart. Falls back to Groq Llama 3.3 silently on Gemini quota errors.

---

## Web Interface

### 💬 Chat Tab
- Ask any question about the research papers in natural language
- Markdown-rendered responses with headers, code blocks, and lists
- Collapsible **Routing & Retrieval Details** panel showing:
  - Route chosen and reasoning
  - Resolved graph seed nodes with confidence scores
  - Traversal metrics (nodes visited, edges retained, latency)
  - Top-ranked nodes and raw vector snippets

### 🕸️ Graph Explorer Tab
- Interactive vis.js knowledge graph visualization
- Click any node to inspect its type, connections, and description
- Generate AI descriptions for nodes on demand (saved back into the graph)
- Node-focused chat — start a conversation scoped to any node

---

## Dependencies

| Package | Purpose |
|---|---|
| `flask` | Web application framework |
| `networkx` | Knowledge graph construction and traversal |
| `faiss-cpu` | Local vector similarity search |
| `langchain`, `langchain-community` | Vector RAG pipeline |
| `sentence-transformers` | Text embedding (`all-MiniLM-L6-v2`) |
| `google-genai` | Gemini LLM API |
| `groq` | Groq LLM API |
| `PyMuPDF` | PDF parsing |
| `pyvis` | Graph visualization |
| `pydantic` | Data validation |
| `python-dotenv` | Environment variable management |

---

## Example Queries

```
# Factual → routes to RAG
"What is the masked language model objective used in BERT?"

# Relational → routes to GRAPH_RAG
"Who are the authors of the paper that proposed the Transformer architecture?"

# Multi-hop comparison → routes to COMBINED
"How does BERT differ from ALBERT in terms of architecture?"

# Graph explorer
"What papers does Vaswani et al. cite?"
```

---

## License

This project was built as a research prototype exploring hybrid retrieval architectures for scientific literature.

---

*Built with Python · Flask · NetworkX · FAISS · LangChain · Groq · Google Gemini*
