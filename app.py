import os
import sys
import json
from pathlib import Path
from flask import Flask, render_template, request, jsonify

# Import RAG Orchestration Components
from query_processor.router import QueryOrchestrator
from ingestion.ingest import IngestionPipeline
from retrieval.retrieve import RetrievalPipeline
from graph.retriever import GraphRetriever

# Reconfigure stdout/stderr to use UTF-8 to prevent 'charmap' encode crashes on Windows
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# Initialize Flask application
app = Flask(__name__,
            static_folder="static",
            template_folder="templates")

# Setup paths
base_dir = Path(__file__).resolve().parent
papers_dir = base_dir / "data" / "papers"
graphs_dir = base_dir / "data" / "graphs"
global_graph_path = graphs_dir / "global_graph.graphml"

# Initialize retrievers on startup
print("\n[Startup] Initializing RAG search indices and loading Knowledge Graph...")
ingestion_pipeline = IngestionPipeline()
rag_retriever = RetrievalPipeline()
if not rag_retriever.index_exists():
    print("[Startup] Vector database index not found. Running ingestion pipeline...")
    ingestion_pipeline.run()

graph_retriever = GraphRetriever(global_graph_path)

# Initialize Query Orchestrator
orchestrator = QueryOrchestrator(
    rag_retriever=rag_retriever,
    graph_rag_retriever=graph_retriever
)
print("[Startup] RAG Orchestrator successfully initialized.")

