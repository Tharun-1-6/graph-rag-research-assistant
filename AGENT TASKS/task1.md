# Repository Reverse Engineering & Architecture Documentation

You are acting as a senior software architect, systems analyst, and AI engineer.

You have access to the complete repository.

Your task is **NOT** to fix or modify the code.

Instead, your task is to reverse engineer the entire project and produce comprehensive technical documentation that allows another engineer to completely understand the system without reading the source code.

The repository owner has explicitly stated that the project is **not functioning as intended**. Therefore, you must treat the implementation as potentially incomplete, inconsistent, or partially broken.

Do not assume that comments, README files, variable names, or architecture are correct. Infer the actual design from the implementation.

---

## Phase 1 — Repository Analysis

Read EVERY file inside the repository including but not limited to:

* source code
* configuration files
* documentation
* prompts
* notebooks
* scripts
* Docker files
* package managers
* requirements
* environment files
* build files
* tests
* assets
* examples

Construct a complete understanding before generating any documentation.

Do not skip files because they appear unimportant.

---

## Phase 2 — Reverse Engineer the System

Determine:

* What problem the project attempts to solve
* The intended users
* The expected workflow
* The overall architecture
* How information flows through the system
* What external APIs are used
* What models are used
* Which databases are used
* Which vector databases are used
* Whether knowledge graphs are used
* Whether Graph RAG is implemented correctly
* Which components are complete
* Which components are placeholders
* Which components appear abandoned
* Which files are dead code
* Which files are never referenced
* Which parts of the architecture disagree with each other

Whenever uncertainty exists:

Clearly label it as

"Evidence suggests..."

instead of presenting speculation as fact.

---

## Phase 3 — Produce FIVE Markdown Documents

Generate the following files.

---

### 01_PROJECT_OVERVIEW.md

Include:

* Executive Summary
* Intended Goal
* Core Idea
* Business Problem
* Research Problem
* Target Users
* Expected User Journey
* Features the project attempts to provide
* Current implementation status
* Missing capabilities
* High-level system overview

Include diagrams using Mermaid whenever appropriate.

---

### 02_ARCHITECTURE.md

Produce a complete architecture document.

Include:

* Overall architecture
* Component hierarchy
* Folder responsibilities
* Module interactions
* Data flow
* Request flow
* Response flow
* API communication
* Model communication
* Retrieval pipeline
* Graph construction pipeline
* Graph querying pipeline
* Embedding pipeline
* Storage pipeline

Generate Mermaid diagrams for:

* Component diagram
* Sequence diagram
* Data flow diagram
* Dependency diagram

Every important module should be explained individually.

---

### 03_CODEBASE_BREAKDOWN.md

For every important folder:

Explain

* purpose
* responsibilities
* important classes
* important functions
* major algorithms
* dependencies
* entry points
* exported interfaces

For every important source file:

Include

* purpose
* inputs
* outputs
* dependencies
* what happens internally
* where it is called
* whether it appears complete

This document should act as a developer handbook.

---

### 04_GRAPH_RAG_ANALYSIS.md

Assume the project intends to implement a Graph RAG system.

Determine:

* Is it actually Graph RAG?
* Which Graph RAG architecture it follows (if any)
* Graph creation process
* Entity extraction process
* Relationship extraction
* Community detection
* Retrieval strategy
* Graph traversal strategy
* Embedding strategy
* LLM interaction
* Query planning
* Retrieval ranking

Then compare the implementation against current Graph RAG best practices.

List:

* strengths
* weaknesses
* architectural mistakes
* scalability concerns
* performance bottlenecks
* missing Graph RAG components

If the implementation differs from standard Graph RAG, explain exactly how.

---

### 05_PROJECT_DIAGNOSIS_AND_NEXT_STEPS.md

Perform a technical audit.

Include:

* What currently works
* What likely fails
* What is incomplete
* Architectural inconsistencies
* Technical debt
* Dead code
* Duplicate logic
* Potential bugs
* Missing environment variables
* Missing APIs
* Configuration issues
* Dependency issues
* Build issues

Then provide:

Priority 1 (critical)

Priority 2 (important)

Priority 3 (future improvements)

Finally produce a roadmap showing the recommended order of implementation to transform the repository into a production-ready system.

---

## Documentation Requirements

The documentation must be sufficiently detailed that a new engineer could understand the entire system without opening the source code.

Do not summarize.

Explain.

Use headings.

Use tables.

Use Mermaid diagrams.

Include references to relevant files whenever discussing architecture.

Clearly distinguish:

* Verified facts
* Reasonable inferences
* Unknowns

Do not modify the repository.

Do not generate code changes.

Your only deliverable is the five markdown documents.
