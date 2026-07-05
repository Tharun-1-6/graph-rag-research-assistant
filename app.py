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
        model_choice = data.get("model", "gemini").lower()

        if not user_message:
            return jsonify({"error": "Message content cannot be empty."}), 400

        print(f"\n[API Chat] Processing query: '{user_message}' using model: '{model_choice}'")
        
        # Dynamically switch LLM provider based on dropdown selection
        try:
            from llm.provider.factory import get_provider
            
            if model_choice.startswith(("llama", "mixtral", "gemma")):
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

        return jsonify({
            "answer": final_answer_markdown,
            "status": "success"
        })

    except Exception as e:
        print(f"[API Chat] Error: {str(e)}", file=sys.stderr)
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

if __name__ == "__main__":
    print("Starting Flask server on http://127.0.0.1:5000 ...")
    app.run(host="127.0.0.1", port=5000, debug=True)
