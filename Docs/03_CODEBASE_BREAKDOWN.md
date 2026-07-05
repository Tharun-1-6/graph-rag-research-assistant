# GraphRAG Codebase Breakdown

This document provides a comprehensive breakdown of the folders and files in the repository. It serves as a developer handbook for understanding the internals of each module.

---

## 1. Folder Breakdowns

### `graph/ingestion/`
- **Purpose:** Converts PDF research papers into clean text represented by unified Pydantic-like structures.
- **Responsibilities:** PDF text extraction, metadata extraction, whitespace normalization, unicode cleaning, and JSON serialization.
- **Dependencies:** `fitz` (PyMuPDF), Python standard library (`json`, `re`, `unicodedata`, `dataclasses`, `pathlib`).
- **Entry Points:** `PDFLoader.load()`
- **Exported Interfaces:** `Document` (data model), `PDFLoader` (loader), `TextCleaner` (cleaner), `DocumentExporter` (exporter).

### `graph/extraction/`
- **Purpose:** Governs the schema, models, parsing, validation, and normalization of LLM outputs.
- **Responsibilities:** Extract schema-conformant nodes and edges; ensure ontology compliance; deduplicate and clean names/IDs.
- **Dependencies:** `pydantic` (for parsing and validation), `llm` (for calling Gemini), `re`, `collections`.
- **Entry Points:** `GraphExtractor.extract()`
- **Exported Interfaces:** `GraphExtractor`, `ExtractionResult`, `NODE_TYPES`, `RELATIONSHIP_TYPES`, `VALID_CONNECTIONS`.

### `graph/graph_builder/`
- **Purpose:** Constructs the NetworkX knowledge graph and manages serialization.
- **Responsibilities:** Map paper metadata, entities, and relationships to NetworkX nodes and edges; enforce uniqueness; save/load graph states.
- **Dependencies:** `networkx`, `pyvis` (visualization).
- **Entry Points:** `GraphBuilder.build()`, `GraphManager.add_extraction()`
- **Exported Interfaces:** `GraphBuilder`, `GraphManager`, `GraphSerializer`.

### `llm/`
- **Purpose:** Standardizes the LLM interaction layer.
- **Responsibilities:** Abstract provider-specific logic (e.g., Google Gemini), handle API keys, specify generation parameters, format prompt templates.
- **Dependencies:** `google-genai` SDK, `python-dotenv`.
- **Entry Points:** `LLMClient` class.
- **Exported Interfaces:** `LLMClient`, `build_extraction_prompt()`.

---

## 2. File-by-File Technical Breakdown

### Ingestion Layer