@app.route("/")
def index():
    """Serve the clean chat interface."""
    return render_template("index.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    """
    POST route to process chat messages using the live GraphRAG system.
    Expects json payload: {"message": "..."}
    """
    try:
        data = request.get_json() or {}
        user_message = data.get("message", "").strip()
        model_choice = data.get("model", "llama-3.3-70b-versatile").lower()

        if not user_message:
            return jsonify({"error": "Message content cannot be empty."}), 400

        print(f"\n[API Chat] Processing query: '{user_message}' using model: '{model_choice}'")
        
        # Dynamically switch LLM provider based on dropdown selection
        try:
            from llm.provider.factory import get_provider
            
            if model_choice.startswith(("llama", "qwen", "openai")):
                provider_name = "groq"
                model_id = model_choice
            else:
                provider_name = "gemini"
                model_id = "gemini-2.5-flash"
                
            current_provider = orchestrator.llm_client.provider
            expected_class = "GroqProvider" if provider_name == "groq" else "GeminiProvider"
            if current_provider.__class__.__name__ != expected_class or current_provider.model != model_id:
                orchestrator.llm_client.provider = get_provider(provider_name, model_id)
        except Exception as provider_err:
            error_msg = f"⚠️ Error: Failed to load selected model '{model_choice}'. Details: {str(provider_err)}"
            return jsonify({
                "answer": error_msg,
                "status": "success"
            })

        # Run orchestrator
        response = orchestrator.run(user_message)
        
        route = response.get("route", "UNKNOWN")
        reasoning = response.get("reasoning", "")
        answer = response.get("answer", "")
        active_model = getattr(orchestrator.llm_client, "active_model", "Gemini")

        # Compile rich Markdown debug trace
        trace_md = []
        trace_md.append("\n***\n")
        trace_md.append("<details>")
        trace_md.append("<summary>🔍 Routing & Retrieval Details</summary>\n")
        
        trace_md.append("### 🛠️ Execution Metadata")
        trace_md.append(f"* **Route Chosen:** `{route}`")
        trace_md.append(f"* **Reasoning:** *{reasoning}*")
        trace_md.append(f"* **Active Model:** `{active_model}`\n")

        # Check for Graph RAG Trace details
        graph_result = response.get("graph_result")
        if graph_result and hasattr(graph_result, "retrieval_trace"):
            trace = graph_result.retrieval_trace
            trace_md.append("### 🕸️ Graph Retrieval Metrics")
            
            # Matched seeds
            matched_seeds = trace.get("matched_seeds", {})
            if matched_seeds:
                seeds_list = ", ".join([f"`{k}` ({v:.2f})" for k, v in matched_seeds.items()])
                trace_md.append(f"* **Resolved Seeds:** {seeds_list}")
            
            # Query Intent
            trace_md.append(f"* **Detected Intent:** `{trace.get('detected_intent', 'Unknown')}`")
            
            # Statistics
            stats = trace.get("statistics", {})
            trace_md.append(f"* **Traversal Latency:** `{stats.get('traversal_latency_ms', 0.0):.2f} ms`")
            trace_md.append(f"* **Graph Nodes Visited:** `{stats.get('nodes_visited', 0)}`")
            trace_md.append(f"* **Graph Nodes Retained:** `{stats.get('nodes_retained', 0)}`")
            trace_md.append(f"* **Graph Edges Retained:** `{stats.get('edges_retained', 0)}` \n")

            # Ranked nodes
            ranked_nodes = trace.get("ranked_nodes", [])
            if ranked_nodes:
                ranked_list = ", ".join([f"`{node_id}` ({score:.2f})" for node_id, score in ranked_nodes[:5]])
                trace_md.append(f"**Top Ranked Nodes:** {ranked_list}\n")

        # Check for Vector RAG Snip details (if RAG ran)
        if route in ["RAG", "COMBINED"] and response.get("rag_context"):
            trace_md.append("### 📄 Vector RAG Source Snippets")
            context_str = response.get("rag_context", "").strip()
            # Split snippets to format them in the details block
            snippets = context_str.split("\n\n---\n\n")
            for idx, snip in enumerate(snippets[:4], 1):
                # Clean up display text
                clean_snip = snip.replace("\n", "\n> ").strip()
                trace_md.append(f"**Snippet {idx}:**\n> {clean_snip}\n")
                
        trace_md.append("</details>")
        
        # Combine the actual LLM answer with the markdown details block
        final_answer_markdown = answer + "\n" + "\n".join(trace_md)

        # Extract graph trace nodes/edges for UI visualization path highlighting
        path_nodes = []
        path_edges = []
        if graph_result and hasattr(graph_result, "retrieval_trace"):
            trace = graph_result.retrieval_trace
            ranked = trace.get("ranked_nodes", [])
            # Map top nodes
            for node_id, score in ranked:
                if node_id in graph_retriever.graph:
                    node_data = graph_retriever.graph.nodes[node_id]
                    path_nodes.append({
                        "id": node_id,
                        "label": node_data.get("name") or node_data.get("title") or node_id,
                        "type": node_data.get("type", "Unknown"),
                        "score": score
                    })
            # Map paths
            node_paths = trace.get("node_paths", {})
            for target_nid, path_links in node_paths.items():
                for link in path_links:
                    if len(link) == 3:
                        u, v, rel = link
                        path_edges.append({
                            "source": u,
                            "target": v,
                            "relationship": rel
                        })

        return jsonify({
            "answer": final_answer_markdown,
            "status": "success",
            "path_nodes": path_nodes,
            "path_edges": path_edges
        })

    except Exception as e:
        print(f"[API Chat] Error: {str(e)}", file=sys.stderr)
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route("/api/graph/data")
def graph_data():
    """Retrieve full knowledge graph data for interactive visualization."""
    try:
        g = graph_retriever.graph
        nodes = []
        edges = []
        
        for node_id, data in g.nodes(data=True):
            # Fall back to abstract or summary details for description values
            desc = data.get("description") or data.get("abstract") or f"Entity Node of type {data.get('type')}"
            nodes.append({
                "id": node_id,
                "label": data.get("name") or data.get("title") or node_id,
                "type": data.get("type", "Unknown"),
                "description": desc,
                "degree": g.degree(node_id)
            })
            
        for u, v, data in g.edges(data=True):
            edges.append({
                "from": u,
                "to": v,
                "relationship": data.get("relationship", "RELATED_TO"),
                "confidence": data.get("confidence", 1.0)
            })
            
        return jsonify({
            "nodes": nodes,
            "edges": edges
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/graph/generate_description", methods=["POST"])
def generate_description():
    """Use a lightweight LLM on Groq to fill in node description attributes using RAG contexts."""
    try:
        data = request.get_json() or {}
        node_id = data.get("node_id")
        node_type = data.get("type", "Entity")
        node_label = data.get("label", node_id)
        
        if not node_id:
            return jsonify({"error": "Node ID is required."}), 400

        # Retrieve localized vector snippets for context grounding
        context = ""
        try:
            raw_context = rag_retriever.run(f"Explain or define what {node_label} is in the context of research literature.")
            if isinstance(raw_context, dict) and "retrieved_chunks" in raw_context:
                from context_builder import build_context
                llm_context_data = build_context(raw_context)
                context = "\n".join([item.get("content", "") for item in llm_context_data.get("context", [])])
            else:
                context = str(raw_context)
        except Exception as e:
            print(f"[Generate Description] Context retrieval warning: {e}")

        # Instantiate a lightweight model specifically for node explanations
        from llm.provider.factory import get_provider
        desc_provider = get_provider(name="groq", model="llama-3.1-8b-instant")
        
        prompt = f"""You are a lightweight metadata summarizer. 
Write a clear, concise definition or summary of the following entity. 
Ensure the summary is grounded ONLY in the retrieved document text below. 
Do not speculate, and do not write introductory remarks like "Here is the summary".
Write exactly 2 to 3 sentences.

Entity: {node_label} (Type: {node_type})

Document Context:
---
{context}
---

Definition/Summary:"""
        
        description_text = desc_provider.generate(prompt, temperature=0.2).strip()
        
        # Save back into live memory graph
        g = graph_retriever.graph
        if node_id in g:
            g.nodes[node_id]["description"] = description_text
            
            # Persist to local GraphML file database
            try:
                import networkx as nx
                nx.write_graphml(g, global_graph_path)
                print(f"[Generate Description] Successfully updated and persisted node '{node_id}' description.")
            except Exception as save_err:
                print(f"[Generate Description] Disk persist error: {save_err}")
                
        return jsonify({
            "status": "success",
            "description": description_text
        })
    except Exception as e:
        import traceback
        print("[Generate Description] Critical Endpoint Error:", file=sys.stderr)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/graph/chat", methods=["POST"])
def graph_node_chat():
    """Contextual chat interface focused around a single node with custom selected models."""
    try:
        data = request.get_json() or {}
        node_id = data.get("node_id")
        node_type = data.get("type", "Entity")
        node_label = data.get("label", node_id)
        user_message = data.get("message", "").strip()
        model_choice = data.get("model", "llama-3.3-70b-versatile").lower()

        if not node_id or not user_message:
            return jsonify({"error": "Node ID and message are required."}), 400

        print(f"\n[Graph Chat] Querying '{node_label}' connections: '{user_message}' using model: '{model_choice}'")

        # 1. Fetch relational context from the graph database
        relationships_context = []
        g = graph_retriever.graph
        if node_id in g:
            # Outbound connections
            for u, v, rdata in g.out_edges(node_id, data=True):
                target_name = g.nodes[v].get("name") or g.nodes[v].get("title") or v
                relationships_context.append(f"- {node_label} --[{rdata.get('relationship', 'RELATED_TO')}]--> {target_name}")
            # Inbound connections
            for u, v, rdata in g.in_edges(node_id, data=True):
                source_name = g.nodes[u].get("name") or g.nodes[u].get("title") or u
                relationships_context.append(f"- {source_name} --[{rdata.get('relationship', 'RELATED_TO')}]--> {node_label}")

        rels_str = "\n".join(relationships_context) if relationships_context else "No direct relational links found in graph ontology."

        # 2. Fetch document snippet context
        text_context = ""
        try:
            # Call the RetrievalPipeline 'run' method
            raw_context = rag_retriever.run(f"Explain how {node_label} relates to other entities in: {user_message}")
            
            # Check if output is a dict containing retrieved_chunks or needs parsing
            if isinstance(raw_context, dict) and "retrieved_chunks" in raw_context:
                from context_builder import build_context
                llm_context_data = build_context(raw_context)
                text_context = "\n".join([item.get("content", "") for item in llm_context_data.get("context", [])])
            elif isinstance(raw_context, str):
                try:
                    # In case raw_context is a JSON string return
                    parsed = json.loads(raw_context)
                    if isinstance(parsed, dict) and "retrieved_chunks" in parsed:
                        from context_builder import build_context
                        llm_context_data = build_context(parsed)
                        text_context = "\n".join([item.get("content", "") for item in llm_context_data.get("context", [])])
                    else:
                        text_context = raw_context
                except Exception:
                    text_context = raw_context
            else:
                text_context = str(raw_context)
        except Exception as e:
            print(f"[Graph Chat] Text context retrieval warning: {e}")
            text_context = "No relevant text documents found."

        # 3. Instantiate the selected model provider dynamically
        from llm.provider.factory import get_provider
        if model_choice.startswith(("llama", "qwen", "openai")):
            provider_name = "groq"
            model_id = model_choice
        else:
            provider_name = "gemini"
            model_id = "gemini-2.5-flash"

        chat_provider = get_provider(name=provider_name, model=model_id)

        prompt = f"""You are an expert AI research assistant.
Answer the user's question about the entity "{node_label}" ({node_type}) and its connections in the research literature.
Answer the query directly and concisely using the provided context. If the answer cannot be found in the context, say so.

Direct Knowledge Graph Connections:
{rels_str}

Relevant Document Excerpts:
---
{text_context}
---

User Question: {user_message}
Answer:"""

        answer_text = chat_provider.generate(prompt, temperature=0.3).strip()

        return jsonify({
            "status": "success",
            "answer": answer_text
        })
    except Exception as e:
        import traceback
        print("[Graph Chat] Critical Endpoint Error:", file=sys.stderr)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("Starting Flask server on http://127.0.0.1:5000 ...")
    app.run(host="127.0.0.1", port=5000, debug=True)