#### [loader.py](file:///d:/Work/PROJECTS/grph-rag-research/graph/ingestion/loader.py)
- **Purpose:** Opens PDFs, extracts text from all pages, and builds an initial `Document` object with page counts and file paths.
- **Inputs:** `pdf_path: str | Path`
- **Outputs:** `Document`
- **Dependencies:** `fitz` (PyMuPDF), [document.py](file:///d:/Work/PROJECTS/grph-rag-research/graph/ingestion/document.py)
- **Internal Logic:** Spawns a fitz reader context, loops over all document pages, invokes `page.get_text("text")`, and joins page strings with `\n`.
- **Where Called:** `tests/test_ingestion.py`, `tests/test_extraction.py`, `tests/test_graph_builder.py`
- **Completeness:** **Complete**. Fully functional.

#### [cleaner.py](file:///d:/Work/PROJECTS/grph-rag-research/graph/ingestion/cleaner.py)
- **Purpose:** Cleans and normalizes extracted text.
- **Inputs:** `document: Document`
- **Outputs:** `Document` (modified in-place)
- **Dependencies:** `unicodedata`, `re`
- **Internal Logic:** Normalizes characters via `NFKC`, standardizes line endings (`\r\n` -> `\n`), strips trailing whitespace from lines, collapses 2+ spaces into 1, and limits consecutive blank lines to 2.
- **Where Called:** `tests/test_ingestion.py`, `tests/test_extraction.py`, `tests/test_graph_builder.py`
- **Completeness:** **Complete**. Fully functional.

#### [document.py](file:///d:/Work/PROJECTS/grph-rag-research/graph/ingestion/document.py)
- **Purpose:** Holds state for a research paper during loading, cleaning, and exporting.
- **Attributes:** `paper_id`, `filename`, `file_path`, `raw_text`, `cleaned_text`, `metadata`.
- **Completeness:** **Complete**.

#### [exporter.py](file:///d:/Work/PROJECTS/grph-rag-research/graph/ingestion/exporter.py)
- **Purpose:** Saves/loads `Document` objects to/from JSON files.
- **Completeness:** **Complete**.

---

### Extraction Layer

#### [schema.py](file:///d:/Work/PROJECTS/grph-rag-research/graph/extraction/schema.py)
- **Purpose:** Serves as the ontology specification for the graph.
- **Key Variables:** 
  - `NODE_TYPES`: Set of allowed nodes (e.g. `Paper`, `Author`, `Method`, `Dataset`, `Task`, `Metric`).
  - `RELATIONSHIP_TYPES`: Set of allowed edge labels (e.g. `AUTHORED`, `USES`, `PROPOSES`, `EVALUATED_ON`).
  - `VALID_CONNECTIONS`: Explicit tuples representing `(Source_Type, Relationship, Target_Type)`.
- **Completeness:** **Complete**.

#### [models.py](file:///d:/Work/PROJECTS/grph-rag-research/graph/extraction/models.py)
- **Purpose:** Defines Pydantic validation schemas (`Paper`, `Entity`, `Relationship`, `ExtractionResult`).
- **Completeness:** **Complete**.

#### [parser.py](file:///d:/Work/PROJECTS/grph-rag-research/graph/extraction/parser.py)
- **Purpose:** Converts raw LLM output into `ExtractionResult`. Handles backward compatibility mapping old prompts (returning keys like `methods`, `datasets`) to generic `Entity` objects.
- **Completeness:** **Complete**.

#### [validator.py](file:///d:/Work/PROJECTS/grph-rag-research/graph/extraction/validator.py)
- **Purpose:** Enforces ontology validity on `ExtractionResult`. Strips edges that fail the `VALID_CONNECTIONS` check, filters duplicate entities, and logs warnings.
- **Completeness:** **Complete**.

#### [normalizer.py](file:///d:/Work/PROJECTS/grph-rag-research/graph/extraction/normalizer.py)
- **Purpose:** Standardizes spacing, capitalization, and IDs of entities. Re-links source and target ID changes in relationships.
- **Completeness:** **Complete**.

#### [extractor.py](file:///d:/Work/PROJECTS/grph-rag-research/graph/extraction/extractor.py)
- **Purpose:** The facade representing the extraction layer. Orchestrates building prompt -> LLM call -> parsing -> validating -> normalizing.
- **Completeness:** **Complete**.

---

### Graph Builder Layer

#### [builder.py](file:///d:/Work/PROJECTS/grph-rag-research/graph/graph_builder/builder.py)
- **Purpose:** Simplistic implementation to build a NetworkX `MultiDiGraph` from an `ExtractionResult`.
- **Completeness:** **Complete**, but overlaps with `graph_manager.py`.

#### [graph_manager.py](file:///d:/Work/PROJECTS/grph-rag-research/graph/graph_builder/graph_manager.py)
- **Purpose:** Wrapper manager class around NetworkX graph operations, node/edge additions, serialization, and statistics.
- **Issues:** **Incomplete/Broken**. 
  - Line 30-31: `from .node_factory import create_node` and `from .edge_factory import create_edge` fail because those functions do not exist in the factories.
  - Line 51: Calls `create_node(entity)`, causing an `ImportError` or `NameError`.
  - Line 73: Calls `create_edge(relationship)`, causing a similar error.
- **Where Called:** Nowhere currently in tests due to import crashes.

#### [node_factory.py](file:///d:/Work/PROJECTS/grph-rag-research/graph/graph_builder/node_factory.py)
- **Purpose:** A factory class wrapping node insertion.
- **Completeness:** **Complete** as a class `NodeFactory`, but lacks the standalone `create_node` function expected by `graph_manager.py`.

#### [edge_factory.py](file:///d:/Work/PROJECTS/grph-rag-research/graph/graph_builder/edge_factory.py)
- **Purpose:** A factory class wrapping edge insertion and validation.
- **Completeness:** **Complete** as a class `EdgeFactory`, but lacks the standalone `create_edge` function expected by `graph_manager.py`.

#### [serializer.py](file:///d:/Work/PROJECTS/grph-rag-research/graph/graph_builder/serializer.py)
- **Purpose:** Serializes a NetworkX graph into/from standard JSON representation.
- **Completeness:** **Complete**.

#### [utils.py](file:///d:/Work/PROJECTS/grph-rag-research/graph/graph_builder/utils.py)
- **Purpose:** Provides ID mapping, deduplication routines, and graph statistics utilities.
- **Completeness:** **Complete**.

---

### LLM Layer

#### [client.py](file:///d:/Work/PROJECTS/grph-rag-research/llm/client.py)
- **Purpose:** Orchestrates factory lookup and serves request calls.
- **Completeness:** **Complete**.

#### [config.py](file:///d:/Work/PROJECTS/grph-rag-research/llm/config.py)
- **Purpose:** Loads environment keys, defines model names, and validates the presence of `GEMINI_API_KEY`.
- **Completeness:** **Complete**.

#### [prompts.py](file:///d:/Work/PROJECTS/grph-rag-research/llm/prompts.py)
- **Purpose:** Prompt templates definition.
- **Completeness:** **Complete**.

#### [provider/factory.py](file:///d:/Work/PROJECTS/grph-rag-research/llm/provider/factory.py)
- **Purpose:** Instantiates providers like `GeminiProvider`.
- **Completeness:** **Complete**.

#### [provider/gemini.py](file:///d:/Work/PROJECTS/grph-rag-research/llm/provider/gemini.py)
- **Purpose:** Invokes Google GenAI Client with appropriate configurations.
- **Completeness:** **Complete**.
